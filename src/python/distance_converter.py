import geopandas as gpd
import pandas as pd
import logging

logging.basicConfig(filename='../../logs/distance_converter.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load your road layer from GeoPackage
gdf = gpd.read_file("geopkg/Merced_Map.gpkg", layer="mylayers — road_centerlines")

logging.info(f"Number of road segments: {len(gdf)}")
logging.info("Column names:", list(gdf.columns))
logging.info(f"CRS: {gdf.crs}")

# Check if Shape_Length exists, if not calculate from geometry
if 'Shape_Length' in gdf.columns:
    # Convert existing Shape_Length from meters to miles
    gdf['length_miles'] = round(gdf['Shape_Length'] / 1609.344, 4)
    logging.info("Converted existing Shape_Length to miles")
else:
    # Calculate length from geometry
    logging.info(f"CRS units: {gdf.crs}")
    
    # EPSG:2227 (California State Plane Zone III) uses feet as units
    if str(gdf.crs) == 'EPSG:2227':
        gdf['length_feet'] = gdf.geometry.length.round(2)
        gdf['length_miles'] = round(gdf['length_feet'] / 5280, 4)  # Convert feet to miles
        logging.info("Calculated geometry length in feet and converted to miles")
    elif gdf.crs.is_geographic:
        # Convert to appropriate projected CRS for accurate length calculation
        gdf = gdf.to_crs('EPSG:3857')  # Web Mercator (meters)
        gdf['length_meters'] = gdf.geometry.length.round(2)
        gdf['length_miles'] = round(gdf['length_meters'] / 1609.344, 4)
        logging.info("Converted to Web Mercator, calculated length in meters, converted to miles")
    else:
        # Assume meters for other projected CRS
        gdf['length_meters'] = gdf.geometry.length.round(2)
        gdf['length_miles'] = round(gdf['length_meters'] / 1609.344, 4)
        logging.info("Calculated geometry length (assuming meters) and converted to miles")

# Save to new GeoPackage layer or CSV
gdf.to_file("geopkg/Merced_Map.gpkg", layer="road_centerlines_with_miles", driver="GPKG")
logging.info("Saved roads with mile lengths to GeoPackage")

# Also save summary to CSV
road_summary = gdf[['length_miles']].copy()
if 'fullrdname' in gdf.columns:
    road_summary['road_name'] = gdf['fullrdname']
road_summary.to_csv("road_lengths_miles.csv", index=False)
logging.info("Saved road lengths summary to CSV")
