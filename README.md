# CatTracks - Intelligent Transit Route Optimization System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![C++](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](https://isocpp.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org/)

CatTracks is an intelligent transit route optimization system designed for Merced County public transportation. The system combines Geographic Information Systems (GIS) data processing with advanced graph algorithms to provide optimal route planning for bus transit users.

## Features

- **Smart Route Planning**: Find optimal paths combining walking and bus transportation
- **Real-time Address Lookup**: Geocoding using Google Maps API with local database fallback
- **Multi-modal Transportation**: Seamlessly integrate walking and bus routes
- **GIS Data Integration**: Process geographical data from GeoPackage files
- **Distance Optimization**: Calculate shortest paths using Dijkstra's algorithm
- **Interactive Route Generation**: Step-by-step directions with distance and time estimates

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage Examples](#usage-examples)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Prerequisites

- **C++ Compiler**: GCC or Clang with C++11 support
- **Python**: 3.8 or higher
- **API Key**: Open Route Service API Key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/CatTracks.git
   cd CatTracks
   ```

2. **Set up Python Environment**
   It is recommended to use a virtual environment.
   ```bash
   cd src/python
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r ../../requirements.txt
   cd ../..
   ```

3. **Configure API Key**
   You need an Open Route Service API key for walking directions.
   ```bash
   export ORS_MAPS_API_KEY='your_api_key_here'
   ```

## 🚀 Quick Start

The current application is a Flask web service backed by GTFS data. The old
C++/CSV route-builder pipeline is no longer the web runtime.

```bash
# Make the script executable (only needed once)
chmod +x build_and_run.sh

# Start the local web app
./build_and_run.sh
```

Open <http://127.0.0.1:5000>. The deployment health check is
<http://127.0.0.1:5000/health>.

Test the complete route engine without opening the website:

```bash
.venv/bin/python -m scripts.smoke_test_route \
  --from-stop "University Transit Center" \
  --to-stop "Merced Mall Target"
```

To prepare a local environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

### GTFS data

The application uses the professional-format canonical feed in `data/gtfs/`.
The original official download is preserved in `data/gtfs_official/`. If the
official source is updated, regenerate the canonical feed with:

```bash
.venv/bin/python -m src.gtfs_normalize
```

The command reads `data/gtfs_official/` and writes `data/gtfs/`. Set
`CATTRACKS_GTFS_DIR` to use a different canonical feed directory.

### Road-following route maps

The planner requests road geometry from an OSRM-compatible routing service and
draws that geometry on the Leaflet map. The default service is the public
OSRM demo endpoint. For production deployments, set
`CATTRACKS_ROUTING_URL` to a hosted or private OSRM-compatible service. If
the service is unavailable, the API keeps the route usable and falls back to
straight lines between the transit stops.

The planner also accepts custom departure and destination addresses. Addresses
are geocoded with the Nominatim service, connected to the nearest CatTracks
stops with walking legs, and routed through the transit graph. Bus transfers
continue to use the same transfer logic between the custom walking legs.

### Deploy on Vercel

The Flask application is exposed through `api/index.py` and configured by
`vercel.json`. From the project root:

```bash
npx vercel
```

Configure `CATTRACKS_ROUTING_URL` and, if needed, `DATABASE_URL` as Vercel
environment variables. The canonical GTFS files in `data/gtfs/` are included
with the deployment.

Docker and Gunicorn configuration are included for deployment. For a
production-like local run:

```bash
website/.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 website.app:app
```

The JSON API is available at `POST /api/route` with `from` and `to` stop names.

### Project Structure (Key Files)

```
CatTracks/
├── build_and_run.sh       # Main execution script
├── data/
│   ├── general/           # General address and intersection data
│   ├── bus_routes/        # Stop names and distance chunks for each bus
│   └── route_metadata/    # JSON/TXT definitions of routes
├── src/
│   ├── cpp/               # C++ Core Logic (Graph, Dijkstra)
│   └── python/            # Python Helpers (Geocoding, API calls)
└── include/               # Header files (Graph.h, Node.h)
```

Required Python packages:
- `geopandas`
- `pandas`
- `numpy`
- `requests`
- `fiona`

### Build Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/suchithgali/CatTracksWebsite.git
   cd CatTracks
   ```

2. **Configure CMake**:
   ```bash
   mkdir build
   cd build
   cmake -DCMAKE_TOOLCHAIN_FILE=[path-to-vcpkg]/scripts/buildsystems/vcpkg.cmake ..
   ```

3. **Build the project**:
   ```bash
   make -j$(nproc)
   ```

## Quick Start

## 🚀 Quick Start

### 1. Set Up API Keys

```bash
# Use the automated setup script
./scripts/setup_api_keys.sh

# OR set manually
export GOOGLE_MAPS_API_KEY="your_google_maps_api_key"
export OPENROUTESERVICE_API_KEY="your_openrouteservice_api_key"
```

### 2. Prepare GIS Data

```bash
cd src/python
python address_lookup.py  # Generate address database
```

### 3. Find Route

```bash
python find_nearest.py
# Enter starting address: 781 IRMA DRIVE
# Enter destination address: UC MERCED
```

### 4. Generate Optimal Path

```bash
cd ../../build
./c1_graph_builder
```

### 5. View Results

```bash
cat ../output/optimal_route_path.txt
```

## 📁 Project Structure

```
CatTracks/
├── README.md                 # Project documentation
├── LICENSE                   # License file
├── CMakeLists.txt           # CMake configuration
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
│
├── src/                     # Source code
│   ├── cpp/                 # C++ implementation
│   │   ├── c1_graph_builder.cpp
│   │   ├── graph_builder.cpp
│   │   ├── multi_stop_graph_builder.cpp
│   │   ├── detailed_route_builder.cpp
│   │   └── database_test.cpp
│   └── python/              # Python scripts
│       ├── find_nearest.py
│       ├── address_lookup.py
│       ├── distance_converter.py
│       ├── intersection_lookup.py
│       ├── layer_lookup.py
│       └── remove_duplicates.py
│
├── include/                 # Header files
│   ├── Graph.h
│   ├── Node.h
│   ├── Edge.h
│   ├── ArrayList.h
│   ├── LinkedList.h
│   └── json.hpp
│
├── data/                    # Data files
│   ├── all_addresses.csv
│   ├── all_intersections.csv
│   ├── all_stops.csv
│   ├── road_lengths_miles.csv
│   ├── route_info.json
│   └── optimal_route_results.json
│
├── output/                  # Generated output files
│   └── optimal_route_path.txt
│
├── geopkg/                  # GeoPackage files
│   ├── merced_county_site_address_pointsshp.gpkg
│   ├── merced_intersections.gpkg
│   └── merced_road_centerlines.gpkg
│
├── build/                   # Build artifacts (auto-generated)
├── cache/                   # API response cache
├── docs/                    # Documentation
├── examples/                # Usage examples
├── scripts/                 # Utility scripts
└── vcpkg/                  # Package manager
```

## Usage Examples

### Example 1: Campus Route Planning

```python
# Run the route finder
python src/python/find_nearest.py

# Input:
# Starting address: 781 IRMA DRIVE
# Destination: UC MERCED

# Output: Generates route_info.json with optimal path data
```

### Example 2: Multi-stop Route Optimization

```bash
# Build and run multi-stop planner
./build/multi_stop_graph_builder

# Processes multiple destinations for efficient routing
```

### Example 3: Custom GIS Data Processing

```python
# Convert road lengths to miles
python src/python/distance_converter.py

# Lookup specific intersections
python src/python/intersection_lookup.py
```

## Configuration

### API Keys

### API Keys

Set your API keys as environment variables:

```bash
# Set Google Maps API key
export GOOGLE_MAPS_API_KEY="your_api_key_here"

# Set OpenRouteService API key
export OPENROUTESERVICE_API_KEY="your_api_key_here"
```

For persistent setup, add these to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
echo 'export GOOGLE_MAPS_API_KEY="your_api_key_here"' >> ~/.zshrc
echo 'export OPENROUTESERVICE_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### Data Sources

Configure GIS data sources in the respective Python scripts:
- Address data: `geopkg/merced_county_site_address_pointsshp.gpkg`
- Intersection data: `geopkg/merced_intersections.gpkg`
- Road centerlines: `geopkg/merced_road_centerlines.gpkg`

## Testing

Run the database test suite:

```bash
./build/database_test
```

Validate walking logic:

```bash
python src/python/test_walking_logic.py
```

## Performance

- **Route Calculation**: < 500ms for typical routes
- **Address Lookup**: < 100ms with local database
- **Memory Usage**: ~50MB for full Merced County dataset
- **Accuracy**: ±10 meters for GPS coordinates

## Contributing

I welcome contributions! Please see my [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style

- **C++**: Follow Google C++ Style Guide
- **Python**: Follow PEP 8
- **Documentation**: Use clear, concise comments

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Merced County for providing GIS data
- Google Maps API for geocoding services
- UC Merced for transit route information
- Open source community for supporting libraries

## 📧 Contact

- **Project Maintainer**: [Suchith Gali](https://github.com/suchithgali)
- **Project Repository**: [CatTracksWebsite](https://github.com/suchithgali/CatTracksWebsite)
- **Issues**: [GitHub Issues](https://github.com/suchithgali/CatTracksWebsite/issues)

## 🗺️ Roadmap

- [ ] Real-time bus tracking integration
- [ ] Mobile application development
- [ ] Machine learning for traffic prediction
- [ ] Multi-language support
- [ ] Accessibility features for disabled users
- [ ] Integration with other transit systems

---

**CatTracks** - Making public transportation smarter, one route at a time.