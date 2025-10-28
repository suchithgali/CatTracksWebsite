import requests
import re
import json
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys

# Get Google Maps API key from environment variable
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

if not GOOGLE_MAPS_API_KEY:
    print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
    print("Please set your Google Maps API key:")
    print("export GOOGLE_MAPS_API_KEY='your_api_key_here'")
    sys.exit(1)

print("API key loaded from environment variable")

# Create a session for connection reuse that way we don't need to setup parameter such as authentication again and reduce latency
session = requests.Session()

#store the starting and ending addresses, remove the whitespace and convert to upper case for consistent format
start_address = input("Enter your starting address: ").strip().upper()
destination_address = input("Enter your destination address: ").strip().upper()

# Load all the addresses in Merced from the csv file
addresses_df = pd.read_csv("all_addresses.csv")
#convert each address in the csv file to upper case for consistent formatting
addresses_df['Address'] = addresses_df['Address'].str.upper()

#function to search for an address in the csv file
def lookup_address(address_name):
    #search for the address by selecting all rows in the csv file where the values in the Address column match
    address_match = addresses_df[addresses_df['Address'] == address_name]
    
    if not address_match.empty:
        # Found in local database
        row = address_match.iloc[0]
        lat = row['Latitude']
        lon = row['Longitude']
        print(f"Found '{address_name}' in local database: ({lat}, {lon})")
        return lat, lon
    else:
        print(f"Error: Address '{address_name}' not found in local database.")
        print("Please check the spelling or try a different address.")
        return None, None
    
#look up both addresses, and stop if a lat is not found that means the address doesn't exist
start_lat, start_lon = lookup_address(start_address)
if start_lat is None:
    exit(1)

dest_lat, dest_lon = lookup_address(destination_address)
if dest_lat is None:
    exit(1)

# Read stop distances and intersections data
stop_distances_df = pd.read_csv("c1_stop_distances.csv")
intersections_df = pd.read_csv("all_intersections.csv")

#save each c1 stop into a set to create a filter of stops for the c1 bus route
unique_indices = set()
unique_indices.update(stop_distances_df['Index1'].tolist())
unique_indices.update(stop_distances_df['Index2'].tolist())

# Filter intersections to only include stops that are in stop_distances.csv
df = intersections_df[intersections_df['Index'].isin(unique_indices)].copy()

# Find closest stop by straight-line distance first as initial approximation
def haversine_distance(lat1, lon1, lat2, lon2):
    #convert the lat and long into radians and save
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    #calculate difference in longitude and latitude
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    #calculate the intermediate value of the haversine formula which is the square of half a chord length between 2 points on the surface of a sphere
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    #calculates the central angle which is the angle of the center of the Earth formed by lines connecting each point to the center of the sphere 
    c = 2 * np.arcsin(np.sqrt(a))
    #multiply by the Earth's mean radius to get the distance along Earth's sphere
    return c * 6371  # km

