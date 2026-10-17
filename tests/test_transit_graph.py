from src.transit_graph import build_graph, build_transit_graph


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


def test_graph_skips_non_monotonic_bus_legs():
    feed = {
        "stops": [
            {"stop_id": "a", "stop_name": "A", "stop_lat": "37.0", "stop_lon": "-120.0"},
            {"stop_id": "b", "stop_name": "B", "stop_lat": "37.001", "stop_lon": "-120.0"},
            {"stop_id": "c", "stop_name": "C", "stop_lat": "37.002", "stop_lon": "-120.0"},
        ],
        "routes": [{"route_id": "r", "route_short_name": "R"}],
        "trips": [{"trip_id": "valid", "route_id": "r"}, {"trip_id": "invalid", "route_id": "r"}],
        "stop_times": [
            {"trip_id": "valid", "stop_id": "a", "stop_sequence": "1", "departure_time": "08:00:00", "arrival_time": "08:00:00"},
            {"trip_id": "valid", "stop_id": "b", "stop_sequence": "2", "departure_time": "08:05:00", "arrival_time": "08:05:00"},
            {"trip_id": "invalid", "stop_id": "b", "stop_sequence": "1", "departure_time": "08:10:00", "arrival_time": "08:10:00"},
            {"trip_id": "invalid", "stop_id": "c", "stop_sequence": "2", "departure_time": "08:09:00", "arrival_time": "08:09:00"},
        ],
    }

    graph = build_transit_graph(feed)
    bus_edges = [
        edge for _, _, edge in graph.edges(data=True) if edge["mode"] == "bus"
    ]

    assert len(bus_edges) == 2
    assert all(
        edge["arrival_time"] >= edge["departure_time"] for edge in bus_edges
    )
