import requests
import pandas as pd
import csv
import os
import sys

# Get OpenRouteService API key from environment variable
OPENROUTESERVICE_API_KEY = os.getenv('OPENROUTESERVICE_API_KEY')

if not OPENROUTESERVICE_API_KEY:
    print("Error: OPENROUTESERVICE_API_KEY environment variable not set")
    print("Please set your OpenRouteService API key:")
    print("export OPENROUTESERVICE_API_KEY='your_api_key_here'")
    sys.exit(1)

print("OpenRouteService API key loaded from environment variable")

def get_coordinates_by_index(index):
    """Get latitude and longitude for a given intersection index"""
    # Read the CSV file
    df = pd.read_csv('all_intersections.csv')
    
    # Find the row with the given index
    row = df[df['Index'] == index]
    
    if not row.empty:
        lat = row['Latitude'].iloc[0]
        lon = row['Longitude'].iloc[0]
        name = row['Intersection Name'].iloc[0]
        return lat, lon, name
    else:
        raise ValueError(f"Index {index} not found in the CSV file")


index1 = 27856  #start intersection
index2 = 27843  #end intersection 

# Get coordinates for both points
lat1, lon1, name1 = get_coordinates_by_index(index1)
lat2, lon2, name2 = get_coordinates_by_index(index2)

print(f"From: Index {index1} - {name1}")
print(f"To: Index {index2} - {name2}")

# Now you can use these coordinates in your API call
api_key = OPENROUTESERVICE_API_KEY
url = f"https://api.openrouteservice.org/v2/directions/driving-car?api_key={api_key}&start={lon1},{lat1}&end={lon2},{lat2}"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("API Response received successfully!")
    
    # Extract distance from the response
    # The response structure is different - distance is in features[0].properties.summary.distance
    if 'features' in data and len(data['features']) > 0:
        feature = data['features'][0]
        if 'properties' in feature and 'summary' in feature['properties']:
            distance_meters = feature['properties']['summary']['distance']
            distance_miles = distance_meters * 0.0006213712  # Convert to miles
            print(f"Distance: {distance_miles:.4f} miles")
        elif 'properties' in feature and 'segments' in feature['properties'] and len(feature['properties']['segments']) > 0:
            # Fallback to segments distance
            distance_meters = feature['properties']['segments'][0]['distance']
            distance_miles = distance_meters * 0.0006213712  # Convert to miles
            print(f"Distance: {distance_miles:.4f} miles")
        else:
            print("No distance found in response")
            print("Full response:", data)
    else:
        print("No features found in response")
        print("Full response:", data)
else:
    print("Request failed:", response.status_code)
    print("Response:", response.text)

import os
import csv

file_exists = os.path.exists("c1_stop_distances.csv") and os.path.getsize("c1_stop_distances.csv") > 0

with open("c1_stop_distances.csv", "a", newline="") as file:
    writer = csv.writer(file)
    
    # Only write header if file is new/empty
    if not file_exists:
        writer.writerow(["Index1", "Index2" "Intersections", "Distance"])
    
    # Write the data row
    writer.writerow([f"{index1}", f"{index2}", f"{name1} - {name2}", f"{distance_miles}"])
