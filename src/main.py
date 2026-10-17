from __future__ import annotations

import math
import re
from pathlib import Path

import networkx as nx
import pandas as pd


def load_stop_lookup() -> dict[str, str]:
    stops_path = Path(__file__).resolve().parents[1] / "data" / "gtfs" / "stops.txt"
    stops = pd.read_csv(stops_path)
    return {
        str(row.stop_id): str(row.stop_name)
        for row in stops.itertuples(index=False)
        if pd.notna(row.stop_id) and pd.notna(row.stop_name)
    }


def load_routes_lookup() -> dict[str, str]:
    routes_path = Path(__file__).resolve().parents[1] / "data" / "gtfs" / "routes.txt"
    routes = pd.read_csv(routes_path)
    return {
        str(row.route_id): str(row.route_short_name)
        for row in routes.itertuples(index=False)
        if pd.notna(row.route_id) and pd.notna(row.route_short_name)
    }


def extract_bus_route(path: list[str], graph: nx.Graph) -> str | None:
    """Extract the bus route ID from a bus segment path."""
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = graph.get_edge_data(u, v)
        if isinstance(edge_data, dict) and edge_data.get("kind") == "bus":
            return str(edge_data.get("route_id", ""))
    return None


def attach_names_to_graph(graph: nx.Graph, stop_lookup: dict[str, str]) -> None:
    for node in graph.nodes:
        node_name = str(node)
        if node_name.startswith("bus_stop_"):
            stop_id = node_name.replace("bus_stop_", "", 1)
            graph.nodes[node]["name"] = stop_lookup.get(stop_id, stop_id)
            graph.nodes[node]["kind"] = "bus_stop"
            graph.nodes[node]["stop_id"] = stop_id
        elif node_name.startswith("street_"):
            street_name = graph.nodes[node].get("name")
            if street_name:
                graph.nodes[node]["name"] = str(street_name)
            else:
                graph.nodes[node]["name"] = f"Intersection {node_name}"
            graph.nodes[node]["kind"] = "street"
        else:
            graph.nodes[node]["name"] = node_name
            graph.nodes[node]["kind"] = "unknown"


def pretty_route(path: list[str], graph: nx.Graph) -> list[str]:
    names: list[str] = []
    last_name: str | None = None
    last_kind: str | None = None

    for node in path:
        raw_name = graph.nodes[node].get("name", str(node))
        name = str(raw_name).strip()
        kind = str(graph.nodes[node].get("kind", "unknown"))

        if not name:
            continue
        if name.startswith("Intersection "):
            continue
        if name == last_name and kind == last_kind:
            continue

        if kind == "bus_stop" and last_kind == "bus_stop" and last_name and name == last_name:
            continue

        names.append(name)
        last_name = name
        last_kind = kind

    return names


def segment_route(path: list[str], graph: nx.Graph) -> list[tuple[str, list[str], str]]:
    if not path:
        return []

    bus_indices = [
        idx for idx, node in enumerate(path)
        if str(graph.nodes[node].get("kind", "unknown")) == "bus_stop"
    ]

    segments: list[tuple[str, list[str], str]] = []

    if not bus_indices:
        return [("walk", path, "Walk to your destination")]

    first_bus_idx = bus_indices[0]
    last_bus_idx = bus_indices[-1]

    if first_bus_idx > 0:
        segments.append(("walk", path[: first_bus_idx + 1], "Walk to the first bus stop"))

    if last_bus_idx > first_bus_idx:
        bus_path = path[first_bus_idx : last_bus_idx + 1]
        segments.append(("bus", bus_path, "Transit directions on the bus"))

    if last_bus_idx < len(path) - 1:
        segments.append(("walk", path[last_bus_idx:], "Walk from the bus stop to your destination"))
    elif last_bus_idx == len(path) - 1 and last_bus_idx > first_bus_idx:
        segments.append(("walk", [path[last_bus_idx]], "Walk from the bus stop to your final destination"))

    if not segments:
        return [("walk", path, "Walk to your destination")]

    return segments


