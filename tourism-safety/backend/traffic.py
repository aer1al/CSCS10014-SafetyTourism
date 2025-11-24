# file: traffic.py
import osmnx as ox
import os

# Tên file để lưu cache (đỡ phải tải lại mỗi lần chạy)
MAP_FILENAME = "vietnam_d1_map.graphml"

def load_graph_data(place_name="District 1, Ho Chi Minh City, Vietnam"):
    """
    Hàm này chỉ làm 1 việc: Trả về đồ thị G (Graph).
    - Nếu có file .graphml rồi -> Load lên (mất 0.5 giây).
    - Nếu chưa có -> Tải từ OSM về (mất 10-20 giây) rồi lưu lại.
    """
    
    # Kiểm tra xem file đã tồn tại chưa
    if os.path.exists(MAP_FILENAME):
        print(f"📂 Đang tải bản đồ từ file {MAP_FILENAME} (Offline)...")
        # Load graph từ file
        G = ox.load_graphml(MAP_FILENAME)
    else:
        print(f"🌍 Đang tải bản đồ '{place_name}' từ Internet (lần đầu)...")
        # Tải graph dành cho xe lái (drive)
        G = ox.graph_from_place(place_name, network_type='drive')
        
        # Lưu lại để lần sau dùng
        print("💾 Đang lưu bản đồ xuống đĩa cứng...")
        ox.save_graphml(G, filepath=MAP_FILENAME)
        
    print(f"✅ Đã nạp xong bản đồ: {len(G.nodes)} nút, {len(G.edges)} cạnh.")
    return G

# Biến toàn cục để các file khác import vào dùng ngay
# Khi start server, dòng này sẽ chạy 1 lần duy nhất
SYSTEM_GRAPH = load_graph_data()