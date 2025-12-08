import requests
import json
import os

def update_real_disasters():
    print("🌍 Đang quét toàn bộ Bão (TC) và Lũ (FL) từ GDACS...")
    
    list_url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
    
    # 🔥 Lấy cả FL (Flood) và TC (Tropical Cyclone)
    params = { 
        "eventlist": "FL;TC",  # Dấu chấm phẩy để lấy nhiều loại
        "alertlevel": "Green;Orange;Red", 
        "fromDate": "", 
        "toDate": "" 
    }
    
    headers = { "User-Agent": "Mozilla/5.0" }
    
    real_disasters = []
    
    try:
        res = requests.get(list_url, params=params, headers=headers, timeout=20)
        
        if res.status_code != 200:
            print(f"❌ Lỗi tải danh sách: {res.status_code}")
            return

        data = res.json()
        print(f"🔍 Tìm thấy tổng {len(data.get('features', []))} sự kiện toàn cầu.")
        
        for feature in data.get('features', []):
            props = feature['properties']
            country = props.get('country', '')
            event_type = props.get('eventtype') # FL hoặc TC
            
            # Lọc khu vực Việt Nam & Biển Đông (Cho Bão)
            # Với bão, đôi khi country là "Pacific" hoặc "Asia", nên ta lọc thêm toạ độ
            center_lng, center_lat = feature['geometry']['coordinates']
            
            is_in_vn_region = (
                ("Vietnam" in country or "Viet Nam" in country) or
                (5.0 <= center_lat <= 25.0 and 100.0 <= center_lng <= 120.0) # Khung Biển Đông
            )
            
            if is_in_vn_region:
                event_date = props.get('todate')
                event_id = props.get('eventid')
                name = props.get('name')
                episode_id = props.get('episodeid')
                
                print(f"   👉 Phát hiện {event_type}: {name}...")
                
                # Gọi API lấy hình vẽ (Geometry)
                geo_url = "https://www.gdacs.org/gdacsapi/api/polygons/getgeometry"
                geo_params = {
                    "eventtype": event_type, # FL hoặc TC
                    "eventid": event_id,
                    "episodeid": episode_id
                }
                
                # Biến lưu geometry (Mặc định là None nếu API lỗi)
                polygon_data = None
                
                try:
                    geo_res = requests.get(geo_url, params=geo_params, headers=headers, timeout=10)
                    if geo_res.status_code == 200:
                        polygon_data = geo_res.json()
                        print("      ✅ Đã tải hình vẽ vùng ảnh hưởng.")
                except:
                    print("      ⚠️ Không tải được hình vẽ (Dùng tâm điểm).")

                # Định nghĩa loại cho Frontend hiển thị icon
                display_type = "flood" if event_type == "FL" else "severeStorms"
                
                # Bán kính mặc định (Dùng cho Core Logic tính toán nhanh)
                # Bão (TC) to hơn Lũ (FL)
                calc_radius = 50.0 if event_type == "TC" else 10.0

                real_disasters.append({
                    "id": str(event_id),
                    "title": f"[{event_type}] {name}",
                    "lat": center_lat,
                    "lng": center_lng,
                    "type": display_type,
                    "radius": calc_radius, 
                    "geometry": polygon_data, # GeoJSON thật (nếu có)
                    "level": props.get('alertlevel'),
                    "date": event_date
                })

        # Lưu xuống file
        if real_disasters:
            with open('real_disasters.json', 'w', encoding='utf-8') as f:
                json.dump(real_disasters, f, ensure_ascii=False, indent=2)
            print(f"🎉 XONG! Đã lưu {len(real_disasters)} sự kiện vào 'real_disasters.json'")
        else:
            print("✅ Không có Bão/Lũ nào ở VN lúc này.")

    except Exception as e:
        print(f"❌ Lỗi cập nhật: {e}")

if __name__ == "__main__":
    update_real_disasters()