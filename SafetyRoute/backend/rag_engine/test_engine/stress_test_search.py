import sys
import os
import time

# --- SETUP ĐƯỜNG DẪN IMPORT ---
# Thêm thư mục gốc (cha của rag_engine) vào path
# Để Python hiểu rag_engine là một package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import Class tìm kiếm mới
from rag_engine.graph_search import GraphSearcher

# --- MÀU SẮC CHO TERMINAL ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def run_stress_test():
    # Khởi tạo GraphSearcher (Tự động lấy config từ file config.py)
    searcher = GraphSearcher()
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("="*60)
    print("   BẮT ĐẦU STRESS TEST CHỨC NĂNG TÌM KIẾM MỜ (FUZZY SEARCH)")
    print("="*60)
    print(f"{Colors.ENDC}")

    # DANH SÁCH 26 TEST CASE
    # Format: (Input, Expected_Keyword, Should_Find)
    test_cases = [
        # --- NHÓM 1: ĐƯỜNG XÁ (Cơ bản) ---
        ("Nguyễn Văn Cừ", "Nguyễn Văn Cừ", True),       # 1. Chính xác 100%
        ("nguyen van cu", "Nguyễn Văn Cừ", True),       # 2. Không dấu hoàn toàn
        ("NGUYEN VAN CU", "Nguyễn Văn Cừ", True),       # 3. CAPS LOCK
        ("nguyễn văn cừ", "Nguyễn Văn Cừ", True),       # 4. Chữ thường có dấu

        # --- NHÓM 2: ĐƯỜNG XÁ (Khó) ---
        ("nguyen  van  cu", "Nguyễn Văn Cừ", True),     # 5. Dư khoảng trắng
        ("nguyễn vãn cừ", "Nguyễn Văn Cừ", True),       # 6. Sai dấu huyền/ngã (Typo)
        ("duong nguyen van cu", "Nguyễn Văn Cừ", True), # 7. Thêm tiền tố "duong"
        ("lý thường kiệt", "Lý Thường Kiệt", True),     # 8. Test đường khác
        ("ly thuong kiet", "Lý Thường Kiệt", True),     # 9. Test đường khác không dấu

        # --- NHÓM 3: TRƯỜNG HỌC (School) ---
        ("đại học bách khoa", "Bách khoa", True),       # 10. Tên phổ thông
        ("dai hoc bach khoa", "Bách khoa", True),       # 11. Không dấu
        ("truong bach khoa", "Bách khoa", True),        # 12. Gọi tắt
        ("bách khoa", "Bách khoa", True),               # 13. Chỉ gọi tên riêng
        ("đại học khoa học tự nhiên", "Tự nhiên", True),# 14. Trường tên dài
        ("khoa hoc tu nhien", "Tự nhiên", True),        # 15. Tên dài không dấu

        # --- NHÓM 4: ĐỊA ĐIỂM (Place/Tourist) ---
        ("chợ bến thành", "Bến Thành", True),           # 16. Địa điểm nổi tiếng
        ("cho ben thanh", "Bến Thành", True),           # 17. Không dấu
        ("ben thanh", "Bến Thành", True),               # 18. Gọi tắt
        ("chợ bình tây", "Bình Tây", True),             # 19. Chợ khác
        ("cho binh tay", "Bình Tây", True),             # 20. Chợ khác không dấu

        # --- NHÓM 5: EDGE CASES (Lắt léo) ---
        ("   nguyen van cu   ", "Nguyễn Văn Cừ", True), # 21. Khoảng trắng đầu đuôi
        ("nGUyễn VăN Cừ", "Nguyễn Văn Cừ", True),       # 22. Viết hoa thường lộn xộn

        # --- NHÓM 6: NEGATIVE (Phải không tìm thấy) ---
        ("đường lên cung trăng", "", False),            # 23. Không tồn tại
        ("trường hogwarts", "", False),                 # 24. Hư cấu
        ("xyzabc123", "", False),                       # 25. Rác
        ("siêu thị mặt trời", "", False)                # 26. Không có trong data
    ]

    pass_count = 0
    fail_count = 0
    
    start_time = time.time()

    for index, (search_term, expected_keyword, should_find) in enumerate(test_cases, 1):
        # Gọi hàm tìm kiếm từ class mới
        node, labels = searcher.find_node_by_name(search_term)
        
        # Logic kiểm tra kết quả
        is_pass = False
        message = ""

        if should_find:
            # Case mong chờ tìm thấy (Positive)
            if node and expected_keyword.lower() in node['name'].lower():
                is_pass = True
                message = f"Found: '{node['name']}'"
            else:
                is_pass = False
                found_name = node['name'] if node else "None"
                message = f"Expected '{expected_keyword}' but got '{found_name}'"
        else:
            # Case mong chờ KHÔNG tìm thấy (Negative)
            if node is None:
                is_pass = True
                message = "Correctly Not Found"
            else:
                is_pass = False
                message = f"Expected None but found '{node['name']}'"

        # In kết quả ra màn hình
        status_color = Colors.OKGREEN if is_pass else Colors.FAIL
        status_text = "PASS" if is_pass else "FAIL"
        
        print(f"Test #{index:02d}: Input='{search_term.ljust(25)}' | {status_color}[{status_text}]{Colors.ENDC} -> {message}")

        if is_pass:
            pass_count += 1
        else:
            fail_count += 1

    end_time = time.time()
    duration = end_time - start_time

    # --- TỔNG KẾT ---
    print("\n" + "="*60)
    print(f"{Colors.BOLD}TỔNG KẾT KẾT QUẢ KIỂM THỬ{Colors.ENDC}")
    print("="*60)
    print(f"Tổng số Test case: {len(test_cases)}")
    print(f"{Colors.OKGREEN}✅ SỐ LƯỢNG PASS : {pass_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}❌ SỐ LƯỢNG FAIL : {fail_count}{Colors.ENDC}")
    print(f"⏱️ Thời gian chạy  : {duration:.2f} giây")
    print("="*60)
    
    # Tính điểm
    if len(test_cases) > 0:
        score = (pass_count / len(test_cases)) * 100
        if score == 100:
            print(f"{Colors.OKGREEN}{Colors.BOLD}🏆 TUYỆT VỜI! HỆ THỐNG TÌM KIẾM HOẠT ĐỘNG HOÀN HẢO!{Colors.ENDC}")
        elif score >= 80:
            print(f"{Colors.OKCYAN}{Colors.BOLD}✨ KHÁ TỐT! Cần tinh chỉnh nhỏ vài trường hợp.{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}⚠️ CẢNH BÁO: Cần xem lại thuật toán tìm kiếm.{Colors.ENDC}")
    
    # Đóng kết nối
    searcher.close()

if __name__ == "__main__":
    run_stress_test()