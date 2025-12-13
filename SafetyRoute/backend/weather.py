# file: weather.py
import requests
import numpy as np # Cần cài numpy: pip install numpy
import os
import json

def get_current_weather(lat, lon):
    """
    Hàm gọi API Open-Meteo lấy thời tiết tại 1 điểm tọa độ.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "windspeed_unit": "ms"
    }
    try:
        resp = requests.get(url, params=params, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            if 'current_weather' in data:
                current = data['current_weather']
                wmo_code = current.get('weathercode', 0)
                wind_speed = current.get('windspeed', 0.0)
                weather_main = wmo_code_to_string(wmo_code)
                return weather_main, wind_speed
    except:
        return "Clear", 0.0
    return "Clear", 0.0

def wmo_code_to_string(code):
    # Mapping mã WMO sang từ khóa
    if code == 0: return "Clear"
    if code in [1, 2, 3]: return "Clouds"
    if code in [45, 48]: return "Fog"
    if code in [51, 53, 55, 56, 57]: return "Drizzle"
    if code in [61, 63, 65, 66, 67, 80, 81, 82]: return "Rain"
    if code in [95, 96, 99]: return "Thunderstorm"
    return "Clear"

def get_realtime_weather_zones(bbox):
    """
    🔥 ĐÂY LÀ HÀM BẠN CẦN: QUÉT LƯỚI TRONG BBOX 🔥
    Input: bbox (south, west, north, east) từ Core Logic.
    Output: Danh sách các vùng mưa (để tính toán và hiển thị).
    """
    south, west, north, east = bbox
    zones = []

    # 1. Chia BBox thành lưới (Grid)
    # Ví dụ: Chia làm 3 điểm chiều dọc, 3 điểm chiều ngang -> Tổng 9 điểm quét
    # Nếu BBox quá nhỏ (đi ngắn), linspace vẫn chia đúng điểm đầu/cuối/giữa.
    lat_steps = np.linspace(south, north, 3)
    lon_steps = np.linspace(west, east, 3)

    # print(f"📡 Đang quét {len(lat_steps)*len(lon_steps)} điểm trong vùng tìm đường...")

    # 2. Duyệt qua từng điểm trong lưới
    for lat in lat_steps:
        for lon in lon_steps:
            # Gọi API thật
            cond, wind = get_current_weather(lat, lon)
            
            # 3. Logic lọc: Chỉ lấy điểm nào có Mưa hoặc Gió to
            is_bad = False
            radius = 2.0 # Bán kính ảnh hưởng mặc định (km)

            if cond in ["Rain", "Thunderstorm", "Drizzle", "Fog"]:
                is_bad = True
                if cond == "Thunderstorm": radius = 4.0 # Bão thì vùng to hơn
            
            if wind >= 10.0: # Gió cấp 5 trở lên
                is_bad = True

            # 4. Nếu xấu -> Thêm vào list
            if is_bad:
                zones.append({
                    "lat": lat,
                    "lng": lon,
                    "radius": radius,
                    "condition": cond,
                    "wind_speed": wind,
                    "description": f"Realtime: {cond}, Gió: {wind}m/s"
                })

    return zones

# Giữ lại hàm Mock cũ để fallback nếu cần, hoặc xóa đi cũng được
def get_mock_weather_zones():
    return []