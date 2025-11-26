import math
import os
import json
from utils import haversine
from utils import get_min_distance_to_segment

def standardize_disaster_score(raw_categories):
    """
    [VALIDATION PATTERN]
    Chuyển đổi mảng category ID (ví dụ: ['floods', 'wildfires']) thành Safety Score.
    Điểm càng cao -> càng nguy hiểm (0.0 - 1.0).
    """
    
    # SCORE_MAP: Đã tinh chỉnh cho bối cảnh Việt Nam
    SCORE_MAP = {
        # --- Nguy hiểm chết người / Tắc đường (Score 1.0) ---
        "severeStorms": 1.0,  # Bão lớn
        "floods": 1.0,        # Lũ lụt (Ngập xe không đi được)
        "landslides": 1.0,    # Sạt lở (Chặn đường hoàn toàn) [Update]
        "volcanoes": 1.0,     # Núi lửa
        "earthquakes": 0.9,   # Động đất (Rung chấn mạnh)

        # --- Nguy hiểm cao (Cảnh báo gắt) ---
        "wildfires": 0.8,     # Cháy rừng (Khói bụi, nhiệt độ)
        
        # --- Nguy hiểm trung bình (Gây khó chịu/Mệt mỏi) ---
        "tempExtremes": 0.5,  # Nắng nóng gay gắt [Update: Giảm xuống 0.5]
        "drought": 0.4,       # Hạn hán
        "manmade": 0.4,       # Sự cố do con người (Tràn dầu, hóa chất...)
        
        # --- Ảnh hưởng thấp (Tầm nhìn/Mỹ quan) ---
        "dustHaze": 0.3,      # Bụi mịn, sương mù ô nhiễm
        "waterColor": 0.2,    # Tảo nở hoa (Chỉ ảnh hưởng nếu đi biển)

        # --- Không liên quan tại VN (Giữ để code không lỗi) ---
        "seaLakeIce": 0.0,    
        "snow": 0.0           
    }
    
    max_score = 0.0
    
    if not raw_categories:
        return 0.0 # An toàn tuyệt đối

    for category_id in raw_categories:
        # Mặc định 0.3 cho các loại thiên tai lạ chưa định nghĩa
        score = SCORE_MAP.get(category_id, 0.3) 
        if score > max_score:
            max_score = score
            
    return max_score

def calculate_disaster_impact_advanced(edge_data, u_node, v_node, disaster_list):
    """
    Input: 
        - edge_data: Dữ liệu của cạnh (chứa geometry nếu là đường cong)
        - u_node, v_node: Tọa độ điểm đầu và cuối (để dự phòng)
        - disaster_list: Danh sách thiên tai
    Output: Điểm rủi ro (0.0 - 1.0)
    """
    max_impact = 0.0
    
    # 1. Lấy danh sách các điểm tọa độ tạo nên con đường
    points = []
    
    if 'geometry' in edge_data:
        # Nếu là đường cong, OSMnx lưu nó dưới dạng LineString
        # Ta trích xuất các điểm tọa độ dọc theo đường cong
        # line_coords = [(lon, lat), (lon, lat)...]
        line_geom = edge_data['geometry']
        points = list(line_geom.coords) 
        # Lưu ý: Shapely/OSMnx thường lưu (Lon, Lat) -> Cần chú ý thứ tự
    else:
        # Nếu là đường thẳng, chỉ có điểm đầu và cuối
        points = [(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])]

    # 2. Duyệt qua từng vùng thiên tai
    for d in disaster_list:
        risk_radius = d.get('radius', 5.0)
        disaster_lat = d['lat']
        disaster_lng = d['lng']
        
        # 3. Kiểm tra khoảng cách từ Tâm bão tới ĐƯỜNG CONG
        # Đường cong được tạo bởi nhiều đoạn thẳng nhỏ nối tiếp nhau
        # Ta check từng đoạn nhỏ xem có đoạn nào cắt vùng bão không
        min_dist_to_road = float('inf')
        
        for i in range(len(points) - 1):
            # Đoạn nhỏ thứ i: nối từ p1 đến p2
            p1_lon, p1_lat = points[i]
            p2_lon, p2_lat = points[i+1]
            
            # Tính khoảng cách từ tâm bão đến đoạn nhỏ này
            dist = get_min_distance_to_segment(disaster_lat, disaster_lng, 
                                             p1_lat, p1_lon, 
                                             p2_lat, p2_lon)
            
            if dist < min_dist_to_road:
                min_dist_to_road = dist

        # 4. Kết luận cho thiên tai này
        if min_dist_to_road <= risk_radius:
            # Nếu bị cắt, tính điểm mức độ nghiêm trọng
            severity = standardize_disaster_score(d.get('categories_raw', []))
            if severity > max_impact:
                max_impact = severity
                
    return max_impact

