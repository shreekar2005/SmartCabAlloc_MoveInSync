import osmnx as ox
import networkx as nx

# Define the location and network type
place_name = "Jodhpur, Rajasthan, India"
network_type = "drive"
file_path = "jodhpur.graphml"

print(f"Downloading road network for {place_name}...")

# Download the road network graph
graph = ox.graph_from_place(place_name, network_type=network_type)

# Get the largest strongly connected component
if not nx.is_strongly_connected(graph):
    print("Graph is not strongly connected. Extracting the largest component.")
    largest_scc = max(nx.strongly_connected_components(graph), key=len)
    graph = graph.subgraph(largest_scc).copy()
else:
    print("Graph is already strongly connected.")


print("Saving the graph to a file...")

ox.save_graphml(graph, filepath=file_path)

print(f"Graph saved successfully to {file_path}")
