from website.app import app


def test_pages_and_health_endpoint():
    app.config.update(TESTING=True)
    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/planner").status_code == 200
    assert client.get("/schedules").status_code == 200
    assert client.get("/contact").status_code == 200
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_planner_rejects_unknown_stops():
    app.config.update(TESTING=True)
    response = app.test_client().post(
        "/planner",
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
        "/planner",
        data={
            "from-stops": "University Transit Center",
            "to-stops": "Merced Mall Target",
        },
    )

    assert response.status_code == 200
    assert b'id="planner-app"' in response.data
    assert b'planner.js' in response.data


def test_route_api_rejects_missing_stops():
    response = app.test_client().post("/api/route", json={})

    assert response.status_code == 400
    assert response.json["status"] == "error"
