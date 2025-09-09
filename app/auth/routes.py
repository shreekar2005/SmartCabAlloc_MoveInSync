import random
from flask import request, jsonify, render_template, redirect, url_for
from. import auth_bp
from..models import User
from..extensions import db
from flask_jwt_extended import create_access_token, set_access_cookies
from flask_jwt_extended import jwt_required, get_jwt_identity

# login routes

@auth_bp.route('/login', methods=['POST'])
def login_post():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.public_id)
    response = jsonify({"message": "Login successful"})
    set_access_cookies(response, access_token)
    return response

@auth_bp.route('/admin/login', methods=['GET'])
def admin_login_page():
    return render_template('admin_login.html')

@auth_bp.route('/employee/login', methods=['GET'])
def employee_login_page():
    return render_template('employee_login.html')

@auth_bp.route('/login', methods=['GET'])
def login_page_redirect():
    return redirect(url_for('auth.employee_login_page'))

# signup routes

BASE_LAT = 26.2389  # jodhpur latitude
BASE_LON = 73.0243  # jodhpur longitude

@auth_bp.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'GET':
        return render_template('admin_signup.html')
    
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User already exists"}), 409

    user = User(
        email=data['email'], 
        role='admin',
        latitude=BASE_LAT + random.uniform(-0.01, 0.01),
        longitude=BASE_LON + random.uniform(-0.01, 0.01)
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Admin user registered successfully"}), 201

@auth_bp.route('/employee/signup', methods=['GET', 'POST'])
def employee_signup():
    if request.method == 'GET':
        return render_template('employee_signup.html')

    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User already exists"}), 409

    user = User(
        email=data['email'], 
        role='employee',
        latitude=BASE_LAT + random.uniform(-0.01, 0.01),
        longitude=BASE_LON + random.uniform(-0.01, 0.01)
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Employee user registered successfully"}), 201


