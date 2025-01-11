#include <iostream>
#include <chrono>
#include <ctime>
#include "stops_data.h"
#include "ArrayList.h"

//holds an object of type time 
auto timeLA = std::chrono::system_clock::now();
//coverts the time object to a printable type
std::time_t timeT = std::chrono::system_clock::to_time_t(timeLA);

bool placeFound = false;

int main(){
  std::string q1;
  std::cout << "Where would you like to go? ";
  std::cin >> q1;
  validatePlace(places, q1, 0, places.getsize() - 1);
}

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

