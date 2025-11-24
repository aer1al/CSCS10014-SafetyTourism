import networkx as nx
import osmnx as ox
from datetime import datetime

# Import các module vệ tinh
from traffic import SYSTEM_GRAPH as G
from weather import get_mock_weather_zones
from disasters import get_natural_disasters
import standardization 

# Tốc độ trung bình giả định (km/h) trong thành phố
BASE_SPEED_KMH = 30.0 

def get_optimal_routes(start_coords, end_coords, preference="balanced"):
    """
    Hàm tìm đường thông minh Safety Tourism.
    """
    print(f"🚀 Bắt đầu tìm đường: {preference}...")
    
    # ==========================================
    # 1. GATHER DATA (Thu thập dữ liệu)
    # ==========================================
    now = datetime.now()
    curr_hour = now.hour + (now.minute / 60)
    is_weekend = now.weekday() >= 5
    
    # Lấy dữ liệu vùng rủi ro (Hình học)
    disaster_zones = get_natural_disasters(start_coords[0], start_coords[1])
    weather_zones = get_mock_weather_zones() # Mock Weather Zones
    
    # Lấy điểm kẹt xe chung (Dùng cho ETA)
    traffic_score = standardization.calculate_traffic_score(curr_hour, is_weekend)
    
    print(f"   - Giờ: {curr_hour:.1f} | Traffic Score: {traffic_score}")
    print(f"   - Disaster Zones: {len(disaster_zones)} | Weather Zones: {len(weather_zones)}")

    # ==========================================
    # 2. DUYỆT CẠNH & TÍNH TOÁN (LOOP)
    # ==========================================
    
    # Cấu hình hệ số ưu tiên (Weights) cho thuật toán Dijkstra
    w_disaster = 1000.0 # Cực sợ chết -> Né tuyệt đối
    w_weather = 50.0    # Sợ ướt -> Né mạnh
    w_crowd = 5.0       # Sợ đông -> Né vừa vừa
    
    if preference == "fastest":
        # Nếu cần nhanh, giảm sợ hãi xuống để chấp nhận đi đường ngắn
        w_weather = 10.0
        w_crowd = 0.0
    
    for u, v, data in G.edges(data=True):
        length_m = data.get('length', 10)
        
        # Lấy thông tin Node đầu/cuối
        node_u = G.nodes[u]
        node_v = G.nodes[v]
        
        # --- A. TÍNH SAFETY SCORE (Disaster + Weather) ---
        # Gọi hàm check cắt ngang vùng hình học
        s_disaster = standardization.calculate_disaster_impact_advanced(
            data, node_u, node_v, disaster_zones
        )
        s_weather = standardization.calculate_weather_impact_geometry(
            data, node_u, node_v, weather_zones
        )
        
        # --- B. TÍNH CROWD SCORE ---
        # Lấy trung điểm cạnh để check điểm nóng
        mid_lat = (node_u['y'] + node_v['y']) / 2
        mid_lon = (node_u['x'] + node_v['x']) / 2
        s_crowd = standardization.calculate_crowd_score(mid_lat, mid_lon, curr_hour)
        
        # --- C. TÍNH TRỌNG SỐ DIJKSTRA (Routing Weight) ---
        # Mục tiêu: Tìm đường đi.
        # Công thức: Length * (1 + Phạt)
        
        penalty = (w_disaster * s_disaster) + \
                  (w_weather * s_weather) + \
                  (w_crowd * s_crowd)
                  
        dijkstra_weight = length_m * (1 + penalty)
        
        # Gán vào cạnh để thuật toán dùng
        data['final_weight'] = dijkstra_weight
        
        # --- D. TÍNH ETA (Estimated Time) ---
        # Mục tiêu: Hiển thị cho user biết đi mất bao lâu.
        # Logic: Tốc độ giảm đi nếu Traffic cao hoặc Weather xấu
        
        # 1. Giảm tốc do kẹt xe (Traffic Score 1.0 -> Tốc độ giảm 60%)
        speed_factor_traffic = 1.0 - (traffic_score * 0.6) 
        
        # 2. Giảm tốc do mưa (Weather Score 1.0 -> Tốc độ giảm thêm 20%)
        # (Lưu ý: s_weather ở đây là điểm cắt ngang vùng mưa)
        speed_factor_weather = 1.0 - (s_weather * 0.2)
        
        # Tốc độ thực tế (m/s)
        real_speed_kmh = BASE_SPEED_KMH * speed_factor_traffic * speed_factor_weather
        real_speed_ms = max(real_speed_kmh / 3.6, 1.0) # Tối thiểu 1m/s
        
        eta_seconds = length_m / real_speed_ms
        data['eta_seconds'] = eta_seconds

    # ==========================================
    # 3. CHẠY THUẬT TOÁN (ROUTING)
    # ==========================================
    orig_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    dest_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
    
    try:
        # Tìm đường ngắn nhất theo trọng số đã tính
        route_nodes = nx.shortest_path(G, orig_node, dest_node, weight='final_weight')
        
        # Tính tổng kết quả trả về
        total_dist = 0
        total_eta = 0
        route_coords = []
        
        for i in range(len(route_nodes) - 1):
            u = route_nodes[i]
            v = route_nodes[i+1]
            # Lấy dữ liệu cạnh đã tính toán
            edge_data = G.get_edge_data(u, v)[0]
            
            total_dist += edge_data.get('length', 0)
            total_eta += edge_data.get('eta_seconds', 0)
            
            # Lấy tọa độ điểm u để vẽ
            route_coords.append([G.nodes[u]['y'], G.nodes[u]['x']])
            
        # Thêm điểm cuối cùng
        last_node = route_nodes[-1]
        route_coords.append([G.nodes[last_node]['y'], G.nodes[last_node]['x']])
        
        return {
            "status": "success",
            "preference": preference,
            "distance_km": round(total_dist / 1000, 2),
            "duration_min": round(total_eta / 60, 0),
            "geometry": route_coords,
            "risk_info": {
                "traffic_level": "High" if traffic_score > 0.7 else "Normal",
                "weather_warning": len(weather_zones) > 0,
                "disaster_warning": len(disaster_zones) > 0
            }
        }
        
    except nx.NetworkXNoPath:
        return {"status": "error", "message": "Không tìm thấy đường đi an toàn."}
    except Exception as e:
        print(f"Lỗi Core Logic: {e}")
        return {"status": "error", "message": str(e)}