import requests
import json
import os
from utils import haversine # Import hàm chung

DEMO_MODE = True # <--- CÔNG TẮC DEMO

def get_natural_disasters(user_lat, user_lon, max_distance_km=500):
    # 1. Chọn nguồn dữ liệu
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
        # API NASA thật
        bbox = "102.14,8.18,109.46,23.39"
        url = f"https://eonet.gsfc.nasa.gov/api/v3/events?status=open&bbox={bbox}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200: raw_events = resp.json().get("events", [])
        except: return []

    # 2. Xử lý & Lọc
    formatted_list = []
    for event in raw_events:
        geo = event.get("geometry", [])
        if not geo: continue
        
        latest = geo[-1]
        coords = latest.get("coordinates")
        etype = latest.get("type")
        
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
                
                # [FIX] Thêm dòng này: Lấy radius từ Mock, nếu không có (API thật) thì gán 10km
                # Nếu là Polygon của NASA, có thể gán mặc định to hơn (ví dụ 20km)
                default_radius = 20.0 if etype == 'Polygon' else 10.0
                event_radius = event.get("radius", default_radius)

                formatted_list.append({
                    'lat': e_lat, 'lng': e_lon,
                    'name': event.get("title"),
                    'type': etype,
                    'radius': event_radius,  # <--- QUAN TRỌNG: Thêm cái này vào output
                    'categories_raw': [c.get("id") for c in cats] 
                })
    return formatted_list