import requests
import json

def get_nearby_places(lat, lon, amenity_type, radius_meters=2000):
    """
    [PHIÊN BẢN ĐÃ CHUẨN HÓA]
    Trả về một MẢNG ĐƠN GIẢN các địa điểm, sẵn sàng cho frontend.
    Trả về [] (mảng rỗng) nếu có lỗi hoặc không tìm thấy.
    """
    
    overpass_url = "http://overpass-api.de/api/interpreter"
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
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=10) # Thêm timeout
        response.raise_for_status() 
        data = response.json()
        
        # Mảng này sẽ được trả về trực tiếp
        formatted_list = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            place_name = tags.get('name', f"{amenity_type.capitalize()} không tên")
            
            place_lat = element.get('lat')
            place_lon = element.get('lon')
            
            if 'center' in element: 
                place_lat = element['center'].get('lat')
                place_lon = element['center'].get('lon')

            if place_lat and place_lon:
                
                # Tạo object đúng chuẩn frontend
                formatted_list.append({
                    'lat': place_lat,
                    'lng': place_lon, # <-- Đổi 'lon' thành 'lng'
                    'name': place_name, # 'name'
                    'description': f"{amenity_type.capitalize()} Location", # 'description'
                    'details': f"OSM ID: {element.get('id')}" # 'details'
                })
        
        # Trả về mảng đã dọn dẹp
        return formatted_list

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi Overpass API: {e}")
        # Trả về mảng rỗng nếu có lỗi
        return []

# --- PHẦN TEST THỬ ---
if __name__ == "__main__":
    user_lat = 10.7580
    user_lon = 106.6604
    
    print("--- Đang tìm Bệnh viện (Hospitals) ---")
    hospital_list = get_nearby_places(user_lat, user_lon, "hospital")
    print(f"Tìm thấy {len(hospital_list)} bệnh viện.")
    print(json.dumps(hospital_list, indent=2, ensure_ascii=False))
    
    print("\n--- Đang tìm Nơi trú ẩn (Shelters) ---")
    shelter_list = get_nearby_places(user_lat, user_lon, "shelter")
    print(f"Tìm thấy {len(shelter_list)} nơi trú ẩn.")
    print(json.dumps(shelter_list, indent=2, ensure_ascii=False))