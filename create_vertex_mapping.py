import osmnx as ox
import pandas as pd
import csv

def create_vertex_mapping_csv(place_name):
    """
    Create a CSV file mapping vertex indices to real road intersections
    """
    print(f"=== CREATING VERTEX MAPPING FOR {place_name} ===")
    
    # Download the network
    print("Downloading road network...")
    G = ox.graph_from_place(place_name, network_type="drive")
    
    # Get node list and create mapping
    nodes = list(G.nodes())
    num_nodes = len(nodes)
    
    print(f"Creating CSV mapping for {num_nodes} vertices...")
    
    # Prepare data for CSV
    csv_data = []
    
    for i, original_id in enumerate(nodes):
        node_data = G.nodes[original_id]
        lat = node_data.get('y', 0)
        lon = node_data.get('x', 0)
        
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
            'Latitude': round(lat, 6),
            'Longitude': round(lon, 6),
            'Primary_Description': description,
            'All_Connected_Streets': all_streets,
        })
    
    # Save to CSV
    df = pd.DataFrame(csv_data)
    csv_filename = 'merced_vertex_mapping.csv'
    df.to_csv(csv_filename, index=False)
    
    print(f"\\nCSV file created: {csv_filename}")
    print(f"Total vertices mapped: {len(csv_data)}")
    
    
    return csv_filename

