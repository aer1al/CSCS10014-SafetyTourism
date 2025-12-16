# rag_engine/intent_router.py
from .llm_client import LLMClient

class IntentRouter:
    def __init__(self):
        self.llm = LLMClient()

    def detect_intent(self, user_input):
        """
        Phân loại ý định với Prompt tối ưu cho model nhỏ (Gemma/Llama 4B).
        """
        prompt = f"""
        Bạn là hệ thống phân loại câu hỏi giao thông. Hãy phân tích kỹ loại thực thể trong câu hỏi.

        ĐỊNH NGHĨA Ý ĐỊNH (INTENT):
        1. STREET: Nếu thực thể là tên đường, quốc lộ, ngã tư, cầu. (Ví dụ: Đường Nguyễn Trãi, Cầu Sài Gòn).
        2. PLACE: Nếu thực thể là địa điểm cụ thể như: Chợ, Trường học, Bệnh viện, Khu du lịch, Sân bay, Bến xe.
           -> LƯU Ý QUAN TRỌNG: Nếu câu hỏi hỏi về kẹt xe/ùn tắc tại một ĐỊA ĐIỂM (như Chợ, Trường), phải chọn là PLACE.
        3. CHAT: Các câu chào hỏi, cảm ơn, hoặc không chứa tên địa danh nào.

        ĐỊNH DẠNG ĐẦU RA (Chỉ trả về 2 dòng):
        INTENT: [STREET hoặc PLACE hoặc CHAT]
        ENTITY: [Tên thực thể tìm được]

        VÍ DỤ MẪU (Học theo cách phân loại này):
        - Input: "Đường Nguyễn Văn Cừ có ngập không?" -> Output: INTENT: STREET\nENTITY: Nguyễn Văn Cừ
        - Input: "Trường Bách Khoa có kẹt xe không?" -> Output: INTENT: PLACE\nENTITY: Trường Đại học Bách Khoa
        - Input: "Chợ Bến Thành giờ này đông không?" -> Output: INTENT: PLACE\nENTITY: Chợ Bến Thành
        - Input: "Khu du lịch Suối Tiên đi đường nào?" -> Output: INTENT: PLACE\nENTITY: Khu du lịch Suối Tiên
        - Input: "Xin chào, bạn tên gì?" -> Output: INTENT: CHAT\nENTITY: None

        CÂU HỎI CỦA NGƯỜI DÙNG: "{user_input}"
        OUTPUT:
        """
        
        response = self.llm.send_prompt(prompt)
        
        # Fallback: Nếu model trả về None hoặc lỗi
        if not response: return "CHAT", ""

        # Parsing kết quả (Xử lý an toàn hơn)
        intent = "CHAT"
        entity = ""
        
        lines = response.strip().split('\n')
        for line in lines:
            clean_line = line.strip()
            # Xử lý trường hợp model trả về: "INTENT: PLACE" hoặc "**INTENT**: PLACE"
            if "INTENT:" in clean_line.upper():
                parts = clean_line.split(":")
                if len(parts) > 1:
                    intent = parts[1].strip().upper().replace("*", "")
            
            if "ENTITY:" in clean_line.upper():
                parts = clean_line.split(":")
                if len(parts) > 1:
                    entity = parts[1].strip().replace("None", "").replace("*", "")
        
        # --- LOGIC PHỤ TRỢ (HYBRID) ---
        # Model nhỏ đôi khi vẫn sai, ta dùng code Python để sửa lỗi (Hard rules)
        # Nếu entity chứa từ khóa đặc thù, cưỡng chế gán Intent đúng
        entity_lower = entity.lower()
        if "chợ" in entity_lower or "trường" in entity_lower or "khu du lịch" in entity_lower or "bệnh viện" in entity_lower:
            intent = "PLACE"
        elif "đường" in entity_lower or "phố" in entity_lower or "đại lộ" in entity_lower or "cầu" in entity_lower:
            intent = "STREET"
            
        return intent, entity