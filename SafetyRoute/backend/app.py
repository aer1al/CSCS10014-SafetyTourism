from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
from dotenv import load_dotenv


# Import Class Chatbot "Nhạc trưởng" mới mà chúng ta vừa xây dựng
# Lưu ý: file này nằm ở rag_engine/chatbot.py
from rag_engine.chatbot import TrafficChatbot

# --- IMPORT MODULE VỆ TINH (GIỮ NGUYÊN CỦA BẠN) ---
# (Giả định bạn vẫn giữ các file này ở thư mục gốc để phục vụ bản đồ)
try:
    import core_logic      # Xử lý tìm đường
    import weather         # Module thời tiết
    import disasters       # Module thiên tai
except ImportError:
    print("⚠️ Cảnh báo: Không tìm thấy các module vệ tinh (core_logic, weather...). Chế độ API Map có thể lỗi.")

# ==========================================
# CẤU HÌNH APP
# ==========================================
load_dotenv()
app = Flask(__name__)
CORS(app)

# ==========================================
# KHỞI TẠO CHATBOT ENGINE
# ==========================================
print("⏳ Đang khởi động hệ thống Safety Tourism AI...")
try:
    # Khởi tạo instance của Chatbot mới
    # Nó sẽ tự động kết nối Neo4j và Ollama theo config bên trong rag_engine
    traffic_bot = TrafficChatbot()
    print("✅ Chatbot Engine đã sẵn sàng nhận lệnh!")
except Exception as e:
    print(f"❌ Lỗi khởi tạo Chatbot: {e}")
    traffic_bot = None

# ==========================================
# 1. HEALTH CHECK
# ==========================================
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "Safety Tourism API is running (Modular RAG Architecture) 🚀",
        "version": "4.0 (Integrated)"
    }), 200

# ==========================================
# 2. API CHATBOT (ĐÃ NÂNG CẤP)
# ==========================================
@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """
    Endpoint nhận tin nhắn từ Web/App -> Gửi vào RAG Engine -> Trả lời
    """
    try:
        if not traffic_bot:
            return jsonify({"reply": "Hệ thống AI đang khởi động hoặc gặp lỗi kết nối. Vui lòng thử lại sau."}), 503

        data = request.json
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"reply": "Bạn chưa nhập nội dung tin nhắn."})

        # --- GỌI VÀO RAG ENGINE MỚI ---
        # Engine sẽ tự động: Router -> Search Neo4j -> Generate Answer
        print(f"📩 User: {user_message}")
        reply = traffic_bot.chat(user_message)
        print(f"🤖 Bot: {reply}")

        return jsonify({"reply": reply})

    except Exception as e:
        print(f"❌ Error in /api/chat: {e}")
        return jsonify({"reply": "Xin lỗi, hệ thống đang gặp sự cố xử lý tin nhắn."}), 500


# ==========================================
# 3. API TÌM ĐƯỜNG (GIỮ NGUYÊN)
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
            
        print(f"📍 [API] Tìm đường ({vehicle_mode}): {start_coords} -> {end_coords}")

        if 'core_logic' in sys.modules:
            result = core_logic.get_optimal_routes(
                start_coords, end_coords, 
                vehicle_mode=vehicle_mode, 
                preferences=user_prefs
            )
            return jsonify(result)
        else:
             return jsonify({"status": "error", "message": "Module core_logic chưa được load"}), 500

    except Exception as e:
        print(f"🔥 Lỗi Server (Find Route): {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 4. API DỮ LIỆU BẢN ĐỒ (GIỮ NGUYÊN)
# ==========================================
@app.route('/api/map-data', methods=['GET'])
def get_map_layers():
    # Logic cũ của bạn để lấy dữ liệu vẽ lên bản đồ
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
        disaster_data = [] 
        if 'disasters' in sys.modules:
            # Fallback logic cũ của bạn
            if os.path.exists('real_disasters.json'):
                try:
                    with open('real_disasters.json', 'r', encoding='utf-8') as f:
                        all_disasters = json.load(f)
                        disaster_data = [d for d in all_disasters if min_lat <= d['lat'] <= max_lat]
                except: pass
            
            if not disaster_data and has_filter:
                disaster_data = disasters.get_natural_disasters(min_lat, min_lng, 50)

        # B. THỜI TIẾT
        weather_data = []
        if 'weather' in sys.modules and has_filter:
            weather_data = weather.get_weather_zones((min_lat, min_lng, max_lat, max_lng))

        return jsonify({
            "status": "success",
            "data": {
                "disasters": disaster_data,
                "weather": weather_data,
                "crowd": [] # Giữ placeholder
            }
        })

    except Exception as e:
        print(f"🔥 Lỗi Server (Map Data): {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 5. API SETTING (GIỮ NGUYÊN)
# ==========================================
@app.route('/api/toggle-demo', methods=['POST'])
def toggle_demo_mode():
    try:
        data = request.json
        is_demo = data.get('demo', False)
        
        if 'weather' in sys.modules: weather.set_demo_mode(is_demo)
        if 'disasters' in sys.modules: disasters.set_demo_mode(is_demo)
        
        return jsonify({"status": "success", "message": f"Chế độ Demo: {is_demo}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':
    # Khi tắt app thì đóng kết nối Neo4j/Chatbot
    try:
        print("\n🚀 SERVER READY (Port 5000)...")
        app.run(debug=True, port=5000, host='0.0.0.0')
    finally:
        if traffic_bot:
            traffic_bot.close()
            print("🛑 Đã đóng kết nối Chatbot.")
