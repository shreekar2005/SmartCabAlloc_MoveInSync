from flask import request, jsonify
from. import admin_bp
from..models import Trip, Cab, User
from..extensions import db
from..utils import load_road_network, find_shortest_path_distance
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import render_template

def is_admin(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    return user and user.role == 'admin'

# Add this new route to the file
@admin_bp.route('/dashboard')
@jwt_required()
def dashboard_view():
    # This route is just to serve the HTML page with the map.
    # The JWT is required to ensure only logged-in users can see it.
    return render_template('index.html')

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

@admin_bp.route('/trips/<int:trip_id>/allocate', methods=['GET','POST'])
@jwt_required()
def allocate_cab(trip_id):
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"message": "Admin access required"}), 403

    trip = Trip.query.get_or_404(trip_id)
    if trip.status!= 'requested':
        return jsonify({"message": "Trip is not in 'requested' state"}), 400

    available_cabs = Cab.query.filter_by(status='available').all()
    if not available_cabs:
        return jsonify({"message": "No available cabs found"}), 404

    graph = load_road_network()
    if not graph:
        return jsonify({"message": "Road network not available"}), 503

    trip_start_coords = (trip.start_lat, trip.start_lon)
    
    best_cab = None
    min_distance = float('inf')

    for cab in available_cabs:
        cab_coords = (cab.current_lat, cab.current_lon)
        distance = find_shortest_path_distance(graph, trip_start_coords, cab_coords)
        
        if distance < min_distance:
            min_distance = distance
            best_cab = cab

    if not best_cab:
        return jsonify({"message": "Could not find a suitable cab"}), 404

    return jsonify({
        "message": "Best cab found",
        "cab_id": best_cab.id,
        "driver_name": best_cab.driver_name,
        "license_plate": best_cab.license_plate,
        "distance_meters": round(min_distance, 2)
    }), 200