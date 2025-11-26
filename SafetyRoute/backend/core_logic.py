import networkx as nx
import osmnx as ox
from datetime import datetime
from tqdm import tqdm
from rtree import index  # <--- THƯ VIỆN MỚI

# Import các module vệ tinh
from traffic import SYSTEM_GRAPH as G
from weather import get_mock_weather_zones
from disasters import get_natural_disasters
import standardization 

# Tốc độ trung bình giả định (km/h)
BASE_SPEED_KMH = 30.0 

def create_spatial_index(zones):
    """
    Hàm phụ trợ: Tạo chỉ mục không gian (R-tree Index) cho danh sách các vùng rủi ro.
    Input: List các dict (disaster hoặc weather)
    Output: Rtree Index object
    """
    idx = index.Index()
    for i, zone in enumerate(zones):
        # 1. Lấy thông tin
        lat = zone['lat']
        lng = zone['lng']
        radius_km = zone.get('radius', 5.0)
        
        # 2. Quy đổi bán kính km sang độ (xấp xỉ) để tạo Bounding Box
        # 1 độ ~ 111km. Cộng thêm chút đệm (buffer) cho an toàn.
        delta_deg = (radius_km / 111.0) * 1.2 
        
        # 3. Tạo hình chữ nhật bao quanh vùng rủi ro (min_x, min_y, max_x, max_y)
        # Lưu ý: Rtree dùng (Left, Bottom, Right, Top) -> (min_lng, min_lat, max_lng, max_lat)
        bbox = (lng - delta_deg, lat - delta_deg, lng + delta_deg, lat + delta_deg)
        
        # 4. Insert vào index (lưu index i để truy xuất ngược lại list gốc)
        idx.insert(i, bbox)
        
    return idx

