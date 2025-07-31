#include "Graph.h"

int main(){

Graph bobcatExpress;

bobcatExpress.addNode("University Transit Center");
bobcatExpress.addNode("Wingstop/ Promenade Center");

bobcatExpress.addEdge(bobcatExpress.getNodes(0), bobcatExpress.getNodes(1));

bobcatExpress.addNode("Merced Mall / Target");

bobcatExpress.addEdge(bobcatExpress.getNodes(1), bobcatExpress.getNodes(2));

bobcatExpress.addNode("Loughborough Dr. (Walmart)");

bobcatExpress.addEdge(bobcatExpress.getNodes(2), bobcatExpress.getNodes(3));

bobcatExpress.addNode("Amtrak Station");

bobcatExpress.addEdge(bobcatExpress.getNodes(3), bobcatExpress.getNodes(4));

bobcatExpress.addNode("K St. & 18th St. & 19th St.");

bobcatExpress.addEdge(bobcatExpress.getNodes(4), bobcatExpress.getNodes(5));

bobcatExpress.addNode("Merced Transpo");

bobcatExpress.addEdge(bobcatExpress.getNodes(5), bobcatExpress.getNodes(6));

bobcatExpress.addNode("Rite Aid / Walgreens");

bobcatExpress.addEdge(bobcatExpress.getNodes(6), bobcatExpress.getNodes(7));

bobcatExpress.addNode("El Portal Plaza & G St.");

bobcatExpress.addEdge(bobcatExpress.getNodes(7), bobcatExpress.getNodes(8));

bobcatExpress.addNode("R St. Village Apartments");

bobcatExpress.addEdge(bobcatExpress.getNodes(8), bobcatExpress.getNodes(9));

bobcatExpress.addNode("El Redondo Dr. (Bus Stop – Jenner Dr.)");

bobcatExpress.addEdge(bobcatExpress.getNodes(9), bobcatExpress.getNodes(10));

bobcatExpress.addNode("Merced College The Bus Terminal");

bobcatExpress.addEdge(bobcatExpress.getNodes(10), bobcatExpress.getNodes(11));

bobcatExpress.addNode("M St. & Bellevue Rd. (Bellevue Ranch)");

bobcatExpress.addEdge(bobcatExpress.getNodes(12), bobcatExpress.getNodes(0));

}