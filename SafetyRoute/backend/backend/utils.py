# file: utils.py
import math

def haversine(lat1, lon1, lat2, lon2):
    """
    Tính khoảng cách đường chim bay giữa 2 tọa độ (km).
    Dùng công thức Haversine chuẩn cho mặt cầu.
    """
    R = 6371.0  # Bán kính Trái Đất (km)
    
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    
    a = (math.sin(dLat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2)
         
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def get_min_distance_to_segment(lat_p, lon_p, lat_a, lon_a, lat_b, lon_b):
    """
    Tính khoảng cách ngắn nhất từ điểm P (Tâm bão) đến đoạn thẳng AB (Con đường).
    Input: Tọa độ P, A, B.
    Output: Khoảng cách (km).
    """
    # 1. Chuyển đổi sang hệ tọa độ phẳng tương đối (để dùng toán Vector)
    # Vì khoảng cách trong thành phố nhỏ, ta dùng phép chiếu Equirectangular approximation
    # 1 độ vĩ (Lat) ~ 110.57 km
    # 1 độ kinh (Lon) ~ 111.32 km * cos(lat)
    
    deg_to_rad = math.pi / 180
    avg_lat = (lat_a + lat_b) / 2 * deg_to_rad
    cos_lat = math.cos(avg_lat)
    
    # Hệ số quy đổi ra km
    kx = 111.32 * cos_lat  # Hệ số cho Longitude
    ky = 110.57            # Hệ số cho Latitude
    
    # Tọa độ các điểm trên mặt phẳng km (Lấy A làm gốc 0,0)
    # P (Điểm cần tính)
    px = (lon_p - lon_a) * kx
    py = (lat_p - lat_a) * ky
    
    # B (Điểm cuối đoạn thẳng)
    bx = (lon_b - lon_a) * kx
    by = (lat_b - lat_a) * ky
    
    # 2. Tính toán Vector
    # Độ dài đoạn thẳng AB bình phương
    len_sq = bx*bx + by*by
    
    if len_sq == 0: 
        # A trùng B (Đoạn đường dài 0m) -> Trả về khoảng cách PA
        return math.sqrt(px*px + py*py)
        
    # 3. Tìm hình chiếu (Projection) của P lên đường thẳng AB
    # t là tham số tỉ lệ: t=0 tại A, t=1 tại B
    # Dot product: P.B / |B|^2
    t = (px*bx + py*by) / len_sq
    
    # Kẹp t trong khoảng [0, 1] để đảm bảo điểm chiếu nằm TRÊN đoạn thẳng
    # (Nếu t < 0 nghĩa là P gần A nhất, t > 1 nghĩa là P gần B nhất)
    t = max(0, min(1, t))
    
    # 4. Tìm tọa độ điểm gần nhất (Closest Point) trên đoạn thẳng
    closest_x = t * bx
    closest_y = t * by
    
    # 5. Tính khoảng cách từ P đến điểm gần nhất đó
    dx = px - closest_x
    dy = py - closest_y
    
    return math.sqrt(dx*dx + dy*dy)