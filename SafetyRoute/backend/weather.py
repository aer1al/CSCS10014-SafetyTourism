import requests
import numpy as np 
import os
import json
import random

DEMO_MODE = False  # Cờ cấu hình nguồn dữ liệu: True (Simulation), False (Live API)

def get_weather_zones(bbox):
    """
    Truy xuất dữ liệu thời tiết theo vùng hiển thị (Viewport-based Data Fetching).
    Hỗ trợ chuyển đổi linh hoạt giữa dữ liệu giả lập và API thực tế.
    """
    south, west, north, east = bbox
    zones = []

    # Tính toán bán kính hiển thị động (Dynamic Radius Calculation) dựa trên mức độ zoom
    # 1. Xác định kích thước bao phủ lớn nhất theo độ
    box_span_deg = max(north - south, east - west)
    
    # 2. Chuyển đổi sang đơn vị km (Xấp xỉ: 1 độ vĩ ~ 111km)
    box_span_km = box_span_deg * 111.0
    
    # 3. Heuristic: Thiết lập bán kính bằng 1/15 kích thước vùng để tối ưu mật độ hiển thị
    # Áp dụng kẹp giá trị (Clamping) trong khoảng [0.1km, 3.0km]
    raw_radius = box_span_km / 15.0
    base_radius = max(0.1, min(3.0, raw_radius))

    # Chế độ Mô phỏng (Simulation Mode)
    if DEMO_MODE:
        # Khởi tạo lưới tọa độ lấy mẫu 4x4 (Grid Sampling)
        lat_steps = np.linspace(south, north, 4) 
        lon_steps = np.linspace(west, east, 4)
        
        for lat in lat_steps:
            for lon in lon_steps:
                # Giả lập xác suất xuất hiện thời tiết xấu (30%)
                if random.random() < 0.3: 
                    zones.append({
                        "lat": lat, "lng": lon, 
                        "radius": base_radius,
                        "condition": "Rain",
                        "wind_speed": 5.0,
                        "description": "Mock Grid Rain"
                    })

    # Chế độ Thực tế (Realtime Mode) - Tích hợp Open-Meteo API
    else:
        # Tạo lưới quét thưa hơn (3x3) để giảm tải Request API
        lat_steps = np.linspace(south, north, 3)
        lon_steps = np.linspace(west, east, 3)

        for lat in lat_steps:
            for lon in lon_steps:
                # Gọi hàm helper để lấy dữ liệu thô
                cond, wind = _fetch_open_meteo(lat, lon)
                
                # Bộ lọc điều kiện bất lợi (Adverse Weather Filter)
                is_bad = False
                radius = base_radius
                if cond in ["Rain", "Thunderstorm", "Drizzle", "Fog"]:
                    is_bad = True
                    if cond == "Thunderstorm": radius = 4.0 # Tăng bán kính cảnh báo nếu có bão
                if wind >= 10.0: is_bad = True

                if is_bad:
                    zones.append({
                        "lat": lat, "lng": lon, "radius": round(radius,2),
                        "condition": cond, "wind_speed": wind,
                        "description": f"Realtime: {cond}, Gió: {wind}m/s"
                    })
    
    return zones

# Các hàm tiện ích (Utility Functions)
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
    # Chuẩn hóa mã WMO (World Meteorological Organization) sang nhãn định danh
    if code in [51, 53, 55, 56, 57]: return "Drizzle"
    if code in [61, 63, 65, 66, 67, 80, 81, 82]: return "Rain"
    if code in [95, 96, 99]: return "Thunderstorm"
    if code in [45, 48]: return "Fog"
    return "Clear" 

# Phương thức Setter cập nhật cấu hình Runtime
def set_demo_mode(status: bool):
    global DEMO_MODE
    DEMO_MODE = status

    print(f"🔄 [SYSTEM] Đã chuyển DEMO_MODE thành: {DEMO_MODE}")
