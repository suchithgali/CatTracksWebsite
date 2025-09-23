# API Documentation

## Python API

### Address Lookup Module (`address_lookup.py`)

Processes GeoPackage files to extract address information and convert to CSV format.

```python
# Usage
python src/python/address_lookup.py
```

**Input**: GeoPackage file with address points
**Output**: `all_addresses.csv` with columns: Address, Latitude, Longitude

### Route Finder Module (`find_nearest.py`)

Interactive route planning system that finds optimal paths between addresses.

```python
# Usage
python src/python/find_nearest.py
```

**Features**:
- Interactive address input
- Google Maps API integration
- Local database fallback
- Multi-threaded processing
- JSON output generation

**Key Functions**:

#### `lookup_address(address_name)`
Searches for address in local database or uses Google Maps API.

**Parameters**:
- `address_name` (str): Address to look up

**Returns**:
- `tuple`: (latitude, longitude) coordinates

#### `geocode_with_google(address, max_retries=3)`
Geocodes address using Google Maps API with retry logic.

**Parameters**:
- `address` (str): Address to geocode
- `max_retries` (int): Maximum retry attempts

**Returns**:
- `tuple`: (latitude, longitude) or (None, None) if failed

### Distance Converter Module (`distance_converter.py`)

Converts road length measurements from meters to miles.

```python
# Usage
python src/python/distance_converter.py
```

**Input**: GeoPackage with road centerlines
**Output**: CSV with road lengths in miles

## C++ API

### Graph Class (`Graph.h`)

Core graph data structure for route optimization.

```cpp
class Graph {
public:
    Graph();
    void addNode(int id, double lat, double lon);
    void addEdge(int from, int to, double weight);
    std::vector<int> dijkstra(int start, int end);
    void printGraph();
};
```

#### Methods:

##### `addNode(int id, double lat, double lon)`
Adds a node to the graph.

**Parameters**:
- `id`: Unique node identifier
- `lat`: Latitude coordinate
- `lon`: Longitude coordinate

##### `addEdge(int from, int to, double weight)`
Adds weighted edge between nodes.

**Parameters**:
- `from`: Source node ID
- `to`: Destination node ID
- `weight`: Edge weight (distance)

##### `dijkstra(int start, int end)`
Finds shortest path using Dijkstra's algorithm.

**Parameters**:
- `start`: Starting node ID
- `end`: Destination node ID

**Returns**:
- `std::vector<int>`: Path as sequence of node IDs

### Node Class (`Node.h`)

Represents graph vertices with geographical coordinates.

```cpp
class Node {
public:
    int id;
    double latitude;
    double longitude;
    std::vector<Edge> edges;
    
    Node(int id, double lat, double lon);
    void addEdge(int dest, double weight);
};
```

### Edge Class (`Edge.h`)

Represents connections between nodes.

```cpp
class Edge {
public:
    int destination;
    double weight;
    
    Edge(int dest, double w);
};
```

## Build System

### CMake Configuration

The project uses CMake for cross-platform building:

```cmake
# Minimum required version
cmake_minimum_required(VERSION 3.15)

# Dependencies
find_package(cpr CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
```

### Available Targets

- `graph_builder`: Basic graph construction
- `c1_graph_builder`: C1 route specific builder
- `multi_stop_graph_builder`: Multi-destination planning
- `detailed_route_builder`: Detailed route generation
- `database_test`: Database connectivity testing

## Data Formats

### Input Formats

#### GeoPackage (`.gpkg`)
- Address points with coordinates
- Road centerlines with geometry
- Intersection data

#### CSV Files
- Address database: `Address, Latitude, Longitude`
- Stop distances: `Stop1, Stop2, Distance`
- Route information: Various route-specific data

### Output Formats

#### JSON
```json
{
    "start_address": "781 IRMA DRIVE",
    "start_lat": 37.123456,
    "start_lon": -120.123456,
    "dest_address": "UC MERCED",
    "dest_lat": 37.234567,
    "dest_lon": -120.234567,
    "optimal_route": [...],
    "total_distance": 3.30,
    "walking_time": 10.2
}
```

#### Text Output
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
...
```

## Error Handling

### Python Modules
- API timeout handling with exponential backoff
- File I/O error recovery
- Graceful degradation when services unavailable

### C++ Components
- Input validation for coordinates
- Memory management for graph structures
- Exception handling for file operations

## Performance Considerations

- **Address Lookup**: Local database queries < 1ms
- **Route Calculation**: Dijkstra's algorithm O(V log V + E)
- **Memory Usage**: Linear with number of intersections
- **API Caching**: Reduces redundant geocoding calls