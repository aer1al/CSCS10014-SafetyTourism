from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys

# --- IMPORT CORE LOGIC ---
import core_logic

# --- IMPORT DỮ LIỆU VỆ TINH ---
from weather import get_mock_weather_zones
from disasters import get_natural_disasters

app = Flask(__name__)
CORS(app) # Cho phép Frontend gọi API thoải mái

# 1. HEALTH CHECK
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "Safety Tourism API is running 🚀",
        "version": "Final Release"
    }), 200

# 2. API TÌM ĐƯỜNG (GỌI AI)
@app.route('/api/find-routes', methods=['POST'])
def find_routes_api():
    try:
        data = request.json
        start_coords = data.get('start')
        end_coords = data.get('end')
        
        # Validate dữ liệu đầu vào
        if not start_coords or not end_coords:
            return jsonify({"status": "error", "message": "Thiếu tọa độ start/end"}), 400
            
        print(f"📩 [API] Tìm đường: {start_coords} -> {end_coords}")

        # Gọi Core Logic (Hàm này đã tích hợp AI Risk + AI Traffic)
        result = core_logic.get_optimal_routes(start_coords, end_coords)
        
        return jsonify(result)

    except Exception as e:
        print(f"🔥 Lỗi Server (Find Route): {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

# 3. API LẤY DỮ LIỆU BẢN ĐỒ (ĐỂ VẼ VÒNG TRÒN ĐỎ/VÀNG)
@app.route('/api/map-data', methods=['GET'])
def get_map_layers():
    print("🌍 [API] Đang tải dữ liệu lớp bản đồ...")
    try:
        # A. Lấy Thiên Tai (Quét bán kính 50km quanh Chợ Bến Thành)
        disasters = get_natural_disasters(10.7721, 106.6983, max_distance_km=50) 
        
        # B. Lấy Thời Tiết (Mock Data)
        weather = get_mock_weather_zones()
        
        # C. Lấy Điểm Nóng (Crowd Data từ file JSON)
        crowd = []
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, 'crowd_zones.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    crowd = json.load(f)
        except Exception as e:
            print(f"⚠️ Lỗi đọc crowd_zones.json: {e}")

        print(f"✅ Trả về: {len(disasters)} thiên tai, {len(weather)} vùng mưa, {len(crowd)} điểm nóng.")

        return jsonify({
            "status": "success",
            "data": {
                "disasters": disasters,
                "weather": weather,
                "crowd": crowd
            }
        })

    except Exception as e:
        print(f"🔥 Lỗi Server (Map Data): {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Server đang khởi động...")
    print("👉 App chạy tại: http://localhost:5000")
    
    # debug=True giúp tự reload khi sửa code
    app.run(debug=True, port=5000, host='0.0.0.0')