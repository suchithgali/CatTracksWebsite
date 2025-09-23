#!/bin/bash

# CatTracks Build Script
# This script automates the build process for the CatTracks project

set -e  # Exit on any error

echo "Starting CatTracks build process..."

# Check if we're in the right directory
if [ ! -f "CMakeLists.txt" ]; then
    echo "Error: CMakeLists.txt not found. Please run this script from the project root."
    exit 1
fi

# Create build directory
echo "Creating build directory..."
mkdir -p build
cd build

# Configure CMake
echo "Configuring CMake..."
if command -v vcpkg &> /dev/null; then
    VCPKG_ROOT=$(vcpkg env | grep VCPKG_ROOT | cut -d= -f2)
    cmake -DCMAKE_TOOLCHAIN_FILE="$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake" ..
else
    echo "Warning: vcpkg not found in PATH. Assuming system-wide installation."
    cmake ..
fi

# Build the project
echo "🔨 Building project..."
make -j$(nproc)

echo "Build completed successfully!"
echo "Executables are located in the build/ directory"
echo ""
echo "Available executables:"
ls -la | grep -E "graph_builder|database_test" | awk '{print "  - " $9}'

cd ..
echo ""
echo "Ready to use CatTracks! See examples/ for usage instructions."