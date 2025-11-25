from flask import Flask, request, jsonify
from flask_cors import CORS
import core_logic

app = Flask(__name__)
# Cho phép Frontend (React/Vue/Mobile) gọi API
CORS(app) 

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Safety Tourism API is running 🚀"}), 200

@app.route('/api/find-routes', methods=['POST'])
def find_routes_api():
    """
    API nhận tọa độ Start/End và trả về đường đi + cảnh báo.
    JSON Body:
    {
        "start": [10.7715, 106.7044],
        "end": [10.7826, 106.6959]
    }
    """
    try:
        data = request.json
        start_coords = data.get('start')
        end_coords = data.get('end')
        
        if not start_coords or not end_coords:
            return jsonify({"status": "error", "message": "Missing start or end coordinates"}), 400

        print(f"📩 Nhận request: {start_coords} -> {end_coords}")

        # Gọi hàm Core Logic (Đã tối ưu)
        result = core_logic.get_optimal_routes(start_coords, end_coords)
        
        return jsonify(result)

    except Exception as e:
        print(f"🔥 Server Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Chạy server ở port 5000
    print("🌍 Server đang chạy tại http://localhost:5000")
    app.run(debug=True, port=5000)