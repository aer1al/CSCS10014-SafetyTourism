import sys
import os
import time

# --- SETUP ĐƯỜNG DẪN IMPORT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rag_engine.intent_router import IntentRouter

# --- MÀU SẮC ---
class Colors:
    HEADER = '\033[95m'
    PASS = '\033[92m' # Xanh lá
    FAIL = '\033[91m' # Đỏ
    WARN = '\033[93m' # Vàng
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def run_stress_test():
    print(f"{Colors.HEADER}⏳ Đang khởi động Intent Router với model Gemma:2b...{Colors.ENDC}")
    router = IntentRouter()
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("="*70)
    print("   STRESS TEST: PHÂN LOẠI Ý ĐỊNH (ROUTER CLASSIFICATION)")
    print("="*70)
    print(f"{Colors.ENDC}")

    # DANH SÁCH 30 TEST CASE
    # Format: (Input, Expected_Intent, Expected_Entity_Keyword)
    # Expected_Entity_Keyword: Từ khóa bắt buộc phải có trong Entity tìm được (để check đúng tên)
    test_cases = [
        # --- NHÓM 1: ĐƯỜNG XÁ (STREET) ---
        ("Đường Nguyễn Văn Cừ ngập không?", "STREET", "Nguyễn Văn Cừ"),
        ("Ngã tư Hàng Xanh đang kẹt xe", "STREET", "Hàng Xanh"),
        ("Cầu Sài Gòn đi được không ad", "STREET", "Cầu Sài Gòn"),
        ("Đại lộ Võ Văn Kiệt có tai nạn", "STREET", "Võ Văn Kiệt"),
        ("Xa lộ Hà Nội đông không", "STREET", "Xa lộ Hà Nội"),
        ("Đường 3 tháng 2", "STREET", "3 tháng 2"),
        ("Phố đi bộ Nguyễn Huệ", "STREET", "Nguyễn Huệ"), # Hybrid logic sẽ bắt từ "Phố"
        ("Hầm Thủ Thiêm có đóng cửa không", "STREET", "Thủ Thiêm"),
        ("Đường cao tốc Long Thành", "STREET", "Long Thành"),
        ("Kẹt xe ở vòng xoay Dân Chủ", "STREET", "Dân Chủ"),

        # --- NHÓM 2: ĐỊA ĐIỂM (PLACE) ---
        ("Chợ Bến Thành giờ này đông không", "PLACE", "Bến Thành"),
        ("Trường Đại học Bách Khoa kẹt xe không", "PLACE", "Bách Khoa"),
        ("Khu du lịch Suối Tiên", "PLACE", "Suối Tiên"),
        ("Bệnh viện Chợ Rẫy", "PLACE", "Chợ Rẫy"),
        ("Sân bay Tân Sơn Nhất", "PLACE", "Tân Sơn Nhất"),
        ("Đến Dinh Độc Lập đi đường nào", "PLACE", "Dinh Độc Lập"),
        ("Landmark 81 có chỗ đậu xe không", "PLACE", "Landmark 81"),
        ("Bến xe Miền Đông mới", "PLACE", "Miền Đông"),
        ("Ùn tắc trước cổng trường Nguyễn Du", "PLACE", "Nguyễn Du"), # Tricky: Hỏi ùn tắc nhưng tại địa điểm
        ("Chợ Bà Chiểu bán chưa", "PLACE", "Bà Chiểu"),

        # --- NHÓM 3: KHÔNG CÓ TIỀN TỐ (Khó hơn) ---
        ("Nguyễn Trãi kẹt không", "STREET", "Nguyễn Trãi"), # Model phải tự đoán là đường
        ("Lê Lợi ngập nước", "STREET", "Lê Lợi"),
        ("Aeon Mall Bình Tân", "PLACE", "Aeon Mall"),

        # --- NHÓM 4: CHAT/RÁC (CHAT) ---
        ("Xin chào bạn", "CHAT", ""),
        ("Bạn tên là gì vậy", "CHAT", ""),
        ("Cảm ơn bot nha", "CHAT", ""),
        ("Hello", "CHAT", ""),
        ("Hôm nay trời đẹp quá", "CHAT", ""),
        ("Chỉ đường cho tôi", "CHAT", ""), # Không có tên cụ thể -> CHAT hoặc hỏi lại
        ("Con gà cục tác lá chanh", "CHAT", "")
    ]

    pass_count = 0
    fail_count = 0
    start_time = time.time()

    for i, (text, exp_intent, exp_entity) in enumerate(test_cases, 1):
        # Gọi Router
        actual_intent, actual_entity = router.detect_intent(text)
        
        # Kiểm tra Intent
        intent_match = (actual_intent == exp_intent)
        
        # Kiểm tra Entity (Chỉ check nếu không phải CHAT)
        entity_match = True
        if exp_intent != "CHAT":
            if exp_entity.lower() not in actual_entity.lower():
                entity_match = False

        # Đánh giá kết quả
        is_pass = intent_match and entity_match
        
        # In ra màn hình
        status = f"{Colors.PASS}[PASS]{Colors.ENDC}" if is_pass else f"{Colors.FAIL}[FAIL]{Colors.ENDC}"
        print(f"#{i:02d} Input: '{text[:25].ljust(25)}' | Expect: {exp_intent} | Got: {actual_intent} -> {status}")
        
        if not is_pass:
            print(f"    ⚠️  Lỗi chi tiết: Mong đợi '{exp_intent}' - '{exp_entity}' | Thực tế: '{actual_intent}' - '{actual_entity}'")

        if is_pass:
            pass_count += 1
        else:
            fail_count += 1

    duration = time.time() - start_time

    # --- TỔNG KẾT ---
    print("\n" + "="*70)
    print(f"{Colors.BOLD}KẾT QUẢ KIỂM THỬ ROUTER (MODEL: gemma:2b){Colors.ENDC}")
    print("="*70)
    print(f"Tổng số Test case: {len(test_cases)}")
    print(f"{Colors.PASS}✅ PASS: {pass_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}❌ FAIL: {fail_count}{Colors.ENDC}")
    print(f"⏱️  Thời gian: {duration:.2f}s (Trung bình: {duration/len(test_cases):.2f}s/req)")
    print("="*70)

    if pass_count >= 25:
        print(f"{Colors.PASS}🏆 TUYỆT VỜI! Model hoạt động rất ổn định.{Colors.ENDC}")
    elif pass_count >= 20:
        print(f"{Colors.WARN}⚠️  KHÁ. Cần xem lại các case thất bại (thường là do không có prefix 'đường/chợ').{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}💀 CẢNH BÁO. Logic phân loại đang có vấn đề.{Colors.ENDC}")

if __name__ == "__main__":
    run_stress_test()