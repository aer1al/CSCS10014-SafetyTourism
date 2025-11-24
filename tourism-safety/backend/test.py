import time
from core_logic import get_optimal_routes

# --- CẤU HÌNH ĐIỂM TEST (Xuyên qua tâm bão giả lập ở Q1) ---
# Điểm đi: Đại học Luật TP.HCM (Quận 4) - Phía Nam vùng bão
START_POINT = (10.761683, 106.709089) 

# Điểm đến: Hồ Con Rùa (Quận 3) - Phía Bắc vùng bão
END_POINT = (10.782862, 106.695869)

def run_test():
    print("=======================================================")
    print("🚦 BẮT ĐẦU TEST HỆ THỐNG SAFETY TOURISM (MOCK DATA)")
    print("=======================================================")
    print(f"📍 Điểm đi: {START_POINT}")
    print(f"📍 Điểm đến: {END_POINT}")
    print("⚠️  Kịch bản: Lộ trình đi xuyên qua vùng 'Mưa Giông Q1' (Mock Weather)")
    print("-------------------------------------------------------\n")

    # --- TEST 1: CHẾ ĐỘ NHANH NHẤT (FASTEST) ---
    # Kỳ vọng: Đi đường ngắn nhất, chấp nhận lao vào bão/ngập.
    t0 = time.time()
    result_fast = get_optimal_routes(START_POINT, END_POINT, preference="fastest")
    t1 = time.time()
    
    if result_fast and result_fast['status'] == 'success':
        print(f"✅ [FASTEST MODE] Tìm thấy đường sau {t1-t0:.2f}s")
        print(f"   - Quãng đường: {result_fast['distance_km']} km")
        print(f"   - Thời gian (ETA): {result_fast['duration_min']} phút")
        print(f"   - Cảnh báo: {result_fast['risk_info']}")
    else:
        print("❌ [FASTEST] Lỗi tìm đường!")

    print("\n-------------------------------------------------------")

    # --- TEST 2: CHẾ ĐỘ AN TOÀN NHẤT (SAFEST) ---
    # Kỳ vọng: Né vùng bão Q1, đường sẽ dài hơn nhưng an toàn hơn.
    t0 = time.time()
    result_safe = get_optimal_routes(START_POINT, END_POINT, preference="safest")
    t1 = time.time()

    if result_safe and result_safe['status'] == 'success':
        print(f"✅ [SAFEST MODE] Tìm thấy đường sau {t1-t0:.2f}s")
        print(f"   - Quãng đường: {result_safe['distance_km']} km")
        print(f"   - Thời gian (ETA): {result_safe['duration_min']} phút")
        print(f"   - Cảnh báo: {result_safe['risk_info']}")
    else:
        print("❌ [SAFEST] Lỗi tìm đường!")

    # --- SO SÁNH KẾT QUẢ ---
    print("\n=======================================================")
    print("📊 KẾT QUẢ SO SÁNH:")
    if result_fast and result_safe:
        diff_dist = result_safe['distance_km'] - result_fast['distance_km']
        diff_time = result_safe['duration_min'] - result_fast['duration_min']
        
        if diff_dist > 0:
            print(f"👉 Đường AN TOÀN dài hơn đường NHANH: +{diff_dist:.2f} km")
            print(f"👉 Lý do: Thuật toán đã đi vòng để né vùng Mock Weather/Disaster!")
        elif diff_dist == 0:
            print(f"👉 Hai đường giống nhau. (Có thể vùng Mock chưa chặn hết lối đi hoặc Rủi ro chưa đủ lớn)")
        else:
            print("👉 Kì lạ: Đường an toàn lại ngắn hơn?")
            
    print("=======================================================")

if __name__ == "__main__":
    run_test()