def get_optimal_routes(start_coords, end_coords):
    print(f"🚀 Bắt đầu tìm đường (Mode: R-tree Optimized)...")
    
    # ==========================================
    # 1. GATHER DATA
    # ==========================================
    now = datetime.now()
    curr_hour = now.hour + (now.minute / 60)
    is_weekend = now.weekday() >= 5
    
    # Load dữ liệu rủi ro
    disaster_zones = get_natural_disasters(start_coords[0], start_coords[1])
    weather_zones = get_mock_weather_zones()
    traffic_score = standardization.calculate_traffic_score(curr_hour, is_weekend)

    # --- [NEW] TẠO INDEX R-TREE ---
    # Giúp tìm kiếm nhanh hơn thay vì duyệt trâu (Brute-force)
    print("🌳 Đang xây dựng chỉ mục không gian (Spatial Indexing)...")
    disaster_idx = create_spatial_index(disaster_zones)
    weather_idx = create_spatial_index(weather_zones)

    # ==========================================
    # 2. CẮT BẢN ĐỒ (SUBGRAPH)
    # ==========================================
    # [FIX CŨ] Với bản đồ Quận 1 nhỏ, ta copy luôn cho an toàn, không cần cắt bbox
    sub_G = G.copy()

    # ==========================================
    # 3. TÍNH TRỌNG SỐ (WEIGHTS)
    # ==========================================
    w_disaster = 1000.0
    w_weather = 30.0
    w_crowd = 5.0

    print(f"🔄 Tính toán rủi ro trên {sub_G.number_of_edges()} cạnh...")
    
    for u, v, data in tqdm(sub_G.edges(data=True), desc="Processing", leave=False):
        length_m = data.get('length', 10)
        
        node_u = sub_G.nodes[u]
        node_v = sub_G.nodes[v]
        
        # Lấy Bounding Box của cạnh đường (Edge BBox)
        min_lng_e = min(node_u['x'], node_v['x'])
        max_lng_e = max(node_u['x'], node_v['x'])
        min_lat_e = min(node_u['y'], node_v['y'])
        max_lat_e = max(node_u['y'], node_v['y'])
        edge_bbox = (min_lng_e, min_lat_e, max_lng_e, max_lat_e)

        # --- A. Tính Score (Dùng R-tree để lọc ứng viên) ---
        
        # 1. DISASTER SCORE
        s_disaster = 0
        if len(disaster_zones) > 0:
            # Chỉ lấy những disaster có BBox giao cắt với cạnh đường này
            candidate_indices = list(disaster_idx.intersection(edge_bbox))
            if candidate_indices:
                # Lọc ra list disaster liên quan
                relevant_disasters = [disaster_zones[i] for i in candidate_indices]
                # Tính toán chi tiết hình học chỉ trên tập nhỏ này (Siêu nhanh)
                s_disaster = standardization.calculate_disaster_impact_advanced(data, node_u, node_v, relevant_disasters)
             
        # 2. WEATHER SCORE
        s_weather = 0
        if len(weather_zones) > 0:
            candidate_indices = list(weather_idx.intersection(edge_bbox))
            if candidate_indices:
                relevant_weathers = [weather_zones[i] for i in candidate_indices]
                s_weather = standardization.calculate_weather_impact_geometry(data, node_u, node_v, relevant_weathers)
        
        # 3. CROWD SCORE
        mid_lat = (node_u['y'] + node_v['y']) / 2
        mid_lon = (node_u['x'] + node_v['x']) / 2
        s_crowd = standardization.calculate_crowd_score(mid_lat, mid_lon, curr_hour)
        
        # --- B. Tính Penalty ---
        penalty = (w_disaster * s_disaster) + (w_weather * s_weather) + (w_crowd * s_crowd)
        
        # Lưu weight để Dijkstra dùng
        data['final_weight'] = length_m * (1 + penalty)
        
        # Lưu các chỉ số rủi ro vào cạnh để lát nữa truy vết (Traceback)
        data['risk_details'] = {
            'has_disaster': s_disaster > 0,
            'has_weather': s_weather > 0,
            'has_crowd': s_crowd > 0.7
        }
        
        # Tính ETA
        speed_factor = (1.0 - traffic_score * 0.6) * (1.0 - s_weather * 0.2)
        real_speed_ms = max((BASE_SPEED_KMH * speed_factor) / 3.6, 1.0)
        data['eta_seconds'] = length_m / real_speed_ms

    # ==========================================
    # 4. TÌM ĐƯỜNG & TRÍCH XUẤT CHI TIẾT
    # ==========================================
    orig_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    dest_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
    
    try:
        route_nodes = nx.shortest_path(sub_G, orig_node, dest_node, weight='final_weight')
        
        total_dist = 0
        total_eta = 0
        route_coords = []
        
        # Danh sách chi tiết các vùng nguy hiểm va phải
        hit_disasters = set() 
        hit_weathers = set()
        
        # Biến đếm số cạnh bị đông đúc
        crowded_edges_count = 0
        
        for i in range(len(route_nodes) - 1):
            u = route_nodes[i]
            v = route_nodes[i+1]
            edge_data = sub_G.get_edge_data(u, v)[0]
            
            total_dist += edge_data.get('length', 0)
            total_eta += edge_data.get('eta_seconds', 0)
            route_coords.append([sub_G.nodes[u]['y'], sub_G.nodes[u]['x']])
            
            # Đếm đông đúc
            if edge_data.get('risk_details', {}).get('has_crowd'):
                 crowded_edges_count += 1
            
            # --- LOGIC MỚI [ĐÃ SỬA LỖI]: Truy vết ---
            node_u_obj = sub_G.nodes[u]
            
            if edge_data.get('risk_details', {}).get('has_disaster'):
                # Dùng R-tree index ở đây cũng được, hoặc loop thường (vì số lượng disaster ít)
                # Loop thường cho đơn giản logic hiển thị
                for d in disaster_zones:
                    # [FIX] Dùng trực tiếp 'lat', 'lng' thay vì 'geometry'
                    dist = standardization.haversine(node_u_obj['y'], node_u_obj['x'], d['lat'], d['lng'])
                    if dist < 0.5: 
                        hit_disasters.add(f"{d['title']} (ID: {d.get('id', 'Unknown')})")

            if edge_data.get('risk_details', {}).get('has_weather'):
                for w in weather_zones:
                    dist = standardization.haversine(node_u_obj['y'], node_u_obj['x'], w['lat'], w['lng'])
                    if dist < w['radius']:
                        hit_weathers.add(f"{w['condition']}: {w['description']}")

        # Thêm điểm cuối
        last_node = route_nodes[-1]
        route_coords.append([sub_G.nodes[last_node]['y'], sub_G.nodes[last_node]['x']])
        
        # Đánh giá mức độ đông đúc tổng thể (trên 20% lộ trình là đông)
        is_crowded = crowded_edges_count > (len(route_nodes) * 0.2)

        return {
            "status": "success",
            "distance_km": round(total_dist / 1000, 2),
            "duration_min": round(total_eta / 60, 0),
            "geometry": route_coords,
            "risk_summary": {
                "traffic_level": "High" if traffic_score > 0.7 else "Normal",
                "crowd_level": "High" if is_crowded else "Low",  # [NEW]
                "weather_warning": len(hit_weathers) > 0,
                "disaster_warning": len(hit_disasters) > 0
            },
            "hit_details": {
                "disasters": list(hit_disasters),
                "weathers": list(hit_weathers)
            }
        }
        
    except nx.NetworkXNoPath:
        return {"status": "error", "message": "Không tìm thấy đường đi an toàn."}
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc() # In chi tiết lỗi để debug
        return {"status": "error", "message": str(e)}