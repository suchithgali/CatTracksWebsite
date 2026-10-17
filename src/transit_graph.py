from __future__ import annotations

import re

import networkx as nx

from src.gtfs_loader import load_gtfs

def normalize_stop_name(value: str) -> str:
    return " ".join(str(value).lower().replace("&", "and").split())

def walking_time(first: dict, second: dict) -> int:
    distance = stop_distance_meters(first, second)
    return max(int(distance / 1.4), 1)


def stop_distance_meters(first: dict, second: dict) -> float:
    latitude_distance = (float(first["stop_lat"]) - float(second["stop_lat"])) * 111_000
    longitude_distance = (
        (float(first["stop_lon"]) - float(second["stop_lon"]))
        * 111_000
        * 0.8
    )
    return max((latitude_distance**2 + longitude_distance**2) ** 0.5, 1)

def gtfs_time_to_seconds(value: str) -> int:
    """Convert a GTFS HH:MM:SS value to seconds.

    GTFS allows hours greater than 23, such as 25:15:00.
    """
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds

def _stop_number(stop_id: str) -> tuple[str, int] | None:
    match = re.fullmatch(r"(.+?)_(\d+)", stop_id)
    return (match.group(1), int(match.group(2))) if match else None

def _complete_trip_stop_times(
    rows: list[dict],
    stop_lookup: dict[str, dict],
) -> list[dict]:
    """Restore route stops omitted from otherwise numbered trip sequences."""
    if not rows:
        return rows
    completed: list[dict] = []
    for current, following in zip(rows, rows[1:]):
        completed.append(current)
        current_number = _stop_number(current["stop_id"])
        following_number = _stop_number(following["stop_id"])
        if (
            not current_number
            or not following_number
            or current_number[0] != following_number[0]
            or following_number[1] - current_number[1] <= 1
        ):
            continue

        departure = gtfs_time_to_seconds(current["departure_time"])
        arrival = gtfs_time_to_seconds(following["arrival_time"])
        if arrival < departure:
            continue
        missing_count = following_number[1] - current_number[1] - 1
        interval = (arrival - departure) / (missing_count + 1)
        for offset in range(1, missing_count + 1):
            stop_id = f"{current_number[0]}_{current_number[1] + offset}"
            if stop_id not in stop_lookup:
                continue
            timestamp = int(round(departure + interval * offset))
            completed.append(
                {
                    "trip_id": current["trip_id"],
                    "stop_id": stop_id,
                    "stop_sequence": int(current["stop_sequence"]) + offset,
                    "arrival_time": str(timestamp),
                    "departure_time": str(timestamp),
                    "_time_seconds": timestamp,
                }
            )
    completed.append(rows[-1])
    last_number = _stop_number(rows[-1]["stop_id"])
    if last_number:
        route_stop_numbers = sorted(
            number
            for stop_id in stop_lookup
            if (parsed := _stop_number(stop_id))
            and parsed[0] == last_number[0]
            for number in [parsed[1]]
        )
        missing_after = [
            number for number in route_stop_numbers if number > last_number[1]
        ]
        if missing_after:
            previous = rows[-2] if len(rows) > 1 else rows[-1]
            interval = max(
                gtfs_time_to_seconds(rows[-1]["departure_time"])
                - gtfs_time_to_seconds(previous["departure_time"]),
                60,
            )
            departure = gtfs_time_to_seconds(rows[-1]["departure_time"])
            for offset, number in enumerate(missing_after, start=1):
                timestamp = departure + interval * offset
                stop_id = f"{last_number[0]}_{number}"
                completed.append(
                    {
                        "trip_id": rows[-1]["trip_id"],
                        "stop_id": stop_id,
                        "stop_sequence": int(rows[-1]["stop_sequence"]) + offset,
                        "arrival_time": _seconds_to_gtfs_time(timestamp),
                        "departure_time": _seconds_to_gtfs_time(timestamp),
                    }
                )
    for row in completed:
        if "_time_seconds" in row:
            row["arrival_time"] = _seconds_to_gtfs_time(row["_time_seconds"])
            row["departure_time"] = row["arrival_time"]
    return completed

