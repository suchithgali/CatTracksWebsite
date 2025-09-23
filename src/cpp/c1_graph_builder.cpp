#include <iostream>
#include "Graph.h"
#include <fstream>
#include <sstream>
#include <string>
#include <map>
#include <set>
#include "json.hpp"

using json = nlohmann::json;

int main(){

    std::ifstream user_file("route_info.json");
    
    /*if (!user_file.is_open()){
        std::cerr << "Could not open user_address_info.json! Run find_nearest.py first." << std::endl;
        return 1;
    }
        */

    json c1_route_info;
    user_file >> c1_route_info;
    user_file.close();

    std::string departure_stop_address = c1_route_info["start_address"];
    double departure_stop_lat = c1_route_info["start_lat"];
    double departure_stop_lng = c1_route_info["start_lon"];  // Fixed: was "start_lng"
    int closest_stop = c1_route_info["start_closest_stop"];
    double distance_to_stop = c1_route_info["start_distance_to_stop"];

    std::cout << "User Address: " << departure_stop_address << std::endl;
    std::cout << "Coordinates: (" << departure_stop_lat << ", " << departure_stop_lng << ")" << std::endl;
    std::cout << "Closest intersection: " << closest_stop << std::endl;
    std::cout << "Distance to intersection: " << distance_to_stop << " miles" << std::endl;

    std::ifstream file("c1_route_distances.csv");
    
    std::string line;
    std::vector<std::vector<std::string>> csvData;

    while (std::getline(file, line)){
        std::stringstream ss(line);
        std::string cell;
        std::vector<std::string> row;

        while (std::getline(ss, cell, ',')){
            row.push_back(cell);
        }
        csvData.push_back(row);
    }
    file.close();

    // First pass: collect all unique intersection indices
    std::set<int> unique_intersections;
    for (int i = 1; i < csvData.size(); i++){
        // Skip empty rows
        if (csvData[i].size() < 2 || csvData[i][0].empty() || csvData[i][1].empty()) {
            std::cout << "Skipping empty row " << i << std::endl;
            continue;
        }
        
        try {
            int index1 = std::stoi(csvData[i][0]);
            int index2 = std::stoi(csvData[i][1]);
            unique_intersections.insert(index1);
            unique_intersections.insert(index2);
        } catch (const std::exception& e) {
            std::cerr << "Error converting row " << i << ": " << e.what() << std::endl;
            return 1;
        }
    }
    
    // Add the user's closest stop to the set
    unique_intersections.insert(closest_stop);
    
    std::cout << "Found " << unique_intersections.size() << " unique intersections in route" << std::endl;
    
    // Create mapping from original indices to graph vertices (0 = user, 1-N = intersections)
    std::map<int, int> index_to_vertex;
    int vertex_counter = 1; // Start from 1 (0 is reserved for user)
    
    for (int original_index : unique_intersections) {
        index_to_vertex[original_index] = vertex_counter;
        std::cout << "Mapping intersection " << original_index << " -> vertex " << vertex_counter << std::endl;
        vertex_counter++;
    }

    int user_vertex = 0;
    int total_vertices = unique_intersections.size() + 1; // +1 for user
    Graph merced(total_vertices, total_vertices * 2); // Estimate edges
    
    // Set the reverse mapping in the graph (vertex -> original index)
    for (const auto& pair : index_to_vertex) {
        merced.setVertexMapping(pair.second, pair.first);
    }

    std::cout << "Building graph with " << total_vertices << " vertices..." << std::endl;

    // Add all intersection edges using mapped vertices
    for (int i = 1; i < csvData.size(); i++){
        // Skip empty rows
        if (csvData[i].size() < 4 || csvData[i][0].empty() || csvData[i][1].empty()) {
            continue;
        }
        
        int original_start = std::stoi(csvData[i][0]);
        int original_end = std::stoi(csvData[i][1]);
        double distance = std::stod(csvData[i][3]);
        
        int mapped_start = index_to_vertex[original_start];
        int mapped_end = index_to_vertex[original_end];
        
        merced.addEdge(mapped_start, mapped_end, distance);
        // Do NOT add reverse edge - this is a directed bus route
    }

     // Add edge from user address (vertex 0) to closest stop
    int mapped_closest = index_to_vertex[closest_stop];
    merced.addEdge(user_vertex, mapped_closest, distance_to_stop);
    merced.addEdge(mapped_closest, user_vertex, distance_to_stop);

    std::cout << "Added user address as vertex " << user_vertex << std::endl;
    std::cout << "Connected to intersection " << closest_stop << " (graph vertex " << mapped_closest << ")" << std::endl;
    std::cout << "Running Dijkstra from user address..." << std::endl;

    // Run Dijkstra from user address
    merced.dijkstra(user_vertex);

    std::cout << "Dijkstra complete! Results saved to dijkstra_paths.csv" << std::endl;

    return 0;


    
}