#!/bin/bash
set -e # Exit on error

echo "Running address lookup (find_nearest.py)..."
cd src/python
./venv/bin/python find_nearest.py
cd ../..

echo "Building graph_builder..."
g++ src/cpp/graph_builder.cpp -o graph_builder -I include -std=c++11

echo "Running graph_builder..."
./graph_builder

echo "Building path_builder..."
g++ src/cpp/path_builder.cpp -o path_builder -I include -std=c++11

echo "Running path_builder..."
./path_builder
