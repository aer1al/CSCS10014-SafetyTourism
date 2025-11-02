from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from disasters import get_natural_disasters
from locations import get_nearby_places

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# API Keys (should be in .env file)
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
WORLDPOP_API_KEY = os.getenv('WORLDPOP_API_KEY')

# Mock data for development (replace with real API calls)
MOCK_DATA = {}

@app.route('/api/weather')
def get_weather():
    lat = request.args.get('lat', '35.6895')
    lon = request.args.get('lon', '139.6917')
    
    if OPENWEATHER_API_KEY:
        try:
            url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}'
            response = requests.get(url)
            data = response.json()
            
            # Transform the data for the frontend
            return jsonify([{
                'lat': float(lat),
                'lng': float(lon),
                'name': f'Weather Alert: {data["weather"][0]["main"]}',
                'description': data["weather"][0]["description"],
                'details': f'Temperature: {round(data["main"]["temp"] - 273.15, 1)}°C'
            }])
        except Exception as e:
            print(f"Error fetching weather data: {e}")
    
    # Return mock data if API key is not available or request fails
    return jsonify([{
        'lat': float(lat),
        'lng': float(lon),
        'name': 'Weather Alert',
        'description': 'Partly cloudy with chance of rain',
        'details': 'Temperature: 22°C'
    }])

@app.route('/api/disaster')
def get_disasters():
    # 1. Lấy lat/lon từ frontend
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if lat is None or lon is None:
        return jsonify({"error": "Thiếu tham số 'lat' hoặc 'lon'."}), 400

    # 2. Gọi hàm "hàng thật" của bạn từ file disasters.py
    # Dùng 200km cho thực tế
    real_disaster_data = get_natural_disasters(lat, lon, max_distance_km=200)

    # 3. Trả kết quả thật về
    return jsonify(real_disaster_data)

@app.route('/api/crowd')
def get_crowds():
    lat = request.args.get('lat', '35.6895')
    lon = request.args.get('lon', '139.6917')
    
    # In a real application, this would use the WorldPop API or similar
    return jsonify([{
        'lat': float(lat),
        'lng': float(lon),
        'name': 'Crowd Alert',
        'description': 'High crowd density detected',
        'details': 'Estimated 1000+ people in area'
    }])

# --- NÂNG CẤP /api/shelter ---
@app.route('/api/shelter')
def get_shelters():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify({"error": "Thiếu 'lat' hoặc 'lon'"}), 400
        
    # Gọi hàm "hàng thật" từ locations.py
    data = get_nearby_places(lat, lon, "shelter") 
    
    # Trả về JSON mà hàm của bạn đã tạo (có 'status', 'count', 'places')
    return jsonify(data)

# --- NÂNG CẤP /api/hospital ---
@app.route('/api/hospital')
def get_hospitals():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify({"error": "Thiếu 'lat' hoặc 'lon'"}), 400
        
    # Gọi hàm "hàng thật" từ locations.py
    data = get_nearby_places(lat, lon, "hospital")
    
    # Trả về JSON mà hàm của bạn đã tạo
    return jsonify(data)

@app.route('/api/emergency', methods=['POST'])
def handle_emergency():
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    
    # In a real application, this would:
    # 1. Log the emergency
    # 2. Notify emergency services
    # 3. Store in database
    
    print(f"Emergency alert received from location: {lat}, {lng}")
    return jsonify({'status': 'success', 'message': 'Emergency services notified'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)