def get_weather_base_score(weather_main: str, wind_speed: float) -> float:
    """
    Tính điểm rủi ro cho MỘT điểm cụ thể dựa trên Trời và Gió.
    Input:
        - weather_main (str): "Rain", "Clear", "Fog"... (từ weather.py)
        - wind_speed (float): Tốc độ gió m/s (từ weather.py)
    Output:
        - float: 0.0 (An toàn) -> 1.0 (Nguy hiểm)
    """
    
    # 1. BẢNG ĐIỂM CƠ BẢN (Base Score)
    # Dựa trên tầm nhìn và độ trơn trượt
    RISK_MAP = {
        "Thunderstorm": 0.9, # Sấm sét nguy hiểm
        "Rain": 0.6,         # Đường trơn, ướt
        "Drizzle": 0.4,      # Mưa phùn, hơi khó chịu
        "Fog": 0.4,          # Sương mù dày, giảm tầm nhìn
        "Mist": 0.3, "Haze": 0.3,
        "Snow": 0.5,         # Tuyết (giữ cho chuẩn logic chung)
        "Clouds": 0.1,       # Mây nhiều -> An toàn
        "Clear": 0.0         # Trời quang -> Tốt nhất
    }
    
    # Lấy điểm cơ bản (Mặc định 0.2 nếu trạng thái lạ)
    score = RISK_MAP.get(weather_main, 0.2)
    
    # 2. HỆ SỐ PHẠT GIÓ (Wind Penalty) - Rất quan trọng
    # Open-Meteo trả về m/s.
    # 10 m/s ~ Cấp 5 (Gió tươi)
    # 15 m/s ~ Cấp 7 (Gió cứng - Cây rung lắc)
    # 25 m/s ~ Cấp 10 (Bão/Lốc)
    
    if wind_speed >= 25.0:
        return 1.0  # Gió bão -> Nguy hiểm tuyệt đối (kể cả trời quang)
        
    elif wind_speed >= 15.0:
        # Gió rất mạnh -> Ít nhất phải là 0.8 (Nguy hiểm cho xe máy)
        score = max(score, 0.8)
        
    elif wind_speed >= 10.0:
        # Gió mạnh vừa -> Cộng thêm 0.2 rủi ro
        score += 0.2
        
    # Kẹp điểm trong khoảng [0.0, 1.0]
    return min(score, 1.0)

# file: standardization.py (Thêm đoạn này vào cuối file)

# ... (Các hàm cũ giữ nguyên) ...

# --- WEATHER GEOMETRY LOGIC (GIỐNG DISASTER) ---
def calculate_weather_impact_geometry(edge_data, u_node, v_node, weather_zones):
    """
    Input: 
        - edge_data: Dữ liệu cạnh (để lấy geometry đường cong)
        - u_node, v_node: Tọa độ 2 đầu
        - weather_zones: Danh sách vùng mưa (từ mock_weather.json)
    Output: 
        - float: Điểm rủi ro thời tiết (0.0 - 1.0) cho cạnh này.
    """
    from utils import get_min_distance_to_segment
    
    max_impact = 0.0
    
    # 1. Lấy các điểm tạo nên con đường (Xử lý đường cong)
    points = []
    if 'geometry' in edge_data:
        points = list(edge_data['geometry'].coords) 
        # Lưu ý: geometry thường là (Lon, Lat). Cần check lại thư viện OSMnx đang dùng.
        # Thông thường OSMnx trả về (x=Lon, y=Lat).
    else:
        points = [(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])]

    # 2. Duyệt qua từng vùng thời tiết
    for zone in weather_zones:
        zone_lat = zone['lat']
        zone_lng = zone['lng']
        zone_radius = zone.get('radius', 5.0)
        
        # Lấy thông tin thời tiết của vùng này để tính điểm
        # (Gọi lại hàm tính điểm cơ bản đã có)
        base_score = get_weather_base_score(zone['condition'], zone['wind_speed'])
        
        if base_score == 0: continue # Vùng nắng đẹp thì bỏ qua, không cần check cắt
        
        # 3. Check khoảng cách (Cắt ngang)
        min_dist = float('inf')
        
        for i in range(len(points) - 1):
            # Điểm trong geometry là (Lon, Lat) -> Cần đảo lại thành (Lat, Lon) cho hàm utils
            p1_lon, p1_lat = points[i]
            p2_lon, p2_lat = points[i+1]
            
            dist = get_min_distance_to_segment(zone_lat, zone_lng, 
                                             p1_lat, p1_lon, 
                                             p2_lat, p2_lon)
            if dist < min_dist:
                min_dist = dist
        
        # 4. Nếu cắt vùng mưa -> Gán điểm
        if min_dist <= zone_radius:
            if base_score > max_impact:
                max_impact = base_score
                
    return max_impact
# file: standardization.py

CROWD_ZONES = []

