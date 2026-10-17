from website.app import app


def test_pages_and_health_endpoint():
    app.config.update(TESTING=True)
    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/plan").status_code == 200
    assert client.get("/planner").status_code == 200
    assert client.get("/schedules").status_code == 200
    assert client.get("/contact").status_code == 200
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_schedules_page_uses_official_uc_merced_schedule_links():
    response = app.test_client().get("/schedules")

    assert response.status_code == 200
    assert b"Fall 2026 service" in response.data
    assert b"https://taps.ucmerced.edu/node/4821" in response.data
    assert b"m-1_fall_2025_8_18_2025.pdf" in response.data


def test_planner_rejects_unknown_stops():
    app.config.update(TESTING=True)
    response = app.test_client().post(
        "/plan",
        data={"from-stops": "not a stop", "to-stops": "also not a stop"},
    )
    assert response.status_code == 200
    assert b'id="planner-app"' in response.data
    assert b'planner.js' in response.data


def test_route_api_returns_route():
    response = app.test_client().post(
        "/api/route",
        json={
            "from": "University Transit Center",
            "to": "Merced Mall Target",
        },
    )

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["segments"]
    assert response.json["distance_meters"] > 0
    assert response.json["points"]


def test_planner_renders_route_map_and_distance():
    response = app.test_client().post(
        "/plan",
        data={
            "from-stops": "University Transit Center",
            "to-stops": "Merced Mall Target",
        },
    )

    assert response.status_code == 200
    assert b'id="planner-app"' in response.data
    assert b'planner.js' in response.data
    assert b'"from": "University Transit Center"' in response.data
    assert b'"to": "Merced Mall Target"' in response.data
    assert b'"route":' in response.data


def test_live_routes_page_uses_official_tracker():
    response = app.test_client().get("/planner")

    assert response.status_code == 200
    assert b"Live bus locations" in response.data
    assert b"https://cattracks.ridesystems.net/routes" in response.data


def test_route_api_rejects_missing_stops():
    response = app.test_client().post("/api/route", json={})

    assert response.status_code == 400
    assert response.json["status"] == "error"


def test_network_offline_shows_legacy_banner_and_uses_static_routes(monkeypatch):
    monkeypatch.setenv("CATTRACKS_NETWORK_ONLINE", "false")
    client = app.test_client()

    page = client.get("/plan")
    assert b"CatTracks network offline" in page.data
    assert b"older version" in page.data
    assert b"status-offline" in page.data

    response = client.post(
        "/api/route",
        json={
            "from": "University Transit Center",
            "to": "Merced Mall Target",
            "departure_time": "08:00",
        },
    )
    assert response.status_code == 200
    assert "departure_time" not in response.json
