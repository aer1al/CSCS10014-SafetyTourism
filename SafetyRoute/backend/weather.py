# file: weather.py
import json
import os
import requests

def get_current_weather(lat, lon):
    """
    Lấy thời tiết hiện tại từ Open-Meteo (Miễn phí, không cần Key).
    
    Input: lat, lon (float)
    Output: Tuple (weather_main, wind_speed)
        - weather_main (str): "Rain", "Clear", "Clouds", "Thunderstorm"...
        - wind_speed (float): Tốc độ gió (m/s)
    """
    # Endpoint Open-Meteo
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Tham số cấu hình
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true", # Chỉ lấy hiện tại
        "windspeed_unit": "ms"     # Lấy đơn vị m/s (để khớp với standardization)
    }
    
    try:
        # Timeout 5s là đủ nhanh
        resp = requests.get(url, params=params, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if 'current_weather' in data:
                current = data['current_weather']
                
                # 1. Lấy mã WMO (số) và tốc độ gió
                wmo_code = current.get('weathercode', 0)
                wind_speed = current.get('windspeed', 0.0)
                
                # 2. Dịch mã số sang chữ (để standardization.py hiểu)
                weather_main = wmo_code_to_string(wmo_code)
                
                return weather_main, wind_speed

    except Exception as e:
        print(f"⚠️ Lỗi kết nối Open-Meteo: {e}")
        pass
    
    # Fallback an toàn nếu lỗi mạng: Trời quang, Gió 0
    return "Clear", 0.0

def wmo_code_to_string(code):
    """
    Hàm phụ: Chuyển đổi mã WMO (World Meteorological Organization) sang từ khóa.
    Mapping này được thiết kế để khớp với `standardization.py`.
    Nguồn mã: https://open-meteo.com/en/docs
    """
    # 0: Trời quang
    if code == 0: 
        return "Clear"
    
    # 1, 2, 3: Có mây (Ít -> Nhiều)
    if code in [1, 2, 3]: 
        return "Clouds"
    
    # 45, 48: Sương mù
    if code in [45, 48]: 
        return "Fog"
    
    # 51, 53, 55: Mưa phùn (Drizzle)
    # 56, 57: Mưa phùn lạnh giá
    if code in [51, 53, 55, 56, 57]: 
        return "Drizzle"
    
    # 61, 63, 65: Mưa vừa -> Mưa to
    # 66, 67: Mưa lạnh giá
    # 80, 81, 82: Mưa rào (Showers)
    if code in [61, 63, 65, 66, 67, 80, 81, 82]: 
        return "Rain"
    
    # 71, 73, 75, 77: Tuyết (Hiếm ở VN nhưng giữ để code chuẩn)
    # 85, 86: Tuyết rơi
    if code in [71, 73, 75, 77, 85, 86]: 
        return "Snow"
    
    # 95: Giông bão (Thunderstorm)
    # 96, 99: Giông bão kèm mưa đá (Nguy hiểm cao)
    if code in [95, 96, 99]: 
        return "Thunderstorm"
        
    # Mặc định an toàn
    return "Clear"

def get_mock_weather_zones():
    """
    Đọc dữ liệu các vùng thời tiết giả lập từ file JSON.
    Trả về: List các dict chứa thông tin vùng mưa/bão.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'mock_weather.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            zones = json.load(f)
            print(f"✅ Đã load {len(zones)} vùng thời tiết giả lập (Mock).")
            return zones
    except Exception as e:
        print(f"❌ Lỗi đọc mock_weather.json: {e}")
        return []