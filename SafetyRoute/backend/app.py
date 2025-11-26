from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys

# Import core logic
import core_logic

# ⚠️ QUAN TRỌNG: Import các hàm lấy dữ liệu vệ tinh
# (Lỗi 500 thường do thiếu 2 dòng này)
from weather import get_mock_weather_zones
from disasters import get_natural_disasters

app = Flask(__name__)
CORS(app) 

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Safety Tourism API is running 🚀"}), 200

@app.route('/api/find-routes', methods=['POST'])
def find_routes_api():
    try:
        data = request.json
        start_coords = data.get('start')
        end_coords = data.get('end')
        
        if not start_coords or not end_coords:
            return jsonify({"status": "error", "message": "Missing start or end coordinates"}), 400

        print(f"📩 Nhận request tìm đường: {start_coords} -> {end_coords}")

        # Gọi hàm Core Logic
        result = core_logic.get_optimal_routes(start_coords, end_coords)
        
        return jsonify(result)

    except Exception as e:
        print(f"🔥 Server Error (Find Route): {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

# --- API MỚI: LẤY DỮ LIỆU BẢN ĐỒ ---
@app.route('/api/map-data', methods=['GET'])
def get_map_layers():
    print("🌍 Đang xử lý request /api/map-data...")
    try:
        # 1. Lấy dữ liệu Thiên tai (Quét bán kính 50km quanh trung tâm Q1)
        disasters = get_natural_disasters(10.7769, 106.7009, max_distance_km=50) 
        
        # 2. Lấy dữ liệu Thời tiết (Mock)
        weather = get_mock_weather_zones()
        
        # 3. Lấy dữ liệu Đám đông (Đọc từ file json)
        crowd = []
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, 'crowd_zones.json')
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    crowd = json.load(f)
            else:
                print("⚠️ Không tìm thấy file crowd_zones.json, trả về rỗng.")
        except Exception as e:
            print(f"⚠️ Lỗi đọc crowd_zones.json: {e}")
            pass 

        # Log kiểm tra xem có dữ liệu không
        print(f"✅ Kết quả: {len(disasters)} thiên tai, {len(weather)} vùng thời tiết, {len(crowd)} điểm nóng.")

        return jsonify({
            "status": "success",
            "data": {
                "disasters": disasters,
                "weather": weather,
                "crowd": crowd
            }
        })

    except Exception as e:
        # In lỗi chi tiết ra Terminal Python để debug
        import traceback
        traceback.print_exc()
        print(f"🔥 CRITICAL ERROR (/api/map-data): {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("🌍 Server đang chạy tại http://localhost:5000")
    # host='0.0.0.0' để cho phép truy cập từ thiết bị khác
    app.run(debug=True, port=5000, host='0.0.0.0')
