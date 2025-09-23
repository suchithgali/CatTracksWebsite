#include <iostream>
#include "Graph.h"
#include <fstream>
#include <sstream>
#include <string>
#include <map>
#include <set>
#include <vector>
#include <limits>
#include "json.hpp"

using json = nlohmann::json;

struct StopInfo {
    int index;
    std::string name;
    double road_distance_miles;
    double walking_duration_minutes;
    double lat;
    double lon;
    double straight_distance;
};

struct RouteResult {
    int start_stop_index;
    int dest_stop_index;
    std::string start_stop_name;
    std::string dest_stop_name;
    double total_distance;
    double total_walking_time;
    double bus_distance;
    double walk_to_start_stop;
    double walk_from_dest_stop;
    bool valid;
};

int main(){
    std::ifstream user_file("route_info.json");
    
    if (!user_file.is_open()){
        std::cerr << "Could not open route_info.json! File not found." << std::endl;
        return 1;
    }

    json route_info;
    user_file >> route_info;
    user_file.close();

    std::string start_address = route_info["start_address"];
    std::string dest_address = route_info["dest_address"];
    
    // Extract 5 closest stops for start location
    std::vector<StopInfo> start_stops;
    for (const auto& stop : route_info["start_closest_5_stops"]) {
        StopInfo info;
        info.index = stop["index"];
        info.name = stop["name"];
        info.road_distance_miles = stop["road_distance_miles"];
        info.walking_duration_minutes = stop["walking_duration_minutes"];
        info.lat = stop["lat"];
        info.lon = stop["lon"];
        info.straight_distance = stop["straight_distance"];
        start_stops.push_back(info);
    }
    
    // Extract 5 closest stops for destination location
    std::vector<StopInfo> dest_stops;
    for (const auto& stop : route_info["dest_closest_5_stops"]) {
        StopInfo info;
        info.index = stop["index"];
        info.name = stop["name"];
        info.road_distance_miles = stop["road_distance_miles"];
        info.walking_duration_minutes = stop["walking_duration_minutes"];
        info.lat = stop["lat"];
        info.lon = stop["lon"];
        info.straight_distance = stop["straight_distance"];
        dest_stops.push_back(info);
    }

    std::cout << "Analyzing routes from: " << start_address << std::endl;
    std::cout << "To: " << dest_address << std::endl;
    std::cout << "Using " << start_stops.size() << " start stops and " << dest_stops.size() << " destination stops" << std::endl;

    // Read the route distances CSV
    std::ifstream file("c1_route_distances.csv");
    if (!file.is_open()){
        std::cerr << "Could not open c1_route_distances.csv!" << std::endl;
        return 1;
    }
    
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

    // Collect all unique intersection indices including start and dest stops
    std::set<int> unique_intersections;
    for (int i = 1; i < csvData.size(); i++){
        if (csvData[i].size() < 2 || csvData[i][0].empty() || csvData[i][1].empty()) {
            continue;
        }
        
        try {
            int index1 = std::stoi(csvData[i][0]);
            int index2 = std::stoi(csvData[i][1]);
            unique_intersections.insert(index1);
            unique_intersections.insert(index2);
        } catch (const std::exception& e) {
            std::cerr << "Error converting row " << i << ": " << e.what() << std::endl;
            continue;
        }
    }
    
    // Add all start and destination stops to the set
    for (const auto& stop : start_stops) {
        unique_intersections.insert(stop.index);
    }
    for (const auto& stop : dest_stops) {
        unique_intersections.insert(stop.index);
    }
    
    std::cout << "Found " << unique_intersections.size() << " unique intersections in network" << std::endl;
    
    // Create mapping from original indices to graph vertices (0 = user start, 1 = user dest, 2+ = stops)
    std::map<int, int> index_to_vertex;
    int vertex_counter = 2; // Start from 2 (0 = user start, 1 = user dest)
    
    for (int original_index : unique_intersections) {
        index_to_vertex[original_index] = vertex_counter;
        vertex_counter++;
    }

    int user_start_vertex = 0;
    int user_dest_vertex = 1;
    int total_vertices = unique_intersections.size() + 2; // +2 for user start and dest
    Graph merced(total_vertices, total_vertices * 2);
    
    // Set the reverse mapping in the graph (vertex -> original index)
    for (const auto& pair : index_to_vertex) {
        merced.setVertexMapping(pair.second, pair.first);
    }

    std::cout << "Building graph with " << total_vertices << " vertices..." << std::endl;

    // Add all intersection edges using mapped vertices
    for (int i = 1; i < csvData.size(); i++){
        if (csvData[i].size() < 4 || csvData[i][0].empty() || csvData[i][1].empty()) {
            continue;
        }
        
        try {
            int original_start = std::stoi(csvData[i][0]);
            int original_end = std::stoi(csvData[i][1]);
            double distance = std::stod(csvData[i][3]);
            
            int mapped_start = index_to_vertex[original_start];
            int mapped_end = index_to_vertex[original_end];
            
            merced.addEdge(mapped_start, mapped_end, distance);
        } catch (const std::exception& e) {
            std::cerr << "Error processing edge in row " << i << ": " << e.what() << std::endl;
            continue;
        }
    }

    // Add edges from user start address to all 5 closest start stops
    for (const auto& start_stop : start_stops) {
        int mapped_stop = index_to_vertex[start_stop.index];
        merced.addEdge(user_start_vertex, mapped_stop, start_stop.road_distance_miles);
    }

    // Add edges from all 5 closest destination stops to user destination address
    for (const auto& dest_stop : dest_stops) {
        int mapped_stop = index_to_vertex[dest_stop.index];
        merced.addEdge(mapped_stop, user_dest_vertex, dest_stop.road_distance_miles);
    }

    std::cout << "Graph built successfully. Running Dijkstra from each start stop..." << std::endl;

    // Store all route results
    std::vector<RouteResult> all_routes;

    // For each start stop, run Dijkstra to find distances to all destination stops
    for (const auto& start_stop : start_stops) {
        if (index_to_vertex.find(start_stop.index) == index_to_vertex.end()) {
            continue;
        }
        
        int start_vertex = index_to_vertex[start_stop.index];
        
        std::cout << "Running Dijkstra from stop " << start_stop.index 
                  << " (" << start_stop.name << ")" << std::endl;
        
        // Run Dijkstra from this start stop
        std::vector<double> dist(total_vertices, std::numeric_limits<double>::infinity());
        std::vector<bool> visited(total_vertices, false);
        std::vector<int> parent(total_vertices, -1);
        
        dist[start_vertex] = 0;

        for (int count = 0; count < total_vertices - 1; count++){
            double min_distance = std::numeric_limits<double>::infinity(); 
            int min_vertex = -1;
            
            for (int i = 0; i < total_vertices; i++){
                if (!visited[i] && dist[i] < min_distance){
                    min_distance = dist[i];
                    min_vertex = i;
                }
            }

            if (min_vertex == -1) break;
            visited[min_vertex] = true;

            for (int j = 0; j < total_vertices; j++){
                if (!std::isinf(merced.W[min_vertex][j]) && !visited[j] && !std::isinf(dist[min_vertex])){
                    if (dist[min_vertex] + merced.W[min_vertex][j] < dist[j]) {
                        dist[j] = dist[min_vertex] + merced.W[min_vertex][j];
                        parent[j] = min_vertex;
                    }
                }
            }
        }
        
        // Check distances to all destination stops
        for (const auto& dest_stop : dest_stops) {
            if (index_to_vertex.find(dest_stop.index) == index_to_vertex.end()) {
                continue;
            }
            
            int dest_vertex = index_to_vertex[dest_stop.index];
            
            RouteResult result;
            result.start_stop_index = start_stop.index;
            result.dest_stop_index = dest_stop.index;
            result.start_stop_name = start_stop.name;
            result.dest_stop_name = dest_stop.name;
            result.walk_to_start_stop = start_stop.road_distance_miles;
            result.walk_from_dest_stop = dest_stop.road_distance_miles;
            result.bus_distance = dist[dest_vertex];
            result.total_distance = start_stop.road_distance_miles + dist[dest_vertex] + dest_stop.road_distance_miles;
            result.total_walking_time = start_stop.walking_duration_minutes + dest_stop.walking_duration_minutes;
            result.valid = !std::isinf(dist[dest_vertex]);
            
            all_routes.push_back(result);
        }
    }

    // Find the best route (minimum total distance)
    RouteResult best_route;
    best_route.valid = false;
    double min_total_distance = std::numeric_limits<double>::infinity();

    std::cout << "\n=== ALL ROUTE OPTIONS ===" << std::endl;
    for (const auto& route : all_routes) {
        if (route.valid) {
            std::cout << "Route via: " << route.start_stop_name << " → " << route.dest_stop_name << std::endl;
            std::cout << "  Walk to start stop: " << route.walk_to_start_stop << " miles" << std::endl;
            std::cout << "  Bus distance: " << route.bus_distance << " miles" << std::endl;
            std::cout << "  Walk from dest stop: " << route.walk_from_dest_stop << " miles" << std::endl;
            std::cout << "  Total distance: " << route.total_distance << " miles" << std::endl;
            std::cout << "  Total walking time: " << route.total_walking_time << " minutes" << std::endl;
            std::cout << "---" << std::endl;
            
            if (route.total_distance < min_total_distance) {
                min_total_distance = route.total_distance;
                best_route = route;
            }
        }
    }

    if (best_route.valid) {
        std::cout << "\n=== OPTIMAL ROUTE ===" << std::endl;
        std::cout << "From: " << start_address << std::endl;
        std::cout << "To: " << dest_address << std::endl;
        std::cout << "Best route found!" << std::endl;
        std::cout << "Start stop: " << best_route.start_stop_name << " (ID: " << best_route.start_stop_index << ")" << std::endl;
        std::cout << "Destination stop: " << best_route.dest_stop_name << " (ID: " << best_route.dest_stop_index << ")" << std::endl;
        std::cout << "Walk to start stop: " << best_route.walk_to_start_stop << " miles" << std::endl;
        std::cout << "Bus distance: " << best_route.bus_distance << " miles" << std::endl;
        std::cout << "Walk from dest stop: " << best_route.walk_from_dest_stop << " miles" << std::endl;
        std::cout << "Total distance: " << best_route.total_distance << " miles" << std::endl;
        std::cout << "Total walking time: " << best_route.total_walking_time << " minutes" << std::endl;
        
        // Save best route results to a JSON file
        json result_json;
        result_json["optimal_route"] = {
            {"start_address", start_address},
            {"dest_address", dest_address},
            {"start_stop_index", best_route.start_stop_index},
            {"start_stop_name", best_route.start_stop_name},
            {"dest_stop_index", best_route.dest_stop_index},
            {"dest_stop_name", best_route.dest_stop_name},
            {"walk_to_start_stop_miles", best_route.walk_to_start_stop},
            {"bus_distance_miles", best_route.bus_distance},
            {"walk_from_dest_stop_miles", best_route.walk_from_dest_stop},
            {"total_distance_miles", best_route.total_distance},
            {"total_walking_time_minutes", best_route.total_walking_time}
        };
        
        result_json["all_routes"] = json::array();
        for (const auto& route : all_routes) {
            if (route.valid) {
                result_json["all_routes"].push_back({
                    {"start_stop_index", route.start_stop_index},
                    {"start_stop_name", route.start_stop_name},
                    {"dest_stop_index", route.dest_stop_index},
                    {"dest_stop_name", route.dest_stop_name},
                    {"walk_to_start_stop_miles", route.walk_to_start_stop},
                    {"bus_distance_miles", route.bus_distance},
                    {"walk_from_dest_stop_miles", route.walk_from_dest_stop},
                    {"total_distance_miles", route.total_distance},
                    {"total_walking_time_minutes", route.total_walking_time}
                });
            }
        }
        
        std::ofstream result_file("optimal_route_results.json");
        result_file << result_json.dump(2);
        result_file.close();
        
        std::cout << "Results saved to optimal_route_results.json" << std::endl;
    } else {
        std::cout << "No valid routes found between any start and destination stops!" << std::endl;
        return 1;
    }

    return 0;
}
