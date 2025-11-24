# file: test.py
from core_logic import apply_risk_weights, find_optimal_route
from traffic import SYSTEM_GRAPH # Đã load xong từ lúc import
from disasters import get_natural_disasters

# 1. Lấy dữ liệu thiên tai (Giả lập hoặc thật)
print("--- Bước 1: Lấy dữ liệu rủi ro ---")
# Giả sử User đang ở HCM
disasters = get_natural_disasters(10.77, 106.70) 

# 2. Áp trọng số lên bản đồ (Chỉ cần làm 1 lần mỗi khi dữ liệu thiên tai cập nhật)
# Trong thực tế, hàm này nên chạy định kỳ (ví dụ 10 phút/lần)
print("--- Bước 2: Cập nhật bản đồ rủi ro ---")
apply_risk_weights(SYSTEM_GRAPH, disaster_zones=disasters)

# 3. Người dùng tìm đường
print("--- Bước 3: Tìm đường ---")
start = (10.7716, 106.7044) # Bitexco
end = (10.7875, 106.7053)   # Zoo

# Tìm đường an toàn
result = find_optimal_route(start, end, mode='safest')

print(f"Kết quả ({result['mode']}):")
print(f" - Quãng đường: {result['distance_m']} mét")
print(f" - Số điểm vẽ: {len(result['geometry'])}")