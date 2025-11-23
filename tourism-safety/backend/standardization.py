import json

def standardize_disaster_score(raw_categories):
    """
    [VALIDATION PATTERN]
    Chuyển đổi mảng category thô từ API (EONET) thành điểm số Safety Score.
    Điểm càng cao -> càng nguy hiểm (theo thang 0.0 đến 1.0).
    """
    
    # Đây là logic 'rule-based' của bạn
    # Gán điểm cho tất cả 13 categories của EONET
    SCORE_MAP = {
        # --- Nguy hiểm cao (Ưu tiên hàng đầu) ---
        "severeStorms": 1.0,  # Bão lớn, lốc xoáy
        "floods": 1.0,        # Lũ lụt
        "landslides": 0.9,    # Sạt lở
        "volcanoes": 0.9,     # Núi lửa (mặc dù hiếm ở VN)
        "earthquakes": 0.8,   # Động đất

        # --- Nguy hiểm trung bình (Cảnh báo) ---
        "wildfires": 0.7,     # Cháy rừng
        "tempExtremes": 0.6,  # Nhiệt độ cực đoan (nắng nóng gay gắt)
        "drought": 0.5,       # Hạn hán
        
        # --- Nguy hiểm thấp (Ít ảnh hưởng trực tiếp đến tuyến đường) ---
        "dustHaze": 0.3,      # Bụi, sương mù (ô nhiễm)
        "waterColor": 0.2,    # Thủy triều đỏ, tảo nở hoa (ảnh hưởng du lịch biển)
        "manmade": 0.4,       # Do con người (ví dụ: tràn dầu)

        # --- Không liên quan (Cho 0 điểm) ---
        "seaLakeIce": 0.0,    # Băng
        "snow": 0.0           # Tuyết
    }
    
    max_score = 0.0
    
    if not raw_categories:
        return max_score # 0.0 điểm (an toàn)

    # Lấy điểm cao nhất nếu một sự kiện có nhiều loại
    for category_id in raw_categories:
        # Dùng .get() để gán 0.1 cho các loại không xác định
        score = SCORE_MAP.get(category_id, 0.1) 
        if score > max_score:
            max_score = score
            
    return max_score

def standardize_weather_score(weather_main, wind_speed):
    """
    [VALIDATION PATTERN]
    Chuyển đổi dữ liệu thời tiết thô (OpenWeatherMap) thành Safety Score.
    Input:
        - weather_main (str): Trạng thái chính (VD: "Rain", "Clear")
        - wind_speed (float): Tốc độ gió (m/s)
    Output:
        - float: Điểm từ 0.0 đến 1.0
    """
    
    # 1. BẢNG ĐIỂM CƠ BẢN (Rule-based Training)
    # Dựa trên mã điều kiện của OpenWeatherMap
    SCORE_MAP = {
        # --- Nguy hiểm cao ---
        "Tornado": 1.0,      # Lốc xoáy -> Tuyệt đối không đi
        "Thunderstorm": 0.9, # Giông bão, sấm sét -> Rất nguy hiểm
        "Squall": 0.8,       # Gió giật mạnh
        
        # --- Nguy hiểm trung bình (Ảnh hưởng tầm nhìn/đường trơn) ---
        "Rain": 0.6,         # Mưa -> Đường trơn, ướt
        "Drizzle": 0.4,      # Mưa phùn -> Hơi khó chịu
        "Snow": 0.5,         # Tuyết (Hiếm ở VN, nhưng gây trơn trượt)
        
        # --- Giảm tầm nhìn (Atmosphere) ---
        "Sand": 0.5, "Dust": 0.5, "Ash": 0.5, # Bụi/Cát/Tro
        "Fog": 0.4,          # Sương mù dày
        "Mist": 0.3,         # Sương mù nhẹ
        "Haze": 0.3, "Smoke": 0.3,
        
        # --- An toàn ---
        "Clouds": 0.1,       # Nhiều mây -> An toàn (0.1 để phân biệt với Clear)
        "Clear": 0.0         # Trời quang -> Hoàn hảo
    }

    # Lấy điểm cơ bản, nếu lạ thì cho 0.2 (an toàn nhưng cảnh giác)
    base_score = SCORE_MAP.get(weather_main, 0.2)
    
    # 2. ĐIỀU CHỈNH THEO GIÓ (Wind Speed Penalty)
    # OpenWeatherMap trả về m/s. 
    # Quy đổi sơ bộ: 10 m/s ~ Cấp 5 (Gió tươi), 20 m/s ~ Cấp 8 (Gió gắt)
    
    if wind_speed >= 25: # ~ Cấp 10 trở lên (Bão)
        base_score = 1.0 # Nguy hiểm tuyệt đối bất kể trời quang hay mưa
    elif wind_speed >= 15: # ~ Cấp 7-8 (Gió rất mạnh)
        base_score = max(base_score, 0.8) # Ít nhất là 0.8
    elif wind_speed >= 10: # ~ Cấp 5-6 (Gió mạnh)
        base_score += 0.2 # Cộng thêm phạt
        
    # Đảm bảo điểm không vượt quá 1.0
    final_score = min(base_score, 1.0)
    
    return round(final_score, 2)