def route_mode_summary(section_type: str, path: list[str], graph: nx.Graph) -> list[str]:
    names = []
    for node in path:
        name = str(graph.nodes[node].get("name", str(node))).strip()
        if not name or name.startswith("Intersection "):
            continue
        names.append(name)

    if section_type == "bus":
        unique_names: list[str] = []
        seen: set[str] = set()
        for name in names:
            if name not in seen:
                unique_names.append(name)
                seen.add(name)
        return unique_names

    deduped: list[str] = []
    last_name: str | None = None
    for name in names:
        if name == last_name:
            continue
        deduped.append(name)
        last_name = name
    return deduped


def street_label(name: str) -> str:
    clean = str(name or "").strip()
    if not clean:
        return ""
    if clean.startswith("Intersection "):
        return ""
    if "/" in clean:
        parts = [part.strip() for part in clean.split("/") if part.strip()]
        clean = parts[0] if parts else clean
    if "(" in clean:
        clean = clean.split("(")[0].strip()
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def node_heading(graph: nx.Graph, a: str, b: str) -> float | None:
    edge = graph.get_edge_data(a, b)
    if isinstance(edge, dict) and "heading" in edge:
        return float(edge["heading"])

    a_attrs = graph.nodes.get(a, {})
    b_attrs = graph.nodes.get(b, {})
    x1 = a_attrs.get("x")
    y1 = a_attrs.get("y")
    x2 = b_attrs.get("x")
    y2 = b_attrs.get("y")
    if x1 is None or y1 is None or x2 is None or y2 is None:
        return None
    return math.degrees(math.atan2(float(x2) - float(x1), float(y2) - float(y1)))


def turn_delta(previous: float | None, current: float | None) -> float | None:
    if previous is None or current is None:
        return None
    delta = current - previous
    while delta > 180:
        delta -= 360
    while delta < -180:
        delta += 360
    return delta


def classify_turn(delta: float | None) -> str:
    """Classify turn direction based on heading change in degrees."""
    if delta is None:
        return ""
    
    abs_delta = abs(delta)
    
    # Straight (within ±15 degrees)
    if abs_delta <= 15:
        return "Continue on"
    
    # Slight turns (15-45 degrees)
    if abs_delta <= 45:
        return "Turn right onto" if delta > 0 else "Turn left onto"
    
    # Sharp turns (45-135 degrees)
    if abs_delta <= 135:
        return "Turn right onto" if delta > 0 else "Turn left onto"
    
    # U-turn (>135 degrees)
    return "Turn around on"


def collapse_street_sequence(path: list[str], graph: nx.Graph) -> list[str]:
    cleaned: list[str] = []
    last_label: str | None = None

    for node in path:
        if str(graph.nodes[node].get("kind", "unknown")) != "street":
            continue
        label = street_label(graph.nodes[node].get("name", ""))
        if not label:
            continue
        if last_label is not None and label == last_label:
            continue
        cleaned.append(label)
        last_label = label

    return cleaned


def summarize_driving_directions(path: list[str], graph: nx.Graph) -> list[str]:
    """Generate Google-Maps-style driving directions with proper turn classification."""
    street_nodes = [node for node in path if str(graph.nodes[node].get("kind", "unknown")) == "street"]
    if len(street_nodes) < 2:
        return ["Head toward your destination"]

    start_label = street_label(graph.nodes[street_nodes[0]].get("name", ""))
    if not start_label:
        start_label = "your starting point"

    # Build list of (street_name, heading) pairs for valid segments
    segments: list[tuple[str, float]] = []
    last_heading: float | None = None

    for idx in range(len(street_nodes)):
        current = street_nodes[idx]
        if idx + 1 < len(street_nodes):
            nxt = street_nodes[idx + 1]
            heading = node_heading(graph, current, nxt)
            if heading is not None:
                last_heading = heading
        
        label = street_label(graph.nodes[current].get("name", ""))
        if label and last_heading is not None:
            segments.append((label, last_heading))

    if not segments:
        return [f"Head toward {start_label}"]

    # Merge consecutive segments on the same street
    merged: list[tuple[str, float]] = []
    current_street = start_label
    current_heading: float | None = None

    for street, heading in segments:
        if street.lower() == current_street.lower():
            # Same street, skip intermediate heading update
            continue
        # Different street: record transition
        if current_heading is None:
            current_heading = heading
        merged.append((street, heading))
        current_street = street

    # Generate Google-Maps-style directions
    directions: list[str] = [f"Head toward {start_label}"]

    if not merged:
        return directions

    prev_heading: float | None = None
    for street, heading in merged:
        if prev_heading is None:
            prev_heading = heading
            continue

        delta = turn_delta(prev_heading, heading)
        if delta is None or abs(delta) > 120:
            # Skip u-turns or invalid turns
            prev_heading = heading
            continue

        # Classify turn and generate instruction
        turn_class = classify_turn(delta)
        if turn_class:
            directions.append(f"{turn_class} {street}")
        prev_heading = heading

    return directions


