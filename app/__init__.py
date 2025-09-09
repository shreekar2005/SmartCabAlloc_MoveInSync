from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
import traceback
from .extensions import db, migrate, socketio, jwt, cache, cors
from .models import Cab
from config import Config
import flask_monitoringdashboard as dashboard

def create_app(config_class=Config):
    temp_app = Flask(__name__)
    temp_app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(temp_app)
    migrate.init_app(temp_app, db)
    jwt.init_app(temp_app)
    cache.init_app(temp_app) # allowing every domain to connect or communicate with our domain (or API end points)
    cors.init_app(temp_app)

    # for real-time location data integration
    socketio.init_app(temp_app, cors_allowed_origins="*")

    # very modular routing, i implemented this for modular design :)
    from .home.routes import home_bp
    from .auth.routes import auth_bp
    from .admin.routes import admin_bp
    from .employee.routes import employee_bp
    temp_app.register_blueprint(home_bp, url_prefix='/')
    temp_app.register_blueprint(auth_bp, url_prefix='/auth')
    temp_app.register_blueprint(admin_bp, url_prefix='/admin')
    temp_app.register_blueprint(employee_bp, url_prefix='/employee')

    # # for system monitoring
    # dashboard.config.enable_telemetry = False # to save our time when monitoring
    # dashboard.bind(temp_app)


    # defines the websocket event handlers for real-time communication.
    from flask_socketio import join_room

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('join_admin_room')
    def handle_join_admin_room():
        # to broadcast messages specifically to admins
        join_room('admins')
        print('An admin connected and joined the admin room.')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('update_location')
    def handle_location_update(data):
        # in a real app, we will authenticate this update (e.g. a jwt sent in the connection headers)
        cab_id = data.get('cab_id')
        lat = data.get('lat')
        lon = data.get('lon')

        if not all([cab_id, lat, lon]):
            return

        with temp_app.app_context():
            cab = Cab.query.get(cab_id)
            if cab:
                cab.current_lat = lat
                cab.current_lon = lon
                db.session.commit()
                
                # broadcast the update to all connected clients
                socketio.emit('location_update', {
                    'cab_id': cab.id,
                    'lat': cab.current_lat,
                    'lon': cab.current_lon,
                    'status': cab.status
                })

    # a centralized handler for all http exceptions.
    @temp_app.errorhandler(HTTPException)
    def handle_http_exception(e):
        response = e.get_response()
        response.data = jsonify({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }).data
        response.content_type = "application/json"
        return response

    # generic handler for any other exceptions.
    @temp_app.errorhandler(Exception)
    def handle_generic_exception(e):
        tb = traceback.format_exc()
        temp_app.logger.error(f"Unhandled exception: {str(e)}\n{tb}")
        response = {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
        return jsonify(response), 500
    
    # for system monitoring
    dashboard.config.enable_telemetry = False # to save our time when monitoring
    dashboard.bind(temp_app)
    
    return temp_app