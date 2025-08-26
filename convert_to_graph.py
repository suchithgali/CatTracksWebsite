import osmnx as ox
import networkx as nx
import numpy as np

def convert_osmnx_to_graph_h(place_name, output_file="merced_graph.cpp"):
    """
    Convert OSMnx road network to Graph.h compatible format
    """
    print(f"=== CONVERTING {place_name} TO GRAPH.H FORMAT ===")

    METERS_TO_MILES = 0.000621371
    
    # Download the network
    print("Downloading road network...")
    G = ox.graph_from_place(place_name, network_type="drive")
    
    # Get node list and create mapping
    nodes = list(G.nodes())

    starting_point = input("Enter an address: ")

    try:
        print(f"Trying to geocode: '{starting_point}'")
        # Try geocoding with different approaches
        try:
            lat, lng = ox.geocode(starting_point)
        except:
            # Try adding "USA" to help geocoding
            lat, lng = ox.geocode(f"{starting_point}, USA")
        
        print(f"✓ Found coordinates: {lat:.6f}, {lng:.6f}")
        nearest_node = ox.distance.nearest_nodes(G, lng, lat)
        nodes.append(f"{starting_point}")
        print(f"✓ Connected to nearest node: {nearest_node}")
        
    except Exception as e:
        print(f"✗ Geocoding failed: {e}")
        print("Continuing without custom node...")
        nearest_node = None

    num_nodes = len(nodes)
    node_to_index = {node_id: i for i, node_id in enumerate(nodes)}
    
    print(f"Network has {num_nodes} nodes and {len(G.edges())} edges")
    
    # Create adjacency list for easier processing
    adjacency_list = {}
    for i in range(num_nodes):
        adjacency_list[i] = []
    
    edge_count = 0
    for u, v, data in G.edges(data=True):
        u_idx = node_to_index[u]
        v_idx = node_to_index[v]
        # Convert to miles and scale up to preserve precision (multiply by 10000)
        weight_miles = data.get('length', 1000) * METERS_TO_MILES
        weight_scaled = int(weight_miles * 10000)  # Convert to integer with precision
        
        adjacency_list[u_idx].append((v_idx, weight_scaled))
        edge_count += 1

    distance_miles = 0
    if nearest_node is not None:
        custom_idx = node_to_index[f"{starting_point}"]
        nearest_idx = node_to_index[nearest_node]

        #calculate distance to nearest_node
        custom_lat, custom_lng = lat, lng
        nearest_lat = G.nodes[nearest_node]['y']
        nearest_lng = G.nodes[nearest_node]['x']
        
        # Simple distance calculation in meters
        import math
        R = 6371000  # Earth radius in meters
        lat1_rad = math.radians(custom_lat)
        lon1_rad = math.radians(custom_lng)
        lat2_rad = math.radians(nearest_lat)
        lon2_rad = math.radians(nearest_lng)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_meters = R * c
        distance_miles = round(distance_meters * METERS_TO_MILES, 4)
        distance_scaled = int(distance_miles * 10000)  # Scale for integer precision
        print(f"Distance to nearest intersection: {distance_miles} miles")
        
        # Connect both ways with actual distance (scaled)
        adjacency_list[custom_idx].append((nearest_idx, distance_scaled))
        adjacency_list[nearest_idx].append((custom_idx, distance_scaled))
        edge_count += 2
    
    # Generate C++ code
    cpp_code = f"""#include "Graph.h"
#include <iostream>

// Auto-generated from OSMnx data for {place_name}
// {num_nodes} intersections, {edge_count} road segments
// Distances scaled by 10000 for integer precision (divide by 10000 to get miles)

Graph create_merced_network() {{
    // Create graph with {num_nodes} vertices and {edge_count} edges
    Graph merced({num_nodes}, {edge_count});
    
    std::cout << "Loading Merced, CA road network..." << std::endl;
    std::cout << "Nodes: {num_nodes}, Edges: {edge_count}" << std::endl;
    std::cout << "Distances are scaled integers (divide by 10000 for miles)" << std::endl;
    
"""
    
    # Add all edges
    cpp_code += "    // Adding road segments with distances in miles\n"
    edge_counter = 0
    
    for from_node in range(num_nodes):
        for to_node, weight in adjacency_list[from_node]:
            cpp_code += f"    merced.addEdge({from_node}, {to_node}, {weight});\n"
            edge_counter += 1
            
            # Add progress indicator every 1000 edges
            if edge_counter % 1000 == 0:
                cpp_code += f"    if ({edge_counter} % 5000 == 0) std::cout << \"Loaded \" << {edge_counter} << \" edges...\" << std::endl;\n"
    
    cpp_code += f"""
    std::cout << "Merced road network loaded successfully!" << std::endl;
    return merced;
}}

int main() {{
    // Create the graph
    Graph merced = create_merced_network();
    
    std::cout << "\\n=== FINDING SHORTEST PATHS IN MERCED ===" << std::endl;
    
    // Run Dijkstra from your custom address (vertex {num_nodes-1 if nearest_node else 'N/A'})
    int source = {num_nodes-1 if nearest_node else 5308};
    std::cout << "\\nRunning Dijkstra from intersection " << source << ":" << std::endl;
    
    // Run Dijkstra's algorithm (it handles CSV output internally)
    merced.dijkstra(merced, source);
    
    return 0;
}}
"""

    # WRITE THE C++ FILE - THIS WAS MISSING!
    print(f"Writing C++ code to {output_file}...")
    with open(output_file, 'w') as f:
        f.write(cpp_code)
    
    print(f"✓ C++ file '{output_file}' generated successfully!")
    if nearest_node is not None:
        print(f"✓ Custom location '{starting_point}' added as node {num_nodes-1}")
        print(f"✓ Connected with {distance_miles} mile road to intersection {nearest_idx}")
    else:
        print("! Network generated without custom location")
    
    return output_file

if __name__ == "__main__":
    try:
        # Call the function with Merced, CA
        output_file = convert_osmnx_to_graph_h("Merced, CA", "merced_graph.cpp")
        print(f"\n=== SUCCESS! ===")
        print(f"Generated: {output_file}")
        print(f"\nTo compile and run:")
        print(f"g++ -o merced_graph {output_file}")
        print(f"./merced_graph")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()