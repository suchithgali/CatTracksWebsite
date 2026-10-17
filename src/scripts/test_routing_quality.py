import networkx as nx
import osmnx as ox
import pandas as pd

GRAPH = "merced_graph/merced_directional.graphml"
ADDRESS_MAP = "merced_graph/address_node_map.csv"

G = ox.io.load_graphml(GRAPH)
addresses = pd.read_csv(ADDRESS_MAP)

origin = 177349
destination = 163464


def get_address_name(node_id):
    """Get an address label from the graph or address map."""

    graph_name = G.nodes[node_id].get("address")

    if graph_name:
        return str(graph_name)

    match = addresses[
        addresses["address_node"].astype(str) == str(node_id)
    ]

    if not match.empty:
        return str(match.iloc[0]["address"])

    return f"Node {node_id}"


def format_distance(distance_m):
    if distance_m >= 1000:
        return f"{distance_m / 1000:.2f} km"

    return f"{distance_m:.0f} m"


if origin not in G:
    raise ValueError(f"Origin node {origin} is not in the graph")

if destination not in G:
    raise ValueError(
        f"Destination node {destination} is not in the graph"
    )

try:
    route = nx.shortest_path(
        G,
        source=origin,
        target=destination,
        weight="travel_time",
        method="dijkstra",
    )

    route_edges = ox.routing.route_to_gdf(
        G,
        route,
        weight="travel_time",
    )

    # Build readable road sections by combining consecutive
    # graph edges that belong to the same road.
    route_sections = []

    for (u, v, key), edge in route_edges.iterrows():
        edge_type = str(edge.get("edge_type", "road"))
        road_name = edge.get("road_name")

        if pd.isna(road_name) or not str(road_name).strip():
            if edge_type == "address_access":
                road_name = "Address access"
            else:
                road_name = "Unnamed road"
        else:
            road_name = str(road_name).strip()

        distance_m = float(edge.get("length", 0))
        travel_time_s = float(edge.get("travel_time", 0))

        # Combine consecutive pieces of the same road.
        if (
            route_sections
            and route_sections[-1]["road_name"] == road_name
            and route_sections[-1]["edge_type"] == edge_type
        ):
            section = route_sections[-1]
            section["distance_m"] += distance_m
            section["travel_time_s"] += travel_time_s
            section["edge_count"] += 1
            section["end_node"] = v
        else:
            route_sections.append(
                {
                    "road_name": road_name,
                    "edge_type": edge_type,
                    "distance_m": distance_m,
                    "travel_time_s": travel_time_s,
                    "edge_count": 1,
                    "start_node": u,
                    "end_node": v,
                }
            )

    origin_name = get_address_name(origin)
    destination_name = get_address_name(destination)

    total_distance_m = float(route_edges["length"].sum())
    total_time_s = float(route_edges["travel_time"].sum())

    print("\n" + "=" * 72)
    print("ROUTE SUMMARY")
    print("=" * 72)
    print(f"From: {origin_name}")
    print(f"To:   {destination_name}")
    print(f"Origin node:      {origin}")
    print(f"Destination node: {destination}")
    print(f"Total distance:   {total_distance_m / 1000:.2f} km")
    print(f"Total time:       {total_time_s / 60:.1f} minutes")
    print(f"Graph edges used: {len(route_edges)}")
    print(f"Road sections:    {len(route_sections)}")

    print("\n" + "=" * 72)
    print("ACTUAL ROUTE")
    print("=" * 72)

    for number, section in enumerate(route_sections, start=1):
        distance_text = format_distance(section["distance_m"])
        time_minutes = section["travel_time_s"] / 60

        if section["edge_type"] == "address_access":
            if number == 1:
                instruction = "Travel from the origin to the road network"
            elif number == len(route_sections):
                instruction = "Leave the road network and reach the destination"
            else:
                instruction = "Use address access connection"
        else:
            instruction = f"Follow {section['road_name']}"

        print(f"{number}. {instruction}")
        print(f"   Road:     {section['road_name']}")
        print(f"   Distance: {distance_text}")
        print(f"   Time:     {time_minutes:.1f} minutes")
        print(
            f"   Nodes:    "
            f"{section['start_node']} -> {section['end_node']}"
        )

    print(f"\nArrive at {destination_name}")

    # Save a visualization of the calculated route.
    fig, ax = ox.plot_graph_route(
        G,
        route,
        route_color="red",
        route_linewidth=4,
        node_size=0,
        show=False,
        close=False,
    )

    fig.savefig(
        "test_route.png",
        dpi=200,
        bbox_inches="tight",
    )

    print("\nRoute map saved as test_route.png")

except nx.NetworkXNoPath:
    print(
        f"No directed route exists from "
        f"{origin_name} to {destination_name}"
    )