from __future__ import annotations

from functools import lru_cache

import networkx as nx

from src.road_routing import geocode_location, route_between, route_geometry
from src.transit_graph import build_graph, normalize_stop_name


class RouteError(ValueError):
    pass

ACCESS_DRIVING_THRESHOLD_METERS = 1_600


def _distance_meters(first: dict, second: dict) -> float:
    latitude_distance = (first["latitude"] - second["latitude"]) * 111_000
    longitude_distance = (
        (first["longitude"] - second["longitude"]) * 111_000 * 0.8
    )
    return max((latitude_distance**2 + longitude_distance**2) ** 0.5, 1)


def _nearest_stop(graph: nx.MultiDiGraph, location: dict) -> str:
    return min(
        graph.nodes,
        key=lambda node: _distance_meters(
            location,
            {
                "latitude": graph.nodes[node]["latitude"],
                "longitude": graph.nodes[node]["longitude"],
            },
        ),
    )


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


def _route_for_path(
    graph: nx.MultiDiGraph,
    path: list[str],
    from_stop: str,
    to_stop: str,
) -> dict:
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
    return _route_for_path(graph, path, from_stop, to_stop)


def find_custom_route(
    from_location: str,
    to_location: str,
    graph: nx.MultiDiGraph | None = None,
) -> dict:
    """Route from arbitrary locations through the transit network."""
    graph = graph or get_graph()
    try:
        departure = geocode_location(from_location)
        destination = geocode_location(to_location)
    except ValueError as error:
        raise RouteError(str(error)) from error
    origin_stop = _nearest_stop(graph, departure)
    destination_stop = _nearest_stop(graph, destination)
    transit_path = _best_path(graph, [origin_stop], [destination_stop])
    transit_route = _route_for_path(
        graph,
        transit_path,
        graph.nodes[origin_stop]["name"],
        graph.nodes[destination_stop]["name"],
    )

    start_stop = {
        "name": graph.nodes[origin_stop]["name"],
        "latitude": graph.nodes[origin_stop]["latitude"],
        "longitude": graph.nodes[origin_stop]["longitude"],
    }
    end_stop = {
        "name": graph.nodes[destination_stop]["name"],
        "latitude": graph.nodes[destination_stop]["latitude"],
        "longitude": graph.nodes[destination_stop]["longitude"],
    }
    first_distance = _distance_meters(departure, start_stop)
    last_distance = _distance_meters(end_stop, destination)
    first_mode = "drive" if first_distance > ACCESS_DRIVING_THRESHOLD_METERS else "walk"
    last_mode = "drive" if last_distance > ACCESS_DRIVING_THRESHOLD_METERS else "walk"
    first_leg = route_between(departure, start_stop) if first_mode == "drive" else {}
    last_leg = route_between(end_stop, destination) if last_mode == "drive" else {}
    first_distance = first_leg.get("distance_meters", first_distance)
    last_distance = last_leg.get("distance_meters", last_distance)
    first_time = (
        int(first_leg.get("duration_seconds", first_distance / 13.4))
        if first_mode == "drive"
        else max(int(first_distance / 1.4), 1)
    )
    last_time = (
        int(last_leg.get("duration_seconds", last_distance / 13.4))
        if last_mode == "drive"
        else max(int(last_distance / 1.4), 1)
    )

    segments = []
    if first_distance > 1:
        segments.append({
            "mode": first_mode,
            "route": "Driving" if first_mode == "drive" else "Walking",
            "from": from_location,
            "to": start_stop["name"],
            "travel_time": first_time,
            "distance_meters": first_distance,
        })
    segments.extend(transit_route["segments"])
    if last_distance > 1:
        segments.append({
            "mode": last_mode,
            "route": "Driving" if last_mode == "drive" else "Walking",
            "from": end_stop["name"],
            "to": to_location,
            "travel_time": last_time,
            "distance_meters": last_distance,
        })
    points = [departure, *transit_route["points"], destination]
    road_route = route_geometry(points)

    return {
        **transit_route,
        "from": from_location,
        "to": to_location,
        "duration_seconds": transit_route["duration_seconds"] + first_time + last_time,
        "distance_meters": round(
            transit_route["distance_meters"] + first_distance + last_distance,
            1,
        ),
        "points": points,
        "geometry": road_route["geometry"],
        "geometry_source": road_route["source"],
        "segments": segments,
        "access_stops": {
            "from": start_stop["name"],
            "to": end_stop["name"],
        },
    }


def find_route_request(
    from_location: str,
    to_location: str,
    graph: nx.MultiDiGraph | None = None,
) -> dict:
    """Use stop names directly, or geocode arbitrary departure/destination text."""
    graph = graph or get_graph()
    if _stop_ids_by_name(graph, from_location) and _stop_ids_by_name(graph, to_location):
        return find_route(from_location, to_location, graph)
    return find_custom_route(from_location, to_location, graph)
