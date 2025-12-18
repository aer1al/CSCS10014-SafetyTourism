# file: fetch_crowd_data.py
import requests
import json

def fetch_hcm_hotspots():
    print("⏳ Đang tải toàn bộ điểm nóng ở TP.HCM từ OpenStreetMap...")
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Định nghĩa giới hạn không gian (Bounding Box) khu vực TP.HCM
    bbox = "10.37,106.33,11.16,107.02"
    
    # Xây dựng truy vấn Overpass QL để thu thập dữ liệu POI (Point of Interest)
    # Mục tiêu: Chợ, Phố đi bộ, Điểm tham quan, Trung tâm thương mại
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="marketplace"]({bbox});
      way["amenity"="marketplace"]({bbox});
      node["highway"="pedestrian"]({bbox});
      node["tourism"="attraction"]({bbox});
      node["shop"="mall"]({bbox});
    );
    out center;
    """
    
    try:
        # Thực hiện HTTP Request đến Overpass API
        response = requests.get(overpass_url, params={'data': query})
        data = response.json()
        
        hotspots = []
        for el in data.get('elements', []):
            # Xử lý chuẩn hóa tọa độ (Lấy tâm hình học nếu đối tượng là Way/Polygon)
            lat = el.get('lat') or el.get('center', {}).get('lat')
            lon = el.get('lon') or el.get('center', {}).get('lon')
            
            tags = el.get('tags', {})
            name = tags.get('name', 'Unknown Spot')
            
            # Phân loại đối tượng để áp dụng heuristic tính mật độ theo giờ
            h_type = "tourism"
            if tags.get('amenity') == 'marketplace': h_type = 'market'
            elif tags.get('shop') == 'mall': h_type = 'mall'
            elif tags.get('highway') == 'pedestrian': h_type = 'nightlife'
            
            if lat and lon:
                hotspots.append({
                    "name": name,
                    "lat": lat,
                    "lng": lon,
                    "type": h_type,
                    "radius": 0.3 # Bán kính ảnh hưởng mặc định (300m) cho Spatial Indexing
                })
                
        # Tuần tự hóa dữ liệu và lưu trữ xuống file JSON cục bộ (Persistence)
        with open('crowd_zones.json', 'w', encoding='utf-8') as f:
            json.dump(hotspots, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Đã lưu {len(hotspots)} điểm nóng vào 'crowd_zones.json'")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    fetch_hcm_hotspots()
