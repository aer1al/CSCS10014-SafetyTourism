from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv

# Import các hàm đã được chuẩn hóa
from disasters import get_natural_disasters
from locations import get_nearby_places

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# -------------------------------------------------------------------
# /api/weather (Vẫn cần dọn dẹp tại đây)
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
            
            # Trả về MẢNG
            return jsonify([{
                'lat': float(lat),
                'lng': float(lon), # Đổi 'lon' thành 'lng'
                'name': f'Weather: {data["weather"][0]["main"]}',
                'description': data["weather"][0]["description"],
                'details': f'Temperature: {round(data["main"]["temp"] - 273.15, 1)}°C'
            }])
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return jsonify([])
    
    return jsonify([{
        'lat': float(lat),
        'lng': float(lon), # Đổi 'lon' thành 'lng'
        'name': 'Weather Alert (Mock)',
        'description': 'Partly cloudy',
        'details': 'Temperature: 22°C'
    }])

# -------------------------------------------------------------------
# /api/disaster (Đã sạch)
# -------------------------------------------------------------------
@app.route('/api/disaster')
def get_disasters():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if lat is None or lon is None:
        return jsonify([]) # Trả về mảng rỗng nếu thiếu

    # Chỉ cần gọi và trả về, vì hàm con đã dọn dẹp rồi
    data = get_natural_disasters(lat, lon, max_distance_km=200)
    return jsonify(data)

# -------------------------------------------------------------------
# /api/crowd (Vẫn cần dọn dẹp tại đây)
# -------------------------------------------------------------------
@app.route('/api/crowd')
def get_crowds():
    lat = request.args.get('lat', '35.6895')
    lon = request.args.get('lon', '139.6917')
    
    # Trả về MẢNG
    return jsonify([{
        'lat': float(lat),
        'lng': float(lon), # Đổi 'lon' thành 'lng'
        'name': 'Crowd Alert (Mock)',
        'description': 'High crowd density detected',
        'details': 'Estimated 1000+ people in area'
    }])

# -------------------------------------------------------------------
# /api/shelter (Đã sạch)
# -------------------------------------------------------------------
@app.route('/api/shelter')
def get_shelters():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify([])
        
    # Chỉ cần gọi và trả về
    data = get_nearby_places(lat, lon, "shelter") 
    return jsonify(data)

# -------------------------------------------------------------------
# /api/hospital (Đã sạch)
# -------------------------------------------------------------------
@app.route('/api/hospital')
def get_hospitals():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify([])
        
    # Chỉ cần gọi và trả về
    data = get_nearby_places(lat, lon, "hospital")
    return jsonify(data)

# -------------------------------------------------------------------
# API Khẩn cấp (Giữ nguyên)
# -------------------------------------------------------------------
@app.route('/api/emergency', methods=['POST'])
def handle_emergency():
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng') 
    
    print(f"Emergency alert received from location: {lat}, {lng}")
    return jsonify({'status': 'success', 'message': 'Emergency services notified'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)