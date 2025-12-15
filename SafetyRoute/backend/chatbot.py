from ollama import Client
import os
from dotenv import load_dotenv
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
load_dotenv()

# Cấu hình Ollama
# Nếu chạy trên máy local thì mặc định là http://localhost:11434
# Nếu chạy server riêng thì đổi IP ở file .env hoặc sửa trực tiếp tại đây
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Tên model (Cần chạy 'ollama pull llama3' hoặc model bạn muốn trước)
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma3:1b") 

# ============================================================
# UTILITY: LẤY TIME SLOT
# ============================================================
def get_time_slot():
    hour = datetime.now().hour
    if 6 <= hour < 9:
        return "SÁNG (giờ cao điểm)"
    elif 9 <= hour < 16:
        return "TRƯA"
    elif 16 <= hour < 19:
        return "CHIỀU (giờ cao điểm)"
    else:
        return "TỐI"

# ============================================================
# CHATBOT CLASS (OLLAMA VERSION)
# ============================================================

class ChatBot:
    def __init__(self):
        # Khởi tạo Client kết nối đến Ollama
        try:
            self.client = Client(host=OLLAMA_HOST)
            self.model = MODEL_NAME
            print(f"🔌 ChatBot đã kết nối Ollama tại {OLLAMA_HOST} (Model: {self.model})")
        except Exception as e:
            print(f"❌ Lỗi kết nối Ollama: {e}")

    def _generate_response(self, prompt: str) -> str:
        """Hàm nội bộ để gọi Ollama và xử lý lỗi"""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7} # Tùy chỉnh độ sáng tạo
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"🔥 Lỗi khi gọi model: {e}")
            return "Xin lỗi, hệ thống AI đang gặp sự cố kết nối."

    # ========================================================
    # CASE 1: CHAT THƯỜNG (GREETING / INFO)
    # ========================================================
    def generate_general_chat(self, message: str) -> str:
        prompt = f"""
        Bạn là trợ lý thân thiện.
        Trả lời ngắn gọn, tự nhiên bằng Tiếng Việt.
        Không phân tích giao thông.
        Không dùng dữ liệu hệ thống.

        Câu hỏi:
        {message}
        """
        return self._generate_response(prompt)

    # ========================================================
    # CASE 2: ROUTING + GRAPH RAG
    # ========================================================
    def generate_route_response(self, user_message: str, context: str, time_slot: str) -> str:
        prompt = f"""
        Bạn là hệ thống phân tích giao thông.
        CHỈ sử dụng dữ liệu được cung cấp bên dưới.

        Thời điểm hiện tại: {time_slot}

        Dữ liệu khu vực (Context):
        {context}

        Yêu cầu người dùng:
        {user_message}

        NHIỆM VỤ:
        - Trước hết hãy nói thông tin tổng quát về khu vực user hỏi ngắn gọn, không dài dòng, nhưng phải hữu ích, phù hợp.
        - Dựa vào dữ liệu khu vực, hãy xác định thêm các khu vực như Chợ / Trường / Công Trình /../ gây ảnh hưởng tới nơi user hỏi. Chú ý tới thời gian.

        BẮT BUỘC trả lời theo format sau (Không thêm lời dẫn thừa):

        Thời điểm: {time_slot}
        Tình trạng chung:
        Yếu tố ảnh hưởng:
        Đánh giá:
        """
        return self._generate_response(prompt)

    # ========================================================
    # CASE 3: PHÂN TÍCH LỘ TRÌNH ĐÃ TÍNH TOÁN
    # ========================================================
    def generate_safety_advice(self, user_query, route_result, rag_context=""):
        try:
            summary = route_result.get("summary", {})
            dist = route_result.get("distance_km", 0)
            dur = route_result.get("duration_min", 0)
            risks = route_result.get("risk_summary", {})

            prompt = f"""
            Bạn đang đóng vai người ngồi sau xe, phân tích lộ trình cho tài xế.

            DỮ LIỆU LỘ TRÌNH:
            - Quãng đường: {dist} km
            - Thời gian: {dur} phút
            - Đánh giá chung: {summary.get('safety_label')} ({summary.get('description')})

            CẢNH BÁO:
            - Kẹt xe: {risks.get('traffic_level', 'Thấp')}
            - Đám đông: {risks.get('crowd_level', 'Thấp')}
            - Thời tiết/Thiên tai: {risks.get('disaster_status', 'Không có')}

            ĐIỂM ĐEN KHU VỰC:
            {rag_context}

            CÂU HỎI:
            {user_query}

            YÊU CẦU:
            - Nói như lời khuyên tự nhiên bằng Tiếng Việt.
            - Nếu an toàn → nói yên tâm.
            - Nếu có rủi ro → chỉ rõ khu vực cần chú ý.
            """
            return self._generate_response(prompt)

        except Exception:
            return "Lộ trình này tạm ổn, bạn cứ đi theo hướng dẫn trên bản đồ nhé."
