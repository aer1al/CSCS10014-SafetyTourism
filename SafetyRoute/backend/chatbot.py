import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Cấu hình API Key (Lấy từ biến môi trường hoặc hardcode nếu bạn test nhanh)
api_key = os.getenv("GEMINI_API_KEY") 
# Hoặc nếu bạn muốn giữ key cứng như cũ (nhưng ko khuyến khích):
# api_key = "AIzaSyAxA1IHzYIKGrMLo8jgaD3A55sBNZ_ud9s"

if not api_key:
    # Fallback key nếu quên cấu hình .env (Dùng tạm key cũ của bạn)
    api_key = "AIzaSyAxA1IHzYIKGrMLo8jgaD3A55sBNZ_ud9s"

genai.configure(api_key=api_key)

# Cấu hình Model (Dùng bản Flash cho nhanh và rẻ)
MODEL_NAME = 'gemini-2.5-flash' 

# ============================================================================
# CASE 1: TƯ VẤN VỚI LOGIC SUY LUẬN TỰ NHIÊN NHẤT
# ============================================================================
def generate_general_chat(user_query, rag_context="", current_time="Không rõ"):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        prompt = f"""
        Bạn là Chuyên gia Giao thông TP.HCM, tự xưng là Safety Bot.
        
        1. THÔNG TIN ĐẦU VÀO:
        - Câu hỏi: "{user_query}"
        - Thời gian hiện tại: {current_time}
        - DỮ LIỆU ĐỊA ĐIỂM TÌM ĐƯỢC (Graph RAG):
        ---------------------
        {rag_context}
        ---------------------

        2. KIẾN THỨC NỀN TẢNG (Quy tắc Giờ Cao Điểm TP.HCM):
        - Sáng: 07:00 - 09:00 | Chiều: 16:30 - 19:00.
        
        3. NHIỆM VỤ SUY LUẬN (PHẢI TUÂN THỦ TỪNG BƯỚC):
        
        A. PHÂN TÍCH CHUNG:
           - Bắt đầu bằng cách nhận định chung về tuyến đường (Ví dụ: Nguyễn Tất Thành là đường ra cảng, nhiều xe tải) và so sánh với thời gian hiện tại ("{current_time}" có nằm trong/gần Giờ Cao Điểm không?).
           - **TUYỆT ĐỐI KHÔNG DÙNG CỤM TỪ:** "Theo dữ liệu hệ thống", "Theo RAG Context", hay "Dựa trên cơ sở dữ liệu". Hãy nói như thể bạn đã biết thông tin đó rồi.

        B. BỔ SUNG CHI TIẾT (Nếu có trong Context):
           - Nếu Dữ liệu Graph (Market, School, RiskZone) có liên quan, hãy dùng nó để giải thích TẠI SAO đường đông.
           - Ví dụ: Nếu {current_time} là 10:30 (như trong ảnh) và có Chợ (Market), hãy nói: "Dù đã qua giờ cao điểm, khu vực này còn ảnh hưởng bởi Chợ Xóm Chiếu nên xe cộ vẫn di chuyển chậm."
           
        C. ĐỊNH DẠNG TRẢ LỜI (Văn phong chuyên nghiệp, thân thiện, ngắn gọn):
           - Lời chào: Ngắn gọn (Ví dụ: "Chào bạn,").
           - Câu trả lời chính: Trả lời trực tiếp vào tình trạng giao thông + Giải thích bằng kiến thức chung (Giờ cao điểm/Cảng).
           - Câu bổ sung: Lồng ghép thông tin Chợ/Trường học để tăng độ chính xác.
           - Lời khuyên: Kết thúc bằng lời khuyên cụ thể (Ví dụ: nên đi chậm, nên kiểm tra Maps).
        
        4. MẪU TRẢ LỜI MONG MUỐN:
        "Chào bạn, lúc này là {current_time}. [Nhận định chung về Giờ Cao Điểm/Đặc điểm đường Nguyễn Tất Thành]. [Bổ sung về Chợ/Trường học]. Bạn nên [Lời khuyên]."
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Xin lỗi, lỗi xử lý: {str(e)}"

# ============================================================================
# CASE 2: PHÂN TÍCH LỘ TRÌNH ĐÃ CÓ
# User hỏi: "Đường đi này như thế nào?" (Khi đã có bản đồ)
# ============================================================================
def generate_safety_advice(user_query, route_result, rag_context=""):
    try:
        # Lấy thông tin tóm tắt từ JSON đường đi
        summary = route_result.get('summary', {})
        dist = route_result.get('distance_km', 0)
        dur = route_result.get('duration_min', 0)
        risks = route_result.get('risk_summary', {})
        
        model = genai.GenerativeModel(MODEL_NAME)
        
        prompt = f"""
        Bạn đang đóng vai là "người ngồi sau xe" phân tích lộ trình cho tài xế.
        
        1. DỮ LIỆU LỘ TRÌNH (Đã được tính toán):
        - Tổng quãng đường: {dist} km.
        - Thời gian dự kiến: {dur} phút.
        - Đánh giá an toàn chung: {summary.get('safety_label')} ({summary.get('description')}).
        - Cảnh báo cụ thể:
          + Mức độ kẹt xe: {risks.get('traffic_level', 'Thấp')}
          + Mức độ đám đông: {risks.get('crowd_level', 'Thấp')}
          + Thiên tai/Bão: {risks.get('disaster_status', 'Không có')}
        
        2. DỮ LIỆU ĐỊA PHƯƠNG (RAG Context - Các điểm đen cụ thể):
        {rag_context}

        3. CÂU HỎI USER: "{user_query}"

        4. YÊU CẦU TRẢ LỜI:
        - Đừng lặp lại thông số khô khan. Hãy nói như một lời khuyên.
        - Nếu lộ trình AN TOÀN: "Tuyến đường này khá ổn, chỉ mất khoảng {dur} phút cho {dist}km. Hệ thống không phát hiện kẹt xe hay ngập nước."
        - Nếu lộ trình NGUY HIỂM (hoặc có cảnh báo): "Lộ trình này tuy ngắn ({dist}km) nhưng bạn cần cẩn thận đoạn... vì hệ thống phát hiện có [Kẹt xe/Đám đông/Chợ]."
        - Dựa vào RAG Context để chỉ đích danh tên đường/khu vực cần chú ý.
        """

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Hệ thống đang bận, bạn cứ đi theo lộ trình trên bản đồ nhé."
