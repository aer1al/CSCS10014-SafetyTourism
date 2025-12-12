import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Cấu hình API Key
genai.configure(api_key=os.getenv("AIzaSyAxA1IHzYIKGrMLo8jgaD3A55sBNZ_ud9s"))

def clean_json_string(text):
    """Làm sạch chuỗi JSON trả về từ AI"""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text

# file: chatbot.py

def generate_safety_advice(user_query, route_result):
    """
    Tư vấn an toàn KHI ĐÃ CÓ lộ trình (GraphRAG)
    """
    try:
        # --- [DEBUG] IN DỮ LIỆU NHẬN ĐƯỢC RA TERMINAL ---
        print("\n🔍 [CHATBOT DEBUG] Dữ liệu nhận được từ Core Logic:")
        print(f"   - Safety Label: {route_result.get('summary', {}).get('safety_label')}")
        print(f"   - Disasters Hit: {route_result.get('hit_details', {}).get('disasters')}")
        print("-" * 50)
        # -------------------------------------------------

        # Lấy dữ liệu chi tiết
        summary = route_result.get('summary', {})
        risks = route_result.get('risk_summary', {})
        details = route_result.get('hit_details', {})
        
        # Xử lý danh sách thiên tai (tránh None)
        disaster_list = details.get('disasters', [])
        weather_list = details.get('weathers', [])
        
        # Tạo Context (Bối cảnh) cho AI
        # Mẹo: Đưa thông tin nguy hiểm lên đầu tiên để AI chú ý
        graph_context = f"""
        THÔNG TIN QUAN TRỌNG NHẤT (BẮT BUỘC CHÚ Ý):
        1. MỨC ĐỘ CẢNH BÁO: {summary.get('safety_label', 'Không rõ')}
        2. DANH SÁCH THIÊN TAI: {', '.join(disaster_list) if disaster_list else 'Không có'}
        
        THÔNG TIN PHỤ (THAM KHẢO):
        - Quãng đường: {route_result.get('distance_km')} km
        - Thời gian: {route_result.get('duration_min')} phút
        - Lý do cảnh báo: {summary.get('description')}
        - Giao thông: {risks.get('traffic_level')} (Low=Vắng, High=Kẹt)
        """

        # Prompt (Kịch bản)
        prompt = f"""
        Bạn là Trợ lý An toàn (Safety Assistant).
        Người dùng hỏi: "{user_query}"
        
        Dữ liệu hệ thống phân tích được:
        {graph_context}
        
        YÊU CẦU XỬ LÝ:
        1. ƯU TIÊN SỐ 1: Nhìn mục "MỨC ĐỘ CẢNH BÁO" và "DANH SÁCH THIÊN TAI".
           - Nếu thấy chữ "CỰC KỲ NGUY HIỂM" hoặc có tên Thiên tai (ví dụ: Cháy, Bão, Ngập), bạn PHẢI ngăn cản người dùng.
           - Tuyệt đối KHÔNG được nói "đường thông thoáng" hay "an toàn" trong trường hợp này, dù giao thông có Low đi nữa.
           
        2. Nếu cảnh báo là "An toàn" (Xanh):
           - Báo tin vui, chúc thượng lộ bình an.
           
        3. Trả lời ngắn gọn (dưới 3 câu), giọng điệu quan tâm, nghiêm túc nếu có nguy hiểm.
        """

        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"🔥 Lỗi Chatbot Logic: {e}")
        return f"Xin lỗi, tôi đang gặp sự cố kỹ thuật. ({str(e)})"
    
def generate_general_chat(user_query):
    """
    Hàm chat tự do KHI CHƯA CÓ lộ trình.
    AI sẽ đóng vai hướng dẫn viên, nhắc user tìm đường.
    """
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        prompt = f"""
        Bạn là Trợ lý ảo của ứng dụng "Safety Route" (Bản đồ an toàn tại TP.HCM).
        Tên bạn là Safety Bot.
        
        Người dùng đang hỏi: "{user_query}"
        Hiện tại người dùng CHƯA chọn lộ trình trên bản đồ.
        
        Nhiệm vụ của bạn:
        1. Nếu người dùng chào hỏi: Hãy chào lại thân thiện và giới thiệu tính năng tìm đường an toàn tránh cướp giật, ngập lụt.
        2. Nếu người dùng hỏi về một địa điểm: Hãy giới thiệu sơ qua về địa điểm đó và nhắc họ: "Bạn có muốn tôi chỉ đường đến đó không?"
        3. Nếu người dùng hỏi linh tinh: Hãy trả lời ngắn gọn và hướng họ về việc tìm đường.
        
        Văn phong: Thân thiện, ngắn gọn, Tiếng Việt tự nhiên.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Xin chào! Tôi là Safety Bot. Bạn hãy nhập điểm đi và đến để tôi phân tích rủi ro nhé!"