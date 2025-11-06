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
	int V;
	int E;
	double** W;
	std::map<int, int> vertexToOriginalIndex;  // Maps graph vertex to original intersection index

	Graph(int V, int E){
		//set the user passed values to the values of the graph attributes
		this->V = V;
		this->E = E;
		//declare array of size V of pointers 
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
		ArrayList<double> dist;
		ArrayList<double> parent;
		ArrayList<bool> visited;

		for (int i = 0; i < V; i++){
			dist.append(std::numeric_limits<double>::infinity());
			visited.append(false);
			parent.append(-1);
		}
		dist[source] = 0;

		for (int count = 0; count < V - 1; count++){
			double min_distance = std::numeric_limits<double>::infinity(); 
        	int min_vertex = -1;
			for (int i = 0; i < V; i++){
				if (!visited[i] && dist[i] < min_distance){
					min_distance = dist[i];
					min_vertex = i;
				}
			}

			// Safety check: if no vertex found, break
			if (min_vertex == -1) break;

			// Mark vertex as visited BEFORE processing edges
			visited[min_vertex] = true;

			for (int j = 0; j < V; j++){
				if (!std::isinf(W[min_vertex][j]) && visited[j] == false && !std::isinf(dist[min_vertex])){
					dist[j] = std::min(dist[j], dist[min_vertex] + W[min_vertex][j]);
					parent[j] = min_vertex;
				}
			}
		}
		
		// Save results to CSV file
		std::cout << "Saving results to CSV file..." << std::endl;
		
		// Read intersection names from all_intersections.csv
		std::map<int, std::string> intersectionNames;
		std::ifstream routeFile("../../data/all_intersections.csv");
		std::string line;
		
		if (routeFile.is_open()) {
			std::getline(routeFile, line); // Skip header
			while (std::getline(routeFile, line)) {
				if (line.empty()) continue;
				
				std::stringstream ss(line);
				std::string idxStr, name, lat, lon;
				std::getline(ss, idxStr, ',');
				std::getline(ss, name, ',');
				std::getline(ss, lat, ',');
				std::getline(ss, lon, ',');
				
				if (idxStr.empty() || name.empty()) continue;
				
				int idx = std::stoi(idxStr);
				intersectionNames[idx] = name;
			}
			routeFile.close();
		}
		
		// For vertex 0 (user address), read from route_info.json
		std::ifstream routeInfoFile("../python/route_info.json");
		if (routeInfoFile.is_open()) {
			std::string routeInfoContent((std::istreambuf_iterator<char>(routeInfoFile)),
                                        std::istreambuf_iterator<char>());
			routeInfoFile.close();
			
			// Parse start address for vertex 0
			size_t startAddressPos = routeInfoContent.find("\"start_address\":");
			if (startAddressPos != std::string::npos) {
				size_t startQuote = routeInfoContent.find("\"", startAddressPos + 16);
				size_t endQuote = routeInfoContent.find("\"", startQuote + 1);
				if (startQuote != std::string::npos && endQuote != std::string::npos) {
					std::string startAddress = routeInfoContent.substr(startQuote + 1, endQuote - startQuote - 1);
					intersectionNames[-1] = startAddress; // Use -1 as key for user address
				}
			}
		}
		
		// Read distances from all_stop_distances.csv (the actual file being used)
		std::map<std::pair<int, int>, double> realDistances;
		std::ifstream distanceFile("../../data/all_stop_distances.csv");
		
		if (distanceFile.is_open()) {
			std::getline(distanceFile, line); // Skip header
			while (std::getline(distanceFile, line)) {
				// Skip empty rows
				if (line.empty()) continue;
				
				std::stringstream ss(line);
				std::string idx1Str, idx2Str, intersections, distanceStr;
				std::getline(ss, idx1Str, ',');
				std::getline(ss, idx2Str, ',');
				std::getline(ss, intersections, ',');
				std::getline(ss, distanceStr, ',');
				
				if (idx1Str.empty() || idx2Str.empty() || distanceStr.empty()) continue;
				
				int idx1 = std::stoi(idx1Str);
				int idx2 = std::stoi(idx2Str);
				double distance = std::stod(distanceStr);
				
				realDistances[{idx1, idx2}] = distance;
				realDistances[{idx2, idx1}] = distance; // Both directions
			}
			distanceFile.close();
		}
		
		std::ofstream outFile("dijkstra_paths.csv");
		outFile << "Destination,Destination_Name,Distance_Miles,Path,Path_Names" << std::endl;
		
		for (int i = 0; i < V; i++) {
			if (i != source && !std::isinf(dist[i])) {
				// Reconstruct path from source to vertex i
				std::vector<int> path;
				int current = i;
				while (current != -1 && current != source) {
					path.push_back(current);
					current = parent[current];
				}
				path.push_back(source);
				std::reverse(path.begin(), path.end());
				
				// Calculate real distance using original indices and actual distances
				double totalDistanceMiles = 0.0;
				for (size_t j = 0; j < path.size() - 1; j++) {
					int fromVertex = path[j];
					int toVertex = path[j + 1];
					
					// Get original indices
					int fromOriginal = (fromVertex == 0) ? -1 : vertexToOriginalIndex[fromVertex];
					int toOriginal = (toVertex == 0) ? -1 : vertexToOriginalIndex[toVertex];
					
					// For user address connections, use the distance from route_info.json
					if (fromVertex == 0 || toVertex == 0) {
						// This should be the walking distance to/from the closest stop
						// Use the value from Dijkstra calculation
						totalDistanceMiles += W[fromVertex][toVertex];
					} else if (realDistances.count({fromOriginal, toOriginal})) {
						totalDistanceMiles += realDistances[{fromOriginal, toOriginal}];
					} else {
						// Fallback to weight matrix
						totalDistanceMiles += W[fromVertex][toVertex];
					}
				}
				
				// Get destination name using original index
				int destOriginalIndex = (i == 0) ? -1 : vertexToOriginalIndex[i];
				std::string destName = intersectionNames.count(destOriginalIndex) ? 
									  intersectionNames[destOriginalIndex] : "Unknown";
				
				outFile << i << "," << destName << "," << totalDistanceMiles << ",";
				
				// Write numeric path
				for (size_t j = 0; j < path.size(); j++) {
					outFile << path[j];
					if (j < path.size() - 1) outFile << " -> ";
				}
				outFile << ",";
				
				// Write path with intersection names
				for (size_t j = 0; j < path.size(); j++) {
					int pathOriginalIndex = (path[j] == 0) ? -1 : vertexToOriginalIndex[path[j]];
					std::string pathName = intersectionNames.count(pathOriginalIndex) ? 
										  intersectionNames[pathOriginalIndex] : "Unknown";
					outFile << pathName;
					if (j < path.size() - 1) outFile << " -> ";
				}
				outFile << std::endl;
			}
		}
		outFile.close();
		std::cout << "Results saved to dijkstra_paths.csv" << std::endl;
	}
};

#endif