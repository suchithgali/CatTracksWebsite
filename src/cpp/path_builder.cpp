#include <iostream>
#include "Graph.h"
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <algorithm>
#include <cctype>
#include "json.hpp"

using json = nlohmann::json;



int main(){
    //create a file stream to read in route_info.json
    std::ifstream user_file("src/python/route_info.json");
//declares a json object and then reads the entire file into the json object and automatically makes key value pairs
    json route_info;
    user_file >> route_info;
    user_file.close();

    //store start address, lat, lng, closest stop to start address, and distance btwn in variables
    std::string destination_stop_address = route_info["dest_address"];
    double destination_stop_lat = route_info["dest_lat"];
    double destination_stop_lng = route_info["dest_lon"];  
    std::string destination_closest_stop = route_info["dest_closest_stop_name"];
    double dest_distance_from_stop = route_info["dest_distance_from_stop"];
    std::vector<std::vector<std::string>> walking_instructions = route_info["start_walking_instructions"];

    //print out stored variables
    std::cout << "Destination Address: " << destination_stop_address << std::endl;
    std::cout << "Coordinates: (" << destination_stop_lat << ", " << destination_stop_lng << ")" << std::endl;
    std::cout << "Closest intersection: " << destination_closest_stop << std::endl;
    std::cout << "Distance to intersection: " << dest_distance_from_stop << " miles" << std::endl;
    
    for (int i = 0; i < walking_instructions.size(); i++){
        for (int j = 0; j < walking_instructions[i].size(); j++){
            std::cout << walking_instructions[i][j];
        }
        std::cout << std::endl;
    }

    std::ifstream routeFile("dijkstra_paths.csv"); // Open CSV file for reading
    std::string actual_path; //Map to store the correct path corresponding to the desired destination
	std::string path_line; // String to hold each line from the file

    if (routeFile.is_open()) { // Check if file opened successfully
			std::getline(routeFile, path_line); // Skip header line
			while (std::getline(routeFile, path_line)) { // Read each subsequent line
				if (path_line.empty()) continue; // Skip empty lines
				
				std::stringstream ss(path_line); // Create stringstream for parsing CSV
				std::string dest_idxStr, dest_name, dest_miles, dest_path, dest_path_names; // Variables for CSV fields
				std::getline(ss, dest_idxStr, ','); // Extract index field
				std::getline(ss, dest_name, ','); // Extract name field
				std::getline(ss, dest_miles, ','); // Extract latitude 
				std::getline(ss, dest_path, ','); // Extract longitude 
                std::getline(ss, dest_path_names, ','); // Extract longitude 
				
				if (dest_name != destination_closest_stop){
                    continue; // Skip invalid rows
                }
                else{
                    actual_path = dest_path_names;
                }
			}
			routeFile.close(); // Close file
		}

    //delcare vector to hold the optimal stops
    std::vector<std::string> optimal_stops;
    //parse the actual path by splitting on " -> "
    std::string delimiter = " -> ";
    size_t pos = 0;
    std::string path_copy = actual_path;
    while ((pos = path_copy.find(delimiter)) != std::string::npos) {
        std::string token = path_copy.substr(0, pos);
        // trim leading/trailing spaces
        token.erase(token.begin(), std::find_if(token.begin(), token.end(), [](unsigned char ch) { return !std::isspace(ch); }));
        token.erase(std::find_if(token.rbegin(), token.rend(), [](unsigned char ch) { return !std::isspace(ch); }).base(), token.end());
        optimal_stops.push_back(token);
        path_copy.erase(0, pos + delimiter.length());
    }
    if (!path_copy.empty()) {
        // trim the last token
        path_copy.erase(path_copy.begin(), std::find_if(path_copy.begin(), path_copy.end(), [](unsigned char ch) { return !std::isspace(ch); }));
        path_copy.erase(std::find_if(path_copy.rbegin(), path_copy.rend(), [](unsigned char ch) { return !std::isspace(ch); }).base(), path_copy.end());
        optimal_stops.push_back(path_copy);
    }

    //Check each bus route
    std::vector<std::string> bus_files = {
        "data/bus_routes/c1_stops.csv",
        "data/bus_routes/c2_stops.csv",
        "data/bus_routes/e1_stops.csv",
        "data/bus_routes/e2_stops.csv",
        "data/bus_routes/fastcat_stops.csv",
        "data/bus_routes/fastcat_2_stops.csv",
        "data/bus_routes/g_line_stops.csv",
        "data/bus_routes/yosemite_express_stops.csv",
        "data/bus_routes/bobcat_express_stops.csv"
    };

    //declares map to hold the bus name and its corresponding stops
    std::map<std::string, std::vector<std::string>> bus_routes;

    // Load all bus routes once (Performance optimization)
    for (const auto& file : bus_files){
        std::ifstream bus_file(file);
        if (!bus_file.is_open()){
            std::cerr << "Could not open " << file << std::endl;
            continue;
        }
        
        std::vector<std::string> stops;
        std::string line;
        bool is_first_line = true;
        while (std::getline(bus_file, line)){
            if (is_first_line) { is_first_line = false; continue; }
            std::stringstream ss(line);
            std::string index, stop_name;
            std::getline(ss, index, ',');
            std::getline(ss, stop_name, ',');
            
            // Trim stop_name
            if (!stop_name.empty()) {
                stop_name.erase(stop_name.begin(), std::find_if(stop_name.begin(), stop_name.end(), [](unsigned char ch) { return !std::isspace(ch); }));
                stop_name.erase(std::find_if(stop_name.rbegin(), stop_name.rend(), [](unsigned char ch) { return !std::isspace(ch); }).base(), stop_name.end());
            }
            stops.push_back(stop_name);
        }
        bus_file.close();

        // Extract bus name
        size_t start = file.find_last_of('/') + 1;
        size_t end = file.find('_', start);
        std::string bus_name = file.substr(start, end - start);
        
        bus_routes[bus_name] = stops;
    }

    // "Furthest Reach" Logic: Find the bus that takes us furthest along our path
    int curr_index = 1;
    while (curr_index < optimal_stops.size() - 1){
        std::string best_bus = "";
        int best_reach_idx = -1;
        int min_stops_count = 999999; // Tie-breaker: prefer bus with fewer intermediate stops

        for (const auto& entry : bus_routes) {
            const std::string& bus_name = entry.first;
            const std::vector<std::string>& stops = entry.second;

            // Does this bus stop at our current location?
            auto it_start = std::find(stops.begin(), stops.end(), optimal_stops[curr_index]);
            if (it_start == stops.end()) continue;

            // Does this bus connect to a future stop in our path?
            // Search backwards from the destination to find the furthest connection
            for (int k = optimal_stops.size() - 1; k > curr_index; --k) {
                if (k < best_reach_idx) break; // Optimization: can't beat current best reach

                // Check if this bus visits optimal_stops[k] AFTER current location
                auto it_end = std::find(it_start + 1, stops.end(), optimal_stops[k]);
                if (it_end != stops.end()) {
                    int stops_count = std::distance(it_start, it_end);
                    
                    if (k > best_reach_idx) {
                        // Found a strictly further reach
                        best_reach_idx = k;
                        best_bus = bus_name;
                        min_stops_count = stops_count;
                    } else if (k == best_reach_idx) {
                        // Same reach, check if this bus has fewer stops (likely an express route)
                        if (stops_count < min_stops_count) {
                            best_bus = bus_name;
                            min_stops_count = stops_count;
                        }
                    }
                    break; // Found furthest reach for this bus, move to next bus
                }
            }
        }

        if (best_reach_idx != -1) {
            std::cout << "Take " << best_bus << " from " << optimal_stops[curr_index] << " to " << optimal_stops[best_reach_idx] << std::endl;
            curr_index = best_reach_idx;
        } 
        else {
            std::cout << "Walk from " << optimal_stops[curr_index] << " to " << optimal_stops[curr_index + 1] << std::endl;
            curr_index++;
        }
    }

    
}