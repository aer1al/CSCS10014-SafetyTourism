import math
import os
import json
import pickle
import numpy as np
import warnings
from datetime import datetime, timezone
from utils import haversine, get_min_distance_to_segment

# Tắt cảnh báo phiền phức của Sklearn
warnings.filterwarnings("ignore", category=UserWarning)


# ==========================================
# 0. AI MODEL LOADER (QUAN TRỌNG)
# ==========================================
# Đoạn này phải nằm ngoài cùng (Global scope) để chỉ load 1 lần khi server chạy

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'traffic_model.pkl')
traffic_model = None

try:
    with open(MODEL_PATH, 'rb') as f:
        traffic_model = pickle.load(f)
    print("🤖 [INIT] Đã nạp thành công 'traffic_model.pkl'!")
except Exception as e:
    print(f"⚠️ [INIT] Không tìm thấy Model AI ({e}). Hệ thống sẽ chạy chế độ Rule-based.")


# ==========================================
# 1. Disaster
# ==========================================

# Bảng điểm rủi ro cơ bản theo loại thiên tai
DISASTER_SCORE_MAP = {
    # Nhóm 1: Nguy hiểm chết người / Tắc đường (Score 1.0)
    "severeStorms": 1.0,  # Bão lớn
    "floods": 1.0,        # Lũ lụt, Ngập sâu
    "landslides": 1.0,    # Sạt lở đất
    "volcanoes": 1.0,     # Núi lửa
    "earthquakes": 0.9,   # Động đất

    # Nhóm 2: Nguy hiểm cao (Cảnh báo gắt)
    "wildfires": 0.8,     # Cháy rừng/Cháy nhà
    "cyclones": 0.9,      # Bão nhiệt đới
    
    # Nhóm 3: Nguy hiểm trung bình
    "tempExtremes": 0.5,  # Nắng nóng kỷ lục
    "drought": 0.4,       # Hạn hán
    "manmade": 0.4,       # Sự cố con người (Tràn dầu...)
    
    # Nhóm 4: Ảnh hưởng thấp
    "dustHaze": 0.3,      # Bụi mịn
    "waterColor": 0.2     # Tảo nở hoa
}

# CÁC HÀM XỬ LÝ THIÊN TAI (DISASTER)

def get_base_disaster_score(categories):
    """
    Tính điểm gốc dựa trên loại thiên tai.
    Input: List các category ID (vd: ['floods', 'severeStorms'])
    Output: Điểm cao nhất trong list (0.0 - 1.0)
    """
    if not categories:
        return 0.0
        
    max_score = 0.0
    for cat in categories:
        # Lấy điểm từ map, mặc định 0.3 nếu là loại lạ
        score = DISASTER_SCORE_MAP.get(cat, 0.3)
        if score > max_score:
            max_score = score
            
    return max_score

def calculate_time_decay(event_date_str):
    """
    Tính hệ số suy giảm theo thời gian (Time Decay).
    Mới xảy ra -> Nguy hiểm cao (1.0)
    Đã lâu -> Nguy hiểm giảm dần.
    """
    if not event_date_str:
        return 1.0 # Không có ngày giờ -> Coi như mới tinh cho an toàn

    try:
        # Xử lý format ngày giờ ISO 8601 (VD: "2023-10-27T10:00:00Z")
        # Thay Z bằng +00:00 để Python đời cũ cũng hiểu được timezone
        event_time = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        
        # Tính khoảng cách thời gian (giờ)
        diff = now - event_time
        hours_passed = diff.total_seconds() / 3600
        
        # Logic suy giảm (Decay Logic)
        if hours_passed < 12: return 1.0      # < 12h: Đang diễn ra/Nóng hổi
        elif hours_passed < 24: return 0.9    # 1 ngày: Vẫn rất nguy hiểm
        elif hours_passed < 48: return 0.7    # 2 ngày: Đã giảm nhiệt
        elif hours_passed < 72: return 0.4    # 3 ngày: Chỉ còn tàn dư
        elif hours_passed < 168: return 0.2   # 1 tuần: Rất thấp
        else: return 0.0                      # > 1 tuần: Hết hạn
        
    except Exception as e:
        # print(f"Lỗi parse ngày: {e}") 
        return 1.0 # Fallback an toàn

