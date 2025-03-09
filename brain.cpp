#include <iostream>
#include <chrono>
#include <ctime>
#include <vector>
#include "stops_data.h"
#include "ArrayList.h"
#include <unordered_set>
#include <future>
#include "HashTable.h"

#include <cpr/cpr.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

std::string q1;
std::string q2;

//holds an object of type time 
auto timeLA = std::chrono::system_clock::now();
//coverts the time object to a printable type
std::time_t timeT = std::chrono::system_clock::to_time_t(timeLA);

bool placeFound = false;

HashTable<std::string> nameBus("nameBus",9);
HashTable<std::string> possible_buses("possiblebuses", 9);
ArrayList<std::string> possible_busnames;
HashTable<std::string> possible_distances("possibledistances", 9);
ArrayList<std::string> shortest_stops;
HashTable<std::string> busGo_stops("busGostops", 9);
HashTable<std::string> distances_dict("distancesdict", 9);
HashTable<std::string> shortestnames_stops("shortestnames_stops", 9);
ArrayList<std::string> distances_list;
HashTable<std::string> named_stops("named_stops", 9);


bool validatePlace(ArrayList<std::string> list, std::string target, int start, int end){
    while (start <= end){
        int middle = start + (end - start) / 2;
        if (list[middle] == target){
            return true;
        }
        else if (list[middle] > target){
            end = middle - 1;
        }
        else{
            start = middle + 1;
        }
    }
    return false;
}


std::string Hash_binary_search(HashTable<std::string>& table, const std::string& target){
    if(table.getBuckets() == 0){
            // Handle empty case as needed
            throw std::runtime_error("HashTable is empty");
        }
  //ArrayList<std::string> sorted_names;
  //sorted_names.insertionSort(bus_names);
  int low = 0;
  int high = table.getKeys().getsize() - 1;

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
  return "";
}


void findBusTaken(){
  for (auto& tables : bus_stops_tables){
    if (Hash_binary_search(tables, q2) == q2){
      nameBus.appendTable(nameBus.HashStrings(q2), tables.getName(), tables);
    }
  }
}

void busGoStops(){
  for (auto& tables : bus_stops_tables){
    if (Hash_binary_search(tables, q1) == q1){
      busGo_stops.appendTable(busGo_stops.HashStrings(q1), tables.getName(), tables);
    }
  }
}

std::vector<float> getRequest(std::string point){
  float lon;
  float lat;
  cpr::Response point_call = cpr::Get(cpr::Url{"https://api.openrouteservice.org/geocode/search"},
    cpr::Parameters{{"text", point}, {"api_key", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
    );

  if(point_call.status_code != 200){
    throw std::runtime_error("API call for point1 failed with status: " + std::to_string(point_call.status_code));
  }
  json jsonResponse = json::parse(point_call.text);
  json features = jsonResponse["features"];
  for (auto& feature : features){
    auto coords = feature["geometry"]["coordinates"];
    lon = coords[0];
    lat = coords[1];
    break;
  }
  return std::vector<float>{lon, lat};
}

float apiCalls(std::string point1, std::string point2, std::string point3){
  auto f1 = getRequest(point1);
  auto f2 = getRequest(point2);
  auto f3 = getRequest(point3);
  std::vector<std::vector<float>> coordinates1 = {f1, f2, f3};

  json requestBody;
  requestBody["coordinates"] = coordinates1;
  requestBody["radiuses"] = json::array({1000, 1000, 1000});
  //std::cout << requestBody.dump(2);
  cpr::Response firstSegment = cpr::Post(cpr::Url{"http://localhost:8080/ors/v2/directions/driving-car"},
                        cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}, {"Content-Type", "application/json"}},
                        cpr::Body{requestBody.dump()}
                        );

  if(firstSegment.status_code != 200){
    throw std::runtime_error("API call for point4 failed with status: " + std::to_string(firstSegment.status_code));
  }

    float distanceMeters = json::parse(firstSegment.text)["routes"][0]["summary"]["distance"].get<float>();;
    return distanceMeters / 1609;
}

//need to search for q1 in all the bus hashtables
//save the names of all the buses in an array
//check if q2 is in any of the buses that were saved in the array
//if it is return that the user should take any of those buses

void findbustoTake(){
  ArrayList<HashTable<std::string>> q1Buses;
  ArrayList<HashTable<std::string>> commonBuses;
  for (int i = 0; i < bus_stops_tables.getsize(); i++){
    for (auto& route : bus_stops_tables[i].getKeys()){
      if (route == q1){
        q1Buses.append(bus_stops_tables[i]);
      }
    }
  }

  for (int j = 0; j < q1Buses.getsize(); j++){
    for (auto& route2 : q1Buses[j].getKeys()){
      if (route2 == q2){
        commonBuses.append(q1Buses[j]);
      }
    }
  }

  std::cout << "To go to " << q2 << " from " << q1 << " take any of these buses: "; 
  
  for (int i = 0; i < commonBuses.getsize(); i++){
    std::cout << commonBuses[i].getName(); 
  }
  
  std::cout << std::endl;

}

