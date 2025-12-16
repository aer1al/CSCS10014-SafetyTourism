import sys
import os
import time

# --- SETUP ĐƯỜNG DẪN IMPORT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rag_engine.response_gen import ResponseGenerator

# --- MÀU SẮC ---
class Colors:
    HEADER = '\033[95m'
    PASS = '\033[92m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def run_gen_test():
    print(f"{Colors.HEADER}⏳ Đang khởi động Response Generator (Gemma:2b)...{Colors.ENDC}")
    generator = ResponseGenerator()
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("="*70)
    print("   STRESS TEST: SINH CÂU TRẢ LỜI (GENERATOR QUALITY)")
    print("="*70)
    print(f"{Colors.ENDC}")

    # DANH SÁCH TEST CASE (Dữ liệu giả lập JSON)
    test_cases = [
        # --- CASE 1: ĐƯỜNG CÓ NGẬP (Cảnh báo nguy hiểm) ---
        {
            "title": "Đường Ngập Nặng",
            "input_text": "Đường Nguyễn Hữu Cảnh có sao không?",
            "mock_data": {
                "query_type": "street_info",
                "street": "Nguyễn Hữu Cảnh",
                "hazards": [{"type": "Flood", "desc": "Ngập sâu 0.5m do triều cường", "severity": "High"}],
                "places": []
            },
            # Mong đợi: Phải nhắc đến "Ngập" và độ sâu "0.5m"
            "required_keywords": ["ngập", "0.5m"]
        },

        # --- CASE 2: ĐƯỜNG AN TOÀN (Bình thường) ---
        {
            "title": "Đường An Toàn",
            "input_text": "Đường Lê Lợi đi ổn không?",
            "mock_data": {
                "query_type": "street_info",
                "street": "Lê Lợi",
                "hazards": [], # Không có rủi ro
                "places": [{"name": "Saigon Centre", "type": "Tourist"}]
            },
            # Mong đợi: Phải có từ tích cực hoặc không có từ tiêu cực
            "required_keywords": ["an toàn", "bình thường", "ổn"], 
            "forbidden_keywords": ["ngập", "tai nạn"] # Cấm bịa ra tai nạn
        },

        # --- CASE 3: ĐỊA ĐIỂM KẸT XE (Traffic Info) ---
        {
            "title": "Chợ Đông Đúc",
            "input_text": "Chợ Bến Thành giờ này đông không?",
            "mock_data": {
                "query_type": "place_info",
                "name": "Chợ Bến Thành",
                "traffic_info": [
                    {"time": "08:00-18:00", "cause": "Khách du lịch đông đúc", "days": "Cuối tuần"}
                ]
            },
            # Mong đợi: Nhắc đến giờ, nguyên nhân
            "required_keywords": ["đông", "du lịch", "08:00", "18:00"]
        },

        # --- CASE 4: KHÔNG TÌM THẤY DỮ LIỆU (None) ---
        {
            "title": "Không có dữ liệu",
            "input_text": "Đường lên sao hỏa",
            "mock_data": None,
            # Mong đợi: Xin lỗi hoặc báo không thấy
            "required_keywords": ["không tìm thấy", "xin lỗi", "chưa có"]
        },

        # --- CASE 5: CHÀO HỎI XÃ GIAO ---
        {
            "title": "Chào hỏi (Chat Casual)",
            "input_text": "Hello bạn",
            "mock_data": "CHAT_INTENT", # Đánh dấu đặc biệt để test hàm chat_casual
            # Mong đợi: Tên Bot
            "required_keywords": ["safety", "tourism", "bot"]
        }
    ]

    pass_count = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{Colors.BOLD}#{i} TEST: {case['title']}{Colors.ENDC}")
        print(f"   Input: '{case['input_text']}'")
        
        # Gọi hàm generate
        start_t = time.time()
        if case['mock_data'] == "CHAT_INTENT":
            response = generator.chat_casual(case['input_text'])
        else:
            response = generator.generate(case['input_text'], case['mock_data'])
        duration = time.time() - start_t
        
        # In câu trả lời của AI ra để bạn đọc xem có tự nhiên không
        print(f"   {Colors.CYAN}Bot Answer ({duration:.2f}s): {response.strip()}{Colors.ENDC}")

        # KIỂM TRA TỪ KHÓA (Logic chấm điểm)
        response_lower = response.lower()
        is_pass = True
        missing = []
        
        # 1. Check từ khóa bắt buộc (Required)
        # Logic: Với mỗi nhóm từ khóa, ít nhất 1 từ phải xuất hiện (để linh hoạt)
        # Nhưng ở đây tôi làm chặt: Tất cả từ trong list phải xuất hiện (hoặc 1 phần của nó)
        for kw in case.get('required_keywords', []):
            if kw.lower() not in response_lower:
                # Thử check lỏng hơn chút (đề phòng AI viết hoa/thường lạ)
                is_pass = False
                missing.append(kw)

        # 2. Check từ khóa cấm (Forbidden) - Cho case đường an toàn
        bad_word_found = None
        for kw in case.get('forbidden_keywords', []):
            if kw.lower() in response_lower:
                is_pass = False
                bad_word_found = kw

        # KẾT QUẢ
        if is_pass:
            print(f"   -> {Colors.PASS}[PASS] Câu trả lời hợp lệ.{Colors.ENDC}")
            pass_count += 1
        else:
            print(f"   -> {Colors.FAIL}[FAIL]{Colors.ENDC}")
            if missing:
                print(f"      Thiếu từ khóa: {missing}")
            if bad_word_found:
                print(f"      Xuất hiện từ cấm (Hallucination): '{bad_word_found}'")

    # TỔNG KẾT
    print("\n" + "="*60)
    print(f"KẾT QUẢ SINH NGÔN NGỮ (GEN): {pass_count}/{len(test_cases)} PASS")
    print("="*60)

if __name__ == "__main__":
    run_gen_test()