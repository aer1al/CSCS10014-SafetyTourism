# file: test_core_logic.py
from core_logic import get_optimal_routes
import time

def run_test_scenario(name, start, end, expect_desc):
    print("\n" + "="*80)
    print(f"🧪 SCENARIO: {name}")
    print(f"🎯 Kỳ vọng: {expect_desc}")
    print("="*80)
    
    t0 = time.time()
    try:
        result = get_optimal_routes(start, end)
        duration = time.time() - t0
        
        if result['status'] == 'success':
            summary = result.get('summary', {})
            hits = result.get('hit_details', {})
            
            print(f"\n✅ KẾT QUẢ TÌM ĐƯỜNG (Mất {duration:.2f}s):")
            print(f"   🚦 Label    : {summary.get('safety_label')} {summary.get('safety_color','').upper()}")
            print(f"   📝 Lý do    : {summary.get('description')}")
            print(f"   📏 Distance : {result.get('distance_km')} km")
            print(f"   ⏱️ ETA      : {summary.get('eta_display')}")
            
            # Check va chạm
            print("\n   🔍 KIỂM TRA VA CHẠM THỰC TẾ:")
            if hits.get('disasters'):
                print(f"      ⛔ Disaster Hit: {hits['disasters']}")
            elif hits.get('weathers'):
                print(f"      🌧️ Weather Hit : {hits['weathers']}")
            else:
                print("      ✅ Không va chạm vùng nguy hiểm nào (AI đã né thành công!)")
                
            # In thử vài tọa độ đầu để xem nó đi hướng nào (Debug)
            # print(f"   📍 5 node đầu tiên: {result['geometry'][:5]}")
            
        else:
            print(f"❌ LỖI: {result.get('message')}")
            
    except Exception as e:
        print(f"🔥 CRASH: {e}")

if __name__ == "__main__":
    
    # CASE 1: Né "Tâm Bão" Nhà Thờ Đức Bà
    # Start: Chợ Bến Thành | End: Hồ Con Rùa (Q3)
    run_test_scenario(
        name="tâm bão fr",
        start=[10.7808, 106.6983], 
        end=[10.7798, 106.6999],
        expect_desc="trong tâm bão, you are cooked fr."
    )

    # CASE 2: Đi vùng an toàn (Q5 -> Q10)
    # Start: Parkson Hùng Vương | End: Vạn Hạnh Mall
    run_test_scenario(
        name="2. ĐƯỜNG AN TOÀN (Safe Zone)",
        start=[10.7558, 106.6629], 
        end=[10.7698, 106.6703],
        expect_desc="Khu vực này sạch bóng mock data -> Label XANH (Green)."
    )

    # CASE 3: Đi qua điểm ngập Nguyễn Hữu Cảnh (Bình Thạnh)
    # Start: Landmark 81 | End: Thảo Cầm Viên
    run_test_scenario(
        name="3. THỬ THÁCH ĐIỂM NGẬP (Flood Test)",
        start=[10.7952, 106.7218], 
        end=[10.7876, 106.7053],
        expect_desc="Nguyễn Hữu Cảnh bị ngập (Mock). AI có thể chọn đi đường Ngô Tất Tố/Điện Biên Phủ để né."
    )