void findBusSimilar(){
  ArrayList<HashTable<std::string>> q1Buses;
  ArrayList<HashTable<std::string>> q2Buses;
  std::unordered_set<std::string> commonBuses;
  ArrayList<std::string> commonBus;
  std::unordered_set<std::string> commonQ2Buses;
  ArrayList<std::string> commonQ2Bus;
  std::unordered_set<int> commonQ2BusIndices; 
  
  float distance;
  ArrayList<float> distances;
  ArrayList<std::string> commonStops;    // <-- Added to store matching stop names

  std::unordered_set<std::string> visitedStops;

  std::string geoQ1 = geo_places[places.index(q1)];
  std::string geoQ2 = geo_places[places.index(q2)];

  // Single loop to collect q1 and q2 buses
  /*for (int i = 0; i < bus_stops_tables.getsize(); i++){
    bool addQ1 = false;
    bool addQ2 = false;
    auto keys = bus_stops_tables[i].getKeys();
    for (auto& route : keys){
      if (route == q1){
        addQ1 = true;
      }
      if (route == q2){
        addQ2 = true;
      }
      if (addQ1 && addQ2){
        break;
      }
    }
    if (addQ1){
      q1Buses.append(bus_stops_tables[i]);
    }
    if (addQ2){
      q2Buses.append(bus_stops_tables[i]);
    }
  }
  */

  for (int i = 0; i < bus_stops_tables.getsize(); i++){
    auto keys = bus_stops_tables[i].getKeys();
    if (q1 == keys.search(q1)){
      q1Buses.append(bus_stops_tables[i]);
    }
    std::cout << keys;
    if (q2 == keys.search(q2)){
      q2Buses.append(bus_stops_tables[i]);
    }
  }
  // Collect all stops from q2Buses into an unordered_set
  std::unordered_set<std::string> q2AllStops;
  for (int l = 0; l < q2Buses.getsize(); l++){
      for (auto& gostop : q2Buses[l].getKeys()){
          q2AllStops.insert(gostop);
      }
  }

  std::unordered_set<std::string> q1AllStops;
  for (int l = 0; l < q1Buses.getsize(); l++){
      for (auto& comestop : q1Buses[l].getKeys()){
          q1AllStops.insert(comestop);
      }
  }

  for (const std::string& element : q1AllStops) {
    std::cout << element << " ";
  }

  // Then iterate over q1AllStops and check membership in q2AllStops
    for (auto stop : q1AllStops){
      std::cout << "hello" << std::endl;
      if (visitedStops.find(stop) != visitedStops.end()) {
          continue; 
      }
      visitedStops.insert(stop);
          // If stop exists in q2AllStops, record it along with the corresponding bus
        if (q2AllStops.find(stop) != q2AllStops.end()){
          // Iterate over q1Buses to find the bus containing the stop
          for (int j = 0; j < q1Buses.getsize(); j++){
            auto keys = q1Buses[j].getKeys();
            std::cout << keys << std::endl;
            if (std::find(keys.begin(), keys.end(), stop) != keys.end()){
                distances.append(apiCalls(geoQ1, geo_places[places.index(stop)], geoQ2));
                commonBuses.insert(q1Buses[j].getName());
                commonStops.append(stop);    // Record the common stop name
                break;
            }
          }
        }
      }
    std::cout << commonStops << std::endl;
    for (const auto& commonStop: commonStops){
      std::cout << "Entered" << std::endl;
      for (int j = 0; j < q2Buses.getsize(); j++){
        auto q2Keys = q2Buses[j].getKeys();
        std::cout << q2Keys <<std::endl;
        // Check if the current q2 bus has the common stop.
        if (std::find(q2Keys.begin(), q2Keys.end(), commonStop) != q2Keys.end()){
          std::cout << q2Keys <<std::endl;
          // Ensure we add the bus only once.
          if (commonQ2BusIndices.find(j) == commonQ2BusIndices.end()){
            commonQ2Buses.insert(q2Buses[j].getName());
            commonQ2BusIndices.insert(j);
            }
          }
        }
    }

        
    for (const auto &busName : commonBuses) {
        commonBus.append(busName);
    }
    for (const auto &busName : commonQ2Buses) {
        commonQ2Bus.append(busName);
    }
   

  std::cout << "To go to " << q1 << " from " << q2 << " take any of these buses: " << commonQ2Bus << " to ";
      
  if (distances.getsize() > 0){
      float minDistance = distances[0];
      int minIndex = 0;
      for (int j = 1; j < distances.getsize(); j++){
          if (distances[j] < minDistance){
              minDistance = distances[j];
              minIndex = j;
          }
      }
      std::string minBus = commonBus[minIndex];
      std::string minStop = commonStops[minIndex];
      std::cout << minStop << " then take any of these buses: " << commonBus << " to " << q1;
  }

  std::cout << std::endl;
}


