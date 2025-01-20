#include <iostream>
#include <chrono>
#include <ctime>
#include "stops_data.h"
#include "ArrayList.h"
#include "HashTable.h"

//holds an object of type time 
auto timeLA = std::chrono::system_clock::now();
//coverts the time object to a printable type
std::time_t timeT = std::chrono::system_clock::to_time_t(timeLA);

bool placeFound = false;

HashTable<HashTable<std::string>> bus_names(9);
HashTable<std::string> possible_buses(9);
ArrayList<std::string> possible_busnames;
HashTable<int> possible_distances(9);
ArrayList<std::string> shortest_stops;
HashTable<std::string> busGo_stops(9);
HashTable<std::string> distances_dict(9);
HashTable<std::string> shortestnames_stops(9);
ArrayList<std::string> distances_list;


bool validatePlace(ArrayList<std::string> list, std::string target, int start, int end){
  if (start > end){
    placeFound = false;
    return placeFound;
  }
  int middle = (start + end) / 2;
  if (list[middle] == target){
        placeFound = true;
        return placeFound;
  }
  else if (list[middle] > target){
        return validatePlace(list, target, start, middle - 1);
  }
    else{
        return validatePlace(list, target, middle + 1, end);
    }
}

std::string Hash_binary_search(HashTable<std::string>& table, const std::string& target){
  //ArrayList<std::string> sorted_names;
  //sorted_names.insertionSort(bus_names);
  int low = 0;
  int high = table.getBuckets() - 1;

  while (low <= high){
    int middle = (low + high) / 2;
    std::string value = table[middle];
    if (value < target){
      low = middle + 1;
    }
    else if (value > target){
      high = middle - 1;
    }
    else{
      return sorted_names[middle];
    }
  }
}

std::string q1;
std::string q2;

void findBusTaken(){
  for (auto& tables : bus_stops_tables){
    if (Hash_binary_search(tables, q2) == q2){
      bus_names[tables.HashStrings(q2)] = tables;
    }
  }
}

void findBusGo(){
  for (auto& tables : bus_stops_tables){
    if (Hash_binary_search(tables, q1) == q1){
      busGo_stops[tables.HashStrings(q1)] = tables;
    }
  }
}


int main(){
  std::cout << "Where would you like to go? ";
  std::cin >> q1;
  validatePlace(places, q1, 0, places.getsize() - 1);

  while (true){
    if (placeFound == false){
        std::cout << "Invalid location" << std::endl;
        std::cout << "Where would you like to go?: R Street Village Apts, El Redondo Dr, Compass Pointe Apts, Merced College The Bus Terminal, M St. At Bellevue RD, University Transit Center, Promenade Center, "
        "Merced Mall Target, Walmart on Loughborough Dr, Amtrak Station, K St. Between 18th & 19th, Merced Transpo (REQ), Rite Aid/Walgreens on G St, "
        "El Portal Plaza & G Street, Granville Apartments, G St. & W. Alexander Ave, El Portal & G Street, Mercy Hospital/TriCollege, TriCollege/Mercy (Bus stop on G next to Tri College), "
        "G St. & W. Alexander Ave. (Bus Stop Paul's Place), Cardella Rd. & M Street (North), Foothill Drive, Cardella Rd. & M Street (South), G Street South Across from Raley's (The Bus Stop),"
        "K St. Between 18Th & 19th, Meadows Ave & Olivewood Dr (Foodmaxx), Yosemite Crossings Shopping Center, M Street Village Apartments, Ironstone Dr. & M St, "
        "Yosemite & Cordova (Merced Physician Center), Moraga Subdivision, University Surgery Center, Cardella Rd. & 'M' Street, Cardella Rd. & 'M' Street,"
        "K St. Between 18th & 19th, UC Merced Downtown Campus Center, Merced Transpo, G Street South" << std::endl;
        validatePlace(places, q1, 0, places.getsize() - 1);
    }else{
        break;
  }
}
/*def validateTime(input_time):
    global valid_time
    try:
        parsed_time = datetime.strptime(input_time, '%H:%M:%S')
        if 0 <= parsed_time.hour < 24 and 0 <= parsed_time.minute < 60 and 0 <= parsed_time.second < 60:
            valid_time = True
        else:
            valid_time = False
    except ValueError:
        valid_time = False
*/

std::cout << "Where are you currently located?: ";
std::cin >> q2;
validatePlace(places, q2, 0, places.getsize() - 1);

  while (true){
    if (placeFound == false){
        std::cout << "Invalid location" << std::endl;
        std::cout << "Where would you like to go?: R Street Village Apts, El Redondo Dr, Compass Pointe Apts, Merced College The Bus Terminal, M St. At Bellevue RD, University Transit Center, Promenade Center, "
        "Merced Mall Target, Walmart on Loughborough Dr, Amtrak Station, K St. Between 18th & 19th, Merced Transpo (REQ), Rite Aid/Walgreens on G St, "
        "El Portal Plaza & G Street, Granville Apartments, G St. & W. Alexander Ave, El Portal & G Street, Mercy Hospital/TriCollege, TriCollege/Mercy (Bus stop on G next to Tri College), "
        "G St. & W. Alexander Ave. (Bus Stop Paul's Place), Cardella Rd. & M Street (North), Foothill Drive, Cardella Rd. & M Street (South), G Street South Across from Raley's (The Bus Stop),"
        "K St. Between 18Th & 19th, Meadows Ave & Olivewood Dr (Foodmaxx), Yosemite Crossings Shopping Center, M Street Village Apartments, Ironstone Dr. & M St, "
        "Yosemite & Cordova (Merced Physician Center), Moraga Subdivision, University Surgery Center, Cardella Rd. & 'M' Street, Cardella Rd. & 'M' Street,"
        "K St. Between 18th & 19th, UC Merced Downtown Campus Center, Merced Transpo, G Street South" << std::endl;
        validatePlace(places, q2, 0, places.getsize() - 1);
    }else{
        break;
  }
}

HashTable<std::string> named_stops(9);

for (int i = 0; i < named_stops.getBuckets(); i++){
  appendHashes(named_stops, bus_names, bus_stops_tables);
}

/*
q3 = input("What time would you like to arrive by? Enter a time (Hour:Minute:Second format): ")
validateTime(q3)
while True:
    if (valid_time == False):
        q3 = input("What time would you like to arrive by? Enter a time (Hour:Minute:Second format)")
        validateTime(q3)
    else:
        break
*/

//from routingpy import ORS
//client = ORS(api_key='5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3')
void findBusGo(){
std::string point1_name;
std::string point2_name;
std::string point3_name;
std::string takenBusStop;
for (const auto& [name, stop] : buses_names){
  for (const auto& j2 : stop2){
    takenBusStops.append(j2);
    for (const auto& [name1, stop2] : busGo_stops.items()){
      for (const auto& j3 : stop3){
        if (Hash_binary_search(stop3, takenBusStop)){
          point1_name = geo_places[places.index(q1)];
          point2_name = geo_places[places.index(q2)];
          point2_name = geo_places[places.index(takenBusStops)];
          //route = client.directions(locations= (pointq2_coordinates, pointq3_coordinates, pointq1_coordinates), profile="driving-car");
          
        }
      }
    }
  }
}
}


}
