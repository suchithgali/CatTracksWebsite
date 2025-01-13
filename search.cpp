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


int main(){
  std::string q1;
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

std::string q2;
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

HashTable<std::string> buses_names();
HashTable<std::string> possible_buses();
ArrayList<std::string> possible_busnames;
HashTable<int> possible_distances();
ArrayList<std::string> shortest_stops;
HashTable<std::string> busGo_stops();
HashTable<std::string> distances_dict();
HashTable<std::string> shortestnames_stops();
ArrayList<std::string> distances_list;

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

void Hash_binary_search(HashTable<std::string>& table, std::string target){
  ArrayList<std::string> sorted_names = insertionSort(bus_names);
  int low = 0;
  int high = sorted_names.size() - 1;

  while (low <= high){
    int middle = (low + high) / 2;
    std::string value = sorted_names[middle];
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

void findBusTaken(){
  for (const auto& [name, stop] : named_stops){
    
  }
}






}
