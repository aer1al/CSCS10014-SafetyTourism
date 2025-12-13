from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys

# --- IMPORT MODULE VỆ TINH ---
import core_logic      # Xử lý tìm đường
import chatbot         # AI Chatbot
import weather         # Module thời tiết (đã có set_demo_mode)
import disasters       # Module thiên tai (đã có set_demo_mode)

app = Flask(__name__)
CORS(app)

# ==========================================
# 1. HEALTH CHECK
# ==========================================
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "Safety Tourism API is running 🚀",
        "version": "2.2 (Fixed Shadowing)"
    }), 200

# ==========================================
# 2. API TÌM ĐƯỜNG
# ==========================================
@app.route('/api/find-routes', methods=['POST'])
def find_routes_api():
    try:
        data = request.json
        start_coords = data.get('start')
        end_coords = data.get('end')
        vehicle_mode = data.get('mode', 'motorbike') 
        user_prefs = data.get('preferences', {}) 
        
        if not start_coords or not end_coords:
            return jsonify({"status": "error", "message": "Thiếu tọa độ start/end"}), 400
            
        print(f"📩 [API] Tìm đường ({vehicle_mode}): {start_coords} -> {end_coords}")

        result = core_logic.get_optimal_routes(
            start_coords, end_coords, 
            vehicle_mode=vehicle_mode, 
            preferences=user_prefs
        )
        return jsonify(result)

    except Exception as e:
        print(f"🔥 Lỗi Server (Find Route): {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 3. API DỮ LIỆU BẢN ĐỒ (Đã fix lỗi trùng tên)
# ==========================================
@app.route('/api/map-data', methods=['GET'])
def get_map_layers():
    print("🌍 [API] Đang tải dữ liệu lớp bản đồ...")
    
    # 1. Lấy Filter BBox
    try:
        min_lat = float(request.args.get('min_lat', -90))
        max_lat = float(request.args.get('max_lat', 90))
        min_lng = float(request.args.get('min_lng', -180))
        max_lng = float(request.args.get('max_lng', 180))
        has_filter = request.args.get('min_lat') is not None
    except:
        min_lat, max_lat, min_lng, max_lng = -90, 90, -180, 180
        has_filter = False

    try:
        # A. THIÊN TAI (Disasters)
        # ----------------------------------------
        disaster_data = [] # Đổi tên biến để không trùng với thư viện 'disasters'
        
        # 1. Ưu tiên đọc file thực
        if os.path.exists('real_disasters.json'):
            try:
                with open('real_disasters.json', 'r', encoding='utf-8') as f:
                    all_disasters = json.load(f)
                    disaster_data = [
                        d for d in all_disasters 
                        if min_lat <= d['lat'] <= max_lat and min_lng <= d['lng'] <= max_lng
                    ]
            except: pass
        
        # 2. Fallback: Nếu list rỗng và đang filter thì gọi hàm scan (Mock/NASA)
        if not disaster_data and has_filter: 
             # Gọi hàm từ module 'disasters'
             disaster_data = disasters.get_natural_disasters(min_lat, min_lng, 50)
             
             # Lọc lại lần nữa cho chắc (vì Mock 50km có thể trả về điểm ở xa)
             disaster_data = [
                d for d in disaster_data
                if min_lat <= d['lat'] <= max_lat and min_lng <= d['lng'] <= max_lng
             ]

        # B. THỜI TIẾT (Weather)
        # ----------------------------------------
        weather_data = [] # Đổi tên biến
        
        if has_filter:
            bbox = (min_lat, min_lng, max_lat, max_lng)
            # Gọi hàm từ module 'weather'
            weather_data = weather.get_weather_zones(bbox)
        
        # C. ĐIỂM NÓNG (Crowd)
        # ----------------------------------------
        crowd_data = [] # Đổi tên biến
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, 'crowd_zones.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_crowd = json.load(f)
                    if has_filter:
                        crowd_data = [
                            c for c in all_crowd 
                            if min_lat <= c['lat'] <= max_lat and min_lng <= c['lng'] <= max_lng
                        ]
                    else:
                        crowd_data = [] # Không filter -> Không trả về gì cả
        except: pass

        return jsonify({
            "status": "success",
            "bbox_used": has_filter,
            "data": {
                "disasters": disaster_data,
                "weather": weather_data,
                "crowd": crowd_data
            }
        })

    except Exception as e:
        print(f"🔥 Lỗi Server (Map Data): {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 4. API CHATBOT
# ==========================================
@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    try:
        data = request.json
        user_message = data.get('message')
        route_info = data.get('route_data')

        if not user_message: return jsonify({"reply": "..."})

        if route_info:
            ai_reply = chatbot.generate_safety_advice(user_message, route_info)
        else:
            ai_reply = chatbot.generate_general_chat(user_message)
        
        return jsonify({"reply": ai_reply})

    except Exception as e:
        return jsonify({"reply": "Xin lỗi, AI đang bảo trì."}), 500
    
# ==========================================
# 5. API CÀI ĐẶT HỆ THỐNG
# ==========================================
@app.route('/api/toggle-demo', methods=['POST'])
def toggle_demo_mode():
    try:
        data = request.json
        is_demo = data.get('demo', False)
        
        # Gọi module an toàn
        weather.set_demo_mode(is_demo)
        disasters.set_demo_mode(is_demo)
        
        mode_text = "DEMO (Mock Data)" if is_demo else "REALTIME (Live API)"
        return jsonify({
            "status": "success", 
            "message": f"Hệ thống đã chuyển sang: {mode_text}"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("\n🚀 SERVER READY...")
    app.run(debug=True, port=5000, host='0.0.0.0')