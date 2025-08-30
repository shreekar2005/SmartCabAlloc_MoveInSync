from flask import request, jsonify, render_template
from. import employee_bp
from..models import Cab, User, Trip
from..extensions import db, socketio
from..utils import load_road_network, find_shortest_path_distance
from flask_jwt_extended import jwt_required, get_jwt_identity

@employee_bp.route('/dashboard')
@jwt_required()
def employee_dashboard():
    current_user_public_id = get_jwt_identity()
    user = User.query.filter_by(public_id=current_user_public_id).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Fetch all 'on_trip' cabs
    on_trip_cabs_query = Cab.query.filter_by(status='on_trip').all()
    on_trip_cabs = []
    for cab in on_trip_cabs_query:
        on_trip_cabs.append({
            'id': cab.id,
            'driver_name': cab.driver_name,
            'license_plate': cab.license_plate,
            'current_lat': cab.current_lat,
            'current_lon': cab.current_lon,
            'status': cab.status
        })

    # Fetch the cab allocated to this specific employee, if any
    allocated_cab = None
    current_trip = Trip.query.filter_by(employee_id=user.id, status='in_progress').first()
    if current_trip and current_trip.cab_id:
        cab = Cab.query.get(current_trip.cab_id)
        if cab:
            allocated_cab = {
                'id': cab.id,
                'driver_name': cab.driver_name,
                'license_plate': cab.license_plate,
                'current_lat': cab.current_lat,
                'current_lon': cab.current_lon,
                'status': cab.status
            }

    return render_template(
        'employee_dashboard.html',
        user_public_id=user.public_id,
        user_location={'lat': user.latitude, 'lon': user.longitude},
        on_trip_cabs=on_trip_cabs,
        allocated_cab=allocated_cab
    )

@employee_bp.route('/request-trip', methods=['POST'])
@jwt_required()
def request_trip():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')

    if not lat or not lon:
        return jsonify({"message": "Latitude and longitude are required"}), 400

    current_user_public_id = get_jwt_identity()
    user = User.query.filter_by(public_id=current_user_public_id).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Create the new trip
    new_trip = Trip(
        employee_id=user.id,
        start_lat=lat,
        start_lon=lon,
        status='requested'
    )
    db.session.add(new_trip)
    db.session.commit()

    # Notify the admin dashboard in real-time
    socketio.emit('new_trip_request', {
        'trip_id': new_trip.id,
        'employee_id': user.id,
        'employee_lat': new_trip.start_lat,
        'employee_lon': new_trip.start_lon
    }, room='admins') # Emitting to a room admins can join

    return jsonify({"message": "Trip requested successfully", "trip_id": new_trip.id}), 201


@employee_bp.route('/cabs/nearby', methods=['GET','POST'])
@jwt_required()
def get_nearby_engaged_cabs():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius_km = request.args.get('radius', type=float, default=5.0)

    if lat is None or lon is None:
        return jsonify({"message": "Latitude and longitude are required parameters"}), 400

    # This logic specifically implements the requirement to show ONLY engaged cabs. [1]
    engaged_cabs = Cab.query.filter_by(status='on_trip').all()
    
    graph = load_road_network()
    if not graph:
        return jsonify({"message": "Road network not available"}), 503

    employee_coords = (lat, lon)
    nearby_cabs = []

    for cab in engaged_cabs:
        cab_coords = (cab.current_lat, cab.current_lon)
        distance_meters = find_shortest_path_distance(graph, employee_coords, cab_coords)
        
        if distance_meters <= radius_km * 1000:
            nearby_cabs.append({
                "id": cab.id,
                "driver_name": cab.driver_name,
                "license_plate": cab.license_plate,
                "lat": cab.current_lat,
                "lon": cab.current_lon,
                "status": cab.status,
                "distance_meters": round(distance_meters, 2)
            })

    # Sort by distance
    nearby_cabs.sort(key=lambda x: x['distance_meters'])

    return jsonify(nearby_cabs), 200