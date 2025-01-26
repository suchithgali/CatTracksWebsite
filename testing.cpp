#include <iostream>
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

int main(int argc, char** argv) {
    cpr::Response r = cpr::Get(cpr::Url{"https://api.openrouteservice.org/geocode/search"},
                          cpr::Parameters{{"text", "355 West 24th Street, Merced, CA"}},
                          cpr::Header{{"Authorization", "5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3"}}
                          );
    //std::cout << "Status Code: " << r.status_code << std::endl;
    //std::cout << "Content-Type: " << r.header["content-type"] << std::endl;
    json jsonResponse = json::parse(r.text);
    json features = jsonResponse["features"];
    for (auto& feature : features){
        auto coords = feature["geometry"]["coordinates"];
        std::cout << "Coordinates: " << coords << std::endl;
        break;
    }
    
    return 0;
}

