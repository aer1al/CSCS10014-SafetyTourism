import requests

# URL API Open-Meteo (Free, No Key)
BASE_URL = "https://api.open-meteo.com/v1/forecast"

def get_current_weather(lat, lng):
    """
    Lấy dữ liệu thời tiết thời gian thực tại MỘT điểm tọa độ (lat, lng).
    Trả về dữ liệu thô (Raw Data) để các module khác tự xử lý.
    """
    try:
        params = {
            "latitude": lat,
            "longitude": lng,
            "current_weather": "true",
            "windspeed_unit": "kmh"
        }
        
        # Timeout 2s để tránh treo nếu mạng lag
        response = requests.get(BASE_URL, params=params, timeout=2)
        
        if response.status_code == 200:
            data = response.json().get('current_weather', {})
            
            # Trả về Dictionary thô
            return {
                "status": "success",
                "lat": lat,
                "lng": lng,
                "wcode": data.get('weathercode', 0), # Mã thời tiết (WMO)
                "temp": data.get('temperature', 0),  # Nhiệt độ
                "wind": data.get('windspeed', 0),    # Tốc độ gió
                "time": data.get('time', '')         # Thời gian cập nhật
            }
        else:
            print(f"⚠️ API Error {response.status_code} tại [{lat}, {lng}]")
            return None

    except Exception as e:
        print(f"❌ Lỗi kết nối Weather API: {e}")
        return None

# Hàm Mock (để test khi mất mạng)
def get_mock_weather_at_point(lat, lng):
    return {
        "status": "mock",
        "lat": lat, "lng": lng,
        "wcode": 95, # Giả lập bão
        "temp": 28,
        "wind": 25.0
    }

# Test nhanh
if __name__ == "__main__":
    # Test thử tại Chợ Bến Thành
    w = get_current_weather(10.7721, 106.6983)
    print("Dữ liệu thời tiết:", w)