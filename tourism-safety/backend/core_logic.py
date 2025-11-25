import networkx as nx
import osmnx as ox
from datetime import datetime
from tqdm import tqdm

# Import các module vệ tinh
from traffic import SYSTEM_GRAPH as G
from weather import get_mock_weather_zones
from disasters import get_natural_disasters
import standardization 

# Tốc độ trung bình giả định (km/h)
BASE_SPEED_KMH = 30.0 

def get_optimal_routes(start_coords, end_coords):
    print(f"🚀 Bắt đầu tìm đường (Mode: MVP Detail)...")
    
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

    # ==========================================
    # 2. CẮT BẢN ĐỒ (SUBGRAPH)
    # ==========================================
    BUFFER = 0.03 # ~3-4km buffer
    min_lat = min(start_coords[0], end_coords[0]) - BUFFER
    max_lat = max(start_coords[0], end_coords[0]) + BUFFER
    min_lng = min(start_coords[1], end_coords[1]) - BUFFER
    max_lng = max(start_coords[1], end_coords[1]) + BUFFER
    
    nodes_in_bbox = [
        node for node, data in G.nodes(data=True) 
        if min_lat < data['y'] < max_lat and min_lng < data['x'] < max_lng
    ]
    
    if len(nodes_in_bbox) < 10:
        sub_G = G.copy()
    else:
        sub_G = G.subgraph(nodes_in_bbox).copy()

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
        
        # --- A. Tính Score ---
        s_disaster = 0
        if len(disaster_zones) > 0:
             s_disaster = standardization.calculate_disaster_impact_advanced(data, node_u, node_v, disaster_zones)
             
        s_weather = 0
        if len(weather_zones) > 0:
            s_weather = standardization.calculate_weather_impact_geometry(data, node_u, node_v, weather_zones)
        
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
        hit_disasters = set() # Dùng set để tránh trùng lặp
        hit_weathers = set()
        
        for i in range(len(route_nodes) - 1):
            u = route_nodes[i]
            v = route_nodes[i+1]
            edge_data = sub_G.get_edge_data(u, v)[0]
            
            total_dist += edge_data.get('length', 0)
            total_eta += edge_data.get('eta_seconds', 0)
            route_coords.append([sub_G.nodes[u]['y'], sub_G.nodes[u]['x']])
            
            # --- LOGIC MỚI: Truy vết xem cạnh này bị phạt vì cái gì ---
            # Lưu ý: Đây là cách kiểm tra nhanh (check lại với list gốc)
            node_u_obj = sub_G.nodes[u]
            node_v_obj = sub_G.nodes[v]
            
            if edge_data.get('risk_details', {}).get('has_disaster'):
                # Quét lại xem trúng disaster nào để lấy tên
                for d in disaster_zones:
                    # Logic kiểm tra đơn giản: Khoảng cách tới tâm
                    dist = standardization.haversine(node_u_obj['y'], node_u_obj['x'], d['geometry'][0]['coordinates'][1], d['geometry'][0]['coordinates'][0])
                    # Nếu gần < 500m thì coi như dính (cho demo)
                    if dist < 0.5: 
                        hit_disasters.add(f"{d['title']} (ID: {d['id']})")

            if edge_data.get('risk_details', {}).get('has_weather'):
                for w in weather_zones:
                    dist = standardization.haversine(node_u_obj['y'], node_u_obj['x'], w['lat'], w['lng'])
                    if dist < w['radius']:
                        hit_weathers.add(f"{w['condition']}: {w['description']}")

        # Thêm điểm cuối
        last_node = route_nodes[-1]
        route_coords.append([sub_G.nodes[last_node]['y'], sub_G.nodes[last_node]['x']])
        
        return {
            "status": "success",
            "distance_km": round(total_dist / 1000, 2),
            "duration_min": round(total_eta / 60, 0),
            "geometry": route_coords,
            "risk_summary": {
                "traffic_level": "High" if traffic_score > 0.7 else "Normal",
                "weather_warning": len(hit_weathers) > 0,
                "disaster_warning": len(hit_disasters) > 0
            },
            # TRẢ VỀ DANH SÁCH CHI TIẾT ĐỂ HIỆN LÊN APP
            "hit_details": {
                "disasters": list(hit_disasters),
                "weathers": list(hit_weathers)
            }
        }
        
    except nx.NetworkXNoPath:
        return {"status": "error", "message": "Không tìm thấy đường đi an toàn."}
    except Exception as e:
        print(f"Lỗi: {e}")
        return {"status": "error", "message": str(e)}