def calculate_disaster_impact_advanced(edge_data, u_node, v_node, disaster_list):
    """
    Tính điểm rủi ro Thiên tai cho MỘT cạnh đường (Edge).
    Kết hợp: Hình học (Cắt đường) + Loại thiên tai + Thời gian.
    
    Input:
        - edge_data: Dữ liệu cạnh (để lấy geometry đường cong)
        - u_node, v_node: Tọa độ 2 đầu mút
        - disaster_list: Danh sách thiên tai (đã lọc theo vùng)
    Output: 
        - Penalty Score (0.0 - 1.0)
    """
    max_impact = 0.0
    
    # 1. Trích xuất tọa độ con đường (Xử lý đường cong)
    points = []
    if 'geometry' in edge_data:
        # Nếu là đường cong, lấy danh sách các điểm uốn
        # Lưu ý: OSMnx geometry thường là (Lon, Lat)
        coords = list(edge_data['geometry'].coords)
        # Đảo lại thành (Lat, Lon) để tính toán cho chuẩn với utils
        points = [(p[1], p[0]) for p in coords] 
    else:
        # Đường thẳng nối 2 node
        points = [(u_node['y'], u_node['x']), (v_node['y'], v_node['x'])]

    # 2. Duyệt qua từng thiên tai trong khu vực
    for d in disaster_list:
        d_lat = d['lat']
        d_lng = d['lng']
        d_radius = d.get('radius', 5.0) # Bán kính ảnh hưởng (km)
        
        # 3. Kiểm tra va chạm hình học (Geometry Intersection)
        # Tính khoảng cách ngắn nhất từ Tâm thiên tai đến Con đường
        min_dist_to_road = float('inf')
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            # Hàm này tính khoảng cách từ điểm (d_lat, d_lng) tới đoạn thẳng p1-p2
            dist = get_min_distance_to_segment(d_lat, d_lng, p1[0], p1[1], p2[0], p2[1])
            
            if dist < min_dist_to_road:
                min_dist_to_road = dist

        # 4. Nếu đường nằm trong vùng ảnh hưởng -> Tính điểm phạt
        if min_dist_to_road <= d_radius:
            
            # A. Điểm gốc (Base Score)
            base_score = get_base_disaster_score(d.get('categories_raw', []))
            
            # B. Hệ số thời gian (Time Decay)
            time_factor = calculate_time_decay(d.get('date'))
            
            # C. Hệ số khoảng cách (Distance Factor - Optional)
            # Càng gần tâm càng nguy hiểm (từ 0.5 -> 1.0)
            # dist_factor = 1.0 - (min_dist_to_road / d_radius) * 0.5 
            
            final_score = base_score * time_factor
            
            if final_score > max_impact:
                max_impact = final_score

    return max_impact


# ==========================================
# 2. Weather
# ==========================================

# CÁC HÀM XỬ LÝ THỜI TIẾT (WEATHER)


def get_weather_base_score(weather_main, wind_speed):
    """
    Tính điểm gốc (Base Score) dựa trên loại thời tiết và gió.
    Input: 'Rain', 'Thunderstorm',... và tốc độ gió (km/h)
    """
    # Bảng điểm cơ bản (Severity)
    RISK_MAP = {
        "Thunderstorm": 1.0, # Bão/Giông -> Nguy hiểm nhất
        "Rain": 0.7,         # Mưa vừa -> Trơn trượt, tầm nhìn kém
        "Drizzle": 0.4,      # Mưa phùn -> Hơi khó chịu
        "Fog": 0.5,          # Sương mù -> Tầm nhìn kém
        "Snow": 0.6,         # Tuyết (ít gặp ở VN nhưng cứ để)
        "Clear": 0.0,
        "Clouds": 0.1
    }
    
    score = RISK_MAP.get(weather_main, 0.2)
    
    # Cộng hưởng Gió (Wind Factor)
    # Gió > 40km/h (Cấp 6) là nguy hiểm cho xe máy
    if wind_speed > 40:
        score += 0.3
    elif wind_speed > 20:
        score += 0.1
        
    return min(1.0, score) # Kẹp trần 1.0

def calculate_distance_decay(distance, radius):
    """
    [LOGIC 5 LỚP] Tính hệ số suy giảm theo khoảng cách.
    Input: Khoảng cách tới tâm (km), Bán kính vùng mưa (km)
    Output: Hệ số (0.0 - 1.0)
    """
    if radius <= 0: return 0.0
    
    ratio = distance / radius
    
    # Chia 5 vùng (Mỗi vùng 20%)
    if ratio <= 0.2:   # 0% - 20% (Tâm bão)
        return 1.0     # Nguyên vẹn sát thương
    elif ratio <= 0.4: # 20% - 40%
        return 0.8
    elif ratio <= 0.6: # 40% - 60%
        return 0.6
    elif ratio <= 0.8: # 60% - 80%
        return 0.4
    elif ratio <= 1.0: # 80% - 100% (Rìa ngoài)
        return 0.2
    else:              # Ngoài vùng
        return 0.0

