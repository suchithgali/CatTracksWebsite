from __future__ import annotations

from functools import lru_cache
import heapq
import math

import networkx as nx

from src.road_routing import geocode_location, route_between, route_geometry
from src.transit_graph import build_graph, normalize_stop_name


class RouteError(ValueError):
    pass

ACCESS_DRIVING_THRESHOLD_METERS = 1_600
TRANSFER_PENALTY_SECONDS = 120
WALKING_DISTANCE_PENALTY = 0.15
TRANSIT_DISTANCE_PENALTY = 0.02
LEGACY_MAX_WALK_SECONDS = 1_800


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


def _routing_cost(_from: str, _to: str, edge_options: dict) -> float:
    """Balance arrival time, walking burden, distance, and transfers."""
    edge = min(edge_options.values(), key=lambda value: value["weight"])
    distance = float(edge.get("distance_meters", 0))
    cost = float(edge["travel_time"])
    if edge["mode"] == "transfer":
        cost += TRANSFER_PENALTY_SECONDS
    elif edge["mode"] == "walk":
        cost += distance * WALKING_DISTANCE_PENALTY
    elif edge["mode"] == "bus":
        cost += distance * TRANSIT_DISTANCE_PENALTY
    return cost


def _static_edge_cost(
    current: str,
    following: str,
    edge_options: dict,
    max_walk_seconds: int | None,
) -> float:
    edge = min(edge_options.values(), key=lambda value: value["weight"])
    if (
        max_walk_seconds is not None
        and edge["mode"] == "walk"
        and edge["travel_time"] > max_walk_seconds
    ):
        return math.inf
    return _routing_cost(current, following, edge_options)


def _time_to_seconds(value: str) -> int:
    try:
        hours, minutes = (int(part) for part in value.split(":")[:2])
    except (TypeError, ValueError) as error:
        raise RouteError("Departure time must use HH:MM format.") from error
    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        raise RouteError("Departure time must use HH:MM format.")
    return hours * 3600 + minutes * 60


def _gtfs_time_seconds(value: str) -> int:
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def _clock_time(seconds: int) -> str:
    return f"{(seconds // 3600) % 24:02d}:{(seconds % 3600) // 60:02d}"


def _schedule_summary(
    graph: nx.MultiDiGraph,
    path: list[str],
    selected_edges: list[dict],
    departure_seconds: int,
) -> dict[str, object]:
    current_time = departure_seconds
    wait_seconds = 0
    bus_edges = 0
    first_wait: tuple[int, str, str] | None = None
    for current, edge in zip(path, selected_edges):
        if edge["mode"] == "bus":
            bus_edges += 1
            bus_departure = _gtfs_time_seconds(edge["departure_time"])
            if bus_departure > current_time and first_wait is None:
                first_wait = (
                    bus_departure - current_time,
                    graph.nodes[current]["name"],
                    edge["route_name"],
                )
            wait_seconds += max(bus_departure - current_time, 0)
            current_time = _gtfs_time_seconds(edge["arrival_time"])
        else:
            current_time += edge["travel_time"]

    if first_wait:
        seconds, stop_name, route_name = first_wait
        return {
            "wait_seconds": wait_seconds,
            "schedule_message": (
                f"Wait {max(1, round(seconds / 60))} min at {stop_name} "
                f"for {route_name}, departing at "
                f"{_clock_time(departure_seconds + seconds)}."
            ),
        }
    if bus_edges == 0:
        return {
            "wait_seconds": 0,
            "schedule_message": (
                "No scheduled bus connection was found after your departure "
                "time; walking is the available route."
            ),
        }
    return {"wait_seconds": wait_seconds}


def _scheduled_edge(edge_options: dict, current_time: int) -> tuple[dict, int] | None:
    candidates = []
    for edge in edge_options.values():
        if edge["mode"] != "bus":
            candidates.append((current_time + edge["travel_time"], edge))
            continue
        departure = _gtfs_time_seconds(edge["departure_time"])
        arrival = _gtfs_time_seconds(edge["arrival_time"])
        if departure >= current_time and arrival >= departure:
            candidates.append((arrival, edge))
    return min(candidates, key=lambda item: item[0]) if candidates else None


