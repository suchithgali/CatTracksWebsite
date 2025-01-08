#include <iostream>
#include "ArrayList.h"
#include "HashTable.h"
#include "LinkedList.h"

#include <ostream>

int main(){

ArrayList<std::string> bobcat_express_stops_keys = {"Amtrak Station", "Compass Pointe Apts", "El Portal & G Street", "El Redondo Dr", 
"K St. Between 18th & 19th", "M St. At Bellevue RD", "Merced College The Bus Terminal", "Merced Mall Target", "Merced Transpo", 
"Promenade Center", "R Street Village Apts", "Rite Aid/Walgreens", "University Transit Center", "Walmart on Loughborough Dr"};


ArrayList<std::vector<std::string>> bobcat_express_stops_values = {{"6:29", "7:09", "7:49", "8:44", "9:24", "10:04", "10:44", "12:09", "1:49", "3:17", "4:57", "6:22", "8:02"}, 
                               {"6:32", "7:12", "7:52", "8:47", "9:27", "10:07", "10:47", "12:12", "1:52", "3:20", "5:00", "6:25", "8:05"}, 
                               {"6:34", "7:14", "7:54", "8:49", "9:29", "10:09", "10:49", "12:14", "1:54", "3:22", "5:02", "6:27", "8:07"}, 
                               {"6:39", "7:19", "7:59", "8:54", "9:34", "10:14", "10:54", "12:19", "1:59", "3:27", "5:07", "6:32", "8:12"}, 
                               {"6:44", "7:24", "8:04", "8:59", "9:39", "10:19", "11:00", "12:25", "2:05", "3:33", "5:13", "6:38", "8:18"}, 
                               {"6:55", "7:35", "8:30", "9:10", "9:50", "10:30", "11:11", "12:51", "2:16", "3:59", "5:24", "7:04", "8:29*"}, 
                               {"11:20", "1:00", "2:25", "4:08", "5:33", "7:13"}, {"11:29", "1:09", "2:37", "4:17", "5:42", "7:22"}, 
                               {"11:38", "1:18", "2:46", "4:26", "5:51", "7:31"}, {"11:50", "1:30", "2:58", "4:38", "6:03", "7:43"}, 
                               {"11:52", "1:32", "3:00", "4:40", "6:05", "7:45"}, {"REQ:", "REQ:", "REQ:", "REQ:", "REQ:", "REQ:"}, 
                               {"12:01", "1:41", "3:09", "4:49", "6:14", "7:54"}, {"12:03", "1:43", "3:11", "4:51", "6:16", "7:56"}};

HashTable<std::string> bobcat_table(10);
for (int i = 0; i < bobcat_express_stops_keys.size(); i++){
    bobcat_table.appendString(bobcat_express_stops_keys[i]);
}
std::cout << bobcat_table << std::endl;

}