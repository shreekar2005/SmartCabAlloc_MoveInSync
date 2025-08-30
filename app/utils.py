import osmnx as ox
import networkx as nx
from.extensions import cache

# This file addresses the "Cost Estimation - Time and Space" plus point.
# The core algorithm is Dijkstra's, which is efficient for finding the shortest path.
# Time Complexity: O(E + V log V) where V is vertices (intersections) and E is edges (roads).
# Space Complexity: O(V + E) to store the graph in memory. [1]

GRAPH_FILE_PATH = "new_york.graphml"

# This uses the "Caching" plus point to avoid reloading the large graph file from disk on every request. [1]
@cache.memoize(timeout=3600) # Cache for 1 hour
def load_road_network():
    """Loads the road network graph from a file."""
    try:
        graph = ox.load_graphml(GRAPH_FILE_PATH)
        return graph
    except FileNotFoundError:
        # This is a fallback and should not happen if generate_graph.py is run first.
        print(f"Graph file not found at {GRAPH_FILE_PATH}. Please run generate_graph.py first.")
        return None

def find_shortest_path_distance(graph, start_coords, end_coords):
    """
    Calculates the shortest path distance in meters between two lat/lon coordinates
    using Dijkstra's algorithm on the road network.
    """
    if not graph:
        return float('inf')

    try:
        # Find the nearest network nodes to the given coordinates
        start_node = ox.distance.nearest_nodes(graph, Y=start_coords, X=start_coords[1])
        end_node = ox.distance.nearest_nodes(graph, Y=end_coords, X=end_coords[1])

        # Calculate the shortest path length using Dijkstra's algorithm
        distance_meters = nx.shortest_path_length(graph, source=start_node, target=end_node, weight='length')
        return distance_meters
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        # Handle cases where no path exists or nodes are not found
        return float('inf')