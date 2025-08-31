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

    # for "System Monitoring"
    # The dashboard will be available at /dashboard.

    # for "Real-Time Location Data Integration" requirement
    # We pass the app instance to SocketIO after all other initializations.
    socketio.init_app(app, cors_allowed_origins="*")

    # very modular routing
    from.home.routes import home_bp
    from.auth.routes import auth_bp
    from.admin.routes import admin_bp
    from.employee.routes import employee_bp
    app.register_blueprint(home_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(employee_bp, url_prefix='/employee')

    dashboard.config.enable_telemetry = False # to save our time when monitoring
    # dashboard.config.BLUEPRINT_NAME = ['auth_bp', 'admin_bp', 'employee_bp', 'home_bp']
    dashboard.bind(app)

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

    #generic handler for any other exceptions.
    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        # for unhandled errors, ensuring a JSON response.
        tb = traceback.format_exc()
        app.logger.error(f"Unhandled exception: {str(e)}\n{tb}")
        response = {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
        return jsonify(response), 500

    #defines the WebSocket event handlers for real-time communication.
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
        # In a real app, we will authenticate this update (e.g. a JWT sent in the connection headers)
        cab_id = data.get('cab_id')
        lat = data.get('lat')
        lon = data.get('lon')

        if not all([cab_id, lat, lon]):
            return

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