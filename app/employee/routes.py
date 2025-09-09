from flask import request, jsonify, render_template
from . import employee_bp
from ..models import Cab, User, Trip
from ..extensions import db, socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

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
    current_trip_id = None
    if user.current_trip_id:
        current_trip = Trip.query.get(user.current_trip_id)
        if current_trip and current_trip.status == 'in_progress' and current_trip.cab_id:
            current_trip_id = current_trip.id
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
        allocated_cab=allocated_cab,
        current_trip_id=current_trip_id
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

    # create the new trip
    new_trip = Trip(
        employee_id=user.id,
        start_lat=lat,
        start_lon=lon,
        status='requested'
    )
    db.session.add(new_trip)
    db.session.commit()

    # notify admins that a new trip has been requested
    socketio.emit('new_trip_request', {
        'id': new_trip.id,
        'employee_id': user.public_id,
        'start_lat': new_trip.start_lat,
        'start_lon': new_trip.start_lon
    }, room='admins')

    return jsonify({
        "message": "Trip requested successfully. Waiting for admin allocation.",
        "trip_id": new_trip.id,
        "status": "requested"
    }), 200


@employee_bp.route('/update-location', methods=['POST'])
@jwt_required()
def update_location():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')

    if not lat or not lon:
        return jsonify({"message": "Latitude and longitude are required"}), 400

    current_user_public_id = get_jwt_identity()
    user = User.query.filter_by(public_id=current_user_public_id).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    user.latitude = lat
    user.longitude = lon
    db.session.commit()

    return jsonify({"message": "Location updated successfully"}), 200



@employee_bp.route('/trips/finish', methods=['POST'])
@jwt_required()
def finish_employee_trip():
    current_user_public_id = get_jwt_identity()
    user = User.query.filter_by(public_id=current_user_public_id).first()

    if not user or not user.current_trip_id:
        return jsonify({"message": "No active trip found for this user."}), 404

    trip = Trip.query.get_or_404(user.current_trip_id)

    # security check: ensure the employee finishing the trip is the one who requested it
    if trip.employee_id != user.id:
        return jsonify({"message": "Forbidden: You are not authorized to modify this trip."}), 403

    if trip.status != 'in_progress':
        return jsonify({"message": f"Trip is not in progress. Current status: {trip.status}"}), 400

    allocated_cab = Cab.query.get(trip.cab_id)

    # update the trip
    trip.status = 'completed'
    trip.end_time = datetime.utcnow()

    # free up the cab
    if allocated_cab:
        allocated_cab.status = 'available'
        allocated_cab.destination_latitude = None
        allocated_cab.destination_longitude = None

        # emit a real-time update that the cab is now available
        socketio.emit('location_update', {
            'cab_id': allocated_cab.id,
            'lat': allocated_cab.current_lat,
            'lon': allocated_cab.current_lon,
            'status': 'available'
        })

    # update user's trip status
    user.current_trip_status = 'not_in_trip'
    user.current_trip_id = None

    db.session.commit()

    socketio.emit('trip_finished', {'id': trip.id})

    return jsonify({"message": "Trip finished successfully."}), 200