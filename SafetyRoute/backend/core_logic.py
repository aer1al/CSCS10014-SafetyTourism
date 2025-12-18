import networkx as nx
import osmnx as ox
import numpy as np
from datetime import datetime
import warnings
import json
import os
import pickle

# Import các module vệ tinh và chuẩn hóa dữ liệu
import traffic
import weather
import disasters
import standardization 
from standardization import CROWD_ZONES

warnings.filterwarnings("ignore")

# Khởi tạo mô hình đánh giá rủi ro từ file binary (Pickle)
RISK_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'risk_model.pkl')
risk_model = None
try:
    with open(RISK_MODEL_PATH, 'rb') as f:
        risk_model = pickle.load(f)
    print("🤖 [CORE] Đã nạp thành công AI Risk Model!")
except Exception as e:
    print(f"⚠️ [CORE] Không tìm thấy Risk Model ({e}). Sẽ dùng công thức cộng thủ công.")

class RoutingEngine:
    def __init__(self):
        print("🚀 [CORE] Routing Engine khởi động...")

    def get_optimal_routes(self, start_coords, end_coords, vehicle_mode="motorbike", preferences=None):
        if preferences is None: preferences = {}
        print(f"🧩 Bắt đầu xử lý: {vehicle_mode.upper()} | Prefs: {preferences}")

        now = datetime.now()
        curr_hour = now.hour + (now.minute / 60)
        is_weekend = now.weekday() >= 5
        
        # 1. Khởi tạo đồ thị và giới hạn không gian tìm kiếm (Bounding Box)
        graph_data = self._prepare_graph(start_coords, end_coords, vehicle_mode)
        if not graph_data:
            return {"status": "error", "message": "Không tải được bản đồ hoặc điểm đi/đến quá xa."}
            
        sub_G, orig_node, dest_node, bbox = graph_data
        
        # 2. Thực thi quy trình định tuyến (Scan Environment -> Weighting -> Pathfinding)
        return self._process_routing(sub_G, orig_node, dest_node, bbox, curr_hour, is_weekend, vehicle_mode, preferences)

    def _prepare_graph(self, start, end, mode):
        net_type = 'walk' if mode == 'walking' else 'drive'
        G_full = traffic.load_graph_by_mode(net_type)
        if G_full is None: return None

        try:
            orig_node = ox.distance.nearest_nodes(G_full, start[1], start[0])
            dest_node = ox.distance.nearest_nodes(G_full, end[1], end[0])
            orig_point = G_full.nodes[orig_node]
            dest_point = G_full.nodes[dest_node]
        except Exception as e:
            print(f"⚠️ Lỗi tìm node: {e}")
            return None

        # Tính khoảng cách Manhattan để ước lượng vùng đệm
        dist_lat = abs(orig_point['y'] - dest_point['y'])
        dist_lon = abs(orig_point['x'] - dest_point['x'])
        
        # Thiết lập Buffer động: Tối thiểu 500m, tối đa 3km tùy độ dài quãng đường
        # Hệ số 0.5 đảm bảo không gian tìm kiếm đủ rộng cho các đường vòng
        raw_buffer = max(dist_lat, dist_lon) * 0.5
        buffer = max(0.003, min(0.03, raw_buffer))
        
        print(f"✂️ Dynamic Buffer: {buffer:.4f} (cho quãng đường ngắn)")
        north = max(orig_point['y'], dest_point['y']) + buffer
        south = min(orig_point['y'], dest_point['y']) - buffer
        east = max(orig_point['x'], dest_point['x']) + buffer
        west = min(orig_point['x'], dest_point['x']) - buffer
        bbox = (south, west, north, east)

        try:
            nodes_in_bbox = [
                n for n, d in G_full.nodes(data=True) 
                if south < d['y'] < north and west < d['x'] < east
            ]
            # Tạo Subgraph để tối ưu hóa hiệu năng tính toán
            sub_G = G_full.subgraph(nodes_in_bbox).copy()
            if orig_node not in sub_G.nodes or dest_node not in sub_G.nodes:
                return G_full, orig_node, dest_node, bbox
            return sub_G, orig_node, dest_node, bbox
        except:
            return G_full, orig_node, dest_node, bbox

    def _scan_environment(self, bbox):
        """
        Thu thập dữ liệu môi trường không gian trong vùng BBox.
        Phục vụ tính toán trọng số và hiển thị minh chứng trên Frontend.
        """
        south, west, north, east = bbox
        
        # 1. Thu thập dữ liệu Thiên tai
        raw_disasters = []
        
        # Ưu tiên nạp dữ liệu từ Local Cache
        if os.path.exists('real_disasters.json'):
            try:
                with open('real_disasters.json', 'r', encoding='utf-8') as f:
                    raw_disasters = json.load(f)
            except: pass
            
        # Fallback sang Mock API nếu không có cache (bán kính 50km)
        if not raw_disasters:
            mid_lat, mid_lng = (south+north)/2, (west+east)/2
            # Lưu ý: Hàm trả về toàn bộ dữ liệu trong bán kính quét
            raw_disasters = disasters.get_natural_disasters(mid_lat, mid_lng, max_distance_km=50)

        # Lọc dữ liệu theo tọa độ hình chữ nhật (Spatial Filtering/Clipping)
        # Chỉ giữ lại các điểm rủi ro nằm trong BBox
        disaster_zones = [
            d for d in raw_disasters
            if south <= d['lat'] <= north and west <= d['lng'] <= east
        ]

        # 2. Truy xuất lưới dữ liệu Thời tiết (Realtime Grid)
        weather_zones = weather.get_weather_zones(bbox) 

        # 3. Truy xuất dữ liệu Mật độ đám đông
        crowd_zones = [
            c for c in CROWD_ZONES 
            if south < c['lat'] < north and west < c['lng'] < east
        ]

        print(f"📦 Môi trường trong hộp: {len(disaster_zones)} Disaster | {len(weather_zones)} Weather | {len(crowd_zones)} Crowd")
        
        return {
            "disasters": disaster_zones,
            "weather": weather_zones,
            "crowd": crowd_zones
        }

    def _calculate_weights(self, sub_G, env_data, curr_hour, is_weekend, vehicle_mode, preferences):
        # Giữ nguyên logic tính toán trọng số
        
        print(f"⚖️ Đang tính trọng số cho {sub_G.number_of_edges()} cạnh...")
        base_traffic_score = standardization.calculate_traffic_score(curr_hour, is_weekend, weather_score=0.0)
        # Tạo Spatial Index (R-tree) để tăng tốc độ truy vấn va chạm
        disaster_idx = standardization.create_spatial_index(env_data['disasters'])
        weather_idx  = standardization.create_spatial_index(env_data['weather'])
        
        def clip(val): return max(0.0, min(2.0, float(val)))
        uf_disaster = clip(preferences.get('disaster', 1.0))
        uf_weather  = clip(preferences.get('weather', 1.0))
        uf_crowd    = clip(preferences.get('crowd', 1.0))
        uf_traffic  = clip(preferences.get('traffic', 1.0))

        edge_pointers = []
        ai_inputs = []

        for u, v, data in sub_G.edges(data=True):
            node_u, node_v = sub_G.nodes[u], sub_G.nodes[v]
            edge_bbox = (min(node_u['x'], node_v['x']), min(node_u['y'], node_v['y']), max(node_u['x'], node_v['x']), max(node_u['y'], node_v['y']))
            
            s_disaster = 0
            pot_d = list(disaster_idx.intersection(edge_bbox))
            if pot_d: s_disaster = standardization.calculate_disaster_impact_advanced(data, node_u, node_v, [env_data['disasters'][i] for i in pot_d])

            s_weather = 0
            pot_w = list(weather_idx.intersection(edge_bbox))
            if pot_w: s_weather = standardization.calculate_weather_impact_geometry(data, node_u, node_v, [env_data['weather'][i] for i in pot_w])

            mid_lat, mid_lon = (node_u['y'] + node_v['y']) / 2, (node_u['x'] + node_v['x']) / 2
            s_crowd = standardization.calculate_crowd_score(mid_lat, mid_lon, curr_hour)

            # Luật phạt: Phương tiện lớn đi vào đường hẹp (Residential/Living street)
            hw = data.get('highway', '')
            if vehicle_mode in ['car', 'bus', 'truck'] and hw in ['residential', 'living_street']:
                s_crowd += 5.0

            ai_inputs.append([s_disaster * uf_disaster, s_weather * uf_weather, s_crowd * uf_crowd])
            edge_pointers.append(data)
            data['scores_real'] = (s_disaster, s_weather, s_crowd)

        # Dự đoán rủi ro (Risk Prediction)
        preds = []
        if risk_model and ai_inputs:
            try: preds = risk_model.predict(ai_inputs)
            except: preds = [(x[0]*1000 + x[1]*30 + x[2]*5) for x in ai_inputs]
        else: preds = [(x[0]*1000 + x[1]*30 + x[2]*5) for x in ai_inputs]

        for i, data in enumerate(edge_pointers):
            penalty = float(max(0.0, preds[i]))
            
            # Truy xuất các điểm số thành phần
            s_d, s_w, s_c = data['scores_real'] 
            
            # Tính điểm giao thông (Traffic Score) ngay tại thời điểm xử lý
            raw_traffic_score = standardization.calculate_traffic_score(curr_hour, is_weekend, s_w)

            # Tính lại ETA dựa trên vận tốc thực tế (đã giảm do rủi ro)
            real_speed = standardization.calculate_segment_speed(data, curr_hour, is_weekend, s_w, vehicle_mode)
            eta = data.get('length', 10) / (real_speed / 3.6)
            
            # Gán trọng số cuối cùng dùng cho thuật toán Dijkstra
            data['final_weight'] = eta * (1.0 + penalty)
            
            # Lưu Metadata phục vụ quá trình Audit tuyến đường
            data['meta_info'] = {
                'eta': eta, 
                'penalty': penalty,
                'risk_flags': {'disaster': s_d > 0, 'weather': s_w > 0, 'crowd': s_c > 0.7},
                'raw_traffic': raw_traffic_score, 
                'raw_crowd': s_c
            }
            
            # Giải phóng bộ nhớ biến tạm
            if 'scores_real' in data:
                del data['scores_real']

    def _process_routing(self, sub_G, orig_node, dest_node, bbox, curr_hour, is_weekend, vehicle_mode, preferences):
        # 1. Quét môi trường lấy dữ liệu minh chứng
        env_data = self._scan_environment(bbox)
        
        # 2. Tính toán trọng số cho toàn bộ đồ thị
        self._calculate_weights(sub_G, env_data, curr_hour, is_weekend, vehicle_mode, preferences)
        
        # 3. Tìm Top-K lộ trình tối ưu (K=3)
        routes_found = []
        labels = ["Best Route", "Alternative 1", "Alternative 2"] # Định danh tuyến đường
        
        for i in range(3): 
            try:
                # Tìm đường ngắn nhất trên đồ thị có trọng số
                path = nx.shortest_path(sub_G, orig_node, dest_node, weight='final_weight')
                
                # Kiểm tra trùng lặp lộ trình dựa trên độ dài và node trung gian
                is_duplicate = False
                for existing in routes_found:
                    if len(path) == len(existing['geometry']) and path[len(path)//2] == existing['_mid_node']:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    # Audit lộ trình: Tính tổng rủi ro và gán nhãn
                    route_info = self._audit_route(sub_G, path, env_data, labels[len(routes_found)])
                    route_info['_mid_node'] = path[len(path)//2] # Lưu node giữa để check trùng
                    routes_found.append(route_info)
                
                # Cơ chế phạt trọng số (Penalty) để tìm các đường thay thế
                # Tăng trọng số các cạnh đã đi qua lên 300% để ép thuật toán tìm hướng khác
                for k in range(len(path) - 1):
                    u, v = path[k], path[k+1]
                    if sub_G.has_edge(u, v):
                        for key in sub_G[u][v]:
                            sub_G[u][v][key]['final_weight'] *= 3.0 
                            
            except nx.NetworkXNoPath:
                break 
            except Exception as e:
                print(f"Lỗi tìm đường phụ {i}: {e}")
                break
                
            if len(routes_found) >= 3: break

        if not routes_found:
             return {"status": "error", "message": "Không tìm thấy đường đi an toàn."}
             
        # 4. Đóng gói kết quả trả về kèm dữ liệu bản đồ
        return {
            **routes_found[0], # Thông tin đường tối ưu nhất
            "alternatives": routes_found[1:], # Danh sách đường phụ
            "map_data": { # Dữ liệu minh chứng cho Frontend vẽ lớp phủ
                "disasters": env_data['disasters'],
                "weather": env_data['weather'],
                "crowd": env_data['crowd'],
                "bbox": bbox 
            }
        }

    def _audit_route(self, G, route_nodes, env_data, route_name="Route"):
        total_dist = 0
        total_eta = 0
        total_risk = 0
        path_coords = []
        
        hit_disasters = set()
        hit_weathers = set()
        hit_traffic = set()
        
        # Biến tích lũy dùng tính trung bình trọng số
        sum_traffic_score = 0
        sum_crowd_score = 0
        
        for i in range(len(route_nodes) - 1):
            u, v = route_nodes[i], route_nodes[i+1]
            data = G.get_edge_data(u, v)[0]
            meta = data.get('meta_info', {})
            length = data.get('length', 10)
            
            total_dist += length
            total_eta += meta.get('eta', 0)
            total_risk += (meta.get('penalty',0) * length)
            
            # Tích lũy điểm số theo độ dài đoạn đường
            t_score = meta.get('raw_traffic', 0.1)
            c_score = meta.get('raw_crowd', 0.0)
            
            sum_traffic_score += (t_score * length)
            sum_crowd_score += (c_score * length)

            path_coords.append([G.nodes[u]['y'], G.nodes[u]['x']])
            
            flags = meta.get('risk_flags', {})
            if flags.get('disaster'): hit_disasters.add("Vùng nguy hiểm")
            if flags.get('weather'): hit_weathers.add("Mưa/Gió")
            if t_score > 0.6: hit_traffic.add("Kẹt xe") 

        path_coords.append([G.nodes[route_nodes[-1]]['y'], G.nodes[route_nodes[-1]]['x']])
        
        # Phân loại mức độ (Classification: Low/Medium/High)
        avg_traffic = sum_traffic_score / total_dist if total_dist > 0 else 0
        avg_crowd = sum_crowd_score / total_dist if total_dist > 0 else 0
        
        def get_level_label(score):
            if score >= 0.7: return "High"
            if score >= 0.4: return "Medium"
            return "Low"

        risk_summary = {
            "traffic_level": get_level_label(avg_traffic),
            "crowd_level": get_level_label(avg_crowd)
        }
        
        # Bản đồ ánh xạ nhãn hiển thị tiếng Việt
        vn_map = {
            "High": "Cao",
            "Medium": "Trung bình",
            "Low": "Thấp"
        }

        safety_label = "🟢 An toàn"
        safety_color = "green"
        
        if len(hit_disasters) > 0: 
            safety_label = "🔴 NGUY HIỂM"
            safety_color = "red"
        elif len(hit_weathers) > 0:
            safety_label = "🟡 Mưa/Thời tiết xấu"
            safety_color = "yellow"
        elif risk_summary["traffic_level"] == "High": 
            safety_label = "🟠 Kẹt xe nghiêm trọng"
            safety_color = "orange"

        return {
            "name": route_name,
            "geometry": path_coords,
            "distance_km": round(total_dist/1000, 2),
            "duration_min": round(total_eta/60),
            "summary": {
                "safety_label": safety_label,
                "safety_color": safety_color,
                "description": f"Lộ trình {risk_summary['traffic_level']} kẹt xe, {risk_summary['crowd_level']} đông đúc.",
                "avoidance_proof": f"Đã né {len(hit_disasters)} điểm thiên tai" if hit_disasters else "",
                "description": f"Kẹt xe mức {vn_map[risk_summary['traffic_level']]}, đám đông mức {vn_map[risk_summary['crowd_level']]}."
            },
            # Dữ liệu phục vụ hiển thị Badge UI
            "risk_summary": risk_summary, 
            "hit_details": {
                "disasters": list(hit_disasters),
                "weathers": list(hit_weathers),
                "traffic": list(hit_traffic)
            }
        }
engine = RoutingEngine()
def get_optimal_routes(start, end, vehicle_mode="walking", preferences=None):
    return engine.get_optimal_routes(start, end, vehicle_mode, preferences)
