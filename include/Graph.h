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
		W[u][v] = w;
	}

	void dijkstra(int source){
		ArrayList<double> dist; //array to hold the distances from the source vertex
		ArrayList<double> parent; //array to track the previous vertex in the shortest path
		ArrayList<bool> visited; //array to keep track of the visitied vertices

		for (int i = 0; i < V; i++){
			dist.append(std::numeric_limits<double>::infinity()); //initialize all distances to infinity
			visited.append(false); // all visited false
			parent.append(-1); //all parents -1 as default value, no parents
		}
		dist[source] = 0; // set distance to source vertex 0

		for (int count = 0; count < V - 1; count++){
			double min_distance = std::numeric_limits<double>::infinity(); //min_distance is intially infinty
        	int min_vertex = -1; //default value for the min_vertex index
			// iterate through all vertices to find the unvisited one with the smallest dist[i], updating min_distance and min_vertex accordingly
			for (int i = 0; i < V; i++){ 
				if (!visited[i] && dist[i] < min_distance){ //if the vertex is not visited and the distance to the vertex from the source is less than the current min_distance
					min_distance = dist[i]; //update and finalize the min_distance 
					min_vertex = i; //set the current min_vertex to ith vertex
				}
			}

			// if no vertex found, break
			if (min_vertex == -1) break;

			// Mark vertex as visited before processing edges
			visited[min_vertex] = true;
			
			//for each edge that is going out of the min_vertex, make sure there is a valid edge (not infinity) and not visited
			for (int j = 0; j < V; j++){
				if (!std::isinf(W[min_vertex][j]) && visited[j] == false && !std::isinf(dist[min_vertex])){ //if these conditions satisfied then check to make sure the distance to the min_vertex is not infinity
					dist[j] = std::min(dist[j], dist[min_vertex] + W[min_vertex][j]); //check if current distance to vertex j is less than the distance from min_vertex plus weight of edge 
					parent[j] = min_vertex; //update parent of vertex j as the min_vertex
				}
			}
		}
		
		// Save results to CSV file
		std::cout << "Saving results to CSV file..." << std::endl;
		
		// Read intersection names from all_intersections.csv
		std::map<int, std::string> intersectionNames; // Map to store intersection index to name
		std::ifstream routeFile("../../data/all_intersections.csv"); // Open CSV file for reading
		std::string line; // String to hold each line from the file
		
		if (routeFile.is_open()) { // Check if file opened successfully
			std::getline(routeFile, line); // Skip header line
			while (std::getline(routeFile, line)) { // Read each subsequent line
				if (line.empty()) continue; // Skip empty lines
				
				std::stringstream ss(line); // Create stringstream for parsing CSV
				std::string idxStr, name, lat, lon; // Variables for CSV fields
				std::getline(ss, idxStr, ','); // Extract index field
				std::getline(ss, name, ','); // Extract name field
				std::getline(ss, lat, ','); // Extract latitude 
				std::getline(ss, lon, ','); // Extract longitude 
				
				if (idxStr.empty() || name.empty()) continue; // Skip invalid rows
				
				int idx = std::stoi(idxStr); // Convert index to int
				intersectionNames[idx] = name; // Store in map
			}
			routeFile.close(); // Close file
		}
		
		// For vertex 0 (user address), read from route_info.json
		std::ifstream routeInfoFile("../python/route_info.json"); // Open JSON file
		if (routeInfoFile.is_open()) { // Check if file opened
			std::string routeInfoContent((std::istreambuf_iterator<char>(routeInfoFile)), // Read entire file into string
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
		
		// Read distances from all_stop_distances.csv (the actual file being used)
		std::map<std::pair<int, int>, double> realDistances; // Map to store real distances between intersections
		std::ifstream distanceFile("../../data/all_stop_distances.csv"); // Open CSV file for distances
		
		if (distanceFile.is_open()) { // Check if file opened successfully
			std::getline(distanceFile, line); // Skip header line
			while (std::getline(distanceFile, line)) { // Read each subsequent line
				// Skip empty rows
				if (line.empty()) continue; // Skip if line is empty
				
				std::stringstream ss(line); // Create stringstream for parsing
				std::string idx1Str, idx2Str, intersections, distanceStr; // Variables for fields
				std::getline(ss, idx1Str, ','); // Extract first intersection index
				std::getline(ss, idx2Str, ','); // Extract second intersection index
				std::getline(ss, intersections, ','); // Extract intersections string 
				std::getline(ss, distanceStr, ','); // Extract distance string
				
				if (idx1Str.empty() || idx2Str.empty() || distanceStr.empty()) continue; // Skip invalid rows
				
				int idx1 = std::stoi(idx1Str); // Convert first index to int
				int idx2 = std::stoi(idx2Str); // Convert second index to int
				double distance = std::stod(distanceStr); // Convert distance to double
				
				realDistances[{idx1, idx2}] = distance; // Store distance for idx1 to idx2
				realDistances[{idx2, idx1}] = distance; // Store distance for idx2 to idx1 (bidirectional)
			}
			distanceFile.close(); // Close file
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
				path.push_back(source); // Add the source vertex to the path
				std::reverse(path.begin(), path.end()); // Reverse to get source-to-destination order
				
				// Calculate the total real-world distance along the path
				double totalDistanceMiles = 0.0; // Accumulator for total distance in miles
				// Iterate over each edge in the path (from vertex j to j+1)
				for (size_t j = 0; j < path.size() - 1; j++) {
					int fromVertex = path[j]; // Starting vertex of the edge
					int toVertex = path[j + 1]; // Ending vertex of the edge
					
					// Map graph vertices back to original intersection indices
					int fromOriginal = (fromVertex == 0) ? -1 : vertexToOriginalIndex[fromVertex]; // -1 for user address
					int toOriginal = (toVertex == 0) ? -1 : vertexToOriginalIndex[toVertex]; // -1 for user address
					
					// Special handling for edges involving the user address (vertex 0)
					if (fromVertex == 0 || toVertex == 0) {
						// Use walking distance from Dijkstra's weight matrix
						totalDistanceMiles += W[fromVertex][toVertex];
					} else if (realDistances.count({fromOriginal, toOriginal})) {
						// Use actual distance from CSV if available
						totalDistanceMiles += realDistances[{fromOriginal, toOriginal}];
					} else {
						// Fallback to weight matrix distance
						totalDistanceMiles += W[fromVertex][toVertex];
					}
				}
				
				// Get the name of the destination using its original index
				int destOriginalIndex = (i == 0) ? -1 : vertexToOriginalIndex[i]; // -1 if user address
				std::string destName = intersectionNames.count(destOriginalIndex) ? 
									  intersectionNames[destOriginalIndex] : "Unknown"; // Default to "Unknown" if not found
				
				// Write the destination vertex, name, and total distance to CSV
				outFile << i << "," << destName << "," << totalDistanceMiles << ",";
				
				// Write the numeric path (sequence of vertex numbers)
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
		std::cout << "Results saved to dijkstra_paths.csv" << std::endl; // Confirmation message
	}
};

#endif