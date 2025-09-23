import geopandas as gpd
import pandas as pd
import csv
import os

# Read the GeoPackage layer
gdf = gpd.read_file("geopkg/merced_intersections.gpkg", layer="merced_intersections — filtered_no_duplicates")


file_name = "all_intersections.csv"

# Create CSV file with all addresses
with open(file_name, "w", newline="") as file:
    writer = csv.writer(file)
    # Write header with index column
    writer.writerow(["Index", "Intersection Name", "Latitude", "Longitude"])
    
    # Process each address in the GeoDataFrame
    csv_index = 0  # Separate index for CSV (starts from 0)
    for index, row in gdf.iterrows():
        try:
            # Build intersection name from components
            road_name_1 = []
            road_name_2 = []

            # Add first street name and type
            if pd.notna(row.get('st_name')):
                road_name_1.append(str(row['st_name']))
            if pd.notna(row.get('st_postyp')):
                road_name_1.append(str(row['st_postyp']))

            # Add second street name and type
            if pd.notna(row.get('st_name_2')):
                road_name_2.append(str(row['st_name_2']))
            if pd.notna(row.get('st_postyp_2')):
                road_name_2.append(str(row['st_postyp_2']))

            # Join intersection name as 'road_name_1 and road_name_2'
            name1 = ' '.join(road_name_1) if road_name_1 else ''
            name2 = ' '.join(road_name_2) if road_name_2 else ''
            if name1 and name2:
                full_address = f"{name1} and {name2}"
            elif name1:
                full_address = name1
            elif name2:
                full_address = name2
            else:
                full_address = f"Intersection_{csv_index}"

            lat = float(row['ycoord']) if pd.notna(row.get('ycoord')) else 0.0
            lon = float(row['xcoord']) if pd.notna(row.get('xcoord')) else 0.0
            
            # Write to CSV with index
            writer.writerow([csv_index, full_address, lat, lon])
            csv_index += 1  # Increment CSV index
            
            # Print progress every 1000 addresses
            if csv_index % 1000 == 0:
                print(f"Processed {csv_index} addresses...")
                
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue

print(f"All addresses saved to {file_name}")