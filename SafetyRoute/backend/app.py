from flask import Flask, request, jsonify
from flask_cors import CORS
from ollama import Client  # <--- THAY THẾ GEMINI
import json
import os
import sys
from dotenv import load_dotenv

# --- IMPORT MODULE VỆ TINH ---
import core_logic      # Xử lý tìm đường
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_engine'))
from rag_service import rag_engine
from chatbot import ChatBot, get_time_slot      # AI Chatbot

import weather         # Module thời tiết
import disasters       # Module thiên tai

# ==========================================
# CẤU HÌNH APP & OLLAMA
# ==========================================
load_dotenv()
app = Flask(__name__)
CORS(app)

# Cấu hình Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")

# Khởi tạo Client Ollama
try:
    ollama_client = Client(host=OLLAMA_HOST)
    print(f"🔌 App Server kết nối Ollama tại {OLLAMA_HOST} (Model Intent: {OLLAMA_MODEL})")
except Exception as e:
    print(f"❌ Lỗi khởi tạo Ollama Client: {e}")
    ollama_client = None

# Khởi tạo Chatbot
chatbot = ChatBot()

# ==========================================
# LOGIC PHÂN LOẠI Ý ĐỊNH (INTENT) - OLLAMA
# ==========================================
def detect_intent_with_ai(message: str) -> str:
    # Cấu hình Prompt chuyên dụng để phân loại
    prompt = f"""
    Nhiệm vụ: Phân loại câu của người dùng vào 1 trong 4 nhãn sau:

    1. GREETING: 
       - Chào hỏi xã giao (hi, hello, xin chào).
       - Hỏi bot là ai, chức năng của bot (help, giúp với).
    
    2. ROUTING: 
       - Hỏi về tình trạng giao thông, đường xá, kẹt xe.
       - Hỏi về địa điểm, thời tiết tại khu vực, tìm đường đi.
       - Ví dụ: "đường nguyễn tất thành ổn không", "đường A có kẹt xe không".

    3. MORE INFO: 
       - Hỏi chung chung: "chỗ nào ngập", "chỗ nào kẹt xe", "có tai nạn không".
       - Không có địa điểm cụ thể.

    4. UNKNOWN: 
       - Câu vô nghĩa, spam, teencode không dịch được.

    Câu hỏi của User: "{message}"

    YÊU CẦU TUYỆT ĐỐI: CHỈ TRẢ VỀ DUY NHẤT 1 TỪ LÀ NHÃN (VIẾT HOA). KHÔNG GIẢI THÍCH.
    """

    try:
        if not ollama_client:
            return "UNKNOWN"

        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0} # Nhiệt độ 0 để kết quả nhất quán
        )
        
        text = response['message']['content'].strip().upper()

        # Logic so sánh lỏng lẻo hơn (Ưu tiên theo thứ tự)
        if "ROUTING" in text:
            return "ROUTING"
        if "GREETING" in text:
            return "GREETING"
        
        # Xử lý trường hợp Model trả về "INFO" thay vì "MORE INFO"
        if "MORE INFO" in text or ("INFO" in text and "MORE" in text):
             return "MORE INFO"
             
        if "UNKNOWN" in text:
            return "UNKNOWN"

        return "UNKNOWN" # Fallback cuối cùng

    except Exception as e:
        print(f"⚠️ Intent Detection Error: {e}")
        return "UNKNOWN"
# ==========================================
# 1. HEALTH CHECK
# ==========================================
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "Safety Tourism API is running (Ollama Version) 🚀",
        "version": "3.0 (Ollama)"
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
# 3. API DỮ LIỆU BẢN ĐỒ
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
        disaster_data = [] 
        
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
        
        # 2. Fallback
        if not disaster_data and has_filter: 
             disaster_data = disasters.get_natural_disasters(min_lat, min_lng, 50)
             disaster_data = [
                d for d in disaster_data
                if min_lat <= d['lat'] <= max_lat and min_lng <= d['lng'] <= max_lng
             ]

        # B. THỜI TIẾT (Weather)
        weather_data = [] 
        if has_filter:
            bbox = (min_lat, min_lng, max_lat, max_lng)
            weather_data = weather.get_weather_zones(bbox)
        
        # C. ĐIỂM NÓNG (Crowd)
        crowd_data = [] 
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
                        crowd_data = []
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
        user_message = data.get("message", "")

        # 1️⃣ Detect intent (Dùng Ollama)
        intent = detect_intent_with_ai(user_message)
        print(f"🧠 Detected Intent: {intent}") # Debug log

        # 2️⃣ Lấy time slot
        time_slot = get_time_slot()

        # 3️⃣ DISPATCH THEO INTENT
        if intent == "GREETING":
            reply = chatbot.generate_general_chat(user_message)

        elif intent == "ROUTING":
            rag_data = rag_engine.search(user_message)
            reply = chatbot.generate_route_response(
                user_message,
                rag_data["combined_context"],
                time_slot
            )

        elif intent == "INFO" or intent == "MORE INFO":
            # Xử lý MORE INFO như ROUTING nhưng không có context cụ thể
            # Hoặc bạn có thể viết hàm riêng cho MORE INFO
            reply = chatbot.generate_general_chat(user_message)

        else:
            reply = "Mình chưa hiểu rõ câu hỏi. Bạn có thể hỏi cụ thể hơn về tuyến đường không?"

        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ Error in /api/chat:", e)
        return jsonify({"reply": "Hệ thống đang gặp lỗi."})

    
# ==========================================
# 5. API CÀI ĐẶT HỆ THỐNG
# ==========================================
@app.route('/api/toggle-demo', methods=['POST'])
def toggle_demo_mode():
    try:
        data = request.json
        is_demo = data.get('demo', False)
        
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
    print("\n🚀 SERVER READY (Ollama Enabled)...")
    app.run(debug=True, port=5000, host='0.0.0.0')
