# file: core_logic.py (PHẦN 1)
import networkx as nx
import osmnx as ox
import numpy as np
from datetime import datetime
import warnings
import json    # <--- BẠN ĐANG THIẾU DÒNG NÀY
import os      # <--- Cần cái này để xử lý đường dẫn file
import pickle  # <--- Cần cái này để load AI Model

# Import các module vệ tinh (Đã chuẩn bị trước đó)
import traffic
import weather
import disasters
import standardization 
from standardization import CROWD_ZONES

# Tắt cảnh báo
warnings.filterwarnings("ignore")

# 🔥 [FIX] LOAD RISK MODEL TẠI ĐÂY (GLOBAL SCOPE)
# Để đảm bảo nó được load 1 lần duy nhất khi server chạy
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
        """
        Khởi tạo bộ máy tìm đường.
        Load sẵn các model hoặc dữ liệu tĩnh nếu cần.
        """
        print("🚀 [CORE] Routing Engine khởi động...")
        # Có thể load thêm cache ở đây nếu cần tối ưu cực đại

    def get_optimal_routes(self, start_coords, end_coords, vehicle_mode="motorbike", preferences=None):
        """
        Hàm chính (Public Interface) để gọi từ bên ngoài.
        """
        if preferences is None: preferences = {}
        
        print(f"🧩 Bắt đầu xử lý: {vehicle_mode.upper()} | Prefs: {preferences}")

        # 1. Chuẩn bị dữ liệu thời gian
        now = datetime.now()
        curr_hour = now.hour + (now.minute / 60)
        is_weekend = now.weekday() >= 5
        
        # 2. Xử lý bản đồ (Graph Management)
        # Hàm này sẽ trả về: Đồ thị con (sub_G), và các node đầu/cuối
        graph_data = self._prepare_graph(start_coords, end_coords, vehicle_mode)
        
        if not graph_data:
            return {"status": "error", "message": "Không tải được bản đồ hoặc điểm đi/đến quá xa."}
            
        sub_G, orig_node, dest_node, bbox = graph_data
        
        # ... (Các bước tiếp theo sẽ code ở Phần 2 & 3) ...
        # Tạm thời return để test code chạy được không
        return self._process_routing(sub_G, orig_node, dest_node, bbox, curr_hour, is_weekend, vehicle_mode, preferences)

    def _prepare_graph(self, start, end, mode):
        """
        PRIVATE: Chọn bản đồ, cắt Bounding Box (Pruning) và lọc cạnh.
        """
        # A. Chọn loại bản đồ
        net_type = 'walk' if mode == 'walking' else 'drive'
        G_full = traffic.load_graph_by_mode(net_type)
        
        if G_full is None: return None

        # B. Tìm Node gần nhất
        try:
            orig_node = ox.distance.nearest_nodes(G_full, start[1], start[0])
            dest_node = ox.distance.nearest_nodes(G_full, end[1], end[0])
            
            orig_point = G_full.nodes[orig_node]
            dest_point = G_full.nodes[dest_node]
        except Exception as e:
            print(f"⚠️ Lỗi tìm node: {e}")
            return None

        # C. Cắt Bounding Box (Kỹ thuật Pruning)
        # Buffer 0.03 độ (~3km) để có không gian đi vòng
        buffer = 0.03 
        north = max(orig_point['y'], dest_point['y']) + buffer
        south = min(orig_point['y'], dest_point['y']) - buffer
        east = max(orig_point['x'], dest_point['x']) + buffer
        west = min(orig_point['x'], dest_point['x']) - buffer
        
        # Lưu bbox lại để dùng cho bước quét môi trường
        bbox = (south, west, north, east)

        print(f"✂️ Đang cắt bản đồ trong vùng: {bbox}")

        try:
            # Cắt thủ công (An toàn nhất, không lo lỗi thư viện)
            nodes_in_bbox = [
                n for n, d in G_full.nodes(data=True) 
                if south < d['y'] < north and west < d['x'] < east
            ]
            
            # Tạo đồ thị con (Subgraph)
            sub_G = G_full.subgraph(nodes_in_bbox).copy()
            
            # Fallback: Nếu cắt lẹm mất điểm đầu/cuối thì dùng Full Graph
            if orig_node not in sub_G.nodes or dest_node not in sub_G.nodes:
                print("⚠️ Cắt map bị lẹm, dùng Full Graph.")
                return G_full, orig_node, dest_node, bbox
                
            return sub_G, orig_node, dest_node, bbox

        except Exception as e:
            print(f"⚠️ Lỗi cắt map: {e}")
            return G_full, orig_node, dest_node, bbox
        
        # ... (Tiếp theo của class RoutingEngine) ...

    def _scan_environment(self, bbox):
        """
        PRIVATE: Quét dữ liệu môi trường trong vùng Bounding Box.
        Input: bbox (south, west, north, east)
        Output: Dictionary chứa 3 list rủi ro đã lọc.
        """
        south, west, north, east = bbox
        
        # 1. Lấy Thiên Tai (Bão/Lũ) - Load từ file real_disasters.json
        # (File này do script update_disasters.py tạo ra)
        disaster_zones = []
        try:
            with open('real_disasters.json', 'r', encoding='utf-8') as f:
                all_disasters = json.load(f)
                # Lọc sơ bộ (nếu cần tối ưu thêm)
                disaster_zones = all_disasters
        except:
            # Nếu không có file thật thì dùng Mock
            disaster_zones = disasters.get_natural_disasters(0, 0, max_distance_km=9999)

        # 2. Lấy Thời Tiết (Mưa/Gió) - Quét lưới API Open-Meteo
        # Gọi weather.py để lấy các điểm mưa trong hộp
        # (Mở rộng hộp ra 0.1 độ để không sót mép)
        scan_bbox = (south - 0.1, west - 0.1, north + 0.1, east + 0.1)
        weather_zones = weather.get_realtime_weather_zones(scan_bbox)
        
        if not weather_zones:
            weather_zones = weather.get_mock_weather_zones()

        # 3. Lấy Đám Đông (Chợ/Trường) - Lọc từ biến toàn cục
        # (Biến CROWD_ZONES đã được import từ standardization)
        crowd_zones = [
            c for c in CROWD_ZONES 
            if south < c['lat'] < north and west < c['lng'] < east
        ]

        print(f"📦 Môi trường: {len(disaster_zones)} Disaster | {len(weather_zones)} Weather | {len(crowd_zones)} Crowd")
        
        return {
            "disasters": disaster_zones,
            "weather": weather_zones,
            "crowd": crowd_zones
        }

    def _calculate_weights(self, sub_G, env_data, curr_hour, is_weekend, vehicle_mode, preferences):
        """
        PRIVATE: Duyệt qua từng cạnh và tính toán Trọng số (Weight).
        Đây là bước áp dụng AI và công thức động.
        """
        print(f"⚖️ Đang tính trọng số cho {sub_G.number_of_edges()} cạnh...")
        
        # 1. Chuẩn bị AI & Chỉ số
        # Gọi standardization để lấy chỉ số Traffic chung (Base)
        base_traffic_score = standardization.calculate_traffic_score(curr_hour, is_weekend, weather_score=0.0)
        
        # Tạo index không gian cho Disaster & Weather (để check giao cắt nhanh)
        disaster_idx = standardization.create_spatial_index(env_data['disasters'])
        weather_idx  = standardization.create_spatial_index(env_data['weather'])
        
        # Xử lý Preference (Kẹp giá trị an toàn)
        def clip(val): return max(0.0, min(2.0, float(val)))
        
        uf_disaster = clip(preferences.get('disaster', 1.0))
        uf_weather  = clip(preferences.get('weather', 1.0))
        uf_crowd    = clip(preferences.get('crowd', 1.0))
        uf_traffic  = clip(preferences.get('traffic', 1.0))

        # 2. Batch Processing (Chuẩn bị dữ liệu cho AI Risk)
        edge_pointers = []
        ai_inputs = []

        for u, v, data in sub_G.edges(data=True):
            node_u, node_v = sub_G.nodes[u], sub_G.nodes[v]
            
            # --- A. Tính điểm rủi ro gốc (Raw Scores) ---
            # 1. Disaster Impact
            s_disaster = 0
            # (Logic tìm giao cắt: Lấy bbox cạnh -> tìm trong index -> tính chi tiết)
            # Để code gọn, ta giả định standardization có hàm hỗ trợ
            # Ở đây mình viết logic check nhanh:
            edge_bbox = (min(node_u['x'], node_v['x']), min(node_u['y'], node_v['y']), 
                         max(node_u['x'], node_v['x']), max(node_u['y'], node_v['y']))
            
            potential_disasters = list(disaster_idx.intersection(edge_bbox))
            if potential_disasters:
                relevant_d = [env_data['disasters'][i] for i in potential_disasters]
                s_disaster = standardization.calculate_disaster_impact_advanced(data, node_u, node_v, relevant_d)

            # 2. Weather Impact
            s_weather = 0
            potential_weather = list(weather_idx.intersection(edge_bbox))
            if potential_weather:
                relevant_w = [env_data['weather'][i] for i in potential_weather]
                s_weather = standardization.calculate_weather_impact_geometry(data, node_u, node_v, relevant_w)

            # 3. Crowd Impact (Lấy trung điểm)
            mid_lat = (node_u['y'] + node_v['y']) / 2
            mid_lon = (node_u['x'] + node_v['x']) / 2
            s_crowd = standardization.calculate_crowd_score(mid_lat, mid_lon, curr_hour)

            # --- B. Lọc phương tiện (Hard Constraint / Luật Cấm) ---
            hw_type = data.get('highway', '')
            
            # Nhóm xe lớn (Cấm đi hẻm)
            # residential: Đường dân sinh/hẻm nhỏ
            # living_street: Đường nội bộ khu dân cư
            is_big_vehicle = vehicle_mode in ['car', 'bus', 'truck']
            is_small_road = hw_type in ['residential', 'living_street', 'service']
            
            if is_big_vehicle and is_small_road:
                # Phạt cực nặng (tương đương đi vào đường cụt)
                # Với Bus thì phạt nặng hơn cả Car vì Bus to hơn
                penalty_weight = 50.0 if vehicle_mode == 'bus' else 5.0
                s_crowd += penalty_weight

            # --- C. Áp dụng Preference (Tâm lý) ---
            eff_disaster = s_disaster * uf_disaster
            eff_weather  = s_weather  * uf_weather
            eff_crowd    = s_crowd    * uf_crowd

            edge_pointers.append(data)
            ai_inputs.append([eff_disaster, eff_weather, eff_crowd])
            
            # Lưu lại điểm gốc và điểm hiệu dụng
            data['scores'] = {
                'real': (s_disaster, s_weather, s_crowd),
                'eff': (eff_disaster, eff_weather, eff_crowd)
            }

        # 3. Gọi AI Risk Model (Batch Prediction)
        # standardization.risk_model đã được load sẵn
        predicted_penalties = []
        if risk_model and ai_inputs:
            try:
                predicted_penalties = standardization.risk_model.predict(ai_inputs)
            except:
                # Fallback công thức cộng
                predicted_penalties = [(x[0]*1000 + x[1]*30 + x[2]*5) for x in ai_inputs]
        else:
             predicted_penalties = [(x[0]*1000 + x[1]*30 + x[2]*5) for x in ai_inputs]

        # 4. Gán trọng số cuối cùng vào Graph
        for i, data in enumerate(edge_pointers):
            penalty = float(max(0.0, predicted_penalties[i]))
            
            # Lấy lại điểm thực để tính tốc độ
            s_dis_real, s_wth_real, s_crd_real = data['scores']['real']
            
            # Tính Traffic Score cục bộ (bị ảnh hưởng bởi Mưa Thật và Prefs Traffic)
            local_traffic = base_traffic_score
            if s_wth_real > 0:
                local_traffic = min(1.0, base_traffic_score + 0.2)
            
            # Áp dụng Preference Traffic (Nếu user sợ kẹt xe -> Giảm tốc độ ảo xuống để né)
            local_traffic_eff = local_traffic * uf_traffic

            # Tính Tốc độ & ETA
            # Lưu ý: Hàm này dùng s_wth_real (Mưa thật) để tính vật lý
            real_speed_kmh = standardization.calculate_segment_speed(
                data, curr_hour, is_weekend, s_wth_real, vehicle_mode
            )
            
            length_m = data.get('length', 10)
            real_speed_ms = real_speed_kmh / 3.6
            eta_seconds = length_m / max(0.1, real_speed_ms)

            # --- TRỌNG SỐ CUỐI CÙNG ---
            # Weight = Thời gian * (1 + Penalty Rủi ro)
            final_weight = eta_seconds * (1.0 + penalty)
            
            # Lưu vào data để Dijkstra dùng
            data['final_weight'] = final_weight
            
            # Lưu meta info để hiển thị sau này
            data['meta_info'] = {
                'eta': eta_seconds,
                'penalty': penalty,
                'risk_flags': {
                    'disaster': s_dis_real > 0,
                    'weather': s_wth_real > 0,
                    'crowd': s_crd_real > 0.7
                }
            }
            # Xóa biến tạm
            del data['scores']

        print("✅ Đã tính xong trọng số.")

        # ... (Tiếp theo của _calculate_weights) ...

    def _process_routing(self, sub_G, orig_node, dest_node, bbox, curr_hour, is_weekend, vehicle_mode, preferences):
        """
        PRIVATE: Điều phối luồng xử lý chính: Quét -> Tính -> Tìm đường -> Trả kết quả.
        """
        # 1. Quét môi trường
        env_data = self._scan_environment(bbox)
        
        # 2. Tính trọng số (Lần 1 - Best Route)
        # Hàm này sẽ update trực tiếp vào sub_G
        self._calculate_weights(sub_G, env_data, curr_hour, is_weekend, vehicle_mode, preferences)
        
        # 3. Tìm Đa Lộ trình (Multi-path Logic)
        routes_found = []
        
        # A. Route 1: Tối ưu nhất (Best)
        try:
            path1 = nx.shortest_path(sub_G, orig_node, dest_node, weight='final_weight')
            routes_found.append(self._audit_route(sub_G, path1, env_data, "Best Route", start_coords=None, end_coords=None))
            
            # --- KỸ THUẬT PHẠT (PENALIZING) ĐỂ TÌM ĐƯỜNG KHÁC ---
            # Tăng trọng số các cạnh của đường 1 lên gấp đôi để ép thuật toán tìm đường khác
            for i in range(len(path1) - 1):
                u, v = path1[i], path1[i+1]
                if sub_G.has_edge(u, v):
                    # MultiDiGraph có thể có nhiều key, phạt hết
                    for key in sub_G[u][v]:
                        sub_G[u][v][key]['final_weight'] *= 2.0 
                        
            # B. Route 2: Thay thế (Alternative)
            try:
                path2 = nx.shortest_path(sub_G, orig_node, dest_node, weight='final_weight')
                # Chỉ lấy nếu đường 2 khác đường 1 (đơn giản là độ dài khác nhau)
                if len(path2) != len(path1):
                    routes_found.append(self._audit_route(sub_G, path2, env_data, "Alternative 1"))
            except: pass
            
        except nx.NetworkXNoPath:
            return {"status": "error", "message": "Không tìm thấy đường đi an toàn."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

        # 4. Trả kết quả (Lấy đường đầu tiên làm chính)
        if not routes_found:
             return {"status": "error", "message": "Lỗi thuật toán tìm đường."}
             
        primary_route = routes_found[0]
        
        # Đóng gói Map Data để vẽ
        # Chỉ lấy những cái nằm trong bbox (Đã lọc ở bước scan)
        map_data_response = {
            "disasters": env_data['disasters'],
            "weather": env_data['weather'],
            "crowd": env_data['crowd']
        }
        
        # Merge kết quả
        return {
            **primary_route, # Bung các trường status, summary, geometry... ra
            "alternatives": routes_found[1:], # Các đường phụ (nếu có)
            "map_data": map_data_response
        }

    def _audit_route(self, G, route_nodes, env_data, route_name="Route", start_coords=None, end_coords=None):
        """
        PRIVATE: Kiểm tra lại lộ trình, tính tổng ETA, gán nhãn màu sắc.
        CẬP NHẬT: Thêm logic đếm số lượng rủi ro ĐÃ NÉ ĐƯỢC.
        """
        total_dist = 0
        total_eta = 0
        total_risk_score = 0
        max_segment_risk = 0
        
        hit_disasters = set()
        hit_weathers = set()
        crowd_count = 0
        route_coords = []
        
        # Traceback lộ trình (giữ nguyên logic cũ)
        for i in range(len(route_nodes) - 1):
            u, v = route_nodes[i], route_nodes[i+1]
            # ... (giữ nguyên code lấy edge data) ...
            # Lấy data cạnh để cộng dồn khoảng cách/thời gian
            edge = G.get_edge_data(u, v)[0] 
            meta = edge.get('meta_info', {})
            length = edge.get('length', 10)
            
            total_dist += length
            total_eta += meta.get('eta', 0)
            p = meta.get('penalty', 0)
            total_risk_score += (p * length)
            max_segment_risk = max(max_segment_risk, p)
            
            route_coords.append([G.nodes[u]['y'], G.nodes[u]['x']])
            
            # Check flag (giữ nguyên logic cũ)
            flags = meta.get('risk_flags', {})
            if flags.get('crowd'): crowd_count += 1
            
            # SỬA LẠI CHỖ LẤY TÊN (như đã fix ở bước trước)
            if flags.get('disaster'):
                node_obj = G.nodes[u]
                for d in env_data['disasters']:
                    # Tăng radius check lên một chút để bắt dính tên
                    if standardization.haversine(node_obj['y'], node_obj['x'], d['lat'], d['lng']) <= (d.get('radius', 5) + 0.2):
                        hit_disasters.add(d.get('name', 'Thiên tai')) # Sửa title -> name
            
            if flags.get('weather'):
                node_obj = G.nodes[u]
                for w in env_data['weather']:
                     if standardization.haversine(node_obj['y'], node_obj['x'], w['lat'], w['lng']) <= (w.get('radius', 5) + 0.2):
                        hit_weathers.add(f"{w.get('condition')}")

        # Add điểm cuối (giữ nguyên)
        last = route_nodes[-1]
        route_coords.append([G.nodes[last]['y'], G.nodes[last]['x']])
        
        # --- [MỚI] TÍNH TOÁN MINH CHỨNG (PROOF OF AVOIDANCE) ---
        # Tổng số rủi ro có trong vùng Bounding Box (Môi trường)
        total_disasters_in_area = len(env_data['disasters'])
        total_storms_in_area = len([w for w in env_data['weather'] if w['condition'] in ['Rain', 'Thunderstorm']])
        
        # Số rủi ro mình bị dính
        hit_disaster_count = len(hit_disasters)
        # Weather hit thì tính sơ bộ
        hit_storm_count = len(hit_weathers)

        # Số rủi ro ĐÃ NÉ
        avoided_disasters = max(0, total_disasters_in_area - hit_disaster_count)
        avoided_storms = max(0, total_storms_in_area - hit_storm_count)
        
        avoidance_msg = []
        if avoided_disasters > 0:
            avoidance_msg.append(f"Đã né {avoided_disasters} điểm thiên tai")
        if avoided_storms > 0:
            avoidance_msg.append(f"Đã né {avoided_storms} vùng mưa bão")
            
        proof_text = ", ".join(avoidance_msg) if avoidance_msg else "Không có rủi ro lớn trong khu vực."

        # --- TÍNH TOÁN METRICS (Giữ nguyên) ---
        final_eta_min = round((total_eta * 1.15) / 60)
        final_dist_km = round(total_dist / 1000, 2)
        avg_risk = total_risk_score / total_dist if total_dist > 0 else 0
        
        # --- GÁN NHÃN (Cập nhật description) ---
        safety_label = "🟢 An toàn"
        safety_color = "green"
        reasons = []

        if len(hit_disasters) > 0:
            safety_label = "🔴 CỰC KỲ NGUY HIỂM"
            safety_color = "red"
            reasons.append(f"⛔ Đi qua {len(hit_disasters)} vùng nguy hiểm!")
        elif max_segment_risk > 20.0:
            safety_label = "🔴 Nguy hiểm"
            safety_color = "red"
            reasons.append("⚠️ Có đoạn rủi ro rất cao")
        elif len(hit_weathers) > 0 or (crowd_count / len(route_nodes) > 0.3):
            safety_label = "🟡 Cẩn trọng"
            safety_color = "yellow"
            if len(hit_weathers) > 0: reasons.append(f"🌧️ Mưa: {', '.join(hit_weathers)}")
            if crowd_count > 0: reasons.append("👥 Đông đúc")
        
        # Ghép minh chứng vào description
        base_desc = " | ".join(reasons) if reasons else "Lộ trình thuận lợi."
        full_description = f"{base_desc} ({proof_text})"
        
        traffic_status = "High" if avg_risk > 0.7 else "Medium" if avg_risk > 0.4 else "Low"
        crowd_status = "High" if crowd_count > 2 else "Medium" if crowd_count > 0 else "Low"

        return {
            "status": "success",
            "name": route_name,
            "distance_km": final_dist_km,
            "duration_min": final_eta_min,
            "summary": {
                "safety_label": safety_label,
                "safety_color": safety_color,
                "description": full_description, # <--- Đã cập nhật dòng này
                "avoidance_proof": proof_text,   # <--- Thêm trường riêng để Frontend dễ hiển thị
                "eta_display": f"{final_eta_min} phút"
            },
            "risk_summary": {
                "traffic_level": traffic_status,
                "crowd_level": crowd_status
            },
            "metrics": {
                "avg_risk_score": round(avg_risk, 2),
                "max_segment_risk": round(max_segment_risk, 2)
            },
            "geometry": route_coords,
            "hit_details": {
                "disasters": list(hit_disasters),
                "weathers": list(hit_weathers)
            }
        }
# --- KHỞI TẠO SINGLETON ---
# Để app.py gọi được
engine = RoutingEngine()

def get_optimal_routes(start, end, vehicle_mode="walking", preferences=None):
    # Wrapper function để tương thích với app.py cũ
    return engine.get_optimal_routes(start, end, vehicle_mode, preferences)