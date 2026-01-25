#include <iostream>
#include "Graph.h"
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include "json.hpp"

using json = nlohmann::json;



int main(){
    //create a file stream to read in route_info.json
    std::ifstream user_file("../python/route_info.json");
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
}