def standardize_traffic_score(duration, distance):
    """
    [VALIDATION PATTERN]
    Tính Traffic Score dựa trên tốc độ trung bình.
    Tốc độ càng chậm (kẹt xe) -> Điểm càng cao (Nguy hiểm/Khó chịu).
    """
    if duration == 0: return 0
    
    # Tính tốc độ trung bình (km/h)
    # distance (m) / 1000 -> km
    # duration (s) / 3600 -> h
    avg_speed_kmh = (distance / 1000) / (duration / 3600)
    
    # Rule-based scoring
    if avg_speed_kmh < 10: # Tắc đường nghiêm trọng
        return 0.9
    elif avg_speed_kmh < 20: # Ùn ứ
        return 0.7
    elif avg_speed_kmh < 40: # Đông đúc
        return 0.4
    else: # Thông thoáng
        return 0.1
    print("--- TEST WEATHER SCORING ---")
    
    # Test 1: Mưa bình thường
    print(f"Mưa, gió nhẹ (5m/s): {standardize_weather_score('Rain', 5)}") 
    # Mong đợi: 0.6

    # Test 2: Trời quang nhưng Bão (Gió 30m/s)
    print(f"Trời quang, gió bão (30m/s): {standardize_weather_score('Clear', 30)}") 
    # Mong đợi: 1.0 (Do gió)

    # Test 3: Sương mù
    print(f"Sương mù, gió nhẹ: {standardize_weather_score('Mist', 2)}") 
    # Mong đợi: 0.3

    # Test 4: Giông bão
    print(f"Giông bão: {standardize_weather_score('Thunderstorm', 10)}") 
    # Mong đợi: 0.9 hoăc cao hơn
    
    # Kịch bản 1: Cháy rừng (Lào/Campuchia)
    test_1 = ['wildfires']
    score_1 = standardize_disaster_score(test_1)
    print(f"Điểm của {test_1}: {score_1}") # Mong đợi: 0.7

    # Kịch bản 2: Mock data Lũ lụt (Hội An)
    test_2 = ['floods']
    score_2 = standardize_disaster_score(test_2)
    print(f"Điểm của {test_2}: {score_2}") # Mong đợi: 1.0

    # Kịch bản 3: Mock data Sạt lở (Hải Vân)
    test_3 = ['landslides']
    score_3 = standardize_disaster_score(test_3)
    print(f"Điểm của {test_3}: {score_3}") # Mong đợi: 0.9

    # Kịch bản 4: Sự kiện có 2 loại (Lấy điểm cao nhất)
    test_4 = ['floods', 'landslides']
    score_4 = standardize_disaster_score(test_4)
    print(f"Điểm của {test_4}: {score_4}") # Mong đợi: 1.0 (vì floods = 1.0)
    
    # Kịch bản 5: Sự kiện không liên quan (Tảng băng)
    test_5 = ['seaLakeIce']
    score_5 = standardize_disaster_score(test_5)
    print(f"Điểm của {test_5}: {score_5}") # Mong đợi: 0.0

    # Kịch bản 6: Rỗng (An toàn)
    test_6 = []
    score_6 = standardize_disaster_score(test_6)
    print(f"Điểm của {test_6}: {score_6}") # Mong đợi: 0.0

def standardize_crowd_score(poi_count: int, current_hour: int, is_weekend: bool) -> float:
    """
    Chuyển đổi số lượng POI thành Crowd Score.
    Input:
        - poi_count (int): Số lượng địa điểm đông đúc xung quanh.
        - current_hour (int): Giờ hiện tại (0-23).
        - is_weekend (bool): Có phải cuối tuần không.
    Output:
        - float: Điểm từ 0.0 (Vắng) đến 1.0 (Chen chúc).
    """
    
    # 1. BASE SCORE (Dựa trên mật độ địa điểm)
    # Giả định: 50 địa điểm trong bán kính 500m là rất đông (Trung tâm Q1)
    if poi_count == 0:
        base_score = 0.0
    elif poi_count < 5:
        base_score = 0.2  # Thưa thớt
    elif poi_count < 15:
        base_score = 0.4  # Trung bình
    elif poi_count < 30:
        base_score = 0.6  # Đông
    elif poi_count < 50:
        base_score = 0.8  # Rất đông
    else:
        base_score = 1.0  # Cực đông
        
    # 2. TIME FACTOR (Điều chỉnh theo thời gian)
    multiplier = 1.0
    
    # Giờ cao điểm ăn uống/du lịch (11h-13h và 17h-21h)
    if (11 <= current_hour <= 13) or (17 <= current_hour <= 21):
        multiplier += 0.2
    elif (0 <= current_hour <= 5): # Đêm khuya
        multiplier -= 0.3
        
    # Cuối tuần thường đông hơn
    if is_weekend:
        multiplier += 0.1
        
    # Tính điểm cuối
    final_score = base_score * multiplier
    
    # Clamping (Kẹp giá trị trong khoảng 0.0 - 1.0)
    final_score = max(0.0, min(final_score, 1.0))
    
    return round(final_score, 2)