# file: core_logic.py
import networkx as nx
import osmnx as ox
from traffic import SYSTEM_GRAPH as G  # Lấy bản đồ sạch về
from utils import haversine

# --- HÀM 1: ÁP TRỌNG SỐ (WEIGHTING) ---
def apply_risk_weights(graph, disaster_zones=[], crowd_zones=[]):
    """
    Duyệt qua từng con đường (cạnh) trên bản đồ và tính lại 'độ khó đi'.
    Input: Đồ thị gốc, Danh sách vùng rủi ro.
    Output: Đồ thị đã được gán trọng số (Fast, Safe, Balanced).
    """
    print("⚡ Đang tính toán trọng số rủi ro cho toàn bộ bản đồ...")
    
    # Duyệt qua tất cả các cạnh (u, v) trong đồ thị
    # u, v là ID của 2 giao lộ. data chứa thông tin độ dài, tên đường...
    for u, v, data in graph.edges(data=True):
        
        # 1. Lấy độ dài gốc (mét)
        length = data.get('length', 10) # Mặc định 10m nếu lỗi
        
        # 2. Kiểm tra xem đoạn đường này có nằm trong vùng rủi ro không
        # (Để tối ưu, ta lấy tọa độ điểm đầu u để check)
        node_u = graph.nodes[u]
        lat = node_u['y']
        lon = node_u['x']
        
        is_risky = check_if_point_in_risk_zone(lat, lon, disaster_zones)
        
        # 3. Tạo 3 loại trọng số (Weight)
        
        # A. FASTEST: Chỉ quan tâm độ dài (Kệ rủi ro)
        data['weight_fast'] = length
        
        # B. SAFEST: Sợ rủi ro (Nếu rủi ro -> Đường dài gấp 50 lần)
        if is_risky:
            data['weight_safe'] = length * 50 
        else:
            data['weight_safe'] = length
            
        # C. BALANCED: Cân bằng (Nếu rủi ro -> Đường dài gấp 3 lần)
        if is_risky:
            data['weight_balanced'] = length * 3
        else:
            data['weight_balanced'] = length
            
    return graph # Trả về đồ thị đã "khôn" hơn

def check_if_point_in_risk_zone(lat, lon, disaster_list):
    """Hàm phụ: Check xem tọa độ có gần thiên tai nào không"""
    # Logic đơn giản: Quét danh sách thiên tai
    for d in disaster_list:
        # Giả sử d có toạ độ d['lat'], d['lng']
        # Nếu khoảng cách < 500m thì coi như dính
        if haversine(lat, lon, d['lat'], d['lng']) < 0.5:
            return True
    return False

# --- HÀM 2: CHẠY DIJKSTRA (ROUTING) ---
def find_optimal_route(start_coords, end_coords, mode='fastest'):
    """
    Chạy thuật toán Dijkstra trên đồ thị đã gán trọng số.
    mode: 'fastest', 'safest', 'balanced'
    """
    # 1. Tìm nút (Node) trên bản đồ gần nhất với tọa độ người dùng nhập
    # (Vì người dùng nhập tọa độ bất kỳ, ta phải map nó vào ngã tư gần nhất)
    orig_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0]) # Lưu ý: (X=Lon, Y=Lat)
    dest_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
    
    # 2. Chọn loại trọng số dựa trên mode
    weight_key = 'weight_fast'
    if mode == 'safest': weight_key = 'weight_safe'
    if mode == 'balanced': weight_key = 'weight_balanced'
    
    try:
        # 3. CHẠY DIJKSTRA (Dòng quan trọng nhất)
        route_nodes = nx.shortest_path(G, orig_node, dest_node, weight=weight_key)
        
        # 4. Chuyển đổi list ID nút thành toạ độ để vẽ lên bản đồ
        route_geometry = []
        total_dist = 0
        
        for node_id in route_nodes:
            node = G.nodes[node_id]
            route_geometry.append([node['y'], node['x']]) # [Lat, Lon] cho Google Maps
            
        # Tính tổng độ dài (ước lượng)
        dist = nx.path_weight(G, route_nodes, weight='length')
        
        return {
            "status": "OK",
            "mode": mode,
            "distance_m": dist,
            "geometry": route_geometry
        }
        
    except nx.NetworkXNoPath:
        return {"status": "No Path Found"}