import requests
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

def get_natural_disasters(user_lat, user_lon, max_distance_km=1000): # <-- ĐÃ SỬA THÀNH 2000 ĐỂ TEST
    """
    [PHIÊN BẢN HOÀN CHỈNH]
    Lấy các sự kiện thiên tai (bão, lũ,...) gần vị trí user từ NASA EONET.
    """
    api_url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        nearby_events = []
        
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
                    event_info = {
                        "title": event.get("title"),
                        "distance_km": round(distance, 2),
                        "latitude": event_lat,
                        "longitude": event_lon,
                        "categories": [cat.get("title") for cat in event.get("categories", [])]
                    }
                    nearby_events.append(event_info)
                    
        if not nearby_events:
            return {"warning": False, "message": "Không có thiên tai (bão, lũ,...) nào được ghi nhận gần đây (trong bán kính 2000km)."}
        
        # Đây là output backend sẽ gửi lên frontend
        return {"warning": True, "message": f"Phát hiện {len(nearby_events)} sự kiện thiên tai gần bạn (trong bán kính 2000km).", "events": nearby_events}

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API NASA EONET: {e}")
        return None

# ----- TEST THỬ VỚI TỌA ĐỘ VŨNG TÀU -----
# Giờ nó sẽ bắt được các sự kiện ở Indonesia/Trung Quốc
print("--- Đang kiểm tra tại Vũng Tàu (10.34, 107.08) với bán kính 500km ---")
disaster_alerts_vn = get_natural_disasters(user_lat=10.34, user_lon=107.08)
print(disaster_alerts_vn)