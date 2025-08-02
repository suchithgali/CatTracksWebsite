#ifndef GRAPH_H
#define GRAPH_H

#include "Node.h"
#include "Edge.h"
#include <iostream>
#include <climits>
#include <vector>
#include <algorithm>
#include "ArrayList.h"

class Graph{
public:
	int V;
	int E;
	int** W;

	Graph(int V, int E){
		this->V = V;
		this->E = E;
		W = new int*[V];
		for (int i = 0; i < V; i++){
			W[i] = new int[V];
			for (int j = 0; j < V; j++){
				if (i == j){
					W[i][j] = 0;
				}
				else{
					W[i][j] = INT_MAX;
				}
			}
		}
	}


	void addEdge(int u, int v, int w){
		W[u][v] = w;
	}

	void dijkstra(int source){
		ArrayList<int> dist;
		ArrayList<bool> visited;
		
		// Initialize distances and visited array
		for (int i = 0; i < V; i++){
				dist.append(INT_MAX);
				visited.append(false);
		}
		dist[source] = 0;  // Distance to source is 0
		
		for (int count = 0; count < V - 1; count++) {
				// Find minimum distance vertex from unvisited set
				int min_dist = INT_MAX;
				int min_index = -1;
				
				for (int v = 0; v < V; v++) {
						if (!visited[v] && dist[v] <= min_dist) {
								min_dist = dist[v];
								min_index = v;
						}
				}
				
				if (min_index == -1) break;
				
				// Mark the picked vertex as processed
				visited[min_index] = true;
				
				// Update distances of adjacent vertices
				for (int v = 0; v < V; v++) {
						if (!visited[v] && W[min_index][v] != INT_MAX && dist[min_index] != INT_MAX) {
								dist[v] = std::min(dist[v], dist[min_index] + W[min_index][v]);
						}
				}
		}
	}

};

#endif
