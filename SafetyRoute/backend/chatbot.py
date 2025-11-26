import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Cấu hình API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def clean_json_string(text):
    """Làm sạch chuỗi JSON trả về từ AI"""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text


def generate_safety_advice(user_query, route_result):
    """
    Tư vấn an toàn KHI ĐÃ CÓ lộ trình (GraphRAG)
    """
    try:
        risks = route_result.get('risk_summary', {})
        details = route_result.get('hit_details', {})
        
        graph_context = f"""
        - Quãng đường: {route_result.get('distance_km')} km
        - Thời gian: {route_result.get('duration_min')} phút
        - Giao thông: {risks.get('traffic_level')}
        - Cảnh báo thời tiết: {', '.join(details.get('weathers', [])) if risks.get('weather_warning') else 'Không'}
        - Cảnh báo thiên tai: {', '.join(details.get('disasters', [])) if risks.get('disaster_warning') else 'Không'}
        - Đám đông: {risks.get('crowd_level')}
        """

        prompt = f"""
        Bạn là trợ lý SafetyRoute. User hỏi: "{user_query}"
        Dữ liệu lộ trình thực tế: {graph_context}
        Hãy trả lời ngắn gọn, cảnh báo rủi ro nếu có. Chúc đi an toàn nếu đường sạch.
        """

        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
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