try:
    # Lấy đường dẫn thư mục chứa file code hiện tại
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'crowd_zones.json')
    
    # Mở và đọc file
    with open(file_path, 'r', encoding='utf-8') as f:
        CROWD_ZONES = json.load(f)
    print(f"✅ Đã nạp thành công {len(CROWD_ZONES)} địa điểm nóng từ crowd_zones.json")

except Exception as e:
    print(f"⚠️ Cảnh báo: Không đọc được crowd_zones.json. Lỗi: {e}")
    # Nếu lỗi thì dùng danh sách rỗng để code không bị crash
    CROWD_ZONES = []

def calculate_crowd_score(lat, lon, current_hour):
    
    """
    Tính điểm đám đông dựa trên:
    1. Khoảng cách tới điểm nóng.
    2. Khung giờ hoạt động (Time Factor).
    3. Độ nổi tiếng của địa điểm (Weight Factor).
    """
    nearby_hotspot = None
    
    # 1. Tìm điểm nóng gần nhất
    for spot in CROWD_ZONES:
        # Lấy bán kính riêng của từng điểm (mặc định 0.3km)
        radius = spot.get('radius', 0.3)
        dist = haversine(lat, lon, spot['lat'], spot['lng'])
        
        if dist <= radius:
            nearby_hotspot = spot
            break 
            
    if not nearby_hotspot: return 0.0 
    
    # 2. Lấy thông tin cơ bản
    h_type = nearby_hotspot.get('type', 'unknown')
    hotspot_weight = nearby_hotspot.get('weight', 0.5) # Mặc định 0.5 nếu không ghi weight
    
    time_factor = 0.1 # Mặc định vắng
    
    # 3. Tính Time Factor (Theo giờ & Loại hình)
    # Logic này xác định: "Giờ này chỗ đó CÓ HOẠT ĐỘNG KHÔNG?"
    
    if h_type == "nightlife": # Bar, Phố đi bộ
        if 18 <= current_hour <= 24: time_factor = 1.0   # Giờ vàng
        elif 17 <= current_hour < 18: time_factor = 0.5  # Mới mở
        else: time_factor = 0.1                          # Ban ngày vắng tanh
        
    elif h_type == "market": # Chợ
        if 6 <= current_hour <= 11: time_factor = 1.0    # Chợ sáng
        elif 16 <= current_hour <= 19: time_factor = 0.8 # Chợ chiều
        elif 11 < current_hour < 16: time_factor = 0.4   # Trưa vắng
        else: time_factor = 0.1
        
    elif h_type == "mall": # TTTM
        if 17 <= current_hour <= 21: time_factor = 1.0   # Tối đông
        elif 10 <= current_hour < 17: time_factor = 0.6  # Ban ngày lai rai
        else: time_factor = 0.1
        
    elif h_type == "tourism": # Bảo tàng, Dinh thự
        if 8 <= current_hour <= 17: time_factor = 0.8    # Giờ hành chính
        else: time_factor = 0.0                          # Đóng cửa
        
    elif h_type == "transport": # Bến xe, Sân bay
        if (7 <= current_hour <= 9) or (16 <= current_hour <= 19): 
            time_factor = 1.0 # Giờ cao điểm
        else: 
            time_factor = 0.4 # Luôn có người
            
    # 4. TÍNH ĐIỂM CUỐI CÙNG (QUAN TRỌNG NHẤT)
    # Score = Time (0.0-1.0) * Weight (Độ nổi tiếng 0.0-1.0)
    
    final_score = time_factor * hotspot_weight
    
    return round(final_score, 2)

# file: standardization.py (Thêm vào cuối file)

# ... (Các hàm crowd, disaster, weather cũ giữ nguyên) ...

def calculate_traffic_score(current_hour: float, is_weekend: bool) -> float:
    """
    Tính điểm kẹt xe dựa trên khung giờ.
    Output: 0.1 (Vắng) -> 1.0 (Kẹt cứng).
    Dùng để giảm tốc độ di chuyển khi tính ETA.
    """
    score = 0.1 # Mặc định đêm khuya

    if not is_weekend: # --- NGÀY THƯỜNG ---
        if 6.5 <= current_hour < 9.0: score = 0.8    # Cao điểm sáng (Kẹt)
        elif 9.0 <= current_hour < 11.0: score = 0.4 # Làm việc
        elif 11.0 <= current_hour < 13.5: score = 0.5 # Nghỉ trưa
        elif 13.5 <= current_hour < 16.0: score = 0.4 # Chiều
        elif 16.0 <= current_hour < 19.5: score = 1.0 # Tan tầm (Kẹt cứng)
        elif 19.5 <= current_hour < 22.0: score = 0.6 # Đi chơi tối
    else: 
        # --- CUỐI TUẦN ---
        if 9.0 <= current_hour < 12.0: score = 0.5   # Sáng T7/CN
        elif 16.0 <= current_hour < 21.0: score = 0.7 # Tối cuối tuần
        
    return score