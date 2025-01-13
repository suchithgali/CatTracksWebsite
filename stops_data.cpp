#include "stops_data.h"

int main(){
    appendHashes(bobcat_table, bobcat_express_stops_keys, bobcat_express_stops_values);
    appendHashes(C1_table, C1_stops_keys, C1_stops_values);
    appendHashes(C2_table, C2_stops_keys, C2_stops_values);
    appendHashes(E1_table, E1_stops_keys, E1_stops_values);
    appendHashes(E2_table, E2_stops_keys, E2_stops_values);
    appendHashes(Fastcat_table, Fastcat_stops_keys, Fastcat_stops_values);
    appendHashes(Fastcat2_table, Fastcat2_stops_keys, Fastcat2_stops_values);
    appendHashes(G_line_table, G_line_stops_keys, G_line_stops_values);
    appendHashes(yosemite_express_table, yosemite_express_stops_keys, yosemite_express_stops_values);
}