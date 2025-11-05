from flask import Flask, jsonify, request, g
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
from werkzeug.security import check_password_hash 

from disasters import get_natural_disasters
from locations import get_nearby_places

from user_management import (
    register_user, 
    find_user_by_username, 
    find_user_by_id, 
    load_users, 
    save_users
)
from auth import create_access_token, jwt_required

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app) 

OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
# SECRET_KEY cũng được tải trong auth.py và user_management.py

# -------------------------------------------------------------------
# /api/weather 
# -------------------------------------------------------------------
@app.route('/api/weather')
def get_weather():
    lat = request.args.get('lat', '35.6895')
    lon = request.args.get('lon', '139.6917')
    
    if OPENWEATHER_API_KEY:
        try:
            url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}'
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            return jsonify([{
                'lat': float(lat),
                'lng': float(lon), 
                'name': f'Weather: {data["weather"][0]["main"]}',
                'description': data["weather"][0]["description"],
                'details': f'Temperature: {round(data["main"]["temp"] - 273.15, 1)}°C'
            }])
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return jsonify([])
    
    return jsonify([{
        'lat': float(lat),
        'lng': float(lon), 
        'name': 'Weather Alert (Mock)',
        'description': 'Partly cloudy',
        'details': 'Temperature: 22°C'
    }])

# -------------------------------------------------------------------
# /api/disaster 
# -------------------------------------------------------------------
@app.route('/api/disaster')
def get_disasters():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if lat is None or lon is None:
        return jsonify([]) 

    data = get_natural_disasters(lat, lon, max_distance_km=200)
    return jsonify(data)

# -------------------------------------------------------------------
# /api/crowd 
# -------------------------------------------------------------------
@app.route('/api/crowd')
def get_crowds():
    lat = request.args.get('lat', '35.6895')
    lon = request.args.get('lon', '139.6917')
    
    return jsonify([{
        'lat': float(lat),
        'lng': float(lon), 
        'name': 'Crowd Alert (Mock)',
        'description': 'High crowd density detected',
        'details': 'Estimated 1000+ people in area'
    }])

# -------------------------------------------------------------------
# /api/shelter 
# -------------------------------------------------------------------
@app.route('/api/shelter')
def get_shelters():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify([])
        
    data = get_nearby_places(lat, lon, "shelter") 
    return jsonify(data)

# -------------------------------------------------------------------
# /api/hospital 
# -------------------------------------------------------------------
@app.route('/api/hospital')
def get_hospitals():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify([])
        
    data = get_nearby_places(lat, lon, "hospital")
    return jsonify(data)

# -------------------------------------------------------------------
# API Khẩn cấp 
# -------------------------------------------------------------------
@app.route('/api/emergency', methods=['POST'])
def handle_emergency():
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng') 
    
    print(f"Emergency alert received from location: {lat}, {lng}")
    return jsonify({'status': 'success', 'message': 'Emergency services notified'})

# -------------------------------------------------------------------
# API Đăng ký 
# -------------------------------------------------------------------
@app.route('/api/register', methods=['POST'])
def handle_register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    address = data.get('address') 

    if not username or not password or not email:
        return jsonify({"error": "Username, password, and email are required"}), 400

    new_user = register_user(username, password, email, address)
    
    if new_user is None:
        return jsonify({"error": "Username already exists"}), 409

    return jsonify({
        "id": new_user['id'],
        "username": new_user['username'],
        "email": new_user['email'],
        "address": new_user['address']
    }), 201

# -------------------------------------------------------------------
# API Đăng nhập 
# -------------------------------------------------------------------
@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = find_user_by_username(username)

    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid username or password"}), 401 

    access_token = create_access_token(user_id=user['id'])
    
    return jsonify({"access_token": access_token})

# -------------------------------------------------------------------
# API Profile 
# -------------------------------------------------------------------
@app.route('/api/profile', methods=['GET', 'PUT'])
@jwt_required # <-- Đây là khóa bảo vệ!
def handle_profile():
    current_user = g.current_user 
    
    if request.method == 'GET':
        return jsonify({
            "id": current_user['id'],
            "username": current_user['username'],
            "email": current_user['email'],
            "address": current_user['address'],
            "favorite_locations": current_user.get('favorite_locations', [])
        })

    if request.method == 'PUT':
        data = request.json
        users = load_users()
        user_to_update = None
        for user in users:
            if user['id'] == current_user['id']:
                user_to_update = user
                break
        
        if not user_to_update:
            return jsonify({"error": "User not found during update"}), 404
            
        user_to_update['email'] = data.get('email', user_to_update['email'])
        user_to_update['address'] = data.get('address', user_to_update['address'])
        
        save_users(users) 
        
        return jsonify({
            "id": user_to_update['id'],
            "username": user_to_update['username'],
            "email": user_to_update['email'],
            "address": user_to_update['address'],
            "favorite_locations": user_to_update.get('favorite_locations', [])
        })


if __name__ == '__main__':
    app.run(debug=True, port=5000)