def _best_scheduled_path(
    graph: nx.MultiDiGraph,
    origins: list[str],
    destinations: list[str],
    departure_seconds: int,
) -> tuple[list[str], int, list[dict]]:
    best: dict[str, tuple[int, float, list[str]]] = {}
    queue = [
        (departure_seconds, 0.0, origin, [origin], [])
        for origin in origins
    ]
    while queue:
        arrival, score, current, path, selected_edges = heapq.heappop(queue)
        previous = best.get(current)
        if previous and (arrival, score) >= previous[:2]:
            continue
        best[current] = (arrival, score, path)
        if current in destinations:
            return path, arrival, selected_edges
        for following in graph.successors(current):
            scheduled = _scheduled_edge(
                graph.get_edge_data(current, following),
                arrival,
            )
            if scheduled is None:
                continue
            next_arrival, edge = scheduled
            next_score = score + _routing_cost(
                current,
                following,
                graph.get_edge_data(current, following),
            )
            heapq.heappush(
                queue,
                (
                    next_arrival,
                    next_score,
                    following,
                    [*path, following],
                    [*selected_edges, edge],
                ),
            )
    raise RouteError("No route is available after the selected departure time.")


def _best_path(
    graph: nx.MultiDiGraph,
    origins: list[str],
    destinations: list[str],
    max_walk_seconds: int | None = None,
) -> list[str]:
    best_path: list[str] | None = None
    best_weight: float | None = None

    for origin in origins:
        for destination in destinations:
            try:
                path = nx.shortest_path(
                    graph,
                    origin,
                    destination,
                    weight=lambda current, following, options: _static_edge_cost(
                        current,
                        following,
                        options,
                        max_walk_seconds,
                    ),
                )
                weight = sum(
                    _static_edge_cost(
                        current,
                        following,
                        graph.get_edge_data(current, following),
                        max_walk_seconds,
                    )
                    for current, following in zip(path, path[1:])
                )
                if not math.isfinite(weight):
                    continue
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
    selected_edges: list[dict] | None = None,
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

    for edge_index, (current, following) in enumerate(zip(path, path[1:])):
        edge = (
            selected_edges[edge_index]
            if selected_edges is not None
            else min(
                graph.get_edge_data(current, following).values(),
                key=lambda value: value["weight"],
            )
        )
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
        if segment["from"] == segment["to"]:
            continue
        if segments and segments[-1]["mode"] == segment["mode"] and (
            segments[-1].get("route") == segment.get("route")
        ):
            segments[-1]["to"] = segment["to"]
            segments[-1]["travel_time"] += segment["travel_time"]
            segments[-1]["distance_meters"] += segment["distance_meters"]
        else:
            segments.append(segment)

    road_route = route_geometry(points)
    segments = [
        segment
        for segment in segments
        if segment["from"] != segment["to"]
    ]
    return {
        "status": "ok",
        "from": from_stop,
        "to": to_stop,
        "duration_seconds": total_time,
        "distance_meters": round(total_distance, 1),
        "points": points,
        "geometry": road_route["geometry"],
        "geometry_source": road_route["source"],
        "directions": road_route.get("directions", []),
        "stops": [graph.nodes[node]["name"] for node in path],
        "segments": segments,
    }