def normalize_name(value: str) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_street_key(query: str) -> str:
    text = normalize_name(query)
    if not text:
        return ""
    tokens = text.split()
    if tokens and tokens[0].isdigit():
        tokens = tokens[1:]
    return " ".join(tokens)


def find_node_by_name(graph: nx.Graph, name_query: str) -> str:
    target = name_query.strip()
    street_key = extract_street_key(target)
    if not street_key:
        raise ValueError(f"No graph node matched '{name_query}'")

    exact_matches = []
    contains_matches = []
    strong_matches = []

    for node, attrs in graph.nodes(data=True):
        if not str(node).startswith("street_"):
            continue
        name = str(attrs.get("name", ""))
        norm_name = normalize_name(name)
        if not norm_name:
            continue

        if norm_name == street_key:
            exact_matches.append(node)
        elif street_key in norm_name:
            contains_matches.append(node)
        elif norm_name.endswith(street_key):
            strong_matches.append(node)

    if exact_matches:
        return exact_matches[0]
    if strong_matches:
        return strong_matches[0]
    if contains_matches:
        # prefer nodes where the street name is not a generic crossstreet suffix
        ranked = sorted(
            contains_matches,
            key=lambda node: (
                0 if " street " in normalize_name(graph.nodes[node].get("name", "")) else 1,
                normalize_name(graph.nodes[node].get("name", "")).count(" ")
            ),
        )
        return ranked[0]
    raise ValueError(f"No graph node matched '{name_query}'")


def main() -> None:
    graph_path = Path(__file__).resolve().parents[1] / "data" / "graphs" / "merced_multimodal.graphml"
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    graph = nx.read_graphml(str(graph_path))
    stop_lookup = load_stop_lookup()
    routes_lookup = load_routes_lookup()
    attach_names_to_graph(graph, stop_lookup)

    start_name = "781 Irma Drive"
    end_name = "1507 O Street"

    start = find_node_by_name(graph, start_name)
    end = find_node_by_name(graph, end_name)

    if start not in graph or end not in graph:
        raise ValueError(f"Requested nodes not found in graph: {start}, {end}")

    path = nx.shortest_path(graph, source=start, target=end, weight="weight")
    total_time = nx.shortest_path_length(graph, source=start, target=end, weight="weight")
    route_names = pretty_route(path, graph)
    segments = segment_route(path, graph)

    print(f"Route from {start_name} to {end_name}")
    print(f"Total travel time: {total_time} seconds")
    print()

    if segments:
        for section_type, section_path, label in segments:
            print(f"{label}:")
            
            # For bus segments, identify which route to take
            if section_type == "bus":
                route_id = extract_bus_route(section_path, graph)
                if route_id and route_id in routes_lookup:
                    route_name = routes_lookup[route_id]
                    print(f"  → Take the {route_name} bus")
                    print()
            
            names = route_mode_summary(section_type, section_path, graph)
            for name in names:
                print(f"  - {name}")
            print()
    else:
        print("Full path with intersections and stops:")
        for name in route_names:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
