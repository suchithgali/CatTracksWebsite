#ifndef GRAPH_H
#define GRAPH_H

#include "Node.h"
#include "Edge.h"
#include <iostream>
#include <climits>
#include <vector>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <string>
#include <map>
#include "ArrayList.h"

class Graph{
public:
	int V;
	int E;
	int** W;

	Graph(int V, int E){
		//set the user passed values to the values of the graph attributes
		this->V = V;
		this->E = E;
		//declare array of size V of pointers 
		W = new int*[V];
		for (int i = 0; i < V; i++){
			//set each pointer to point to an array of ints of size V
			W[i] = new int[V];
			for (int j = 0; j < V; j++){
				//if row and column are equal (aka no edge) set the weight to 0
				if (i == j){
					W[i][j] = 0;
				}
				//otherwise set the weight of the edge to infinity as unknown
				else{
					W[i][j] = INT_MAX;
				}
			}
		}
	}

	//method to add an edge between 2 user defined vertices with a user defined weight
	void addEdge(int u, int v, int w){
		W[u][v] = w;
	}

	void dijkstra(Graph g, int source){
		ArrayList<int> dist;
		ArrayList<bool> visited;

		for (int i = 0; i < V; i++){
			dist.append(INT_MAX);
			visited.append(false);
		}
		dist[source] = 0;

		for (int count = 0; count < V - 1; count++){
			int min_distance = INT_MAX; 
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
				if (W[min_vertex][j] != INT_MAX && visited[j] == false && dist[min_vertex] != INT_MAX){
					dist[j] = std::min(dist[j], dist[min_vertex] + W[min_vertex][j]);
				}
			}
		}
		
		// Save results to CSV file
		std::cout << "Saving results to CSV file..." << std::endl;
		
		// Read vertex mapping file to get street names
		std::map<int, std::string> vertexNames;
		std::ifstream mappingFile("merced_vertex_mapping.csv");
		std::string line;
		
		if (mappingFile.is_open()) {
			std::getline(mappingFile, line); // Skip header
			while (std::getline(mappingFile, line)) {
				std::stringstream ss(line);
				std::string token;
				std::vector<std::string> tokens;
				
				// Parse CSV line
				while (std::getline(ss, token, ',')) {
					tokens.push_back(token);
				}
				
				if (tokens.size() >= 5) {
					int vertexIndex = std::stoi(tokens[0]);
					std::string description = tokens[4]; // Primary_Description column
					vertexNames[vertexIndex] = description;
				}
			}
			mappingFile.close();
		}
		
		std::ofstream csvFile("dijkstra_results.csv");
		
		if (csvFile.is_open()) {
			// Write CSV header with source information
			csvFile << "# Dijkstra shortest paths from source vertex " << source << "\n";
			csvFile << "# Source location: " << (vertexNames.count(source) ? vertexNames[source] : "Unknown location") << "\n";
			csvFile << "Vertex_Index,Distance_Miles,Status,Intersection_Name\n";
			
			// Conversion factor: meters to miles
			const double METERS_TO_MILES = 0.000621371;
			
			// Write data for each vertex
			for (int i = 0; i < V; i++) {
				csvFile << i << ",";
				if (dist[i] == INT_MAX) {
					csvFile << "UNREACHABLE,UNREACHABLE,";
				} else {
					double miles = dist[i] * METERS_TO_MILES;
					csvFile << miles << ",REACHABLE,";
				}
				
				// Add intersection name
				if (vertexNames.count(i)) {
					csvFile << vertexNames[i] << "\n";
				} else {
					csvFile << "Unknown intersection\n";
				}
			}
			
			csvFile.close();
			std::cout << "Results saved to 'dijkstra_results.csv'" << std::endl;
		} else {
			std::cout << "Error: Unable to open CSV file for writing!" << std::endl;
		}
	}
};

#endif
