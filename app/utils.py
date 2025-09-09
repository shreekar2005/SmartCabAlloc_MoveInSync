import osmnx as ox
import networkx as nx
from .extensions import cache
from .models import Cab
from math import radians, cos, sin, asin, sqrt

# using dijkstra's, which is one of best algorith for finding the shortest path.
# time complexity: o((e + v) log v) where v is vertices (intersections) and e is edges (roads).
# space complexity: o(v + e) to store the graph in memory.

GRAPH_FILE_PATH = "jodhpur.graphml"
SEARCH_RADIUS_KM = 5.0

# this uses the caching to avoid reloading the large graph file from disk on every request.
@cache.memoize(timeout=3600) # cache for 1 hour
def load_road_network():
    try:
        graph = ox.load_graphml(GRAPH_FILE_PATH)
        return graph
    except FileNotFoundError:
        # this is a fallback and should not happen if generate_graph.py is run first.
        print(f"Graph file not found at {GRAPH_FILE_PATH}. Please run generate_graph.py first.")
        return None

def find_shortest_path_distance(graph, start_coords, end_coords):
    if not graph:
        return float('inf')

    try:
        # find the nearest network nodes to the given coordinates
        # the correct usage is x=longitude, y=latitude
        start_node = ox.distance.nearest_nodes(graph, X=start_coords[1], Y=start_coords[0])
        end_node = ox.distance.nearest_nodes(graph, X=end_coords[1], Y=end_coords[0])

        # calculate the shortest path length using dijkstra's algorithm
        distance_meters = nx.shortest_path_length(graph, source=start_node, target=end_node, weight='length')
        return distance_meters
    
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        # handle cases where no path exists or nodes are not found
        return float('inf')

def haversine_distance(lat1, lon1, lat2, lon2):
    # convert decimal degrees to radians
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])

    # haversine formula
    dlon = rlon2 - rlon1
    dlat = rlat2 - rlat1
    a = sin(dlat / 2)**2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    R = 6371.0 # earth's radius in kilometers
    distance = R * c
    return distance

# so first haversine distance is calculate to check that is there any cab in <5KM radius 
def allocate_cab_to_trip(trip):
    all_available_cabs = Cab.query.filter_by(status='available').all()
    if not all_available_cabs:
        return None, "No available cabs found anywhere"
    
    trip_start_coords = (trip.start_lat, trip.start_lon)
    nearby_cabs = []

    for cab in all_available_cabs:
        distance_as_crow_flies = haversine_distance(
            trip_start_coords[0], trip_start_coords[1],
            cab.current_lat, cab.current_lon
        )
        if distance_as_crow_flies <= SEARCH_RADIUS_KM:
            nearby_cabs.append(cab)

    if not nearby_cabs:
        return None, f"No available cabs found within a {SEARCH_RADIUS_KM} km radius"

    graph = load_road_network()
    if not graph:
        return None, "Road network not available"
    
    best_cab = None
    min_distance = float('inf')

    for cab in nearby_cabs: 
        cab_coords = (cab.current_lat, cab.current_lon)
        distance = find_shortest_path_distance(graph, trip_start_coords, cab_coords)
        
        if distance < min_distance:
            min_distance = distance
            best_cab = cab

    if not best_cab:
        return None, "Could not find a suitable cab with a viable route"

    return best_cab, "Cab allocated successfully"