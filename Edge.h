#ifndef EDGE_H
#define EDGE_H

#include "Node.h"

class Edge{

int edgeWeight;

  public:
    void createEdge(Node node1, Node node2, int edgeWeight){
      this->edgeWeight = edgeWeight;
      node2.setWeight(node1.getWeight() + edgeWeight);
    }

};


#endif