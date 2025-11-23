import requests

# THAY KEY CỦA BẠN VÀO ĐÂY
API_KEY = "801ff2014ac5c7a869731ba98b240c51" 

def get_current_weather(lat, lon):
    """Trả về (weather_main, wind_speed) hoặc (None, None) nếu lỗi"""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            main = data['weather'][0]['main']
            wind = data['wind']['speed']
            return main, wind
    except:
        pass
    return "Clear", 0.0 # Mặc định an toàn nếu lỗi