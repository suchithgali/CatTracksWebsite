#ifndef GRAPH_H
#define GRAPH_H

#include "Node.h"
#include "Edge.h"
#include <iostream>
#include <climits>
#include <vector>

class Graph{
public:
	std::vector<Node> nodes;
	std::vector<std::vector<bool>> adjacency_matrix; 
	std::unordered_map<std::string, int> rowName;
	std::unordered_map<std::string, int> columnName;

	void addNode(const std::string& name){
		if (rowName.find(name) != rowName.end()) {
            std::cout << "Node " << name << " already exists.\n";
            return;
        }
		nodes.push_back(Node(name, INFINITY));
		rowName[name] = nodes.size() - 1;
		columnName[name] = nodes.size() - 1;
		int newSize = nodes.size();
    adjacency_matrix.resize(newSize);
		for (auto &row : adjacency_matrix) {
			row.resize(newSize, INT_MAX); 
		}
		adjacency_matrix[newSize - 1][newSize - 1] = 0;
	}

	void addEdge(Node node1, Node node2){
		int i = rowName[node1.getName()];
		int j = columnName[node2.getName()];
		adjacency_matrix[i][j] = 1;
		node2.setWeight(node1.getWeight() + 5); 
	}
	
  };

#endif