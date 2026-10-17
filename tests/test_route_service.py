from src.route_service import find_custom_route, find_route
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
