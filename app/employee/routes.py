from flask import request, jsonify
from. import employee_bp
from..models import Cab
from..utils import load_road_network, find_shortest_path_distance
from flask_jwt_extended import jwt_required

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