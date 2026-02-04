#ifndef GRAPH_H
#define GRAPH_H

#include "Node.h"
#include "Edge.h"
#include <iostream>
#include <climits>
#include <limits>
#include <cmath>
#include <vector>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <map>
#include <string>
#include "ArrayList.h"

class Graph{
public:
	int V; //holds # of vertices we have
	int E; //holds # of edges we have
	double** W; //declaration of dynamically allocated 2D matrix that informs whether there is an edge or not between i and j and holds the edge weight
	std::map<int, int> vertexToOriginalIndex;  // declaration of map that maps the graph vertex to original intersection index
    std::map<int, std::string> intersectionNames; // Map of original intersection index -> Name

	Graph(int V, int E){
		//set the user passed values to the values of the graph attributes
		this->V = V;
		this->E = E;
		//initialization of array of size V of pointers 
		W = new double*[V];
		for (int i = 0; i < V; i++){
			//set each pointer to point to an array of doubles of size V
			W[i] = new double[V];
			for (int j = 0; j < V; j++){
				//if row and column are equal (aka no edge) set the weight to 0
				if (i == j){
					W[i][j] = 0;
				}
				//otherwise set the weight of the edge to infinity as unknown
				else{
					W[i][j] = std::numeric_limits<double>::infinity();
				}
			}
		}
	}
	
	// Method to set the mapping from graph vertex to original intersection index
	void setVertexMapping(int graphVertex, int originalIndex) {
		vertexToOriginalIndex[graphVertex] = originalIndex;
	}

	//method to add an edge between 2 user defined vertices with a user defined weight
	void addEdge(int u, int v, double w){
		W[u][v] = w; // w is effectively "weight" or "distance"
	}

