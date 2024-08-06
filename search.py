import time
#start_time = time.time()
from datetime import datetime
import pytz
tz_LA = pytz.timezone('America/Los_Angeles')
datetime_LA = datetime.now(tz_LA)

from route_datatypes import*

placeFoundq1 = False
placeFoundq2 = False
def validatePlaceq1(target, start, end):
    places.sort()
    global placeFoundq1
    if (start > end):
        placeFoundq1 = False
        return placeFoundq1
    middle = (start + end) // 2
    if (places[middle] == target):
        placeFoundq1 = True
        return placeFoundq1
    elif (places[middle] > target):
        return validatePlaceq1(target, start, middle - 1)
    else:
        return validatePlaceq1(target, middle + 1, end)
    
def validatePlaceq2(target, start, end):
    places.sort()
    global placeFoundq2
    if (start > end):
        placeFoundq2 = False
        return placeFoundq2
    middle = (start + end) // 2
    if (places[middle] == target):
        placeFoundq2 = True
        return placeFoundq2
    elif (places[middle] > target):
        return validatePlaceq2(target, start, middle - 1)
    else:
        return validatePlaceq2(target, middle + 1, end)

def validateTime(input_time):
    global valid_time
    try:
        parsed_time = datetime.strptime(input_time, '%H:%M:%S')
        if 0 <= parsed_time.hour < 24 and 0 <= parsed_time.minute < 60 and 0 <= parsed_time.second < 60:
            valid_time = True
        else:
            valid_time = False
    except ValueError:
        valid_time = False

    

q1 = input("Where would you like to go?: ")
validatePlaceq1(q1, 0, len(places) - 1)

while True:
    if (placeFoundq1 == False):
        print("Invalid location")
        q1 = input('''Where would you like to go?: 
        R Street Village Apts, El Redondo Dr, Compass Pointe Apts, Merced College The Bus Terminal, M St. At Bellevue RD, University Transit Center, Promenade Center, 
        Merced Mall Target, Walmart on Loughborough Dr, Amtrak Station, K St. Between 18th & 19th, Merced Transpo (REQ), Rite Aid/Walgreens on G St, 
        El Portal Plaza & G Street, Granville Apartments, G St. & W. Alexander Ave, El Portal & G Street, Mercy Hospital/TriCollege, TriCollege/Mercy (Bus stop on G next to Tri College), 
        G St. & W. Alexander Ave. (Bus Stop Paul's Place), Cardella Rd. & 'M' Street (North), Foothill Drive, Cardella Rd. & 'M' Street (South), G Street South Across from Raley's (The Bus Stop),
        K St. Between 18Th & 19th, Meadows Ave & Olivewood Dr (Foodmaxx), Yosemite Crossings Shopping Center, M Street Village Apartments, Ironstone Dr. & M St, 
        Yosemite & Cordova (Merced Physician Center), Moraga Subdivision, University Surgery Center, Cardella Rd. & 'M' Street, Cardella Rd. & 'M' Street,
        K St. Between 18th & 19th, UC Merced Downtown Campus Center, Merced Transpo, G Street South\n''')
        validatePlaceq1(q1, 0, len(places) - 1)
    else:
        break

q2 = input("Where are you currently located?: ")
    
validatePlaceq2(q2, 0, len(places) - 1)
while True:
    if(placeFoundq2 == False):
        print("Invalid location")
        q2 = input('''Where are you currently located?: 
        R Street Village Apts, El Redondo Dr, Compass Pointe Apts, Merced College The Bus Terminal, M St. At Bellevue RD, University Transit Center, Promenade Center, 
        Merced Mall Target, Walmart on Loughborough Dr, Amtrak Station, K St. Between 18th & 19th, Merced Transpo (REQ), Rite Aid/Walgreens on G St, 
        El Portal Plaza & G Street, Granville Apartments, G St. & W. Alexander Ave, El Portal & G Street, Mercy Hospital/TriCollege, TriCollege/Mercy (Bus stop on G next to Tri College), 
        G St. & W. Alexander Ave. (Bus Stop Paul's Place), Cardella Rd. & 'M' Street (North), Foothill Drive, Cardella Rd. & 'M' Street (South), G Street South Across from Raley's (The Bus Stop),
        K St. Between 18Th & 19th, Meadows Ave & Olivewood Dr (Foodmaxx), Yosemite Crossings Shopping Center, M Street Village Apartments, Ironstone Dr. & M St, 
        Yosemite & Cordova (Merced Physician Center), Moraga Subdivision, University Surgery Center, Cardella Rd. & 'M' Street, Cardella Rd. & 'M' Street,
        K St. Between 18th & 19th, UC Merced Downtown Campus Center, Merced Transpo, G Street South\n''')
        validatePlaceq2(q2, 0, len(places) - 1)
    else:
        break


    