def get_distance_with_route(start_lon, start_lat, end_lon, end_lat):
    #define the api endpoint url
    url = "https://maps.googleapis.com/maps/api/directions/json"
    #define the parameters for the api endpoint
    params = {
        "origin": f"{start_lat},{start_lon}",
        "destination": f"{end_lat},{end_lon}",
        "mode": "walking",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        #make the api request using get and use session for connection reuse
        response = session.get(url, params=params, timeout=5)  
        #save response 
        data = response.json()

        #if the request was not succesful print out the error message
        if data.get("status") != "OK":
            print(f"Google API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
            return {'distance_miles': float('inf'), 'success': False}

        # Extract distance in meters and duration in seconds
        leg = data["routes"][0]["legs"][0]
        distance_meters = leg["distance"]["value"]
        duration_seconds = leg["duration"]["value"]

        # Convert meters to miles
        distance_miles = distance_meters * 0.000621371

        # Convert seconds to minutes
        duration_minutes = duration_seconds / 60

        # Clean HTML tags from steps and extract instructions
        instructions = []
        for step in leg["steps"]:
            # Replace HTML tags with spaces to avoid words running together
            instruction_text = re.sub(r"<[^>]+>", " ", step["html_instructions"])
            # Clean up multiple spaces and strip
            instruction_text = re.sub(r"\s+", " ", instruction_text).strip()
            
            if instruction_text:
                # Split on specific patterns that indicate new instructions
                # Pattern 1: Split on ". " followed by capital letter (sentence boundaries)
                parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', instruction_text)
                instructions.append(parts)

        return {
            "distance_miles": distance_miles,
            "duration_minutes": duration_minutes,
            "instructions": instructions,
            "success": True
        }
    #if coordinates not valid for api url
    except requests.exceptions.Timeout:
        print(f"Timeout for coordinates ({start_lat}, {start_lon}) to ({end_lat}, {end_lon})")
        return {'distance_miles': float('inf'), 'success': False}
    except Exception as e:
        print(f"Error for coordinates ({start_lat}, {start_lon}) to ({end_lat}, {end_lon}): {e}")
        return {'distance_miles': float('inf'), 'success': False}


def find_closest_intersection_with_route(lat, lon, location_name, get_instructions=True):    
    # First, calculate straight-line distances to all stops as closest mileage distance will mostly always be included in an area with a good road network
    df['straight_distance'] = df.apply(lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']), axis=1)
    
    # Get the top 5 closest by straight-line distance to reduce API calls
    top_candidates = df.nsmallest(5, 'straight_distance')
    
    road_distances = []
    
    # Use parallel processing for faster API calls
    def process_candidate(row):
        #make the api request to get the route
        route_result = get_distance_with_route(lon, lat, row['Longitude'], row['Latitude'])
        
        if route_result['success']:
            return {
                'index': int(row['Index']),  # Convert pandas types
                'name': row['Intersection Name'],
                'road_distance_miles': route_result['distance_miles'],
                'walking_duration_minutes': route_result['duration_minutes'],
                'walking_instructions': route_result['instructions'] if get_instructions else [],
                'lat': float(row['Latitude']),
                'lon': float(row['Longitude']),
                'straight_distance': row['straight_distance']
            }
        else:
            return {
                'index': int(row['Index']),  # Convert pandas types
                'name': row['Intersection Name'],
                'road_distance_miles': float('inf'),
                'walking_duration_minutes': 0,
                'walking_instructions': [],
                'lat': float(row['Latitude']),
                'lon': float(row['Longitude']),
                'straight_distance': row['straight_distance']
            }
    
    # Process candidates in parallel (max 5 concurrent requests)
    with ThreadPoolExecutor(max_workers=5) as executor:
        #get the routes for each of the top 5 shortest straight line routes with parrallel processing
        #save the result of process_candidate as key and the row index as the key value pair in futures
        futures = {executor.submit(process_candidate, row): idx for idx, row in top_candidates.iterrows()}
        
        for future in as_completed(futures):
            result = future.result()
            road_distances.append(result)
        
    # Filter out failed API calls (infinite distances) and sort by road distance
    valid_distances = [d for d in road_distances if d['road_distance_miles'] != float('inf')]
    
    if not valid_distances:
        print("Error: No valid walking routes found. Check API connectivity.")
        return None
    
    #sort based on distance
    valid_distances.sort(key=lambda x: x['road_distance_miles'])
    
    # Return up to 5 closest stops instead of just the closest one
    return valid_distances[:5]

# Find closest bus stops for both addresses
# Get detailed walking instructions for start (where you need to walk TO the bus)
start_closest_stops = find_closest_intersection_with_route(start_lat, start_lon, "STARTING ADDRESS", get_instructions=True)
# For destination, find closest stop but we need the distance FROM that stop TO the destination
dest_closest_stops = find_closest_intersection_with_route(dest_lat, dest_lon, "DESTINATION ADDRESS", get_instructions=False)

# Check if we found valid intersections
if start_closest_stops is None or dest_closest_stops is None:
    print("Error: Could not find valid bus stops. Exiting.")
    exit(1)

# Get the primary (closest) stops for backward compatibility, simnce sorted it will be the first key value pair
start_closest = start_closest_stops[0] if start_closest_stops else None
dest_closest = dest_closest_stops[0] if dest_closest_stops else None

if start_closest is None or dest_closest is None:
    print("Error: Could not find valid bus stops. Exiting.")
    exit(1)

# Write both addresses info for C++ program
route_info = {
    'start_address': start_address,
    'start_lat': start_lat,
    'start_lon': start_lon,
    'start_closest_stop': start_closest['index'],
    'start_closest_stop_name': start_closest['name'],
    'start_distance_to_stop': start_closest['road_distance_miles'],  # Walking FROM start TO bus stop
    'start_walking_duration_minutes': start_closest['walking_duration_minutes'],
    'start_walking_instructions': start_closest['walking_instructions'],
    
    # Add all 5 closest start stops
    'start_closest_5_stops': start_closest_stops,
    
    'dest_address': destination_address,
    'dest_lat': dest_lat,
    'dest_lon': dest_lon,
    'dest_closest_stop': dest_closest['index'],
    'dest_closest_stop_name': dest_closest['name'],
    'dest_distance_from_stop': dest_closest['road_distance_miles'],  # Walking FROM bus stop TO destination
    'dest_walking_duration_minutes': dest_closest.get('walking_duration_minutes', 0),
    
    # Add all 5 closest destination stops
    'dest_closest_5_stops': dest_closest_stops,
    
    'route_summary': {
        'total_walking_distance': start_closest['road_distance_miles'] + dest_closest['road_distance_miles'],
        'total_walking_time_minutes': start_closest['walking_duration_minutes'] + dest_closest.get('walking_duration_minutes', 0),
        'start_stop': start_closest['name'],
        'end_stop': dest_closest['name'],
        'walking_to_bus_miles': start_closest['road_distance_miles'],
        'walking_from_bus_miles': dest_closest['road_distance_miles']
    }
}

# Save to file for C++ to read
with open('route_info.json', 'w') as f:
    json.dump(route_info, f, indent=2)