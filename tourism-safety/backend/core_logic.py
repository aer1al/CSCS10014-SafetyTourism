from utils import haversine
from disasters import get_natural_disasters
from weather import get_current_weather
from traffic import get_routes_from_mapbox
from standardization import standardize_disaster_score, standardize_weather_score

def check_risks_on_route(route_geometry):
    # 1. Lấy thiên tai (Mock data)
    start_lng, start_lat = route_geometry[0]
    disasters = get_natural_disasters(start_lat, start_lng)
    
    # 2. Lấy thời tiết
    w_main, w_speed = get_current_weather(start_lat, start_lng)
    weather_score = standardize_weather_score(w_main, w_speed)
    
    max_disaster_score = 0.0
    detected_risks = []
    
    # 3. Quét rủi ro (Sampling mỗi 10 điểm)
    step = 10
    for i in range(0, len(route_geometry), step):
        p_lng, p_lat = route_geometry[i]
        for d in disasters:
            # Bán kính 500m (0.5km) cho chính xác trong phố
            if haversine(p_lat, p_lng, d['lat'], d['lng']) <= 0.5:
                d_score = standardize_disaster_score(d['categories_raw'])
                if d_score > max_disaster_score:
                    max_disaster_score = d_score
                if d['name'] not in detected_risks:
                    detected_risks.append(d['name'])
    
    final_risk = max(max_disaster_score, weather_score)
    return final_risk, detected_risks, w_main

def calculate_optimal_routes(start_coords, end_coords):
    """Hàm chính: Trả về 3 key riêng biệt (Logic cũ)"""
    
    routes = get_routes_from_mapbox(start_coords[0], start_coords[1], end_coords[0], end_coords[1])
    if not routes: return None

    analyzed_candidates = []

    for route in routes:
        risk_score, risks, weather = check_risks_on_route(route['geometry'])
        
        # Time Score: 1 giờ = 1.0 cost
        time_score = route['duration'] / 3600.0 
        
        analyzed_candidates.append({
            "data": route,
            "risk_score": risk_score,
            "time_score": time_score,
            "details": {
                "risks": risks,
                "weather": weather,
                "duration_min": round(route['duration']/60)
            }
        })

    # --- TÌM NGƯỜI CHIẾN THẮNG CHO TỪNG HẠNG MỤC ---
    
    # FASTEST (90% Time, 10% Risk)
    best_fast = min(analyzed_candidates, key=lambda x: (0.9 * x['time_score'] + 0.1 * x['risk_score']))
    
    # SAFEST (10% Time, 90% Risk)
    best_safe = min(analyzed_candidates, key=lambda x: (0.1 * x['time_score'] + 0.9 * x['risk_score']))
    
    # BALANCED (50% Time, 50% Risk)
    best_balanced = min(analyzed_candidates, key=lambda x: (0.5 * x['time_score'] + 0.5 * x['risk_score']))

    # --- TRẢ VỀ CẤU TRÚC DICTIONARY (KHÔNG GỘP) ---
    # Helper function để format output
    def format_output(candidate):
        return {
            "summary": candidate['data']['summary'],
            "duration": candidate['details']['duration_min'],
            "distance": round(candidate['data']['distance'] / 1000, 1),
            "risk_level": candidate['risk_score'],
            "risks_found": candidate['details']['risks'],
            "weather": candidate['details']['weather'],
            "geometry": candidate['data']['geometry']
        }

    return {
        "status": "OK",
        "fastest": format_output(best_fast),
        "safest": format_output(best_safe),
        "balanced": format_output(best_balanced)
    }

# --- TEST ---
if __name__ == "__main__":
    # Test: Sài Gòn (Bitexco -> Lotte Q7)
    START = (10.7716, 106.7044)
    END = (10.7326, 106.6992)
    
    print("--- ĐANG TÍNH TOÁN... ---")
    result = calculate_optimal_routes(START, END)
    
    if result:
        # Xóa geometry để in ra terminal cho gọn (fix lỗi del function call cũ)
        if 'fastest' in result: result['fastest'].pop('geometry', None)
        if 'safest' in result: result['safest'].pop('geometry', None)
        if 'balanced' in result: result['balanced'].pop('geometry', None)
        
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Không tìm thấy đường.")