import time
import random
import socketio
import osmnx as ox
from app import create_app, db
from app.models import Cab

# --- Configuration ---
GRAPH_FILE = "jodhpur.graphml"
NUM_CABS = 3
SERVER_URL = 'http://127.0.0.1:5000'

# Load the graph
print(f"Loading graph from {GRAPH_FILE}...")
graph = ox.load_graphml(GRAPH_FILE)
nodes = list(graph.nodes)
print("Graph loaded successfully.")

# --- Helper Functions ---
def create_sample_cabs(app):
    """Creates sample cabs in the database if they don't exist."""
    with app.app_context():
        if Cab.query.count() == 0:
            print("Creating sample cabs...")
            cabs = []
            for i in range(NUM_CABS):
                random_node = random.choice(nodes)
                node_data = graph.nodes[random_node]
                cabs.append(
                    Cab(
                        driver_name=f'driver{i}',
                        license_plate=f'RJ19PA{1000 + i}',
                        current_lat=node_data['y'],
                        current_lon=node_data['x'],
                        status='available'
                    )
                )
            db.session.bulk_save_objects(cabs)
            db.session.commit()
            print(f"{NUM_CABS} sample cabs created.")
        else:
            print("Cabs already exist in the database.")

# --- Main Simulation Logic ---
if __name__ == "__main__":
    # Create a Flask app context to interact with the database
    app = create_app()
    create_sample_cabs(app)

    # Initialize Socket.IO client
    sio = socketio.Client()

    @sio.event
    def connect():
        print("Successfully connected to the server.")

    @sio.event
    def connect_error(data):
        print(f"Connection failed: {data}")

    @sio.event
    def disconnect():
        print("Disconnected from the server.")

    # Connect to the server
    try:
        sio.connect(SERVER_URL)
    except socketio.exceptions.ConnectionError as e:
        print(f"Error connecting to server: {e}")
        exit()

    # Start simulation loop
    print("Starting cab simulation...")
cab_nodes = {}
try:
    with app.app_context():
        while True:
            cabs = Cab.query.all()
            for cab in cabs:
                if cab.id not in cab_nodes:
                    cab_nodes[cab.id] = ox.distance.nearest_nodes(graph, X=cab.current_lon, Y=cab.current_lat)

                current_node = cab_nodes[cab.id]
                neighbors = list(graph.neighbors(current_node))

                if neighbors:
                    next_node = random.choice(neighbors)
                    cab.current_lat = graph.nodes[next_node]['y']
                    cab.current_lon = graph.nodes[next_node]['x']
                    cab_nodes[cab.id] = next_node

                location_data = {
                    'cab_id': cab.id,
                    'lat': cab.current_lat,
                    'lon': cab.current_lon,
                    'status': cab.status
                }
                
                sio.emit('update_location', location_data)
                print(f"Updated location for Cab ID {cab.id}: {location_data['lat']:.4f}, {location_data['lon']:.4f}, Status: {location_data['status']}")
            
            db.session.commit()
            time.sleep(2) # Wait for 2 seconds before the next update

except KeyboardInterrupt:
    print("\nSimulation stopped by user.")
finally:
    sio.disconnect()