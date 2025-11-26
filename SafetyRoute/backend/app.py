# file: app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import core_logic
import sys

app = Flask(__name__)
CORS(app) # Cho phép mọi domain gọi vào

@app.route('/api/find-routes', methods=['POST'])
def find_routes_api():
    try:
        data = request.json
        # 1. Validation kỹ hơn
        if not data or 'start' not in data or 'end' not in data:
            return jsonify({
                "status": "error", 
                "message": "Thiếu dữ liệu 'start' hoặc 'end'. Format: [lat, lng]"
            }), 400

        start_coords = data['start']
        end_coords = data['end']
        
        # Validate kiểu dữ liệu (tránh frontend gửi string)
        if not (isinstance(start_coords, list) and len(start_coords) == 2):
             return jsonify({"status": "error", "message": "Start coords phải là list [lat, lng]"}), 400

        print(f"📩 Request: {start_coords} -> {end_coords}")

        # 2. Gọi Core Logic
        result = core_logic.get_optimal_routes(start_coords, end_coords)
        
        # 3. Trả về status code phù hợp
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            # Tìm đường thất bại thì trả về 404 hoặc 422
            return jsonify(result), 422

    except Exception as e:
        # In lỗi ra terminal server để debug
        print(f"🔥 UNEXPECTED ERROR: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": "Lỗi Server nội bộ"}), 500

if __name__ == '__main__':
    # Tắt debug=True khi deploy thật, nhưng dev thì để True OK
    # Host='0.0.0.0' để cho phép các máy khác trong mạng LAN (hoặc mobile thật) gọi vào được
    app.run(debug=True, port=5000, host='0.0.0.0')