def _seconds_to_gtfs_time(value: int) -> str:
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def build_transit_graph(feed: dict[str, list[dict]]) -> nx.MultiDiGraph:
    """Build a directed transit graph from a GTFS feed."""
    stops = feed["stops"]
    routes = feed["routes"]
    trips = feed["trips"]
    stop_times = feed["stop_times"]

    stop_lookup = {stop["stop_id"]: stop for stop in stops}
    route_lookup = {route["route_id"]: route["route_short_name"] for route in routes}

    graph = nx.MultiDiGraph()

    for stop_id, stop in stop_lookup.items():
        graph.add_node(
            stop_id,
            name=stop["stop_name"],
            latitude=float(stop["stop_lat"]),
            longitude=float(stop["stop_lon"]),
            mode="bus_stop",
        )

    trip_routes = {trip["trip_id"]: trip["route_id"] for trip in trips}

    trips_by_id: dict[str, list[dict]] = {}
    for stop_time in stop_times:
        trips_by_id.setdefault(stop_time["trip_id"], []).append(stop_time)

    for trip_id, trip_stop_times in trips_by_id.items():
        ordered = sorted(trip_stop_times, key=lambda row: row["stop_sequence"])
        ordered = _complete_trip_stop_times(ordered, stop_lookup)
        route_id = trip_routes[trip_id]
        route_name = route_lookup.get(route_id, route_id)

        rows = ordered

        for current, following in zip(rows, rows[1:]):
            departure = gtfs_time_to_seconds(current["departure_time"])
            arrival = gtfs_time_to_seconds(following["arrival_time"])

            if current["stop_id"] not in stop_lookup:
                raise ValueError(f"Unknown stop ID: {current['stop_id']}")

            if following["stop_id"] not in stop_lookup:
                raise ValueError(f"Unknown stop ID: {following['stop_id']}")

            # A malformed stop-time pair cannot represent a usable trip leg.
            # Keeping it with a one-second fallback makes static routing prefer
            # an impossible bus over a valid scheduled or walking connection.
            if arrival < departure:
                continue

            edge_data = {
                "mode": "bus",
                "trip_id": trip_id,
                "route_id": route_id,
                "route_name": route_name,
                "departure_time": current["departure_time"],
                "arrival_time": following["arrival_time"],
                "travel_time": max(arrival - departure, 1),
                "distance_meters": stop_distance_meters(
                    stop_lookup[current["stop_id"]],
                    stop_lookup[following["stop_id"]],
                ),
                "weight": max(arrival - departure, 1),
            }
            graph.add_edge(current["stop_id"], following["stop_id"], **edge_data)
            graph.add_edge(following["stop_id"], current["stop_id"], **edge_data)

    stops_by_name: dict[str, list[str]] = {}
    for stop_id, stop in stop_lookup.items():
        key = normalize_stop_name(stop["stop_name"])
        stops_by_name.setdefault(key, []).append(stop_id)

    for stop_ids in stops_by_name.values():
        for current in stop_ids:
            for following in stop_ids:
                if current == following:
                    continue
                graph.add_edge(
                    current,
                    following,
                    mode="transfer",
                    route_id="",
                    route_name="Transfer",
                    travel_time=60,
                    distance_meters=0,
                    weight=60,
                )

    stop_items = list(stop_lookup.items())
    for current_id, current in stop_items:
        for following_id, following in stop_items:
            if current_id == following_id or normalize_stop_name(
                current["stop_name"]
            ) == normalize_stop_name(following["stop_name"]):
                continue
            travel_time = walking_time(current, following)
            graph.add_edge(
                current_id,
                following_id,
                mode="walk",
                route_id="",
                route_name="Walking",
                travel_time=travel_time,
                distance_meters=stop_distance_meters(current, following),
                weight=travel_time,
            )

    return graph

def build_graph() -> nx.MultiDiGraph:
    """Load GTFS data and build the transit graph."""
    return build_transit_graph(load_gtfs())

if __name__ == "__main__":
    graph = build_graph()

    print(f"Nodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")