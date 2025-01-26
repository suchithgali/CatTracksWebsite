#include <iostream>
#include <chrono>
#include <ctime>
#include "stops_data.h"
#include "ArrayList.h"
#include "HashTable.h"
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

//holds an object of type time 
auto timeLA = std::chrono::system_clock::now();
//coverts the time object to a printable type
std::time_t timeT = std::chrono::system_clock::to_time_t(timeLA);

bool placeFound = false;

HashTable<std::string> nameBus(9);
HashTable<std::string> possible_buses(9);
ArrayList<std::string> possible_busnames;
HashTable<int> possible_distances(9);
ArrayList<std::string> shortest_stops;
HashTable<std::string> busGo_stops(9);
HashTable<std::string> distances_dict(9);
HashTable<std::string> shortestnames_stops(9);
ArrayList<std::string> distances_list;


HashTable<std::string> named_stops(9);


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
    ArrayList<std::string> keys = table.getKeys();
    std::string value = keys[middle];
    if (value < target){
      low = middle + 1;
    }
    else if (value > target){
      high = middle - 1;
    }
    else{
      return table.search(value);
    }
  }
}

std::string q1;
std::string q2;

void findBusTaken(){
  for (auto& tables : bus_stops_tables){
    if (Hash_binary_search(tables, q2) == q2){
      nameBus.appendTable(tables.HashStrings(q2), q2, tables);
    }
  }
}

void busGoStops(){
  for (auto& tables : bus_stops_tables){
    if (Hash_binary_search(tables, q1) == q1){
      busGo_stops.appendTable(tables.HashStrings(q1), q1, tables);
    }
  }
}

void apiCalls(std::string point1, std::string point2, std::string point3){
  std::vector<std::vector<float>> coordinates;
  cpr::Response point1_call = cpr::Get(cpr::Url{"https://api.openrouteservice.org/geocode/search"},
                          cpr::Parameters{{"text", point1}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
                          );
    //std::cout << "Status Code: " << r.status_code << std::endl;
    //std::cout << "Content-Type: " << r.header["content-type"] << std::endl;
    json jsonResponse = json::parse(point1_call.text);
    json features = jsonResponse["features"];
    for (auto& feature : features){
        auto coords = feature["geometry"]["coordinates"];
        coordinates.push_back(coords);
        break;
    }

    cpr::Response point2_call = cpr::Get(cpr::Url{"https://api.openrouteservice.org/geocode/search"},
                          cpr::Parameters{{"text", point2}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
                          );
    //std::cout << "Status Code: " << r.status_code << std::endl;
    //std::cout << "Content-Type: " << r.header["content-type"] << std::endl;
    json jsonResponse2 = json::parse(point2_call.text);
    json features2 = jsonResponse2["features"];
    for (auto& feature : features2){
        auto coords2 = feature["geometry"]["coordinates"];
        coordinates.push_back(coords2);
        break;
    }

    cpr::Response point3_call = cpr::Get(cpr::Url{"https://api.openrouteservice.org/geocode/search"},
                          cpr::Parameters{{"text", point3}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
                          );
    //std::cout << "Status Code: " << r.status_code << std::endl;
    //std::cout << "Content-Type: " << r.header["content-type"] << std::endl;
    json jsonResponse3 = json::parse(point3_call.text);
    json features3 = jsonResponse3["features"];
    for (auto& feature : features2){
        auto coords3 = feature["geometry"]["coordinates"];
        coordinates.push_back(coords3);
        break;
    }

    cpr::Response firstSegment = cpr::Get(cpr::Url{"https://api.openrouteservice.org/v2/directions/driving-car"},
                          cpr::Parameters{{"profile", "driving-car"}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}},
                          cpr::Body{json(coordinates).dump()}
                          );
          json jsonResponse = json::parse(firstSegment.text);
          json features = jsonResponse["features"];
          std::cout << features;
          for (auto& feature : features){
              auto distance = feature["summary"]["distance"];
              std::cout << "Distance: " << distance << std::endl;
              break;
          }
}

//from routingpy import ORS
//client = ORS(api_key='5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3')
void findBusGo(){
std::string point1_name;
std::string point2_name;
std::string point3_name;
std::string takenBusStop;
for (const auto& name : nameBus.getKeys()){
  auto stop = nameBus.search(name);
  for (const auto& j2 : nameBus[stop].getKeys()){
    takenBusStop = j2;
    for (const auto& name1 : busGo_stops.getKeys()){
      auto stop2 = busGo_stops.search(name1);
      for (const auto& j3 : busGo_stops[stop2].getKeys()){
        if (Hash_binary_search(busGo_stops, stop2) == j3){
          point1_name = geo_places[places.index(q1)];
          point2_name = geo_places[places.index(q2)];
          point3_name = geo_places[places.index(takenBusStop)];
          
          //route = client.directions(locations= (pointq2_coordinates, pointq3_coordinates, pointq1_coordinates), profile="driving-car");
          cpr::Response firstSegment = cpr::Get(cpr::Url{"https://api.openrouteservice.org/v2/directions/driving-car"},
                          cpr::Parameters{{"start", point1_name}, {"end", point2_name}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
                          );
          json jsonResponse = json::parse(firstSegment.text);
          json features = jsonResponse["features"];
          for (auto& feature : features){
              auto distance = feature["summary"]["distance"];
              std::cout << "Distance: " << distance << std::endl;
              break;
          }

          possible_distances[route.distance] = j3;
          possible_busnames.append(name);
          shortest_stops.append(j3);
          possible_buses[j3] = name1;     
          
        }
      }
    }
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

for (int i = 0; i < named_stops.getBuckets(); i++){
  named_stops.appendHashes(bus_names, bus_stops_tables);
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


void findShortestBus(){
  int min_distance = min(possible_distances.getKeys());
  std::string min_stop = possible_distances[min_distance];
  for (const auto& [stop, route] : possible_buses.getValues()){
    ArrayList<std::string> min_bus;
    if (Hash_binary_search(possible_buses, min_stop) == stop):
      min_bus = route;
      break;   
  }


}

findBusTaken();
busGoStops();
findBusGo();
findShortestBus();
std::cout << possible_buses << std::endl;

}