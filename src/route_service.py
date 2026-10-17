from __future__ import annotations

from functools import lru_cache

import networkx as nx

from src.road_routing import route_geometry
from src.transit_graph import build_graph, normalize_stop_name


class RouteError(ValueError):
    pass


@lru_cache(maxsize=1)
def get_graph() -> nx.MultiDiGraph:
    return build_graph()


def _stop_ids_by_name(graph: nx.MultiDiGraph, name: str) -> list[str]:
    target = normalize_stop_name(name)
    return [
        node
        for node, data in graph.nodes(data=True)
        if normalize_stop_name(data.get("name", "")) == target
    ]


def _best_path(
    graph: nx.MultiDiGraph,
    origins: list[str],
    destinations: list[str],
) -> list[str]:
    best_path: list[str] | None = None
    best_weight: float | None = None

    for origin in origins:
        for destination in destinations:
            try:
                path = nx.shortest_path(graph, origin, destination, weight="weight")
                weight = nx.path_weight(graph, path, "weight")
            except nx.NetworkXNoPath:
                continue
            if best_weight is None or weight < best_weight:
                best_path = path
                best_weight = weight

    if best_path is None:
        raise RouteError("No route could be found between these stops.")
    return best_path


def find_route(
    from_stop: str,
    to_stop: str,
    graph: nx.MultiDiGraph | None = None,
) -> dict:
    graph = graph or get_graph()
    origins = _stop_ids_by_name(graph, from_stop)
    destinations = _stop_ids_by_name(graph, to_stop)

    if not origins:
        raise RouteError(f"Unknown starting stop: {from_stop}")
    if not destinations:
        raise RouteError(f"Unknown destination stop: {to_stop}")

    path = _best_path(graph, origins, destinations)
    segments = []
    total_time = 0
    total_distance = 0.0
    points = [
        {
            "name": graph.nodes[node]["name"],
            "latitude": graph.nodes[node]["latitude"],
            "longitude": graph.nodes[node]["longitude"],
        }
        for node in path
    ]

    for current, following in zip(path, path[1:]):
        edge_options = graph.get_edge_data(current, following)
        edge = min(edge_options.values(), key=lambda value: value["weight"])
        total_time += edge["travel_time"]
        total_distance += edge.get("distance_meters", 0)
        segment = {
            "mode": edge["mode"],
            "route": edge["route_name"],
            "from": graph.nodes[current]["name"],
            "to": graph.nodes[following]["name"],
            "travel_time": edge["travel_time"],
            "distance_meters": edge.get("distance_meters", 0),
        }
        if segments and segments[-1]["mode"] == segment["mode"] and (
            segments[-1].get("route") == segment.get("route")
        ):
            segments[-1]["to"] = segment["to"]
            segments[-1]["travel_time"] += segment["travel_time"]
            segments[-1]["distance_meters"] += segment["distance_meters"]
        else:
            segments.append(segment)

    road_route = route_geometry(points)

    return {
        "status": "ok",
        "from": from_stop,
        "to": to_stop,
        "duration_seconds": total_time,
        "distance_meters": round(total_distance, 1),
        "points": points,
        "geometry": road_route["geometry"],
        "geometry_source": road_route["source"],
        "stops": [graph.nodes[node]["name"] for node in path],
        "segments": segments,
    }
