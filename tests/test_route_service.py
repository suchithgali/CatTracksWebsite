from src.route_service import find_route
from src.transit_graph import build_graph


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
