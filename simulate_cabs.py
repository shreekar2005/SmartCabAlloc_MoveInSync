import time
import random
import socketio
import osmnx as ox
from app import create_app, db
from app.models import Cab
import networkx # Added to handle pathfinding errors

GRAPH_FILE = "jodhpur.graphml"
NUM_CABS = 3
SERVER_URL = 'http://127.0.0.1:5000'

# Load the graph
print(f"Loading graph from {GRAPH_FILE}...")
graph = ox.load_graphml(GRAPH_FILE)
nodes = list(graph.nodes)
print("Graph loaded successfully.")

def create_sample_cabs(app):
    """Creates or resets sample cabs in the database."""
    with app.app_context():
        if Cab.query.count() < NUM_CABS:
            Cab.query.delete() # Clear old cabs if count is wrong
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
                        status='available',
                        # Ensure destination is initially null
                        destination_latitude=None,
                        destination_longitude=None
                    )
                )
            db.session.bulk_save_objects(cabs)
            db.session.commit()
            print(f"{NUM_CABS} sample cabs created.")
        else:
            print("Cabs already exist in the database.")


if __name__ == "__main__":
    app = create_app()
    create_sample_cabs(app)

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

    try:
        sio.connect(SERVER_URL)
    except socketio.exceptions.ConnectionError as e:
        print(f"Error connecting to server: {e}")
        exit()

    print("Starting cab simulation...")
    
    cab_nodes = {}
    cab_routes = {} # For destination-based movement

    try:
        with app.app_context():
            while True:
                cabs = Cab.query.all()
                for cab in cabs:
                    
                    # Cab has a destination and is on a trip
                    if cab.destination_latitude is not None and cab.destination_longitude is not None:
                        # If cab just got a destination, calculate its route
                        if cab.id not in cab_routes or not cab_routes[cab.id]['route']:
                            print(f"Cab {cab.id} calculating route to destination...")
                            start_node = ox.distance.nearest_nodes(graph, cab.current_lon, cab.current_lat)
                            end_node = ox.distance.nearest_nodes(graph, cab.destination_longitude, cab.destination_latitude)
                            try:
                                route = ox.shortest_path(graph, start_node, end_node, weight='length')
                                # Ensure the route is valid before assigning
                                if route:
                                    cab_routes[cab.id] = {'route': route, 'index': 0}
                                else:
                                    print(f"No path found for Cab {cab.id} (empty route). It will wait.")
                                    cab_routes[cab.id] = {'route': [], 'index': 0} # Prevent recalculating
                                    continue
                            except networkx.NetworkXNoPath:
                                print(f"No path found for Cab {cab.id}. It will wait.")
                                cab_routes[cab.id] = {'route': [], 'index': 0} # Prevent recalculating
                                continue 

                        # Move cab one step along its calculated route
                        state = cab_routes.get(cab.id)
                        # Safely check for route existence and index
                        if state and state.get('route') and state['index'] < len(state['route']):
                            next_node = state['route'][state['index']]
                            cab.current_lat = graph.nodes[next_node]['y']
                            cab.current_lon = graph.nodes[next_node]['x']
                            state['index'] += 1
                        else:
                            print(f"Cab {cab.id} has arrived at its destination.")
                            # When trip is over, clear destination and route
                            cab.destination_latitude = None
                            cab.destination_longitude = None
                            cab.status = 'available'
                            cab_routes[cab.id] = {'route': [], 'index': 0}

                    # Cab is available and moves randomly
                    else:
                        if cab.id not in cab_nodes:
                            cab_nodes[cab.id] = ox.distance.nearest_nodes(graph, cab.current_lon, cab.current_lat)

                        current_node = cab_nodes[cab.id]
                        neighbors = list(graph.neighbors(current_node))

                        if neighbors:
                            next_node = random.choice(neighbors)
                            cab.current_lat = graph.nodes[next_node]['y']
                            cab.current_lon = graph.nodes[next_node]['x']
                            cab_nodes[cab.id] = next_node
                    

                    # This part runs for all cabs, regardless of how they moved
                    location_data = {
                        'cab_id': cab.id,
                        'lat': cab.current_lat,
                        'lon': cab.current_lon,
                        'status': cab.status
                    }
                    
                    sio.emit('update_location', location_data)
                    print(f"Updated location for Cab ID {cab.id}: {location_data['lat']:.4f}, {location_data['lon']:.4f}, Status: {location_data['status']}")
                
                db.session.commit()
                time.sleep(1) # Wait for 2 seconds before the next update

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    finally:
        if sio.connected:
            sio.disconnect()