def calculate_weather_impact_geometry(edge_data, u_node, v_node, weather_zones):
    """
    Tính điểm phạt thời tiết cho một cạnh đường.
    Sử dụng logic 5 lớp vòng tròn đồng tâm.
    """
    max_impact = 0.0
    
    # 1. Lấy geometry của đường (xử lý đường cong)
    points = []
    if 'geometry' in edge_data:
        coords = list(edge_data['geometry'].coords)
        points = [(p[1], p[0]) for p in coords] # Đảo lại (Lat, Lon)
    else:
        points = [(u_node['y'], u_node['x']), (v_node['y'], v_node['x'])]

    # 2. Duyệt qua các vùng thời tiết
    for w in weather_zones:
        w_lat = w['lat']
        w_lng = w['lng']
        w_radius = w.get('radius', 2.0)
        
        # Lấy điểm gốc của cơn mưa này
        # Lưu ý: w['wind'] ở đây là lấy từ dữ liệu weather.py trả về
        base_score = get_weather_base_score(w['condition'], w.get('wind', 0))
        
        if base_score == 0: continue

        # 3. Tìm khoảng cách ngắn nhất từ Mưa tới Đường
        min_dist = float('inf')
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            dist = get_min_distance_to_segment(w_lat, w_lng, p1[0], p1[1], p2[0], p2[1])
            if dist < min_dist:
                min_dist = dist
        
        # 4. Tính điểm phạt (Score = Base * Decay)
        if min_dist <= w_radius:
            decay_factor = calculate_distance_decay(min_dist, w_radius)
            final_score = base_score * decay_factor
            
            # Lấy cơn mưa nào nặng nhất ảnh hưởng tới đường này
            if final_score > max_impact:
                max_impact = final_score
                
    return max_impact


# ==========================================
# 3. Crowd 
# ==========================================

# Load dữ liệu Crowd Zones một lần duy nhất khi khởi động App
CROWD_ZONES = []

def load_crowd_data():
    global CROWD_ZONES
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'crowd_zones.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            CROWD_ZONES = json.load(f)
            
        print(f"✅ Đã nạp {len(CROWD_ZONES)} điểm nóng (Chế độ: Simple List).")
        
    except Exception as e:
        print(f"⚠️ Lỗi nạp Crowd Data: {e}")
        CROWD_ZONES = []   

# Gọi hàm load ngay khi import
load_crowd_data()

def calculate_crowd_score(lat, lon, current_hour):
    """
    Tính điểm đám đông (Phiên bản không cần R-tree).
    Sử dụng bộ lọc hình hộp (Box Filter) để tối ưu tốc độ.
    """
    if not CROWD_ZONES: return 0.0
    
    max_score = 0.0
    
    # 1. BỘ LỌC NHANH (FAST FILTER)
    # Chỉ xét những điểm nằm trong phạm vi ~1km (0.01 độ) quanh xe
    # Phép toán abs() cực nhẹ, chạy vèo cái là xong list 2000 điểm
    search_range = 0.01 
    
    for zone in CROWD_ZONES:
        # Nếu điểm nóng nằm quá xa (ngoài hộp 1km) -> Bỏ qua ngay
        if abs(lat - zone['lat']) > search_range or abs(lon - zone['lng']) > search_range:
            continue
            
        # 2. TÍNH TOÁN CHI TIẾT (Chỉ chạy cho vài điểm lọt qua vòng 1)
        dist = haversine(lat, lon, zone['lat'], zone['lng'])
        radius = zone.get('radius', 0.3)
        
        if dist <= radius:
            # --- Logic tính điểm (Copy y nguyên bài cũ) ---
            z_type = zone.get('type', 'general')
            base_weight = zone.get('base_weight', 0.5)
            time_factor = 0.1
            
            # Logic giờ cao điểm
            if z_type == 'market':
                if 6 <= current_hour <= 11 or 16 <= current_hour <= 19: time_factor = 1.0
                elif 11 < current_hour < 16: time_factor = 0.5
            elif z_type == 'school':
                if 6.5 <= current_hour <= 7.5 or 16.5 <= current_hour <= 17.5: time_factor = 1.0
            elif z_type in ['mall', 'tourist']:
                if 17 <= current_hour <= 21 or (10 <= current_hour <= 17 and z_type == 'tourist'): time_factor = 1.0
                elif 10 <= current_hour < 17: time_factor = 0.6
            elif z_type == 'nightlife':
                if 19 <= current_hour <= 24: time_factor = 1.0
            
            # Distance Decay
            dist_factor = 1.0 - (dist / radius) * 0.5
            final_score = base_weight * time_factor * dist_factor
            
            if final_score > max_score:
                max_score = final_score

    return round(min(1.0, max_score), 2)


# ==========================================
# 4. Traffic
# ==========================================

