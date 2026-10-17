from src.transit_graph import build_graph


def test_transit_graph_builds_despite_legacy_gtfs_time_values():
    graph = build_graph()

    assert graph.number_of_nodes() == 90
    assert graph.number_of_edges() > 0


def test_transit_edges_have_route_and_positive_travel_time():
    graph = build_graph()
    _, _, edge = next(iter(graph.edges(data=True)))

    assert edge["mode"] == "bus"
    assert edge["route_id"]
    assert edge["route_name"]
    assert edge["travel_time"] > 0


def test_graph_has_transfer_edges_for_shared_stop_names():
    graph = build_graph()
    transfer_edges = [
        data for _, _, data in graph.edges(data=True) if data["mode"] == "transfer"
    ]

    assert transfer_edges
