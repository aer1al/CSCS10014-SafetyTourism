from core_logic import get_optimal_routes

# ==========================================
# CẤU HÌNH TEST CASE 1
# ==========================================
# Kịch bản: Đi xuyên qua tâm bão giả lập (W_STORM_Q1) tại Quận 1.
# Vùng bão mock data: lat 10.776, lng 106.700 (Gần Nhà Thờ Đức Bà)

# Điểm đi: Bitexco Financial Tower (Q1)
START_POINT = (10.7715, 106.7044) 

# Điểm đến: Hồ Con Rùa (Q3 - Gần Q1)
END_POINT = (10.7826, 106.6959)   

def run_test():
    print("\n" + "="*60)
    print("🧪 TEST CASE 1: KIỂM TRA ĐI QUA VÙNG BÃO (QUẬN 1)")
    print("="*60)
    print(f"📍 Điểm đi (Start): {START_POINT}")
    print(f"🏁 Điểm đến (End)  : {END_POINT}")
    print("-" * 60)

    try:
        # Gọi hàm Core Logic
        result = get_optimal_routes(START_POINT, END_POINT)

        # In kết quả
        if result['status'] == 'success':
            print(f"✅ TÌM ĐƯỜNG THÀNH CÔNG!")
            print(f"   -----------------------")
            print(f"   📏 Quãng đường      : {result['distance_km']} km")
            print(f"   ⏱️ Thời gian dự kiến: {result['duration_min']} phút")
            print(f"   ⚠️ Thông tin rủi ro : {result['risk_info']}")
            
            # Phân tích nhanh kết quả
            risks = result['risk_info']
            if risks['weather_warning'] or risks['disaster_warning']:
                print(f"\n   => 💡 KẾT LUẬN: Thuật toán ĐÃ NHẬN DIỆN được nguy hiểm trên đường đi.")
                if risks['weather_warning']: print("      - Có cảnh báo Mưa/Bão (Weather) 🌧️")
                if risks['disaster_warning']: print("      - Có cảnh báo Thiên tai (Disaster) 🌋")
            else:
                print(f"\n   => 💡 KẾT LUẬN: Đường đi sạch, hoặc đã né thành công vùng nguy hiểm.")
                
            print(f"   - Số lượng điểm toạ độ trả về: {len(result['geometry'])}")
        else:
            print(f"❌ TÌM ĐƯỜNG THẤT BẠI: {result['message']}")

    except Exception as e:
        print(f"🔥 LỖI KHI CHẠY TEST: {e}")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    run_test()