import time
import random
import socketio
from app import create_app, db
from app.models import Cab

# --- Configuration ---
BASE_LAT = 26.4715  # IIT Jodhpur Latitude
BASE_LON = 73.1134  # IIT Jodhpur Longitude
NUM_CABS = 3
SERVER_URL = 'http://127.0.0.1:5000'

# --- Helper Functions ---
def get_random_offset():
    """Generates a small random offset for coordinates."""
    return random.uniform(-0.01, 0.01)

def create_sample_cabs(app):
    """Creates sample cabs in the database if they don't exist."""
    with app.app_context():
        if Cab.query.count() == 0:
            print("Creating sample cabs...")
            cabs = [
                Cab(driver_name=f'driver{i}', license_plate=f'RJ19PA{1000 + i}', current_lat=BASE_LAT + get_random_offset(), current_lon=BASE_LON + get_random_offset(), status='available')
                for i in range(NUM_CABS)
            ]
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
    try:
        with app.app_context():
            cabs = Cab.query.all()
            while True:
                for cab in cabs:
                    # Update cab's location slightly
                    cab.current_lat += random.uniform(-0.001, 0.001)
                    cab.current_lon += random.uniform(-0.001, 0.001)
                    
                    # Randomly change status
                    # if random.random() < 0.1:
                    #     cab.status = 'on_trip' if cab.status == 'available' else 'available'

                    location_data = {
                        'cab_id': cab.id,
                        'lat': cab.current_lat,
                        'lon': cab.current_lon,
                        'status': cab.status
                    }
                    
                    sio.emit('update_location', location_data)
                    print(f"Updated location for Cab ID {cab.id}: {location_data['lat']:.4f}, {location_data['lon']:.4f}, Status: {location_data['status']}")
                
                time.sleep(1) # Wait for 1 seconds before the next update

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    finally:
        sio.disconnect()
