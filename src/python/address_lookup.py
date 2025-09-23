import geopandas as gpd
import pandas as pd
import csv
import os

# Read the GeoPackage layer
gdf = gpd.read_file("geopkg/merced_county_site_address_pointsshp.gpkg", layer="Merced_Map — mylayers2 — merced_county_site_address_pointsshp")

print(f"Number of addresses: {len(gdf)}")

file_name = "all_addresses.csv"

# Create CSV file with all addresses
with open(file_name, "w", newline="") as file:
    writer = csv.writer(file)
    # Write header
    writer.writerow(["Address", "Latitude", "Longitude"])
    
    # Process each address in the GeoDataFrame
    for index, row in gdf.iterrows():
        try:
            # Build full address from components
            address_parts = []
            
            # Add address number
            if pd.notna(row.get('add_number')):
                address_parts.append(str(int(row['add_number'])))
            
            # Add full road name
            if pd.notna(row.get('fullrdname')):
                address_parts.append(row['fullrdname'])
            
            # Create full address
            full_address = ' '.join(address_parts) if address_parts else f"Address_{index}"
            
            # Get coordinates
            lat = float(row['lat']) if pd.notna(row['lat']) else 0.0
            lon = float(row['long']) if pd.notna(row['long']) else 0.0
            
            # Write to CSV
            writer.writerow([full_address, lat, lon])
            
            # Print progress every 1000 addresses
            if (index + 1) % 1000 == 0:
                print(f"Processed {index + 1} addresses...")
                
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue

print(f"All addresses saved to {file_name}")