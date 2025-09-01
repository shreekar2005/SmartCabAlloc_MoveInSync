from flask import request, jsonify
from . import admin_bp
from ..models import Trip, Cab, User
from ..extensions import db, socketio
from ..utils import load_road_network, find_shortest_path_distance
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import render_template
from math import radians, cos, sin, asin, sqrt

def is_admin(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    return user and user.role == 'admin'


@admin_bp.route('/dashboard')
@jwt_required()
def dashboard_view():
    # Fetch all cabs
    all_cabs_query = Cab.query.all()
    all_cabs = []
    for cab in all_cabs_query:
        all_cabs.append({
            'id': cab.id,
            'driver_name': cab.driver_name,
            'license_plate': cab.license_plate,
            'current_lat': cab.current_lat,
            'current_lon': cab.current_lon,
            'status': cab.status
        })

    # Fetch pending trip requests
    pending_trips_query = Trip.query.filter_by(status='requested').all()
    pending_trips = []
    for trip in pending_trips_query:
        # Fetch the employee to get their public ID for consistency
        employee = User.query.get(trip.employee_id)
        if employee:
            pending_trips.append({
                'id': trip.id,
                'employee_id': employee.public_id, 
                'start_lat': trip.start_lat,
                'start_lon': trip.start_lon
            })

    return render_template('index.html', all_cabs=all_cabs, pending_trips=pending_trips)


@admin_bp.route('/trips', methods=['GET','POST'])
@jwt_required() 
def create_trip():
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"message": "Admin access required"}), 403

    data = request.get_json()
    user = User.query.filter_by(public_id=data.get('employee_public_id')).first()
    if not user:
        return jsonify({"message": "Employee not found"}), 404

    new_trip = Trip(
        employee_id=user.id,
        start_lat=data['start_lat'],
        start_lon=data['start_lon']
    )
    db.session.add(new_trip)
    db.session.commit()
    return jsonify({"message": "Trip created", "trip_id": new_trip.id}), 201




def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert decimal degrees to radians
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = rlon2 - rlon1
    dlat = rlat2 - rlat1
    a = sin(dlat / 2)**2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    
    distance = R * c
    return distance
# --- Add the haversine_distance function here (from the section above) ---

@admin_bp.route('/trips/<int:trip_id>/allocate', methods=['POST'])
@jwt_required()
def allocate_cab(trip_id):
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"message": "Admin access required"}), 403

    trip = Trip.query.get_or_404(trip_id)
    if trip.status != 'requested':
        return jsonify({"message": "Trip is not in 'requested' state"}), 400

    # Get all available cabs first
    all_available_cabs = Cab.query.filter_by(status='available').all()
    if not all_available_cabs:
        return jsonify({"message": "No available cabs found anywhere"}), 404
    
    trip_start_coords = (trip.start_lat, trip.start_lon)
    nearby_cabs = []
    SEARCH_RADIUS_KM = 5.0

    # Filter for cabs within the 5km radius
    for cab in all_available_cabs:
        distance_as_crow_flies = haversine_distance(
            trip_start_coords[0], trip_start_coords[1],
            cab.current_lat, cab.current_lon
        )
        if distance_as_crow_flies <= SEARCH_RADIUS_KM:
            nearby_cabs.append(cab)

    if not nearby_cabs:
        return jsonify({"message": f"No available cabs found within a {SEARCH_RADIUS_KM} km radius"}), 404

    graph = load_road_network()
    if not graph:
        return jsonify({"message": "Road network not available"}), 503
    
    best_cab = None
    min_distance = float('inf')

    for cab in nearby_cabs: 
        cab_coords = (cab.current_lat, cab.current_lon)
        # This expensive calculation is now only done for cabs that are already close
        distance = find_shortest_path_distance(graph, trip_start_coords, cab_coords)
        
        if distance < min_distance:
            min_distance = distance
            best_cab = cab

    if not best_cab:
        return jsonify({"message": "Could not find a suitable cab with a viable route"}), 404

    # Assign the cab and update statuses
    trip.cab_id = best_cab.id
    trip.status = 'in_progress'
    best_cab.status = 'on_trip'

    employee_user = User.query.get(trip.employee_id)
    employee_user.current_trip_status = 'in_trip'
    employee_user.current_trip_id = trip.id

    db.session.commit()

    # Notify dashboards in real-time
    employee_user = User.query.get(trip.employee_id)
    allocation_data = {
        'trip_id': trip.id,
        'employee_id': employee_user.public_id,
        'employee_lat': trip.start_lat,
        'employee_lon': trip.start_lon,
        'cab_id': best_cab.id,
        'cab_lat': best_cab.current_lat,
        'cab_lon': best_cab.current_lon
    }
    socketio.emit('trip_allocated', allocation_data)

    return jsonify({
        "message": f"Cab {best_cab.id} allocated to trip {trip.id}",
        "cab_id": best_cab.id,
        "trip_id": trip.id
    }), 200