import networkx as nx
import osmnx as ox
from datetime import datetime
from rtree import index
import pickle
import os
import numpy as np
import warnings

# Tắt cảnh báo sklearn spam
warnings.filterwarnings("ignore")

# Import các module vệ tinh
from traffic import SYSTEM_GRAPH as G
from weather import get_mock_weather_zones
from disasters import get_natural_disasters
import standardization 
from standardization import CROWD_ZONES

# --- AI LOADER ---
RISK_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'risk_model.pkl')
risk_model = None

try:
    with open(RISK_MODEL_PATH, 'rb') as f:
        risk_model = pickle.load(f)
    print("🤖 [CORE] Đã nạp Risk Model (Batch Processing Mode)!")
except Exception as e:
    print(f"⚠️ [CORE] Không tìm thấy Risk Model ({e}).")

# -----------------------------

def create_spatial_index(zones):
    idx = index.Index()
    for i, zone in enumerate(zones):
        lat, lng = zone['lat'], zone['lng']
        radius_km = zone.get('radius', 5.0)
        delta_deg = (radius_km / 111.0) * 1.2 
        bbox = (lng - delta_deg, lat - delta_deg, lng + delta_deg, lat + delta_deg)
        idx.insert(i, bbox)
    return idx

def get_optimal_routes(start_coords, end_coords):
    print(f"🚀 Bắt đầu tìm đường (Mode: Manual Pruning)...")
    
    # ==========================================
    # 1. GATHER DATA
    # ==========================================
    now = datetime.now()
    curr_hour = now.hour + (now.minute / 60)
    is_weekend = now.weekday() >= 5
    
    disaster_zones = get_natural_disasters(start_coords[0], start_coords[1])
    weather_zones = get_mock_weather_zones()
    
    # 🔥 [FIX] Tính điểm Traffic chung cho toàn thành phố ngay tại đây
    # (Đổi tên từ base_traffic_score -> traffic_score để dùng xuyên suốt)
    traffic_score = standardization.calculate_traffic_score(curr_hour, is_weekend, weather_score=0.0)
    
    disaster_idx = create_spatial_index(disaster_zones)
    weather_idx = create_spatial_index(weather_zones)

    # ==========================================
    # 2. PRUNING (Cắt bản đồ)
    # ==========================================
    orig_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    dest_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
    orig_point, dest_point = G.nodes[orig_node], G.nodes[dest_node]
    
    buffer = 0.03 
    north = max(orig_point['y'], dest_point['y']) + buffer
    south = min(orig_point['y'], dest_point['y']) - buffer
    east = max(orig_point['x'], dest_point['x']) + buffer
    west = min(orig_point['x'], dest_point['x']) - buffer
    
    print(f"✂️ Đang cắt bản đồ & lọc dữ liệu: N={north:.2f}, S={south:.2f}...")

    # Lọc dữ liệu hiển thị (Map Data)
    scanned_data = {
        "disasters": [d for d in disaster_zones if south < d['lat'] < north and west < d['lng'] < east],
        "weather": [w for w in weather_zones if south < w['lat'] < north and west < w['lng'] < east],
        "crowd": [c for c in CROWD_ZONES if south < c['lat'] < north and west < c['lng'] < east]
    }
    
    print(f"📦 Dữ liệu trong vùng quét: {len(scanned_data['disasters'])} disasters, {len(scanned_data['weather'])} weather, {len(scanned_data['crowd'])} crowd.")

    # Cắt Map Thủ Công (Manual Slicing)
    try:
        nodes_in_bbox = [
            n for n, d in G.nodes(data=True) 
            if south < d['y'] < north and west < d['x'] < east
        ]
        sub_G = G.subgraph(nodes_in_bbox).copy()
        
        if orig_node not in sub_G.nodes: sub_G = G.copy()
        elif dest_node not in sub_G.nodes: sub_G = G.copy()
            
    except Exception as e:
        print(f"⚠️ Lỗi cắt thủ công ({e}), dùng Full Graph.")
        sub_G = G.copy()

    # ==========================================
    # 3. BATCH PROCESSING
    # ==========================================
    print(f"🔄 Đang xử lý {sub_G.number_of_edges()} cạnh...")

    edge_pointers = []
    ai_inputs = []     
    
    for u, v, data in sub_G.edges(data=True):
        node_u, node_v = sub_G.nodes[u], sub_G.nodes[v]
        edge_bbox = (min(node_u['x'], node_v['x']), min(node_u['y'], node_v['y']), 
                     max(node_u['x'], node_v['x']), max(node_u['y'], node_v['y']))

        # 1. Disaster
        s_disaster = 0
        if len(disaster_zones) > 0:
            indices = list(disaster_idx.intersection(edge_bbox))
            if indices:
                relevant = [disaster_zones[i] for i in indices]
                s_disaster = standardization.calculate_disaster_impact_advanced(data, node_u, node_v, relevant)

        # 2. Weather
        s_weather = 0
        if len(weather_zones) > 0:
            indices = list(weather_idx.intersection(edge_bbox))
            if indices:
                relevant = [weather_zones[i] for i in indices]
                s_weather = standardization.calculate_weather_impact_geometry(data, node_u, node_v, relevant)

        # 3. Crowd
        mid_lat, mid_lon = (node_u['y'] + node_v['y']) / 2, (node_u['x'] + node_v['x']) / 2
        s_crowd = standardization.calculate_crowd_score(mid_lat, mid_lon, curr_hour)
        
        edge_pointers.append(data)
        ai_inputs.append([s_disaster, s_weather, s_crowd])
        data['temp_scores'] = (s_disaster, s_weather, s_crowd)

    # Batch Prediction
    predicted_penalties = []
    if risk_model and len(ai_inputs) > 0:
        try:
            predicted_penalties = risk_model.predict(ai_inputs)
        except:
            predicted_penalties = [(x[0]*1000 + x[1]*30 + x[2]*5) for x in ai_inputs]
    else:
        predicted_penalties = [(x[0]*1000 + x[1]*30 + x[2]*5) for x in ai_inputs]

    # Update Graph & Calculate Dynamic ETA
    for i, data in enumerate(edge_pointers):
        penalty = float(max(0.0, predicted_penalties[i]))
        s_disaster, s_weather, s_crowd = data['temp_scores']
        length_m = data.get('length', 10)
        
        # Tính Traffic Score cục bộ (Local) dựa trên điểm chung + thời tiết riêng
        # (Dùng biến traffic_score đã tính ở đầu hàm)
        local_traffic_score = traffic_score 
        if s_weather > 0: 
            local_traffic_score = min(1.0, traffic_score + 0.2)
            
        max_speed = 30.0
        try:
            raw_ms = data.get('maxspeed', 30)
            if isinstance(raw_ms, list): raw_ms = raw_ms[0]
            max_speed = float(raw_ms)
        except: pass
        
        efficiency = 1.0 - (local_traffic_score * 0.8)
        real_speed_ms = max(1.0, (max_speed * efficiency) / 3.6)
        
        eta_seconds = length_m / real_speed_ms
        data['final_weight'] = eta_seconds * (1.0 + penalty)
        data['meta_info'] = {
            'eta': eta_seconds, 'penalty': penalty,
            'risk_flags': {'disaster': s_disaster > 0, 'weather': s_weather > 0, 'crowd': s_crowd > 0.7}
        }
        del data['temp_scores']

    # ==========================================
    # 4. PATHFINDING & FINAL OUTPUT
    # ==========================================
    try:
        route_nodes = nx.shortest_path(sub_G, orig_node, dest_node, weight='final_weight')
        
        total_dist_m = 0
        total_eta_s = 0
        total_weighted_risk = 0
        max_segment_risk = 0
        hit_disasters = set()
        hit_weathers = set()
        crowd_count = 0
        route_coords = []

        # Traceback Loop
        for i in range(len(route_nodes) - 1):
            u, v = route_nodes[i], route_nodes[i+1]
            edge = sub_G.get_edge_data(u, v)[0]
            meta = edge.get('meta_info', {})
            length = edge.get('length', 10)
            
            total_dist_m += length
            total_eta_s += meta.get('eta', 0)
            
            p = meta.get('penalty', 0)
            total_weighted_risk += (p * length)
            max_segment_risk = max(max_segment_risk, p)
            
            route_coords.append([sub_G.nodes[u]['y'], sub_G.nodes[u]['x']])
            
            flags = meta.get('risk_flags', {})
            if flags.get('crowd'): crowd_count += 1
            
            # Check chi tiết để lấy tên hiển thị
            if flags.get('disaster'):
                node_obj = sub_G.nodes[u]
                for d in disaster_zones:
                    if standardization.haversine(node_obj['y'], node_obj['x'], d['lat'], d['lng']) <= (d.get('radius',5)+1):
                        hit_disasters.add(d.get('title', 'Thiên tai'))
            if flags.get('weather'):
                node_obj = sub_G.nodes[u]
                for w in weather_zones:
                     if standardization.haversine(node_obj['y'], node_obj['x'], w['lat'], w['lng']) <= (w.get('radius',5)+1):
                        hit_weathers.add(f"{w.get('condition')} ({w.get('description')})")

        # Add điểm cuối
        route_coords.append([sub_G.nodes[route_nodes[-1]]['y'], sub_G.nodes[route_nodes[-1]]['x']])
        
        # --- FORCE CHECK: KIỂM TRA ĐIỂM ĐẦU/CUỐI ---
        # (Chống lọt lưới khi đứng trong tâm bão)
        for d in disaster_zones:
            d_start = standardization.haversine(start_coords[0], start_coords[1], d['lat'], d['lng'])
            d_end = standardization.haversine(end_coords[0], end_coords[1], d['lat'], d['lng'])
            if d_start <= (d.get('radius', 5)+0.1) or d_end <= (d.get('radius', 5)+0.1):
                hit_disasters.add(f"{d.get('title')} (Tại điểm dừng)")

        # --- SUMMARY METRICS ---
        final_eta_min = round((total_eta_s * 1.15) / 60)
        final_dist_km = round(total_dist_m / 1000, 2)
        avg_risk_score = total_weighted_risk / total_dist_m if total_dist_m > 0 else 0
        
        safety_label = "🟢 An toàn"
        safety_color = "green"
        reasons = []

        if len(hit_disasters) > 0:
            safety_label = "🔴 CỰC KỲ NGUY HIỂM"
            safety_color = "red"
            reasons.append(f"⛔ Đi qua {len(hit_disasters)} điểm thiên tai!")
            avg_risk_score = 100.0
        elif max_segment_risk > 20.0:
            safety_label = "🔴 Nguy hiểm"
            safety_color = "red"
            reasons.append("⚠️ Có đoạn rủi ro rất cao")
        elif len(hit_weathers) > 0 or (crowd_count / len(route_nodes) > 0.3):
            safety_label = "🟡 Cẩn trọng"
            safety_color = "yellow"
            if len(hit_weathers) > 0: reasons.append(f"🌧️ Có {len(hit_weathers)} vùng thời tiết xấu")
            if crowd_count > 0: reasons.append("👥 Mật độ giao thông khá đông")
            
        description = "Lộ trình thuận lợi." if not reasons else " | ".join(reasons)

        # 🔥 [FIXED] TÍNH TOÁN STATUS TRAFFIC & CROWD (3 CẤP ĐỘ)
        # Bây giờ traffic_score đã được define ở đầu hàm, không bị lỗi nữa
        if traffic_score <= 0.4: traffic_status = "Low"
        elif traffic_score <= 0.7: traffic_status = "Medium"
        else: traffic_status = "High"

        if crowd_count == 0: crowd_status = "Low"
        elif crowd_count <= 2: crowd_status = "Medium"
        else: crowd_status = "High"

        return {
            "status": "success",
            "distance_km": final_dist_km,
            "duration_min": final_eta_min,
            "summary": {
                "safety_label": safety_label,
                "safety_color": safety_color,
                "description": description,
                "eta_display": f"{final_eta_min // 60}h {final_eta_min % 60}p" if final_eta_min > 60 else f"{final_eta_min} phút"
            },
            "risk_summary": {
                "traffic_level": traffic_status,
                "crowd_level": crowd_status
            },
            "metrics": {
                "avg_risk_score": round(avg_risk_score, 2),
                "max_segment_risk": round(max_segment_risk, 2)
            },
            "geometry": route_coords,
            "hit_details": {
                "disasters": list(hit_disasters),
                "weathers": list(hit_weathers)
            },
            "map_data": scanned_data
        }

    except nx.NetworkXNoPath:
        return {"status": "error", "message": "Không tìm thấy đường đi an toàn."}
    except Exception as e:
        return {"status": "error", "message": str(e)}