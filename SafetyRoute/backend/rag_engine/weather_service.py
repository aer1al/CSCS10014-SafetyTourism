# rag_engine/weather_service.py
import requests
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env (nếu có)
load_dotenv()

class WeatherService:
    def __init__(self):
        # Lấy API Key từ biến môi trường. 
        # Nếu bạn test nhanh có thể paste cứng key vào đây (không khuyến khích khi deploy)
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE") 
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_current_weather(self, location_name="TP.HCM"):
        """
        Gọi API OpenWeatherMap để lấy dữ liệu thật.
        """
        # Xử lý tên địa điểm để API hiểu chính xác hơn
        # Ví dụ: "Quận 1" -> "District 1, Ho Chi Minh City, VN"
        search_query = self._format_location_name(location_name)
        
        params = {
            "q": search_query,
            "appid": self.api_key,
            "units": "metric", # Để lấy độ C
            "lang": "vi"       # Để lấy mô tả tiếng Việt
        }

        try:
            print(f"☁️ Đang gọi Weather API cho: {search_query}...")
            response = requests.get(self.base_url, params=params, timeout=5)
            data = response.json()

            if response.status_code == 200:
                # Trích xuất dữ liệu quan trọng
                weather_desc = data['weather'][0]['description'] # VD: "mưa nhẹ"
                main_condition = data['weather'][0]['main']      # VD: "Rain"
                temp = int(data['main']['temp'])
                humidity = data['main']['humidity']
                
                # Logic phân tích rủi ro ngập dựa trên dữ liệu thật
                flood_warning = self._analyze_flood_risk(main_condition, weather_desc)

                return {
                    "condition": weather_desc.capitalize(),
                    "temperature": f"{temp}°C",
                    "humidity": f"{humidity}%",
                    "flood_warning": flood_warning,
                    "is_raining": "Rain" in main_condition or "Thunderstorm" in main_condition
                }
            else:
                print(f"⚠️ Weather API Error: {data.get('message')}")
                return self._get_fallback_data() # Nếu lỗi API thì trả về data mặc định an toàn

        except Exception as e:
            print(f"❌ Lỗi kết nối Weather Service: {e}")
            return self._get_fallback_data()

    def _format_location_name(self, name):
        """Chuẩn hóa tên quận huyện cho OpenWeatherMap"""
        name_lower = name.lower()
        
        # Nếu input quá ngắn hoặc chung chung, mặc định là TP.HCM
        if len(name) < 3 or "hcm" in name_lower or "thành phố" in name_lower:
            return "Ho Chi Minh City, VN"
            
        # Mapping các tên tiếng Việt sang tiếng Anh để API dễ tìm hơn
        # OpenWeather tìm "Quan 1" đôi khi không chuẩn bằng "District 1"
        mapping = {
            "quận 1": "District 1", "quận 2": "District 2", "quận 3": "District 3",
            "quận 4": "District 4", "quận 5": "District 5", "quận 6": "District 6",
            "quận 7": "District 7", "quận 8": "District 8", "quận 9": "District 9",
            "quận 10": "District 10", "quận 11": "District 11", "quận 12": "District 12",
            "bình thạnh": "Binh Thanh", "phú nhuận": "Phu Nhuan", "gò vấp": "Go Vap",
            "tân bình": "Tan Binh", "tân phú": "Tan Phu", "bình tân": "Binh Tan",
            "thủ đức": "Thu Duc", "bình chánh": "Binh Chanh", "củ chi": "Cu Chi",
            "hóc môn": "Hoc Mon", "nhà bè": "Nha Be", "cần giờ": "Can Gio"
        }
        
        for key, val in mapping.items():
            if key in name_lower:
                return f"{val}, Ho Chi Minh City, VN"
        
        # Fallback: Cứ gửi nguyên văn kèm hậu tố VN
        return f"{name}, Ho Chi Minh City, VN"

    def _analyze_flood_risk(self, main_condition, desc):
        """Phân tích rủi ro ngập dựa trên tình trạng mưa"""
        if main_condition == "Thunderstorm":
            return "CAO (Mưa dông lớn)"
        elif main_condition == "Rain":
            if "heavy" in desc or "lớn" in desc:
                return "CAO (Mưa to)"
            return "TRUNG BÌNH (Đang mưa)"
        elif main_condition == "Drizzle":
            return "THẤP (Mưa phùn)"
        else:
            return "KHÔNG"

    def _get_fallback_data(self):
        """Dữ liệu dự phòng khi mất mạng hoặc hết quota API"""
        return {
            "condition": "Không rõ (Lỗi kết nối)",
            "temperature": "--°C",
            "humidity": "--%",
            "flood_warning": "Không rõ",
            "is_raining": False
        }