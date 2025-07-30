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
	std::unordered_map<std::string, int> nameToIndex;

	void addNode(std::string& name){
		if (nameToIndex.find(name) != nameToIndex.end()) {
            std::cout << "Node " << name << " already exists.\n";
            return;
        }
		nodes.push_back(Node(name, INFINITY));
		nameToIndex[name] = nodes.size() - 1;
		int newSize = nodes.size();
    adjacency_matrix.resize(newSize);
		for (auto &row : adjacency_matrix) {
			row.resize(newSize, INT_MAX); 
		}
		adjacency_matrix[newSize - 1][newSize - 1] = 0;
	}
  };

#endif