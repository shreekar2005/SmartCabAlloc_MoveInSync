from.extensions import db
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True, default=lambda: str(uuid4()))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee') # 'admin' or 'employee'
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    trips = db.relationship('Trip', backref='employee', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Cab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_name = db.Column(db.String(100), nullable=False)
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    current_lat = db.Column(db.Float, nullable=False)
    current_lon = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available') # 'available', 'on_trip', 'unavailable'

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cab_id = db.Column(db.Integer, db.ForeignKey('cab.id'), nullable=True)
    start_lat = db.Column(db.Float, nullable=False)
    start_lon = db.Column(db.Float, nullable=False)
    end_lat = db.Column(db.Float, nullable=True)
    end_lon = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='requested') # 'requested', 'in_progress', 'completed', 'cancelled'