#q3 = input("What time do you want to arrive by?")
#print("Pacific time:", datetime_LA.strftime("%I:%M:%p"))
named_stops = {"Bobcat Express": bobcat_express_stops, "C1": C1_stops, "C2": C2_stops, "E1": E1_stops, "E2": E2_stops, "Fastcat": Fastcat_stops, "Fastcat 2": Fastcat2_stops, "G Line": G_line_stops, "Yosemite Express" : yosemite_express_stops}
bus_names = {}
possible_buses = {}
possible_busnames = []
possible_distances = {}
shortest_stops = []
busGo_stops = {}
distances_dict = {}
shortestnames_stops = {}
distances_list = []

q3 = input("What time would you like to arrive by? Enter a time (Hour:Minute:Second format): ")
validateTime(q3)
while True:
    if (valid_time == False):
        q3 = input("What time would you like to arrive by? Enter a time (Hour:Minute:Second format)")
        validateTime(q3)
    else:
        break
def dict_binary_search(name, target):
    sorted_names = sorted(list(name.keys()))
    low = 0 
    high = len(sorted_names) - 1 
    while (low <= high): 
        middle = (low + high) // 2 
        value = sorted_names[middle] 
        if (value < target): 
            low = middle + 1 
        elif(value > target): 
            high = middle - 1 
        else: 
            return sorted_names[middle]

        
def findBusTaken():
    for name, stop in named_stops.items():
        if (dict_binary_search(stop, q2) == q2):
            bus_names[name] = stop

def busGoStops():
    for name, stop in named_stops.items():
        if (dict_binary_search(stop, q1) == q1):
            busGo_stops[name] = stop
            
from routingpy import ORS
from pprint import pprint
client = ORS(api_key='5b3ce3597851110001cf6248e4dacfb3ab0a4b1d83a0511ffdd542f3')
def findBusGo():
    global possible_buses
    global distanceBusGo
    global distancepointq2_q3
    global distancepointq3_q1
    global totalDistance
    global pointq1
    global pointr1
    global pointq1_coordinates
    global pointq2
    global pointr2
    global pointq2_coordinates
    global pointq3
    global pointq3_coordinates
    #when the stop you want to go to is not found in the stops of the bus you took, code checks if the other stops on the bus you took are found in other busses, if stop found in other buses, adds name of the buss to possible buses list
    global takenBusStops
    for name, stop2 in bus_names.items():
        for j2 in stop2:
            takenBusStops = j2
            for name1, stop3 in busGo_stops.items():
                for j3 in stop3:
                    if (dict_binary_search(stop3, takenBusStops) == j3):
                        pointq1_coordinates = (geo_pyPlacesCoords[places.index(q1)])  #where wanna go
                        pointq2_coordinates = (geo_pyPlacesCoords[places.index(q2)])  # where currently located
                        pointq3_coordinates = (geo_pyPlacesCoords[places.index(takenBusStops)]) #coordinates of similar bus stop
                        #coords = [pointq1_coordinates, pointq2_coordinates, pointq3_coordinates]
                        route = client.directions(locations= (pointq2_coordinates, pointq3_coordinates, pointq1_coordinates), profile="driving-car")
                        possible_distances[route.distance] = j3
                        possible_busnames.append(name)
                        shortest_stops.append(j3)
                        possible_buses[j3] = name1                                     
def findshortestBus():
    global pointq4
    global pointq5
    min_distance = min(possible_distances.keys())
    global bus_stop
    global b_name
    global index 
    global min_stop
    
    min_stop = possible_distances[min_distance]
    for stop, route in possible_buses.items():
        global min_bus
        if (dict_binary_search(possible_buses, min_stop) == stop): #check if bianry vs linear faster here
            min_bus = route
            break   
    


findBusTaken()
busGoStops()
findBusGo()
findshortestBus()
#print(possible_distances)
#print(possible_busnames)
print(possible_buses)
potential_buses = set()
if (min_stop == q2 or min_stop == q1):
    print(f'Take {min_bus} to {q1}')
else:
    for name, stop in bus_names.items():
        if (dict_binary_search(stop, q2) == q2 and dict_binary_search(stop, min_stop) == min_stop):
            potential_buses.add(name)
    unique_list = list(potential_buses)
    print(f'Take {", ".join(potential_buses)} to {min_stop} then take {min_bus} to {q1}')

#print("Process finished --- %s seconds ---" % (time.time() - start_time))
