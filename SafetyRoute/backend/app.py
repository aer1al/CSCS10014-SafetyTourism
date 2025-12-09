from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys

# --- IMPORT CÁC MODULE VỆ TINH ---
import core_logic      # Bộ não tìm đường
import chatbot         # Trợ lý ảo AI
from disasters import get_natural_disasters # Hàm fallback
from weather import get_mock_weather_zones  # Hàm fallback

app = Flask(__name__)
CORS(app) # Cho phép Frontend gọi API thoải mái

# ==========================================
# 1. HEALTH CHECK (Kiểm tra Server sống/chết)
# ==========================================
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "Safety Tourism API is running 🚀",
        "version": "2.0 (Full AI Integration)"
    }), 200

# ==========================================
# 2. API TÌM ĐƯỜNG (CORE FEATURE)
# ==========================================
@app.route('/api/find-routes', methods=['POST'])
def find_routes_api():
    try:
        data = request.json
        start_coords = data.get('start')
        end_coords = data.get('end')
        
        # Nhận thêm tham số nâng cao (Optional)
        # Mặc định là 'motorbike' nếu Frontend không gửi
        vehicle_mode = data.get('mode', 'motorbike') 
        
        # Mặc định preferences là {} (Core sẽ tự hiểu là 1.0)
        user_prefs = data.get('preferences', {}) 
        
        # Validation
        if not start_coords or not end_coords:
            return jsonify({"status": "error", "message": "Thiếu tọa độ start/end"}), 400
            
        print(f"📩 [API] Tìm đường ({vehicle_mode}): {start_coords} -> {end_coords}")
        print(f"   ⚙️ Prefs: {user_prefs}")

        # GỌI CORE LOGIC
        # Hàm này đã được bọc (wrap) trong core_logic.py để gọi qua Class
        result = core_logic.get_optimal_routes(
            start_coords, 
            end_coords, 
            vehicle_mode=vehicle_mode, 
            preferences=user_prefs
        )
        
        return jsonify(result)

    except Exception as e:
        print(f"🔥 Lỗi Server (Find Route): {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 3. API DỮ LIỆU BẢN ĐỒ (VISUALIZATION)
# ==========================================
@app.route('/api/map-data', methods=['GET'])
def get_map_layers():
    """
    Trả về dữ liệu để Frontend vẽ các vòng tròn Đỏ/Vàng/Cam.
    Ưu tiên dữ liệu thật (Real-time), fallback về Mock.
    """
    print("🌍 [API] Đang tải dữ liệu lớp bản đồ...")
    try:
        # A. THIÊN TAI (Disasters)
        disasters = []
        if os.path.exists('real_disasters.json'):
            try:
                with open('real_disasters.json', 'r', encoding='utf-8') as f:
                    disasters = json.load(f)
                print(f"   -> Đã load {len(disasters)} thiên tai thực tế.")
            except: pass
            
        if not disasters:
            # Fallback nếu không có file thật
            disasters = get_natural_disasters(10.77, 106.69, 50)

        # B. THỜI TIẾT (Weather)
        # Frontend sẽ dùng Radar (RainViewer), còn đây là dữ liệu điểm (nếu có)
        weather = get_mock_weather_zones()
        
        # C. ĐIỂM NÓNG (Crowd)
        crowd = []
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, 'crowd_zones.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    crowd = json.load(f)
        except: pass

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

# ==========================================
# 4. API CHATBOT (AI ASSISTANT)
# ==========================================
@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    try:
        data = request.json
        user_message = data.get('message')
        route_info = data.get('route_data') # Dữ liệu lộ trình frontend gửi lên

        if not user_message:
            return jsonify({"reply": "Bạn cần hỏi gì đó..."})

        # Gọi Chatbot Module
        if route_info:
            # Nếu đã có lộ trình -> Tư vấn dựa trên lộ trình (Context-aware)
            ai_reply = chatbot.generate_safety_advice(user_message, route_info)
        else:
            # Nếu chưa có -> Chat xã giao / Hướng dẫn
            ai_reply = chatbot.generate_general_chat(user_message)
        
        return jsonify({"reply": ai_reply})

    except Exception as e:
        print(f"🔥 Lỗi Chatbot: {e}", file=sys.stderr)
        return jsonify({"reply": "Xin lỗi, não bộ AI đang gặp sự cố kết nối."}), 500

# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == '__main__':
    print("\n🚀 SERVER ĐANG KHỞI ĐỘNG...")
    print("👉 API Route: http://localhost:5000/api/find-routes")
    print("👉 API Map:   http://localhost:5000/api/map-data")
    print("👉 API Chat:  http://localhost:5000/api/chat")
    print("-" * 50)
    
    # debug=True để tự reload khi sửa code, host='0.0.0.0' để truy cập từ mobile/LAN
    app.run(debug=True, port=5000, host='0.0.0.0')