import json
import os

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# 1. Lấy vị trí của file script này (đang nằm trong rag_engine)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Lấy thư mục gốc dự án (backend) bằng cách lùi lại 1 cấp
ROOT_DIR = os.path.dirname(CURRENT_DIR)

# 3. Đường dẫn input: File crowd_zones.json (Nằm trong folder data ở root)
# Code sẽ thử tìm ở ../data/crowd_zones.json trước
INPUT_FILE = os.path.join(ROOT_DIR, 'data', 'crowd_zones.json')

# Nếu không thấy, thử tìm ngay ở root (trường hợp bạn chưa gom vào data)
if not os.path.exists(INPUT_FILE):
    INPUT_FILE = os.path.join(ROOT_DIR, 'crowd_zones.json')

# 4. Đường dẫn output: File dataFilter.json (Lưu ngay tại đây)
OUTPUT_FILE = os.path.join(CURRENT_DIR, 'dataFilter.json')

def generate_description(item):
    name = item.get('name', 'Địa điểm chưa đặt tên')
    t_type = item.get('type', 'place')
    
    if t_type == 'market':
        return f"Khu vực {name}. Chợ truyền thống/Khu mua sắm, thường xuyên đông đúc, xe cộ di chuyển chậm vào buổi sáng và giờ tan tầm."
    elif t_type == 'nightlife':
        return f"Khu vực {name}. Phố đi bộ/Giải trí về đêm. Rất đông đúc, ồn ào và hạn chế giao thông vào buổi tối."
    elif t_type == 'mall':
        return f"Trung tâm thương mại {name}. Điểm đến mua sắm, giải trí, thường đông đúc vào cuối tuần và ngày lễ."
    elif t_type == 'school':
        return f"Khu vực trường học {name}. Thường xuyên kẹt xe cục bộ vào khung giờ đưa đón học sinh."
    else:
        return f"Khu vực {name}. Điểm tập trung đông người, mật độ giao thông cao."

def get_time_rule(t_type):
    if t_type == 'market': return {"start": "06:00", "end": "19:00"}
    if t_type == 'nightlife': return {"start": "18:00", "end": "02:00"}
    if t_type == 'school': return {"start": "16:00", "end": "17:30"}
    if t_type == 'mall': return {"start": "10:00", "end": "22:00"}
    return {"start": "07:00", "end": "21:00"}

def main():
    print(f"📂 Đang đọc dữ liệu từ: {INPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ LỖI: Không tìm thấy file crowd_zones.json!")
        print(f"👉 Code đang tìm tại: {INPUT_FILE}")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            crowd_raw = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc file JSON: {e}")
        return

    normalized_data = []
    
    for idx, item in enumerate(crowd_raw):
        # Bỏ qua các điểm không rõ tên
        if "Unknown" in item.get('name', ''): continue
        
        t_type = item.get('type', 'crowd')
        
        entry = {
            "id": f"CROWD_{idx}_{t_type.upper()}",
            "type": f"crowd_{t_type}",
            "description": generate_description(item),
            "time": get_time_rule(t_type),
            "geometry": {
                "lat": item['lat'],
                "lng": item['lng'],
                "radius": item.get('radius', 0.3)
            },
            "attributes": {
                "severity": item.get('weight', 0.5),
                "original_type": t_type
            },
            "affected_roads": []  # Chờ bước sau điền vào
        }
        normalized_data.append(entry)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(normalized_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã xử lý xong {len(normalized_data)} địa điểm!")
    print(f"💾 File kết quả: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()