    // Method to read bus, stop distances from a CSV file and add edges to the graph
    // Requires a mapping from original intersection indices to graph vertices
    void addBusEdgesFromCSV(const std::string& filename, std::map<int, int>& indexToVertex) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Warning: Could not open bus file: " << filename << std::endl;
            return;
        }

        std::string line;
        std::getline(file, line); // Skip header
        while (std::getline(file, line)) {
            if (line.empty()) continue;
            std::stringstream ss(line);
            std::string idx1Str, idx2Str, temp, distStr;
            
            // Expected format: index1,index2,names,distance
            std::getline(ss, idx1Str, ','); // Index1
            std::getline(ss, idx2Str, ','); // Index2
            std::getline(ss, temp, ',');    // Names (ignored)
            std::getline(ss, distStr, ','); // Distance
            
            try {
                if (idx1Str.empty() || idx2Str.empty() || distStr.empty()) continue;

                int u = std::stoi(idx1Str);
                int v = std::stoi(idx2Str);
                double dist = std::stod(distStr);
                
                //Only add if these stops exist in our map
				//counts number of times key u in map, since dictionary keys unique
                if (indexToVertex.count(u) && indexToVertex.count(v)) {
					//gets the values associated with keys u and v
                    int map_u = indexToVertex[u];
                    int map_v = indexToVertex[v];
                    // Add directed edge with the specific bus distance
                    addEdge(map_u, map_v, dist);
                }
            } catch (...) {
                // Ignore parsing errors for individual lines
            }
        }
        file.close();
    }

    // Method to read bus stop names from a CSV file (Index, StopName)
    void loadNamesFromCSV(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) return;
        
        std::string line;
        std::getline(file, line); // Skip header (Index, Stop)
        while (std::getline(file, line)) {
            if (line.empty()) continue;
            std::stringstream ss(line);
            std::string idxStr, name;
            
            if (std::getline(ss, idxStr, ',') && std::getline(ss, name, ',')) {
                 // Trim whitespace from name if needed
                size_t first = name.find_first_not_of(" \t\r\n");
				//if the first letter of the name exists then continue to look the end
                if (first == std::string::npos) continue;
                size_t last = name.find_last_not_of(" \t\r\n");
                name = name.substr(first, (last - first + 1));
                
                try {
					//convert the index of the current stop name to integer
                    int idx = std::stoi(idxStr);
					//add the stop name to the map where index is key and value is stop name
                    intersectionNames[idx] = name;
                } catch (...) {}
            }
        }
        file.close();
    }

	void dijkstra(int source){
		std::ofstream graph_log("logs/graph_dijkstra.log", std::ios::app);
		ArrayList<double> dist; //array to hold the distances from the source vertex
		ArrayList<double> parent; //array to track the previous vertex in the shortest path
		ArrayList<bool> visited; //array to keep track of the visitied vertices

		for (int i = 0; i < V; i++){
			dist.append(std::numeric_limits<double>::infinity()); //initialize all distances to infinity
			visited.append(false); // initialize all vertexes visited as false
			parent.append(-1); // initialize all parents -1 as default value, no parents so far
		}
		dist[source] = 0; // set distance to source vertex 0

		for (int count = 0; count < V - 1; count++){ //V - 1 because we already know distance to source 
			double min_distance = std::numeric_limits<double>::infinity(); //min_distance is intially infinty
        	int min_vertex = -1; //default value for the min_vertex index
			// iterate through all vertices to find the unvisited one with the smallest dist[i], updating min_distance and min_vertex accordingly
			for (int i = 0; i < V; i++){ 
				if (!visited[i] && dist[i] < min_distance){ //if the vertex is not visited and the distance to the vertex is less than the current min_distance
					min_distance = dist[i]; //update and finalize the min_distance for this vertex
					min_vertex = i; //set the current min_vertex to ith vertex
				}
			}
			//so by the time this for loop finishes we will have found the next vertex with the smallest distance 
			// if no vertex found, break
			if (min_vertex == -1) break;

			// Mark vertex as visited before processing edges
			visited[min_vertex] = true;
			
			//for each edge that is going out of the min_vertex, make sure there is a valid edge and not visited
			for (int j = 0; j < V; j++){
				if (!std::isinf(W[min_vertex][j]) && visited[j] == false && !std::isinf(dist[min_vertex])){ //if these conditions satisfied then check to make sure the distance to the min_vertex is not infinity
                    double new_dist = dist[min_vertex] + W[min_vertex][j]; // update the distance to the vertices directly reachable from the current min_vertex
                    if (new_dist < dist[j]) { // when the new_distance is less than the currently known distance to the directly reachable vertex
                        dist[j] = new_dist;     // Update distance to the directly reachable vertex
                        parent[j] = min_vertex; // Update parent only if a shorter path is found
                    }
				}
			}
		}
		
		// Save results to CSV file
		graph_log << "Saving results to CSV file..." << std::endl;
		
		// For vertex 0 (user address), read from route_info.json
		std::ifstream routeInfoFile("src/python/route_info.json"); // Open JSON file
		if (routeInfoFile.is_open()) { // Check if file opened
			std::string routeInfoContent((std::istreambuf_iterator<char>(routeInfoFile)), // first iterator initialized with file stream so represents the beginning of the file, 2nd one is the default iterator and represents the end
                                        std::istreambuf_iterator<char>());
			routeInfoFile.close(); // Close file
			
			// Parse start address for vertex 0
			size_t startAddressPos = routeInfoContent.find("\"start_address\":"); // Find start_address key
			if (startAddressPos != std::string::npos) { // If found
				size_t startQuote = routeInfoContent.find("\"", startAddressPos + 16); // Find opening quote of value
				size_t endQuote = routeInfoContent.find("\"", startQuote + 1); // Find closing quote
				if (startQuote != std::string::npos && endQuote != std::string::npos) { // If both quotes found
					std::string startAddress = routeInfoContent.substr(startQuote + 1, endQuote - startQuote - 1); // Extract address
					intersectionNames[-1] = startAddress; // Store with key -1 for user address
				}
			}
		}
		
		std::ofstream outFile("dijkstra_paths.csv");
		outFile << "Destination,Destination_Name,Distance_Miles,Path,Path_Names" << std::endl;
		
		// Loop through all vertices to output shortest paths for reachable destinations
		for (int i = 0; i < V; i++) {
			// Only process vertices that are not the source and have finite distance 
			if (i != source && !std::isinf(dist[i])) {
				// Reconstruct the shortest path from source to vertex i using parent pointers
				std::vector<int> path; // Vector to hold the sequence of vertices in the path
				int current = i; // Start from the destination vertex
				// Traverse backwards from destination to source via parents
				while (current != -1 && current != source) {
					path.push_back(current); // Add current vertex to path
					current = parent[current]; // Move to the parent vertex
				}
				path.push_back(source); // Add the source vertex to the path, path to each vertex will be examined individually
				std::reverse(path.begin(), path.end()); // Reverse to get source-to-destination order
				
				// Calculate the total real-world distance along the path
				double totalDistanceMiles = 0.0; // Accumulator for total distance in miles
				// Iterate over each edge in the path (from vertex j to j+1)
				for (size_t j = 0; j < path.size() - 1; j++) {
					int fromVertex = path[j]; // Starting vertex of the edge
					int toVertex = path[j + 1]; // Ending vertex of the edge
					
                    // Use the graph weight directly. 
                    // This trusts that graph_builder.cpp populated W with the most accurate 
                    // distance (whether it be walking or a generic bus edge).
					totalDistanceMiles += W[fromVertex][toVertex];
				}
				
				// Get the name of the destination using its original index
				int destOriginalIndex = (i == 0) ? -1 : vertexToOriginalIndex[i]; // if not source then -1 so look for the original index and save that in destOriginalIndex
				std::string destName = intersectionNames.count(destOriginalIndex) ? // if count returns 1 meaning the name of the index destOriginalIndex is in intersectionNames, then get the name of the stop associated with that index
									  intersectionNames[destOriginalIndex] : "Unknown"; // Default to "Unknown" if not found
				
				// Write the destination vertex, name, and total distance to CSV
				outFile << i << "," << destName << "," << totalDistanceMiles << ",";
				
				// Write the numeric path 
				for (size_t j = 0; j < path.size(); j++) {
					outFile << path[j]; // Output vertex number
					if (j < path.size() - 1) outFile << " -> "; // Add arrow separator if not last
				}
				outFile << ","; // Comma separator for next field
				
				// Write the path with intersection names
				for (size_t j = 0; j < path.size(); j++) {
					int pathOriginalIndex = (path[j] == 0) ? -1 : vertexToOriginalIndex[path[j]]; // Get original index
					std::string pathName = intersectionNames.count(pathOriginalIndex) ? 
										  intersectionNames[pathOriginalIndex] : "Unknown"; // Get name or "Unknown"
					outFile << pathName; // Output name
					if (j < path.size() - 1) outFile << " -> "; // Add arrow separator if not last
				}
				outFile << std::endl; // End the CSV row
			}
		}
		outFile.close(); // Close the output file
		graph_log << "Results saved to dijkstra_paths.csv" << std::endl; // Confirmation message
	}
};

#endif
