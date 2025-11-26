# file: traffic.py
import osmnx as ox
import os

# Đổi tên file cache để không bị nhầm với file Quận 1 cũ
MAP_FILENAME = "hcm_city_map.graphml" # Đổi tên file lại

def load_graph_data(place_name="Ho Chi Minh City, Vietnam"):
    """
    Hàm này tải và trả về đồ thị G (Graph) cho toàn bộ TP.HCM.
    """
    
    # 1. Kiểm tra xem file cache đã có chưa
    if os.path.exists(MAP_FILENAME):
        print(f"📂 [CACHE] Đang tải bản đồ TP.HCM từ file '{MAP_FILENAME}'...")
        # Load graph từ file (nhanh hơn tải mới)
        G = ox.load_graphml(MAP_FILENAME)
    else:
        print(f"🌍 [DOWNLOAD] Đang tải bản đồ '{place_name}' từ OSM (Sẽ hơi lâu)...")
        print("   -> Vui lòng chờ 1-2 phút...")
        
        # Tải graph dành cho xe lái (drive)
        # simplify=True giúp giảm bớt các node thừa để nhẹ hơn
        G = ox.graph_from_place(place_name, network_type='drive', simplify=True)
        
        # Lưu lại xuống đĩa cứng để lần sau dùng ngay
        print("💾 [SAVE] Đang lưu bản đồ xuống đĩa cứng...")
        ox.save_graphml(G, filepath=MAP_FILENAME)
        
    print(f"✅ Đã nạp xong bản đồ TP.HCM: {len(G.nodes)} nút, {len(G.edges)} cạnh.")
    return G

# Biến toàn cục chứa bản đồ (Load ngay khi import file này)
SYSTEM_GRAPH = load_graph_data()