def calculate_traffic_score(current_hour: float, is_weekend: bool, weather_score: float = 0.0) -> float:
    """
    Tính điểm kẹt xe dự báo (Forecast Traffic).
    Ưu tiên dùng AI Model. Nếu lỗi thì dùng Rule-based.
    Output: 0.0 (Vắng) -> 1.0 (Kẹt cứng).
    """
    
    # 1. CÁCH 1: DÙNG AI (Nếu model đã load thành công)
    if traffic_model:
        try:
            # Input model: [[hour, is_weekend, weather]]
            input_data = [[current_hour, int(is_weekend), weather_score]]
            predicted_score = traffic_model.predict(input_data)[0]
            
            return float(max(0.0, min(1.0, predicted_score)))
        except Exception as e:
            # print(f"Lỗi AI Traffic: {e}")
            pass

    # 2. CÁCH 2: IF-ELSE CŨ (Fallback an toàn)
    score = 0.1 # Đêm khuya vắng vẻ
    
    if not is_weekend: # Ngày thường
        # Cao điểm sáng (6h30 - 9h)
        if 6.5 <= current_hour < 9.0: score = 0.8
        # Giờ hành chính (9h - 11h)
        elif 9.0 <= current_hour < 11.0: score = 0.4
        # Nghỉ trưa
        elif 11.0 <= current_hour < 13.5: score = 0.5
        # Chiều làm việc
        elif 13.5 <= current_hour < 16.0: score = 0.4
        # Cao điểm chiều (16h - 19h30) -> Kẹt nhất
        elif 16.0 <= current_hour < 19.5: score = 1.0 
        # Tối
        elif 19.5 <= current_hour < 22.0: score = 0.6
    else: 
        # Cuối tuần: Ngủ nướng, đông trưa và tối
        if 9.0 <= current_hour < 12.0: score = 0.5
        elif 16.0 <= current_hour < 21.0: score = 0.7
        
    return score

def calculate_segment_speed(edge_data, current_hour, is_weekend, weather_score, vehicle_mode="motorbike"):
    """
    Tính tốc độ thực tế (km/h) cho từng đoạn đường.
    Dựa trên: Loại đường (OSM) + Điểm kẹt xe (Traffic Score) + Loại xe.
    """
    
    # 1. Cấu hình tốc độ cơ bản (Max Speed Profile)
    # Heuristic: [Trục chính, Đường nhánh, Hẻm nhỏ]
    SPEED_PROFILES = {
        "motorbike": {"primary": 50, "secondary": 40, "residential": 30},
        "car":       {"primary": 60, "secondary": 35, "residential": 10}, 
        "walking":   {"primary": 5,  "secondary": 5,  "residential": 5},
        "bus":       {"primary": 45, "secondary": 30, "residential": 1},
        "bike":      {"primary": 20, "secondary": 15, "residential": 15}
    }
    
    # Lấy profile hiện tại (Mặc định là motorbike nếu không tìm thấy)
    profile = SPEED_PROFILES.get(vehicle_mode, SPEED_PROFILES["motorbike"])
    
    # 2. Xác định loại đường
    highway_type = edge_data.get('highway', 'residential')
    if isinstance(highway_type, list): highway_type = highway_type[0]
    
    if highway_type in ['trunk', 'primary']: 
        max_speed = profile['primary']
    elif highway_type in ['secondary', 'tertiary']: 
        max_speed = profile['secondary']
    else: 
        max_speed = profile['residential']

    # Ưu tiên maxspeed từ bản đồ nếu có (nhưng phải kẹp trần theo sức xe)
    try:
        osm_max = float(edge_data.get('maxspeed', 0))
        if osm_max > 0:
            max_speed = min(max_speed, osm_max)
    except: pass

    # 3. Tính hệ số giảm tốc
    tf_score = calculate_traffic_score(current_hour, is_weekend, weather_score)
    
    # Logic ảnh hưởng riêng cho từng loại xe
    # - Ô tô: Sợ Kẹt xe (0.9), Ít sợ Mưa (0.4)
    # - Xe máy/Xe đạp/Đi bộ: Sợ Mưa (0.8), Ít sợ Kẹt xe (0.6 - do luồn lách được)
    
    is_protected_vehicle = vehicle_mode in ["car", "bus"] # Xe có mái che, to xác
    
    weather_impact = weather_score * (0.4 if is_protected_vehicle else 0.8)
    traffic_impact = tf_score * (0.9 if is_protected_vehicle else 0.6)
    
    total_penalty = max(weather_impact, traffic_impact)
    
    efficiency = 1.0 - (total_penalty * 0.8)
    
    real_speed_kmh = max(1.0, max_speed * efficiency) # Tối thiểu 1km/h
    
    return real_speed_kmh