# file: test_core.py
from core_logic import engine
import json
import time

# Tọa độ HCM (Lat, Lng)
# Điểm đi: Chợ Bến Thành
start_coords = [10.7721, 106.6983]
# Điểm đến: Dinh Độc Lập
end_coords = [10.7769, 106.6953]

print("🧠 Đang khởi động bộ não tìm đường (Core Logic)...")
start_time = time.time()

# Gọi hàm tìm đường (Giả lập xe máy)
result = engine.get_optimal_routes(
    start_coords, 
    end_coords, 
    vehicle_mode="motorbike",
    preferences={"traffic": 1.0, "weather": 1.0, "disaster": 1.0}
)

duration = time.time() - start_time

print(f"\n⏱️ Xử lý xong trong {duration:.2f} giây!")
print("-" * 50)

if "status" in result and result["status"] == "success":
    print(f"✅ TRẠNG THÁI: {result['status'].upper()}")
    print(f"📍 Lộ trình: {result['name']}")
    print(f"📏 Khoảng cách: {result['distance_km']} km")
    print(f"⏳ Thời gian dự kiến: {result['summary']['eta_display']}")
    print(f"🛡️ Đánh giá an toàn: {result['summary']['safety_label']}")
    print(f"📝 Mô tả: {result['summary']['description']}")
    
    # In thử vài điểm tọa độ để chắc chắn có đường
    path_len = len(result['geometry'])
    print(f"🗺️ Geometry: Có {path_len} điểm tọa độ (Hiển thị 3 điểm đầu):")
    print(f"   {result['geometry'][:3]} ...")
    
    # Kiểm tra đường phụ (Alternatives)
    if "alternatives" in result:
        print(f"\n🔀 Tìm thấy thêm {len(result['alternatives'])} đường phụ.")
else:
    print("❌ LỖI TÌM ĐƯỜNG:")
    print(json.dumps(result, indent=2, ensure_ascii=False))