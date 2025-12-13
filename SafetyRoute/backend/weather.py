import requests
import numpy as np 
import os
import json
import random

DEMO_MODE = True  # <--- CÔNG TẮC: True = Đọc file json, False = Quét API thật

def get_weather_zones(bbox):
    """
    Hàm duy nhất lấy dữ liệu thời tiết (Mưa/Gió).
    Tự động switch giữa Mock File và API Realtime.
    """
    south, west, north, east = bbox
    zones = []

    # --- [MỚI] TÍNH BÁN KÍNH ĐỘNG THEO HỘP ---
    # 1. Tính kích thước hộp (lấy cạnh lớn nhất) theo độ
    box_span_deg = max(north - south, east - west)
    
    # 2. Đổi ra km (1 độ vĩ ~ 111km)
    box_span_km = box_span_deg * 111.0
    
    # 3. Công thức: Radius = 1/4 kích thước hộp
    # (Để các vòng tròn nằm rải rác đẹp mắt, không đè chồng lên nhau quá nhiều)
    # Kẹp giá trị: Tối thiểu 0.3km (để còn nhìn thấy), Tối đa 5.0km
    raw_radius = box_span_km / 15.0
    base_radius = max(0.1, min(3.0, raw_radius))

    # --- CASE 1: CHẠY DEMO (Đọc từ file mock_weather.json) ---
    if DEMO_MODE:
        # Logic: Vẫn chia lưới như thật, nhưng fake dữ liệu
        lat_steps = np.linspace(south, north, 4) # Chia lưới 4x4
        lon_steps = np.linspace(west, east, 4)
        
        for lat in lat_steps:
            for lon in lon_steps:
                # Random 30% là có mưa
                if random.random() < 0.3: 
                    zones.append({
                        "lat": lat, "lng": lon, 
                        "radius": base_radius,
                        "condition": "Rain",
                        "wind_speed": 5.0,
                        "description": "Mock Grid Rain"
                    })

    # --- CASE 2: CHẠY REAL (Quét lưới Open-Meteo) ---
    else:
        # 1. Tạo lưới quét
        lat_steps = np.linspace(south, north, 3)
        lon_steps = np.linspace(west, east, 3)

        for lat in lat_steps:
            for lon in lon_steps:
                # Gọi hàm helper bên dưới
                cond, wind = _fetch_open_meteo(lat, lon)
                
                # Logic lọc xấu
                is_bad = False
                radius = base_radius
                if cond in ["Rain", "Thunderstorm", "Drizzle", "Fog"]:
                    is_bad = True
                    if cond == "Thunderstorm": radius = 4.0
                if wind >= 10.0: is_bad = True

                if is_bad:
                    zones.append({
                        "lat": lat, "lng": lon, "radius": round(radius,2),
                        "condition": cond, "wind_speed": wind,
                        "description": f"Realtime: {cond}, Gió: {wind}m/s"
                    })
    
    return zones

# --- HÀM HỖ TRỢ (PRIVATE) ---
def _fetch_open_meteo(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": lat, "longitude": lon, "current_weather": "true", "windspeed_unit": "ms"}
        resp = requests.get(url, params=params, timeout=3)
        if resp.status_code == 200:
            curr = resp.json().get('current_weather', {})
            return _wmo_to_str(curr.get('weathercode', 0)), curr.get('windspeed', 0.0)
    except: pass
    return "Clear", 0.0

def _wmo_to_str(code):
    if code in [51, 53, 55, 56, 57]: return "Drizzle"
    if code in [61, 63, 65, 66, 67, 80, 81, 82]: return "Rain"
    if code in [95, 96, 99]: return "Thunderstorm"
    if code in [45, 48]: return "Fog"
    return "Clear" # Bao gồm cả Clouds (An toàn)

# --- HÀM SETTER ĐỂ APP GỌI ---
def set_demo_mode(status: bool):
    global DEMO_MODE
    DEMO_MODE = status
    print(f"🔄 [SYSTEM] Đã chuyển DEMO_MODE thành: {DEMO_MODE}")