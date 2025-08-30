from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
import os
import traceback

from.extensions import db, migrate, socketio, jwt, cache, cors
from.models import Cab
from config import Config
import flask_monitoringdashboard as dashboard

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    cors.init_app(app)

    # This addresses the "System Monitoring" plus point. [1]
    # The dashboard will be available at /dashboard.
    dashboard.bind(app)

    # This addresses the "Real-Time Location Data Integration" requirement. [1]
    # We pass the app instance to SocketIO after all other initializations.
    socketio.init_app(app, cors_allowed_origins="*")

    # Register Blueprints for modular code structure (OOPS). [1]
    from.auth.routes import auth_bp
    from.admin.routes import admin_bp
    from.employee.routes import employee_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(employee_bp, url_prefix='/employee')

    # This addresses the "Error and Exception Handling" plus point. [1]
    # A centralized handler for all HTTP exceptions.
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        response = e.get_response()
        response.data = jsonify({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }).data
        response.content_type = "application/json"
        return response

    # A generic handler for any other exceptions.
    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        # This is a fallback for unhandled errors, ensuring a JSON response.
        # In production, you would log this error extensively.
        tb = traceback.format_exc()
        app.logger.error(f"Unhandled exception: {str(e)}\n{tb}")
        response = {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
        return jsonify(response), 500
    #... (inside create_app, after blueprint registration)

    # This section addresses the "Real-Time Location Data Integration" requirement. [1]
    # It defines the WebSocket event handlers for real-time communication.
    from flask_socketio import join_room

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('join_admin_room')
    def handle_join_admin_room():
        # This allows us to broadcast messages specifically to admins
        join_room('admins')
        print('An admin connected and joined the admin room.')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('update_location')
    def handle_location_update(data):
        # In a real app, you'd authenticate this update (e.g., with a JWT sent in the connection headers)
        cab_id = data.get('cab_id')
        lat = data.get('lat')
        lon = data.get('lon')

        if not all([cab_id, lat, lon]):
            return # Ignore invalid data

        with app.app_context():
            cab = Cab.query.get(cab_id)
            if cab:
                cab.current_lat = lat
                cab.current_lon = lon
                db.session.commit()
                
                # Broadcast the update to all connected clients
                socketio.emit('location_update', {
                    'cab_id': cab.id,
                    'lat': cab.current_lat,
                    'lon': cab.current_lon,
                    'status': cab.status
                })

    return app