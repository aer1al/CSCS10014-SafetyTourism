import requests
import json
import os
from utils import haversine # Import module tiện ích tính toán khoảng cách địa lý

DEMO_MODE = False # Cờ cấu hình chế độ chạy: True (Simulation), False (Realtime API)

def get_natural_disasters(user_lat, user_lon, max_distance_km=500):
    # Lựa chọn nguồn dữ liệu đầu vào (Data Ingestion Strategy)
    raw_events = []
    if DEMO_MODE:
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, 'mock_disasters.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_events = json.load(f)
        except Exception as e:
            print(f"Lỗi đọc Mock: {e}")
            return []
    else:
        # Truy vấn dữ liệu thời gian thực từ NASA EONET API (Filter BBox Vietnam)
        bbox = "102.14,8.18,109.46,23.39"
        url = f"https://eonet.gsfc.nasa.gov/api/v3/events?status=open&bbox={bbox}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200: raw_events = resp.json().get("events", [])
        except: return []

    # Xử lý chuẩn hóa dữ liệu và lọc không gian (Spatial Filtering)
    formatted_list = []
    for event in raw_events:
        geo = event.get("geometry", [])
        if not geo: continue
        
        latest = geo[-1]
        coords = latest.get("coordinates")
        etype = latest.get("type")
        
        # Phân tích cấu trúc hình học (Geometry Parsing) để lấy tọa độ tâm
        e_lat, e_lon = None, None
        if etype == "Point":
            e_lon, e_lat = coords
        elif etype == "Polygon":
            if coords and coords[0] and coords[0][0]:
                e_lon, e_lat = coords[0][0]

        if e_lat and e_lon:
            dist = haversine(user_lat, user_lon, e_lat, e_lon)
            if dist <= max_distance_km:
                cats = event.get("categories", [])
                
                # Xác định bán kính ảnh hưởng (Radius Estimation)
                # Fallback giá trị mặc định theo loại hình học nếu API thiếu dữ liệu
                default_radius = 20.0 if etype == 'Polygon' else 10.0
                event_radius = event.get("radius", default_radius)

                formatted_list.append({
                    'lat': e_lat, 'lng': e_lon,
                    'name': event.get("title"),
                    'type': etype,
                    'radius': event_radius,  # Metadata quan trọng cho visualization trên bản đồ
                    'categories_raw': [c.get("id") for c in cats] 
                })
    return formatted_list

# Phương thức Setter cập nhật trạng thái Runtime (Dependency Injection Pattern)
def set_demo_mode(status: bool):
    global DEMO_MODE
    DEMO_MODE = status

    print(f"🌋 [DISASTER] Đã chuyển DEMO_MODE thành: {DEMO_MODE}")
