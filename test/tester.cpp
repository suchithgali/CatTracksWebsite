#include <iostream>
#include "ArrayList.h"
#include "stops_data.h"
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

float apiCalls(std::string point1, std::string point2, std::string point3){
std::vector<std::vector<float>> coordinates1;
float distanceMiles;
  cpr::Response point1_call = cpr::Get(cpr::Url{"https://api.openrouteservice.org/geocode/search"},
                          cpr::Parameters{{"text", point1}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
                          );

    json jsonResponse = json::parse(point1_call.text);
    json features = jsonResponse["features"];
    for (auto& feature : features){
        auto coords = feature["geometry"]["coordinates"];
        float lon = coords[0];
        float lat = coords[1];
        coordinates1.push_back({lon, lat});
        break;
    }

    cpr::Response point2_call = cpr::Get(cpr::Url{"https://api.openrouteservice.org/geocode/search"},
                          cpr::Parameters{{"text", point2}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
                          );

    json jsonResponse2 = json::parse(point2_call.text);
    json features2 = jsonResponse2["features"];
    for (auto& feature : features2){
        auto coords2 = feature["geometry"]["coordinates"];
        float lon = coords2[0];
        float lat = coords2[1];
        coordinates1.push_back({lon, lat});
        break;
    }

    cpr::Response point3_call = cpr::Get(cpr::Url{"https://api.openrouteservice.org/geocode/search"},
                          cpr::Parameters{{"text", point3}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
                          );

    json jsonResponse3 = json::parse(point3_call.text);
    json features3 = jsonResponse3["features"];
    for (auto& feature : features3){
        auto coords3 = feature["geometry"]["coordinates"];
        float lon = coords3[0];
        float lat = coords3[1];
        coordinates1.push_back({lon, lat});
        break;
    }

    json requestBody;
    requestBody["coordinates"] = coordinates1;
    //std::cout << requestBody.dump(2);
    cpr::Response firstSegment = cpr::Post(cpr::Url{"https://api.openrouteservice.org/v2/directions/driving-car"},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}, {"Content-Type", "application/json"}},
                          cpr::Body{requestBody.dump()}
                          );
          json jsonResponse4 = json::parse(firstSegment.text);
          json features4 = jsonResponse4["routes"];
          for (auto& feature : features4){
              float distanceMeters = feature["summary"]["distance"].get<float>();
              distanceMiles = distanceMeters / 1609;
              break;
          }
  return distanceMiles;
}

int  main(){

std::string point1 = "3304, Santa Rosa Court, Merced, Merced County, California, 95348, United States";
std::string point2 = "355 West 24th Street, Merced, CA";
std::string point3 = "3706 El Redondo Drive";

std::cout << apiCalls(point1, point2, point3) << std::endl;
std::cout << places.index("Amtrak Station");

}