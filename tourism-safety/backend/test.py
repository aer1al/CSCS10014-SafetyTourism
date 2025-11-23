# backend/test_core_debug.py
from core_logic import calculate_optimal_routes
import json

# Test: Bitexco (Q1) -> Lotte Mart (Q7)
START = (10.7716, 106.7044)
END = (10.7326, 106.6992)

print("--- TEST CORE LOGIC (DEBUG) ---")
result = calculate_optimal_routes(START, END)

if result and 'routes' in result:
    print(f"✅ Status: {result['status']}")
    print(f"🔢 Số lượng tuyến đường SAU KHI XỬ LÝ: {len(result['routes'])}")
    
    for r in result['routes']:
        # Xóa geometry để in cho gọn
        r.pop('geometry', None) 
        print(json.dumps(r, indent=2, ensure_ascii=False))
else:
    print("❌ Lỗi: Không có kết quả trả về.")