# Basic Route Planning Example

This example demonstrates how to use CatTracks to find an optimal route from a residential address to UC Merced campus.

## Prerequisites

Ensure you have:
- Built the C++ components
- Installed Python dependencies
- Downloaded GIS data files
- Configured Google Maps API key

## Step 1: Prepare Address Database

First, extract all addresses from the GeoPackage file:

```bash
cd src/python
python address_lookup.py
```

This creates `data/all_addresses.csv` with all available addresses in Merced County.

## Step 2: Interactive Route Planning

Run the route finder:

```bash
python find_nearest.py
```

When prompted, enter:
- **Starting address**: `781 IRMA DRIVE`
- **Destination address**: `UC MERCED`

## Step 3: Process Route Data

The script generates `data/route_info.json` with geocoded coordinates and nearest bus stops.

## Step 4: Generate Optimal Path

Build and run the C++ route optimizer:

```bash
cd ../../build
./c1_graph_builder
```

## Step 5: View Results

Check the generated route:

```bash
cat ../output/optimal_route_path.txt
```

## Expected Output

```
OPTIMAL ROUTE DIRECTIONS
========================
Bus Route: C1
From: 781 IRMA DRIVE
To: UC MERCED
Total Distance: 3.30 miles
Total Walking Time: 10.2 minutes

STEP-BY-STEP DIRECTIONS:
------------------------
1. Head northwest on Irma Dr toward Freemark Ave
2. Turn right onto Freemark Ave
3. Turn right onto M Cir
4. Turn left Destination will be on the right
5. Board the C1 bus at M Circle Bus Stop
6. Get down at University Transit Center
7. You have arrived at UC MERCED
```

## Customization

### Using Different Bus Routes

To use other bus routes, modify the route data files:
- Update `data/route_distances.csv`
- Modify `data/stop_distances.csv`
- Adjust the graph builder accordingly

### Adding New Addresses

If your address isn't in the database:
1. The system will automatically use Google Maps API
2. Results are cached for future use
3. Manual coordinates can be added to `data/all_addresses.csv`

## Troubleshooting

### Common Issues

**Address not found**:
- Check spelling and formatting
- Ensure address exists in Merced County
- Verify Google Maps API key is valid

**Build errors**:
- Ensure vcpkg dependencies are installed
- Check CMake configuration
- Verify C++17 compiler support

**Python errors**:
- Install required packages: `pip install -r requirements.txt`
- Check GeoPackage file paths
- Verify data directory structure