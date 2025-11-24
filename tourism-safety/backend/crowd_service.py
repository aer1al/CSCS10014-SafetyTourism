# file: fetch_crowd_data.py
import requests
import json

def fetch_hcm_hotspots():
    print("⏳ Đang tải toàn bộ điểm nóng ở TP.HCM từ OpenStreetMap...")
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Bounding Box của TP.HCM (Nam, Tây, Bắc, Đông)
    bbox = "10.37,106.33,11.16,107.02"
    
    # Query: Lấy tất cả Mall, Market, Attraction, Pedestrian
    # [out:json];
    # (
    #   node["amenity"="marketplace"](10.37,106.33,11.16,107.02);
    #   way["amenity"="marketplace"](10.37,106.33,11.16,107.02);
    #   node["tourism"="attraction"](10.37,106.33,11.16,107.02);
    #   node["shop"="mall"](10.37,106.33,11.16,107.02);
    # );
    # out center;
    
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
        response = requests.get(overpass_url, params={'data': query})
        data = response.json()
        
        hotspots = []
        for el in data.get('elements', []):
            # Lấy tọa độ (nếu là way thì lấy center)
            lat = el.get('lat') or el.get('center', {}).get('lat')
            lon = el.get('lon') or el.get('center', {}).get('lon')
            
            tags = el.get('tags', {})
            name = tags.get('name', 'Unknown Spot')
            
            # Phân loại để tính giờ cao điểm
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
                    "radius": 0.3 # Mặc định bán kính ảnh hưởng 300m
                })
                
        # Lưu vào file
        with open('crowd_zones.json', 'w', encoding='utf-8') as f:
            json.dump(hotspots, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Đã lưu {len(hotspots)} điểm nóng vào 'crowd_zones.json'")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    fetch_hcm_hotspots()