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
    //create a file stream to read in route_info.json
    std::ifstream user_file("src/python/route_info.json");
    
    if (!user_file.is_open()){
        std::cerr << "Could not open route_info.json! Run find_nearest.py first." << std::endl;
        return 1;
    }

    //declares a json object and then reads the entire file into the json object and automatically makes key value pairs
    json route_info;
    user_file >> route_info;
    user_file.close();

    //store start address, lat, lng, closest stop to start address, and distance btwn in variables
    std::string departure_stop_address = route_info["start_address"];
    double departure_stop_lat = route_info["start_lat"];
    double departure_stop_lng = route_info["start_lon"];  
    int closest_stop = route_info["start_closest_stop"];
    double distance_to_stop = route_info["start_distance_to_stop"];

    //print out stored variables
    std::cout << "User Address: " << departure_stop_address << std::endl;
    std::cout << "Coordinates: (" << departure_stop_lat << ", " << departure_stop_lng << ")" << std::endl;
    std::cout << "Closest intersection: " << closest_stop << std::endl;
    std::cout << "Distance to intersection: " << distance_to_stop << " miles" << std::endl;

    // [New Logic] Collect unique intersections directly from the bus route files
    std::set<int> unique_intersections;
    
    // Define the bus files we will use for both vertices and edges
    std::vector<std::string> bus_files = {
        "data/bus_routes/c1_stop_distances.csv", "data/bus_routes/c2_stop_distances.csv", "data/bus_routes/e1_stop_distances.csv",
        "data/bus_routes/e2_stop_distances.csv", "data/bus_routes/fastcat_stop_distances.csv", "data/bus_routes/fastcat_2_stop_distances.csv",
        "data/bus_routes/g_line_stop_distances.csv", "data/bus_routes/yosemite_express_stop_distances.csv", "data/bus_routes/bobcat_express_stop_distances.csv"
    };

    std::cout << "Scanning bus route files to identify stops..." << std::endl;
    for (const auto& filename : bus_files) {
        std::ifstream file(filename);
        if (!file.is_open()) continue;
        
        std::string line;
        std::getline(file, line); // Skip header
        while (std::getline(file, line)) {
            if (line.empty()) continue;
            std::stringstream ss(line);
            std::string idx1Str, idx2Str;
            
            std::getline(ss, idx1Str, ',');
            std::getline(ss, idx2Str, ',');
            
            try {
                if (!idx1Str.empty()) unique_intersections.insert(std::stoi(idx1Str));
                if (!idx2Str.empty()) unique_intersections.insert(std::stoi(idx2Str));
            } catch (...) {}
        }
        file.close();
    }
    
    // Add the user's closest stop to the set
    unique_intersections.insert(closest_stop);
    // Tell the user how many intersections found
    std::cout << "Found " << unique_intersections.size() << " unique intersections in route" << std::endl;
    
    // Create mapping from original indices to graph vertices (0 = closest stop, 1-N = intersections)
    std::map<int, int> index_to_vertex;
    int vertex_counter = 1; // Start from 1 (0 is reserved for closest stop)
    
    //for each original index assign a vertex id starting from 1
    for (int original_index : unique_intersections) {
        index_to_vertex[original_index] = vertex_counter;
        vertex_counter++;
    }

    int user_vertex = 0;
    int total_vertices = unique_intersections.size() + 1; // +1 for user
    Graph merced(total_vertices, total_vertices * 2); // Estimate total edges in the graph
    
    // Set the reverse mapping in the graph (vertex -> original index)
    for (const auto& pair : index_to_vertex) {
        merced.setVertexMapping(pair.second, pair.first);
    }

    std::cout << "Building graph with " << total_vertices << " vertices..." << std::endl;

    // Add Bus Route edges to the graph (using bus_files defined above)

    std::cout << "Adding Direct Bus Edges via Graph::addBusEdgesFromCSV..." << std::endl;
    for (const auto& filename : bus_files) {
        merced.addBusEdgesFromCSV(filename, index_to_vertex);
    }
    
    std::cout << "Loading Bus Stop names..." << std::endl;
    for (const auto& dist_filename : bus_files) {
        // Convert "xyz_stop_distances.csv" to "xyz_stops.csv"
        std::string stops_filename = dist_filename;
        size_t pos = stops_filename.find("stop_distances");
        if (pos != std::string::npos) {
            stops_filename.replace(pos, 14, "stops"); // Replace "stop_distances" with "stops"
            merced.loadNamesFromCSV(stops_filename);
        }
    }

     // Add edge from user address (vertex 0) to closest stop
    int mapped_closest = index_to_vertex[closest_stop]; //get vertex id of closest_stop
    merced.addEdge(user_vertex, mapped_closest, distance_to_stop); //add edges
    merced.addEdge(mapped_closest, user_vertex, distance_to_stop);

    std::cout << "Added user address as vertex " << user_vertex << std::endl;
    std::cout << "Connected to intersection " << closest_stop << " (graph vertex " << mapped_closest << ")" << std::endl;
    std::cout << "Running Dijkstra from user address..." << std::endl;

    // Run Dijkstra from user address
    merced.dijkstra(user_vertex);

    std::cout << "Dijkstra complete! Results saved to dijkstra_paths.csv" << std::endl;
    return 0;


    
}