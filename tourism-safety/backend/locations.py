import requests
import json

def get_nearby_places(lat, lon, amenity_type, radius_meters=1000):
    """
    Lấy các địa điểm (bệnh viện, nơi trú ẩn) từ OpenStreetMap Overpass API.
    
    Args:
        lat (float): Vĩ độ của user
        lon (float): Kinh độ của user
        amenity_type (str): Loại địa điểm ("hospital" hoặc "shelter")
        radius_meters (int): Bán kính tìm kiếm (mét)
    """
    
    # Endpoint của Overpass API
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Ngôn ngữ truy vấn Overpass QL
    # Nó sẽ tìm tất cả 'node' và 'way' có tag 'amenity' = amenity_type
    # xung quanh 1 điểm (around) với bán kính radius_meters
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="{amenity_type}"](around:{radius_meters},{lat},{lon});
      way["amenity"="{amenity_type}"](around:{radius_meters},{lat},{lon});
      relation["amenity"="{amenity_type}"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': overpass_query})
        response.raise_for_status() # Báo lỗi nếu request thất bại
        data = response.json()
        
        places = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            place_name = tags.get('name', f"Địa điểm ({amenity_type})") # Lấy tên, nếu không có thì dùng tên chung
            
            # Lấy tọa độ (khác nhau cho 'node' và 'way')
            place_lat = element.get('lat')
            place_lon = element.get('lon')
            
            if 'center' in element: # Nếu là 'way' (tòa nhà) thì lấy tọa độ trung tâm
                place_lat = element['center'].get('lat')
                place_lon = element['center'].get('lon')

            if place_lat and place_lon:
                places.append({
                    'name': place_name,
                    'lat': place_lat,
                    'lon': place_lon,
                    'type': amenity_type,
                    'osm_id': element.get('id')
                })
        
        return {"status": "success", "count": len(places), "places": places}

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi Overpass API: {e}")
        return {"status": "error", "message": "Lỗi truy vấn OpenStreetMap."}

# --- PHẦN TEST THỬ ---
if __name__ == "__main__":
    # Tọa độ mẫu (Gần Bệnh viện Chợ Rẫy, TP.HCM)
    user_lat = 10.7580
    user_lon = 106.6604
    
    print("--- Đang tìm Bệnh viện (Hospitals) ---")
    hospitals = get_nearby_places(user_lat, user_lon, "hospital")
    print(json.dumps(hospitals, indent=2, ensure_ascii=False)) # Dùng json.dumps để in đẹp
    
    print("\n--- Đang tìm Nơi trú ẩn (Shelters) ---")
    # Lưu ý: 'shelter' ở VN có thể ít dữ liệu, chủ yếu là các cơ sở từ thiện
    shelters = get_nearby_places(user_lat, user_lon, "shelter")
    print(json.dumps(shelters, indent=2, ensure_ascii=False))