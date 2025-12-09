import osmnx as ox
import os

# Cấu hình tên file cache cho từng chế độ
GRAPH_FILES = {
    "drive": "hcm_map_drive.graphml",
    "walk": "hcm_map_walk.graphml"
}

# Biến toàn cục lưu trữ đồ thị đã load
SYSTEM_GRAPHS = {
    "drive": None,
    "walk": None
}

PLACE_NAME = "Ho Chi Minh City, Vietnam"

def load_graph_by_mode(mode="walk"):
    """
    Tải bản đồ theo chế độ (drive/walk).
    Có cơ chế Caching thông minh.
    """
    filename = GRAPH_FILES.get(mode, "hcm_map_drive.graphml")
    
    # 1. Nếu đã load vào RAM rồi thì trả về ngay (Siêu nhanh)
    if SYSTEM_GRAPHS[mode] is not None:
        return SYSTEM_GRAPHS[mode]

    # 2. Nếu chưa có trong RAM, kiểm tra file trên đĩa
    if os.path.exists(filename):
        print(f"📂 [CACHE] Đang tải bản đồ '{mode}' từ file '{filename}'...")
        try:
            G = ox.load_graphml(filename)
            SYSTEM_GRAPHS[mode] = G
            return G
        except Exception as e:
            print(f"⚠️ File lỗi, tải lại từ đầu... ({e})")
    
    # 3. Nếu chưa có gì hết, tải mới từ OSM (Lâu)
    print(f"🌍 [DOWNLOAD] Đang tải bản đồ '{mode}' từ OSM (Sẽ hơi lâu)...")
    
    try:
        # Tải graph theo mode
        G = ox.graph_from_place(PLACE_NAME, network_type=mode, simplify=True)
        
        # Lưu xuống đĩa
        print(f"💾 [SAVE] Đang lưu bản đồ '{mode}' xuống đĩa cứng...")
        ox.save_graphml(G, filepath=filename)
        
        # Lưu vào RAM
        SYSTEM_GRAPHS[mode] = G
        return G
        
    except Exception as e:
        print(f"❌ Lỗi tải bản đồ: {e}")
        return None

def preload_maps():
    """
    Gọi khi khởi động Server để load trước vào RAM.
    """
    print("🚀 Đang khởi động hệ thống bản đồ Đa phương tiện...")
    # Load trước bản đồ Drive (thường dùng nhất)
    load_graph_by_mode("drive")
    # Bản đồ Walk có thể load sau hoặc load luôn tùy RAM server
    # load_graph_by_mode("walk") 
    print("✅ Đã sẵn sàng phục vụ!")

# Tự động chạy preload khi import (nếu cần)
if __name__ != "__main__":
    preload_maps()