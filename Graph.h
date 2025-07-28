#ifndef GRAPH_H
#define GRAPH_H

#include "Edge.h"
#include <iostream>
#include <climits>

class Graph{
public:
	Node node1;
	Node node2;
	Node node3;
	Node node4;
	
	Edge edge1_2, edge1_3, edge1_4;  
	Edge edge2_1, edge2_3, edge2_4;  
	Edge edge3_1, edge3_2, edge3_4;  
	Edge edge4_1, edge4_2, edge4_3;  

	Graph() {
		node1 = Node("University Transit Center (UTC)", 0);
		node2 = Node("Starbucks / Promenade Center", INT_MAX);
		node3 = Node("Merced Mall / Target ", INT_MAX);
		node4 = Node("Loughborough Dr. (Walmart)", INT_MAX);
		
		edge1_2.createEdge(node1, node2, 5);  
		edge1_3.createEdge(node1, node3, 10); 
		edge1_4.createEdge(node1, node4, 15); 
		
		edge2_1.createEdge(node2, node1, 5);
		edge2_3.createEdge(node2, node3, 8);
		edge2_4.createEdge(node2, node4, 12);
		
		edge3_1.createEdge(node3, node1, 10);
		edge3_2.createEdge(node3, node2, 8);
		edge3_4.createEdge(node3, node4, 6);
		
		edge4_1.createEdge(node4, node1, 15);
		edge4_2.createEdge(node4, node2, 12);
		edge4_3.createEdge(node4, node3, 6);
	}

  };



#endif