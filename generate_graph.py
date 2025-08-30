import osmnx as ox

# Define the location and network type
place_name = "Indian Institute of Technology Jodhpur, Jodhpur, Rajasthan, India"
network_type = "drive"
file_path = "iit_jodhpur.graphml"

print(f"Downloading road network for {place_name}...")

# Download the road network graph
# This can take a few minutes depending on the size of the area and your internet connection.
graph = ox.graph_from_place(place_name, network_type=network_type)

print("Saving the graph to a file...")

# Save the graph to a file for faster loading in the main application
ox.save_graphml(graph, filepath=file_path)

print(f"Graph saved successfully to {file_path}")