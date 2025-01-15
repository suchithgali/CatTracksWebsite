#include <iostream>
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

int main(int argc, char** argv) {
    cpr::Response r = cpr::Get(cpr::Url{"https://nominatim.openstreetmap.org/search"},
                          cpr::Parameters{{"q", "New York"}, {"format", "json"}});
    //std::cout << "Status Code: " << r.status_code << std::endl;
    //std::cout << "Content-Type: " << r.header["content-type"] << std::endl;
    json jsonResponse = json::parse(r.text);
    for (const auto& item : jsonResponse){
        std::cout << "Latitude: " << item["lat"] << " Longitude: " << item["lon"] << std::endl;
        break;
    }
    return 0;
}

