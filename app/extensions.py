from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
jwt = JWTManager()
cache = Cache()
cors = CORS()