def find_route(
    from_stop: str,
    to_stop: str,
    graph: nx.MultiDiGraph | None = None,
    departure_time: str | None = None,
    max_walk_seconds: int | None = None,
) -> dict:
    graph = graph or get_graph()
    origins = _stop_ids_by_name(graph, from_stop)
    destinations = _stop_ids_by_name(graph, to_stop)

    if not origins:
        raise RouteError(f"Unknown starting stop: {from_stop}")
    if not destinations:
        raise RouteError(f"Unknown destination stop: {to_stop}")

    if departure_time:
        departure_seconds = _time_to_seconds(departure_time)
        path, arrival_seconds, selected_edges = _best_scheduled_path(
            graph, origins, destinations, departure_seconds
        )
        route = _route_for_path(
            graph,
            path,
            from_stop,
            to_stop,
            selected_edges,
        )
        route["duration_seconds"] = arrival_seconds - departure_seconds
        route["departure_time"] = departure_time
        route.update(
            _schedule_summary(
                graph,
                path,
                selected_edges,
                departure_seconds,
            )
        )
        return route
    path = _best_path(graph, origins, destinations, max_walk_seconds)
    return _route_for_path(graph, path, from_stop, to_stop)


def find_custom_route(
    from_location: str,
    to_location: str,
    graph: nx.MultiDiGraph | None = None,
    departure_time: str | None = None,
    max_walk_seconds: int | None = None,
) -> dict:
    """Route from arbitrary locations through the transit network."""
    graph = graph or get_graph()
    try:
        departure = _location_for_input(graph, from_location)
        destination = _location_for_input(graph, to_location)
    except ValueError as error:
        raise RouteError(str(error)) from error
    origin_stop = _nearest_stop(graph, departure)
    destination_stop = _nearest_stop(graph, destination)
    departure_seconds = _time_to_seconds(departure_time) if departure_time else None
    access_seconds = 0
    selected_edges = None
    if departure_seconds is not None:
        access_distance = _distance_meters(departure, {
            "latitude": graph.nodes[origin_stop]["latitude"],
            "longitude": graph.nodes[origin_stop]["longitude"],
        })
        access_seconds = max(
            int(
                access_distance
                / (13.4 if access_distance > ACCESS_DRIVING_THRESHOLD_METERS else 1.4)
            ),
            1,
        )
        transit_path, scheduled_arrival, selected_edges = _best_scheduled_path(
            graph,
            [origin_stop],
            [destination_stop],
            departure_seconds + access_seconds,
        )
    else:
        transit_path = _best_path(
            graph,
            [origin_stop],
            [destination_stop],
            max_walk_seconds,
        )
        scheduled_arrival = None
    transit_route = _route_for_path(
        graph,
        transit_path,
        graph.nodes[origin_stop]["name"],
        graph.nodes[destination_stop]["name"],
        selected_edges,
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

    result = {
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
        "directions": road_route.get("directions", []),
        "segments": segments,
        "access_stops": {
            "from": start_stop["name"],
            "to": end_stop["name"],
        },
    }
    if departure_time:
        result["departure_time"] = departure_time
        result["duration_seconds"] = scheduled_arrival - departure_seconds
        result.update(
            _schedule_summary(
                graph,
                transit_path,
                selected_edges or [],
                departure_seconds + access_seconds,
            )
        )
    return result


def _location_for_input(graph: nx.MultiDiGraph, location: str) -> dict:
    """Resolve a stop name from the graph before using external geocoding."""
    stop_ids = _stop_ids_by_name(graph, location)
    if stop_ids:
        stop = graph.nodes[stop_ids[0]]
        return {
            "name": location,
            "latitude": stop["latitude"],
            "longitude": stop["longitude"],
        }
    return geocode_location(location)


def find_route_request(
    from_location: str,
    to_location: str,
    graph: nx.MultiDiGraph | None = None,
    departure_time: str | None = None,
    max_walk_seconds: int | None = None,
) -> dict:
    """Use stop names directly, or geocode arbitrary departure/destination text."""
    graph = graph or get_graph()
    if _stop_ids_by_name(graph, from_location) and _stop_ids_by_name(graph, to_location):
        return find_route(
            from_location,
            to_location,
            graph,
            departure_time,
            max_walk_seconds,
        )
    return find_custom_route(
        from_location,
        to_location,
        graph,
        departure_time,
        max_walk_seconds,
    )
