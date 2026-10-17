import pytest

from src.route_service import (
    RouteError,
    _routing_cost,
    find_custom_route,
    find_route,
)
from src.transit_graph import build_graph
from src.road_routing import geocode_location


def test_route_service_finds_a_route_using_transfers():
    result = find_route(
        "University Transit Center",
        "Merced Mall Target",
        build_graph(),
    )

    assert result["status"] == "ok"
    assert result["segments"]
    assert result["stops"][0] == "University Transit Center"
    assert result["stops"][-1] == "Merced Mall Target"
    assert any(segment["mode"] == "walk" for segment in result["segments"])
    assert result["geometry"]["type"] == "LineString"
    assert result["geometry"]["coordinates"]
    assert "directions" in result
    assert all(
        segment["from"] != segment["to"]
        for segment in result["segments"]
    )


def test_custom_route_adds_walking_legs(monkeypatch):
    monkeypatch.setattr(
        "src.route_service.geocode_location",
        lambda location: {
            "name": location,
            "latitude": 37.3612 if location == "custom start" else 37.335,
            "longitude": -120.4324 if location == "custom start" else -120.486,
        },
    )
    result = find_custom_route(
        "custom start",
        "custom destination",
        build_graph(),
    )

    assert result["status"] == "ok"
    assert result["segments"][0]["mode"] == "walk"
    assert result["segments"][-1]["mode"] == "walk"
    assert any(segment["mode"] == "bus" for segment in result["segments"])
    assert result["access_stops"]["from"]
    assert result["access_stops"]["to"]


def test_custom_route_does_not_geocode_a_known_stop(monkeypatch):
    def geocode(location):
        if location == "custom destination":
            return {
                "name": location,
                "latitude": 37.335,
                "longitude": -120.486,
            }
        raise AssertionError(f"Known stop was sent to geocoder: {location}")

    monkeypatch.setattr("src.route_service.geocode_location", geocode)
    result = find_custom_route(
        "Cardella Rd. & M St. (Southbound)",
        "custom destination",
        build_graph(),
    )

    assert result["status"] == "ok"
    assert result["from"] == "Cardella Rd. & M St. (Southbound)"


def test_distant_custom_route_uses_driving_access(monkeypatch):
    monkeypatch.setattr(
        "src.route_service.geocode_location",
        lambda location: {
            "name": location,
            "latitude": 37.5 if location == "far start" else 37.335,
            "longitude": -121.9 if location == "far start" else -120.486,
        },
    )
    result = find_custom_route("far start", "custom destination", build_graph())

    assert result["segments"][0]["mode"] == "drive"
    assert result["segments"][0]["route"] == "Driving"


def test_geocoder_rejects_locations_outside_merced(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"lat": "37.77", "lon": "-122.42"}]

    monkeypatch.setattr("src.road_routing.requests.get", lambda *args, **kwargs: Response())

    try:
        geocode_location("Rite Aid / Walgreens")
    except ValueError as error:
        assert "outside the Merced CatTracks service area" in str(error)
    else:
        raise AssertionError("Expected an outside-service-area geocode error")


def test_routing_cost_prioritizes_time_but_penalizes_transfers_and_walking():
    walk = {
        "mode": "walk",
        "travel_time": 600,
        "distance_meters": 840,
        "weight": 600,
    }
    transfer = {
        "mode": "transfer",
        "travel_time": 60,
        "distance_meters": 0,
        "weight": 60,
    }
    bus = {
        "mode": "bus",
        "travel_time": 300,
        "distance_meters": 3000,
        "weight": 300,
    }

    assert _routing_cost("a", "b", {"walk": walk}) > _routing_cost("a", "b", {"bus": bus})
    assert _routing_cost("a", "b", {"transfer": transfer}) > transfer["travel_time"]


def test_departure_time_uses_schedule_and_returns_elapsed_duration():
    result = find_route(
        "University Transit Center",
        "Merced Mall Target",
        build_graph(),
        departure_time="08:00",
    )

    assert result["status"] == "ok"
    assert result["departure_time"] == "08:00"
    assert result["duration_seconds"] >= 0
    assert "wait_seconds" in result
    assert "schedule_message" in result or result["wait_seconds"] > 0


def test_scheduled_custom_route_explains_when_no_bus_is_available(monkeypatch):
    monkeypatch.setattr(
        "src.route_service.geocode_location",
        lambda location: {
            "name": location,
            "latitude": 37.3561315,
            "longitude": -120.4833789,
        },
    )
    result = find_custom_route(
        "781 Irma Drive",
        "University Transit Center",
        build_graph(),
        departure_time="14:00",
    )

    assert result["schedule_message"].startswith("No scheduled bus connection")
    assert result["wait_seconds"] == 0


def test_route_graph_does_not_select_non_monotonic_bus_legs():
    graph = build_graph()

    for _, _, edge in graph.edges(data=True):
        if edge["mode"] != "bus":
            continue
        assert edge["arrival_time"] >= edge["departure_time"]


def test_legacy_routing_rejects_implausibly_long_walk_legs():
    with pytest.raises(RouteError, match="No route could be found"):
        find_route(
            "University Transit Center",
            "Merced Mall Target",
            build_graph(),
            max_walk_seconds=1_800,
        )
