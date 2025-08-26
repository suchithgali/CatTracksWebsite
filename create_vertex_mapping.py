import osmnx as ox
import pandas as pd
import csv

def create_vertex_mapping_csv(place_name):
    """
    Create a CSV file mapping vertex indices to real road intersections
    IMPORTANT: This must match the exact same node structure as convert_to_graph.py
    """
    print(f"=== CREATING VERTEX MAPPING FOR {place_name} ===")
    
    # Download the network
    print("Downloading road network...")
    G = ox.graph_from_place(place_name, network_type="drive")
    
    # Get node list and create mapping - SAME AS convert_to_graph.py
    nodes = list(G.nodes())
    
    # Add custom node if user wants one (to match convert_to_graph.py)
    starting_point = input("Enter an address (or press Enter to skip): ")
    
    custom_node_added = False
    if starting_point.strip():
        try:
            print(f"Trying to geocode: '{starting_point}'")
            try:
                lat, lng = ox.geocode(starting_point)
            except:
                lat, lng = ox.geocode(f"{starting_point}, USA")
            
            print(f"✓ Found coordinates: {lat:.6f}, {lng:.6f}")
            nearest_node = ox.distance.nearest_nodes(G, lng, lat)
            nodes.append(f"{starting_point}")  # Add custom node to match graph structure
            custom_node_added = True
            print(f"✓ Custom node added to mapping")
            
        except Exception as e:
            print(f"✗ Geocoding failed: {e}")
            print("Continuing without custom node...")
    
    num_nodes = len(nodes)
    
    print(f"Creating CSV mapping for {num_nodes} vertices...")
    
    # Prepare data for CSV
    csv_data = []
    
    for i, original_id in enumerate(nodes):
        # Handle custom nodes differently from OSM nodes
        if isinstance(original_id, str) and original_id == starting_point:
            # This is the custom address node (last one added)
            # Get the street names from the nearest intersection
            nearest_node_data = G.nodes[nearest_node]
            nearest_idx = nodes.index(nearest_node)
            
            # Find street names connected to the nearest intersection
            nearest_streets = set()
            for u, v, edge_data in G.edges(nearest_node, data=True):
                name = edge_data.get('name', 'Unnamed road')
                if isinstance(name, list):
                    nearest_streets.update(name)
                elif isinstance(name, str):
                    nearest_streets.add(name)
            
            # Also check incoming edges to nearest intersection
            for u, v, edge_data in G.in_edges(nearest_node, data=True):
                name = edge_data.get('name', 'Unnamed road')
                if isinstance(name, list):
                    nearest_streets.update(name)
                elif isinstance(name, str):
                    nearest_streets.add(name)
            
            nearest_streets_list = sorted(list(nearest_streets))
            connected_streets_desc = "; ".join(nearest_streets_list[:3])  # Show up to 3 main streets
            if not connected_streets_desc:
                connected_streets = nearest_idx
            
            csv_data.append({
                'Vertex_Index': i,
                'OSM_Node_ID': f'custom_{i}',
                'Latitude': round(lat, 6),
                'Longitude': round(lng, 6),
                'Primary_Description': f"{starting_point}",
                'All_Connected_Streets': f"{connected_streets_desc}",
            })
            print(f"Added custom node at index {i}: {starting_point}")
            print(f"  Connected to streets: {connected_streets_desc}")
            continue
            
        # Handle regular OSM nodes
        node_data = G.nodes[original_id]
        node_lat = node_data.get('y', 0)
        node_lon = node_data.get('x', 0)
        
        # Find all connected street names
        connected_streets = set()
        for u, v, edge_data in G.edges(original_id, data=True):
            name = edge_data.get('name', 'Unnamed road')
            if isinstance(name, list):
                connected_streets.update(name)
            elif isinstance(name, str):
                connected_streets.add(name)
        
        # Also check incoming edges
        for u, v, edge_data in G.in_edges(original_id, data=True):
            name = edge_data.get('name', 'Unnamed road')
            if isinstance(name, list):
                connected_streets.update(name)
            elif isinstance(name, str):
                connected_streets.add(name)
        
        street_list = sorted(list(connected_streets))
        primary_streets = street_list[:3]  # Take up to 3 main streets
        all_streets = "; ".join(street_list)
        
        # Create description
        if len(primary_streets) >= 2:
            description = f"{primary_streets[0]} & {primary_streets[1]}"
        elif len(primary_streets) == 1:
            description = primary_streets[0]
        else:
            description = f"Intersection {i}"
        
        
        csv_data.append({
            'Vertex_Index': i,
            'OSM_Node_ID': original_id,
            'Latitude': round(node_lat, 6),
            'Longitude': round(node_lon, 6),
            'Primary_Description': description,
            'All_Connected_Streets': all_streets,
        })
    
    # Save to CSV
    df = pd.DataFrame(csv_data)
    csv_filename = 'merced_vertex_mapping.csv'
    df.to_csv(csv_filename, index=False)
    
    print(f"\\nCSV file created: {csv_filename}")
    print(f"Total vertices mapped: {len(csv_data)}")
    if custom_node_added:
        print(f"✓ Custom address '{starting_point}' included as vertex {num_nodes-1}")
    print(f"✓ Mapping matches graph structure from convert_to_graph.py")
    
    
    return csv_filename


if __name__ == "__main__":
    # Create vertex mapping for Merced, CA
    print("Creating vertex mapping that matches the graph structure...")
    print("NOTE: Use the SAME address you used in convert_to_graph.py")
    csv_file = create_vertex_mapping_csv("Merced, CA")
    print(f"\n=== SUCCESS! ===")
    print(f"Vertex mapping saved to: {csv_file}")
    print(f"This mapping now matches your merced_graph.cpp exactly!")