void findBusGo(){
  std::string point1_name;
  std::string point2_name;
  std::string point3_name;
  std::string takenBusStop;
  std::cout << "Entered\n";
  
  for (const auto& name : nameBus.getKeys()){      
      auto buses = nameBus.getValues(name);
      
      for (const auto& bus : buses){
            std::cout << "Entered\n";
          for (const auto& stops : bus.getKeys()){
              std::cout << "Entered third for: " << stops << "\n";
              
              takenBusStop = stops;
              
              for (const auto& name1 : busGo_stops.getKeys()){
                  std::cout << "Entered fourth for: " << name1 << "\n";
                  
                  auto buses2 = busGo_stops.getValues(name1);
                  std::cout << "Number of buses2 for " << name1 << ": " << buses2 << "\n";
                  
                  for (const auto& bus2 : buses2){
                      std::cout << "Entered fifth for\n";
                      
                      for (const auto& j3 : bus2.getKeys()){
                          std::cout << "Checking j3: " << j3 << "\n";
                          
                          if (Hash_binary_search(busGo_stops, takenBusStop) == j3){
                              point1_name = geo_places[places.index(q1)];
                              point2_name = geo_places[places.index(q2)];
                              point3_name = geo_places[places.index(takenBusStop)];
                              
                              ArrayList<std::string> possible_distancesKeys;
                              possible_distancesKeys.append(j3);
                              possible_distances.appendHashes(possible_distancesKeys, apiCalls(point1_name, point2_name, point3_name));
                              possible_busnames.append(name);
                              shortest_stops.append(j3);
                              possible_buses.appendHashes(j3, name1);     
                          }
                      }
                  }
              }
          }
      }
  }
}

void findShortestBus(){
  
  float min_distance = possible_distances.getMinValue();
  std::string min_stop = possible_distances.searchforKey(min_distance);
  for (const auto& stop : possible_buses.getKeys()){
    ArrayList<std::string> min_bus;
    if (Hash_binary_search(possible_buses, min_stop) == stop){
      min_bus.append(possible_buses.search(stop));
      break; 
    }  
  }
}

int main(int argc, char* argv[]){
  /*if (argc < 3){
    std::cerr << "Usage: brain <destination> <current_location>" << std::endl;
    return 1;
  }
  q1 = argv[1];
  q2 = argv[2];
  */

  /*
  std::cout << "Where would you like to go?:" << std::endl;
  std::getline(std::cin, q1);
  placeFound = validatePlace(places, q1, 0, places.getsize() - 1);

  while (placeFound == false){
    if (placeFound == false){
        std::cout << "Invalid location" << std::endl;
        std::cout << "Where would you like to go?: R Street Village Apts, El Redondo Dr, Compass Pointe Apts, Merced College The Bus Terminal, M St. At Bellevue RD, University Transit Center, Promenade Center, "
        "Merced Mall Target, Walmart on Loughborough Dr, Amtrak Station, K St. Between 18th & 19th, Merced Transpo (REQ), Rite Aid/Walgreens on G St, "
        "El Portal Plaza & G Street, Granville Apartments, G St. & W. Alexander Ave, El Portal & G Street, Mercy Hospital/TriCollege, TriCollege/Mercy (Bus stop on G next to Tri College), "
        "G St. & W. Alexander Ave. (Bus Stop Paul's Place), Cardella Rd. & M Street (North), Foothill Drive, Cardella Rd. & M Street (South), G Street South Across from Raley's (The Bus Stop),"
        "K St. Between 18Th & 19th, Meadows Ave & Olivewood Dr (Foodmaxx), Yosemite Crossings Shopping Center, M Street Village Apartments, Ironstone Dr. & M St, "
        "Yosemite & Cordova (Merced Physician Center), Moraga Subdivision, University Surgery Center, Cardella Rd. & 'M' Street, Cardella Rd. & 'M' Street,"
        "K St. Between 18th & 19th, UC Merced Downtown Campus Center, Merced Transpo, G Street South" << std::endl;
    }
    std::getline(std::cin, q1);
    placeFound = validatePlace(places, q1, 0, places.getsize() - 1);
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
/*
std::cout << "Where are you currently located?: ";
std::getline(std::cin, q2);
placeFound = validatePlace(places, q2, 0, places.getsize() - 1);
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
        std::getline(std::cin, q2);
        placeFound = validatePlace(places, q2, 0, places.getsize() - 1);
    }else{
        break;
  }
}
  

for (int i = 0; i < bus_names.getsize(); i++){
  named_stops.appendHashes(bus_names, bus_stops_tables[i]);
}
*/
/*
q3 = input("What timeEl  would you like to arrive by? Enter a time (Hour:Minute:Second format): ")
validateTime(q3)
while True:
    if (valid_time == False):
        q3 = input("What time would you like to arrive by? Enter a time (Hour:Minute:Second format)")
        validateTime(q3)
    else:
        break
*/

//findBusSimilar();
//findbustoTake();
//busGoStops();
//findBusGo();
//findShortestBus();
//std::cout << busGo_stops.getKeys() << std::endl;
std::cout << C1_stops_keys.insertionSort(C1_stops_keys) << std::endl;
return 0;
}