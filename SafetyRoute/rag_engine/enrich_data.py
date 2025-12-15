import json
import os
import sys
import math
import networkx as nx
import osmnx as ox  # Thư viện xử lý bản đồ chuyên dụng

# --- 1. CẤU HÌNH ĐƯỜNG DẪN ---
# Thư mục hiện tại: .../backend/rag_engine
current_dir = os.path.dirname(os.path.abspath(__file__))

# Thư mục gốc dự án (nơi chứa file .graphml): Đi ngược ra 2 cấp
# Từ rag_engine -> backend -> Project_Folder
project_root = os.path.dirname(os.path.dirname(current_dir))

# Đường dẫn tuyệt đối đến file bản đồ
MAP_PATH = os.path.join(project_root, 'hcm_map_drive.graphml')

INPUT_FILE = os.path.join(current_dir, 'dataFilter.json')
OUTPUT_FILE = os.path.join(current_dir, 'dataFilter.json')

# --- 2. HÀM TÍNH KHOẢNG CÁCH (Haversine) ---
# Viết trực tiếp ở đây để khỏi lo lỗi import từ utils.py
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Bán kính trái đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- 3. HÀM TÌM ĐƯỜNG BỊ ẢNH HƯỞNG ---
def find_affected_roads(graph, center_lat, center_lng, radius_km):
    affected_roads = set()
    
    # Duyệt qua tất cả các Node trong Graph
    for node_id, data in graph.nodes(data=True):
        node_lat = data.get('y')
        node_lon = data.get('x')
        
        # Tính khoảng cách
        dist = haversine(center_lat, center_lng, node_lat, node_lon)
        
        if dist <= radius_km:
            # Nếu Node nằm trong vùng -> Lấy các cạnh nối với Node này
            # Cấu trúc edges: (u, v, key, data) hoặc (u, v, data) tùy phiên bản networkx
            try:
                edges = graph.edges(node_id, data=True)
                for u, v, edge_data in edges:
                    road_name = edge_data.get('name', '')
                    
                    if isinstance(road_name, list):
                        for n in road_name:
                            if n: affected_roads.add(n)
                    elif isinstance(road_name, str) and road_name:
                        affected_roads.add(road_name)
            except Exception:
                continue
                    
    return list(affected_roads)

# --- 4. CHƯƠNG TRÌNH CHÍNH ---
def main():
    print("🚀 BẮT ĐẦU QUÁ TRÌNH LÀM GIÀU DỮ LIỆU (ENRICHMENT)")
    print("-" * 50)
    
    # Kiểm tra file input
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Lỗi: Không tìm thấy file {INPUT_FILE}")
        return

    # Kiểm tra file bản đồ
    print(f"📂 Đang tìm bản đồ tại: {MAP_PATH}")
    if not os.path.exists(MAP_PATH):
        print(f"❌ LỖI NGHIÊM TRỌNG: Không tìm thấy file 'hcm_map_drive.graphml'")
        print("👉 Bạn hãy kiểm tra lại xem file này có nằm đúng ở thư mục ngoài cùng không.")
        # Thử gợi ý vị trí khác nếu người dùng để trong backend
        alternative_path = os.path.join(os.path.dirname(current_dir), 'hcm_map_drive.graphml')
        if os.path.exists(alternative_path):
             print(f"💡 Gợi ý: Tìm thấy file ở '{alternative_path}'. Hãy di chuyển nó ra ngoài backend hoặc sửa code.")
        return

    # Load dữ liệu JSON
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load bản đồ
    print("⏳ Đang load bản đồ (sẽ mất khoảng 15-30 giây)...")
    try:
        G = ox.load_graphml(MAP_PATH)
        print(f"✅ Load bản đồ thành công! Tổng số node: {len(G.nodes)}")
    except Exception as e:
        print(f"❌ Lỗi khi load graphml: {e}")
        return

    print("-" * 50)

    # Quét dữ liệu
    count_updated = 0
    for idx, item in enumerate(data):
        geo = item.get('geometry', {})
        lat = geo.get('lat')
        lng = geo.get('lng')
        rad = geo.get('radius', 0.5)
        
        # Chỉ xử lý nếu chưa có dữ liệu affected_roads hoặc list rỗng
        if not item.get('affected_roads'):
            name = item.get('description', 'Địa điểm')[:40] + "..."
            print(f"🔍 [{idx+1}/{len(data)}] Quét vùng: {name}")
            
            roads = find_affected_roads(G, lat, lng, rad)
            item['affected_roads'] = roads
            
            if roads:
                print(f"   L-> Phát hiện {len(roads)} đường: {', '.join(roads[:3])}...")
            else:
                print("   L-> Không tìm thấy đường nào trong bán kính này.")
            
            count_updated += 1

    # Lưu kết quả
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("-" * 50)
    print(f"🎉 HOÀN TẤT! Đã cập nhật {count_updated} địa điểm.")
    print(f"💾 File kết quả: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()