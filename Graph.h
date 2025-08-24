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
	
	}
};

#endif
