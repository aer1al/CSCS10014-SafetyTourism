import requests
import json
import time

def fetch_hcm_hotspots():
    print("⏳ Đang tải dữ liệu điểm nóng (bao gồm cả Cấp 2, C3)...")
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Bounding Box TP.HCM
    bbox = "10.37,106.33,11.16,107.02"
     
    # Query: Đã xóa comment gây lỗi #
    query = f"""
    [out:json][timeout:90];
    (
      node["amenity"="marketplace"]({bbox});
      way["amenity"="marketplace"]({bbox});
      
      node["shop"="mall"]({bbox});
      way["shop"="mall"]({bbox});
      
      node["tourism"="attraction"]({bbox});
      way["tourism"="attraction"]({bbox});
      
      node["amenity"="university"]({bbox});
      way["amenity"="university"]({bbox});
      
      node["amenity"="school"]({bbox});  
      way["amenity"="school"]({bbox});   
      
      node["highway"="pedestrian"]({bbox});
      way["highway"="pedestrian"]({bbox});
    );
    out center;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': query})
        
        if response.status_code != 200:
            print(f"❌ Lỗi API Overpass: {response.status_code}")
            print(response.text) # In ra lỗi chi tiết nếu có
            return

        data = response.json()
        hotspots = []
        
        count_market = 0
        count_mall = 0
        count_school = 0
        count_tourist = 0
        
        for el in data.get('elements', []):
            lat = el.get('lat') or el.get('center', {}).get('lat')
            lon = el.get('lon') or el.get('center', {}).get('lon')
            tags = el.get('tags', {})
            name = tags.get('name', 'Unknown Spot')
            
            if name == 'Unknown Spot': continue

            h_type = "general"
            radius = 0.2
            weight = 0.5
            
            # Logic phân loại
            if tags.get('amenity') == 'marketplace': 
                h_type = 'market'
                radius = 0.3
                weight = 0.8
                count_market += 1
                
            elif tags.get('shop') == 'mall': 
                h_type = 'mall'
                radius = 0.5 
                weight = 0.7
                count_mall += 1
                
            # Gộp University và School vào chung nhóm "school"
            elif tags.get('amenity') in ['university', 'school']:
                h_type = 'school'
                radius = 0.3 # Bán kính tắc đường quanh cổng trường
                weight = 1.0 # Trường học giờ tan tầm là kẹt cứng (Max level)
                count_school += 1
                
            elif tags.get('tourism') == 'attraction':
                h_type = 'tourist'
                count_tourist += 1
                
            if lat and lon:
                hotspots.append({
                    "name": name,
                    "lat": lat,
                    "lng": lon,
                    "type": h_type,
                    "radius": radius,
                    "base_weight": weight
                })
                
        with open('crowd_zones.json', 'w', encoding='utf-8') as f:
            json.dump(hotspots, f, ensure_ascii=False, indent=2)
            
        print("-" * 30)
        print(f"✅ Đã cập nhật xong {len(hotspots)} địa điểm:")
        print(f"   - Chợ: {count_market}")
        print(f"   - TTTM: {count_mall}")
        print(f"   - Trường học: {count_school}")
        print(f"   - Du lịch: {count_tourist}")
        print(f"📁 Dữ liệu mới đã lưu vào 'crowd_zones.json'")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    fetch_hcm_hotspots()