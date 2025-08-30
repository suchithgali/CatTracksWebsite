import geopandas as gpd
import usaddress

# Read the shapefile
gdf = gpd.read_file("shapefiles/Merced_County_Site_Address_Points.shp")

# Get user input and parse it
user_address = input("Please enter your starting address: ")
parsed = usaddress.tag(user_address)[0]

# Abbreviation mappings
abbreviations = {
    'N': 'NORTH', 'S': 'SOUTH', 'E': 'EAST', 'W': 'WEST',
    'NE': 'NORTHEAST', 'NW': 'NORTHWEST', 'SE': 'SOUTHEAST', 'SW': 'SOUTHWEST',
    'ST': 'STREET', 'AVE': 'AVENUE', 'BLVD': 'BOULEVARD', 'RD': 'ROAD',
    'DR': 'DRIVE', 'CT': 'COURT', 'LN': 'LANE', 'WAY': 'WAY', 'PL': 'PLACE'
}

# Build search terms with unabbreviated versions
address_num = float(parsed['AddressNumber'])
street_name = parsed['StreetName']
street_type = parsed.get('StreetNamePostType', '')
street_dir = parsed.get('StreetNamePreDirectional', '')

# Expand abbreviations
if street_dir:
    street_dir = abbreviations.get(street_dir.upper(), street_dir)
else:
    street_dir = ''

if street_type:
    street_type = abbreviations.get(street_type.upper(), street_type)
else:
    street_type = ''

# Build full street name - add parts only if they exist
street = ''
if street_dir:
    street += street_dir + ' '
street += street_name
if street_type:
    street += ' ' + street_type

street = street.upper()

# Find matching address
match = gdf[(gdf['add_number'] == address_num) & (gdf['fullrdname'].str.upper() == street)]

# Print result
if not match.empty:
    print(f"Coordinates: {match['lat'].iloc[0]}, {match['long'].iloc[0]}")
else:
    print("Address not found")