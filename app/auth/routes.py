from flask import request, jsonify
from. import auth_bp
from..models import User
from..extensions import db, jwt
from flask_jwt_extended import create_access_token, create_refresh_token

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User already exists"}), 409

    user = User(email=data['email'], role=data.get('role', 'employee'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.public_id)
    refresh_token = create_refresh_token(identity=user.public_id)

    return jsonify(access_token=access_token, refresh_token=refresh_token), 200