#ifndef NODE_H
#define NODE_H

#include <iostream>

class Node{
  std::string name;
  int weight;

public:
  Node(){
    name = "";
    weight = INFINITY;
  }

  Node(std::string name, int weight){
    this->name = name;
    this->weight = weight;
  }

  void setWeight(int weight){
    this->weight = weight;
  }


};


#endif