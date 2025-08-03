#include "Graph.h"


int main(){

  Graph bobcatExpress(14, 14);
  bobcatExpress.addEdge(0, 1, 3);
  bobcatExpress.addEdge(1, 2, 8);
  bobcatExpress.addEdge(2, 3, 2);
  bobcatExpress.addEdge(3, 4, 1);
  bobcatExpress.addEdge(4, 5, 5);
  bobcatExpress.addEdge(5, 6, 9);
  bobcatExpress.addEdge(6, 7, 3);
  bobcatExpress.addEdge(7, 8, 13);
  bobcatExpress.addEdge(8, 9, 4);
  bobcatExpress.addEdge(9, 10, 7);
  bobcatExpress.addEdge(11, 12, 9);
  bobcatExpress.addEdge(12, 13, 3);
  bobcatExpress.addEdge(13, 14, 10);
  bobcatExpress.addEdge(14, 1, 6);

  bobcatExpress.dijkstra(0);
}