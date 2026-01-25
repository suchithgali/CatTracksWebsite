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
    std::ifstream user_file("../python/route_info.json");
    
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

    //creates a file stream to read in all_stop_distances.csv
    std::ifstream file("../../data/all_stop_distances.csv");
    
    //declare a variable to store the current line and a vector to store the csvData in each line
    std::string line;
    std::vector<std::vector<std::string>> csvData;


    //save the csv cells in each line in a string vector and push that to the 2D vector csvData
    while (std::getline(file, line)){ //reads the file line by line until we reach the end of the file
        std::stringstream ss(line); //converts the line into a string stream object so getline can read through the line making splitting easier
        std::string cell; //holds each individual cell value in the line
        std::vector<std::string> row; //vector of strings to hold all the cells from the current line

        while (std::getline(ss, cell, ',')){
            row.push_back(cell); //add the cells to the row vector
        }
        csvData.push_back(row); //add the row to the csvData vector
    }
    file.close();

    //initialize set to collect all unique intersection indices

    std::set<int> unique_intersections;
    for (int i = 1; i < csvData.size(); i++){
        // Skip empty rows
        if (csvData[i].size() < 2 || csvData[i][0].empty() || csvData[i][1].empty()) {
            std::cout << "Skipping empty row " << i << std::endl;
            continue;
        }
        
        try {
            int index1 = std::stoi(csvData[i][0]); //first index of ith row
            int index2 = std::stoi(csvData[i][1]); //second index of ith row
            unique_intersections.insert(index1); //add both the unique indexes to the set
            unique_intersections.insert(index2); 
        } catch (const std::exception& e) {
            std::cerr << "Error converting row " << i << ": " << e.what() << std::endl;
            return 1;
        }
    }
    
    // Add the user's closest stop to the set
    unique_intersections.insert(closest_stop);
    // Tell the user how many intersections found
    std::cout << "Found " << unique_intersections.size() << " unique intersections in route" << std::endl;
    
    // Create mapping from original indices to graph vertices (0 = closest stop, 1-N = intersections)
    // keys are the intersection indexes that come from the all_stop_distances.csv file, values are the vertex ID's for the graph
    std::map<int, int> index_to_vertex;
    int vertex_counter = 1; // Start from 1 (0 is reserved for closest stop)
    
    //for each original index in the csv file asign a vertex id starting from 1
    for (int original_index : unique_intersections) {
        index_to_vertex[original_index] = vertex_counter;
        std::cout << "Mapping intersection " << original_index << " -> vertex " << vertex_counter << std::endl;
        vertex_counter++; //increase the vertex id for each index
    }

    int user_vertex = 0;
    int total_vertices = unique_intersections.size() + 1; // +1 for user
    Graph merced(total_vertices, total_vertices * 2); // Estimate total edges in the graph
    
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
        //store original indexes and also distance btween the indexes
        int original_start = std::stoi(csvData[i][0]);
        int original_end = std::stoi(csvData[i][1]);
        double distance = std::stod(csvData[i][3]);
        
        //store the new vertex ids in variables
        int mapped_start = index_to_vertex[original_start];
        int mapped_end = index_to_vertex[original_end];
        //add edge using the vertex ids
        merced.addEdge(mapped_start, mapped_end, distance);
        // Do NOT add reverse edge - this is a directed bus route
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