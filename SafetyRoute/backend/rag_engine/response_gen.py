# rag_engine/response_gen.py
from .llm_client import LLMClient
from .json_to_text import TrafficReportFormatter  # <--- Import class mới

class ResponseGenerator:
    def __init__(self):
        self.llm = LLMClient()

    def generate(self, user_input, context_data):
        if not context_data:
            return "Xin lỗi, tôi không tìm thấy thông tin về địa điểm này trong hệ thống dữ liệu."

        # BƯỚC 1: CHUYỂN JSON -> TEXT BÁO CÁO (Dùng module riêng)
        structured_text = TrafficReportFormatter.format(context_data)
        
        # BƯỚC 2: GỬI CHO LLM
        prompt = f"""
        Bạn là Trợ lý Giao thông Safety Tourism.
        Dưới đây là Báo cáo tình trạng giao thông đã được chuẩn hóa (Structured Report):

        {structured_text}
        
        NHIỆM VỤ CỦA BẠN:
        Đọc báo cáo trên và trả lời câu hỏi của người dùng: "{user_input}"
        
        YÊU CẦU ĐỊNH DẠNG VÀ PHONG CÁCH TRẢ LỜI:
        1. **Độ dài & Phong cách:** Trả lời chi tiết, súc tích, độ dài vừa phải (khoảng 5-8 dòng). Dùng giọng điệu cảnh báo, chuyên nghiệp.
        2. **Sử dụng Markdown:** BẮT BUỘC sử dụng Markdown (gạch đầu dòng `-`) để chia bố cục, giúp câu trả lời dễ đọc và nổi bật thông tin quan trọng.
        3. **Nội dung:** PHẢI bao gồm đủ 3 phần chính (Thời tiết, Rủi ro, Ùn tắc) nếu có dữ liệu.
        
        QUY TẮC XỬ LÝ DỮ LIỆU:
        - **Dịch thuật:** Dữ liệu "Nguyên nhân gốc" (tiếng Anh) phải được dịch mượt mà sang tiếng Việt.
        - **Cảnh báo:** Nếu có Hazard Critical, mưa, hoặc giờ cao điểm, phải cảnh báo mạnh mẽ.

        TRẢ LỜI (Theo định dạng Markdown, Tiếng Việt):
        """
        
        return self.llm.send_prompt(prompt)

    def chat_casual(self, user_input):
        return self.llm.send_prompt(f"User: '{user_input}'. Trả lời xã giao, thân thiện, ngắn gọn.")