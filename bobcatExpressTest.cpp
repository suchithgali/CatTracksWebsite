#include "Graph.h"

void dijkstra(){
  for every edge{
    node2.setWeight(min(node2.getWeight(), node1.getWeight() + addEdgeWeight(node1, node2))) 
  }

int main(){

Graph bobcatExpress;

bobcatExpress.addNode("University Transit Center", 5);
bobcatExpress.addNode("Wingstop/ Promenade Center", 2);

bobcatExpress.addEdge(bobcatExpress.getNodes(0), bobcatExpress.getNodes(1), 9);

bobcatExpress.addNode("Merced Mall / Target");

bobcatExpress.addEdge(bobcatExpress.getNodes(1), bobcatExpress.getNodes(2), 1);

bobcatExpress.addNode("Loughborough Dr. (Walmart)");

bobcatExpress.addEdge(bobcatExpress.getNodes(2), bobcatExpress.getNodes(3), 12);

bobcatExpress.addNode("Amtrak Station");

bobcatExpress.addEdge(bobcatExpress.getNodes(3), bobcatExpress.getNodes(4), 6);

bobcatExpress.addNode("K St. & 18th St. & 19th St.");

bobcatExpress.addEdge(bobcatExpress.getNodes(4), bobcatExpress.getNodes(5), 3);

bobcatExpress.addNode("Merced Transpo");

bobcatExpress.addEdge(bobcatExpress.getNodes(5), bobcatExpress.getNodes(6), 9);

bobcatExpress.addNode("Rite Aid / Walgreens");

bobcatExpress.addEdge(bobcatExpress.getNodes(6), bobcatExpress.getNodes(7), 14);

bobcatExpress.addNode("El Portal Plaza & G St.");

bobcatExpress.addEdge(bobcatExpress.getNodes(7), bobcatExpress.getNodes(8), 4);

bobcatExpress.addNode("R St. Village Apartments");

bobcatExpress.addEdge(bobcatExpress.getNodes(8), bobcatExpress.getNodes(9), 10);

bobcatExpress.addNode("El Redondo Dr. (Bus Stop – Jenner Dr.)");

bobcatExpress.addEdge(bobcatExpress.getNodes(9), bobcatExpress.getNodes(10), 2);

bobcatExpress.addNode("Merced College The Bus Terminal");

bobcatExpress.addEdge(bobcatExpress.getNodes(10), bobcatExpress.getNodes(11), 4);

bobcatExpress.addNode("M St. & Bellevue Rd. (Bellevue Ranch)");

bobcatExpress.addEdge(bobcatExpress.getNodes(12), bobcatExpress.getNodes(0), 8);


}