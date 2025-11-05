import requests
import json
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Bán kính Trái Đất (km)
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    a = sin(dLat / 2)**2 + cos(lat1) * cos(lat2) * sin(dLon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_natural_disasters(user_lat, user_lon, max_distance_km=2000): # <-- Giảm bán kính
    """
    [PHIÊN BẢN ĐÃ CHUẨN HÓA]
    Trả về một MẢNG ĐƠN GIẢN các sự kiện, sẵn sàng cho frontend.
    Trả về [] (mảng rỗng) nếu có lỗi hoặc không tìm thấy.
    """
    api_url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open"
    
    try:
        response = requests.get(api_url, timeout=10) # Thêm timeout
        response.raise_for_status()
        data = response.json()
        
        # Mảng này sẽ được trả về trực tiếp
        formatted_list = [] 
        
        for event in data.get("events", []):
            geometry = event.get("geometry", [])
            if not geometry:
                continue
                
            event_coords = geometry[-1].get("coordinates")
            event_type = geometry[-1].get("type")
            
            if event_type == "Point":
                event_lon, event_lat = event_coords
                distance = haversine(user_lat, user_lon, event_lat, event_lon)
                
                if distance <= max_distance_km:
                    
                    # Tạo object đúng chuẩn frontend
                    event_info = {
                        'lat': event_lat,
                        'lng': event_lon, # <-- Đổi 'longitude' thành 'lng'
                        'name': event.get("title", "Sự kiện không tên"), # 'name'
                        'description': ", ".join([cat.get("title") for cat in event.get("categories", [])]), # 'description'
                        'details': f"Cách bạn {round(distance, 2)} km" # 'details'
                    }
                    formatted_list.append(event_info)
                    
        # Trả về mảng đã dọn dẹp
        return formatted_list

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API NASA EONET: {e}")
        # Trả về mảng rỗng nếu có lỗi
        return []

# ----- TEST THỬ VỚI TỌA ĐỘ VŨNG TÀU -----
if __name__ == "__main__":
    print("--- Đang kiểm tra tại Vũng Tàu (10.34, 107.08) ---")
    # Hàm này giờ trả về mảng đơn giản
    disaster_list = get_natural_disasters(user_lat=10.34, user_lon=107.08)
    print(f"Tìm thấy {len(disaster_list)} sự kiện.")
    print(json.dumps(disaster_list, indent=2))