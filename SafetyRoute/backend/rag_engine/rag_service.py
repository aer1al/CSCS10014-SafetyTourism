import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- CẤU HÌNH PATH & IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import đúng tên module bạn đang có
from retriever import SafetyRetriever       
from graph_retriever import GraphRetriever  

load_dotenv()

# Cấu hình AI (Dùng để bắt tên đường chính xác)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

class RAGService:
    def __init__(self):
        print("🔌 Đang khởi động RAG Engine (Mode: Graph Priority)...")
        self.vector_db = None
        self.graph_db = None
        
        # 1. Kết nối ChromaDB
        try:
            self.vector_db = SafetyRetriever()
        except Exception as e:
            print(f"⚠️ Cảnh báo: Không thể kết nối ChromaDB. ({e})")

        # 2. Kết nối Neo4j
        try:
            self.graph_db = GraphRetriever()
        except Exception as e:
            print(f"⚠️ Cảnh báo: Không thể kết nối Neo4j. ({e})")

    def _extract_road_name_with_ai(self, question):
        """
        Dùng AI để sửa lỗi chính tả và lấy tên đường chuẩn.
        """
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Nhiệm vụ: Trích xuất tên đường hoặc địa điểm từ câu hỏi và sửa lỗi chính tả (viết hoa chữ cái đầu).
            Chỉ trả về DUY NHẤT tên đường. Nếu không tìm thấy tên đường nào cụ thể, trả về "None".
            
            Câu hỏi: "{question}"
            
            Ví dụ:
            - "ngyễn tất thành có kẹt ko" -> Nguyễn Tất Thành
            - "đường 3/2 ra sao" -> Đường 3 Tháng 2
            - "chỗ nào ngập" -> None
            
            Trả về (Chỉ tên):
            """
            response = model.generate_content(prompt)
            cleaned_name = response.text.strip()
            
            if "None" in cleaned_name or len(cleaned_name) > 50:
                return None
            return cleaned_name
        except Exception as e:
            print(f"⚠️ Lỗi AI Extract: {e}")
            return None
            
    def search(self, question, n_results=3):
        """
        Logic MỚI: AI Extract -> Graph Search (Chính) -> Vector Search (Phụ)
        """
        response_data = {
            "vector_results": [],
            "graph_results": [],
            "combined_context": "",
            "extracted_entity": None
        }

        # ---------------------------------------------------------
        # BƯỚC 1: XÁC ĐỊNH MỤC TIÊU (Entity Extraction)
        # ---------------------------------------------------------
        road_name = self._extract_road_name_with_ai(question)
        response_data["extracted_entity"] = road_name
        
        if road_name:
            print(f"🎯 AI xác định mục tiêu: '{road_name}'")
        else:
            print("INFO: Không tìm thấy tên đường cụ thể trong câu hỏi.")

        # ---------------------------------------------------------
        # BƯỚC 2: TÌM KIẾM GRAPH (ƯU TIÊN TUYỆT ĐỐI)
        # Chỉ chạy khi AI bắt được tên đường
        # ---------------------------------------------------------
        if self.graph_db and road_name:
            print(f"🔍 Graph đang truy vấn trực tiếp cho: '{road_name}'")
            # Gọi hàm find_related_risks mà bạn đã sửa trong graph_retriever.py
            # (Hàm này giờ đã lọc chỉ lấy Chợ/Trường/RiskZone)
            related_nodes = self.graph_db.find_related_risks(road_name)
            response_data["graph_results"].extend(related_nodes)

        # ---------------------------------------------------------
        # BƯỚC 3: TÌM KIẾM VECTOR (BỔ TRỢ)
        # Vẫn cần chạy để tìm các đoạn văn mô tả sự cố (nếu có)
        # ---------------------------------------------------------
        if self.vector_db:
            try:
                # Nếu có tên đường -> Tìm theo tên đường cho sát
                # Nếu không (hỏi chung chung) -> Tìm theo cả câu hỏi
                search_query = road_name if road_name else question
                
                # print(f"📚 Vector đang tìm bổ sung cho: '{search_query}'")
                response_data["vector_results"] = self.vector_db.query(search_query, n_results)
            except Exception as e:
                print(f"⚠️ Lỗi Vector Search: {e}")

        # ---------------------------------------------------------
        # BƯỚC 4: TỔNG HỢP DỮ LIỆU (CONTEXT)
        # ---------------------------------------------------------
        context_lines = []
        
        # A. Đưa thông tin Graph lên đầu (QUAN TRỌNG NHẤT)
        if response_data["graph_results"]:
            context_lines.append("=== CẤU TRÚC KHU VỰC (GRAPH DATA) ===")
            for item in response_data["graph_results"]:
                # Format: [Market] Chợ Xóm Chiếu - Nằm trên đường này
                info = f"- [{item['type']}] {item['name']}: {item['description']}"
                context_lines.append(info)

        # B. Đưa thông tin Vector xuống dưới (Tham khảo thêm)
        if response_data["vector_results"]:
            context_lines.append("\n=== GHI NHẬN SỰ CỐ/TIN TỨC (VECTOR DATA) ===")
            for item in response_data["vector_results"]:
                # Chỉ lấy những tin có độ tin cậy cao hoặc liên quan trực tiếp
                line = f"- {item['description']} (Mức độ: {item.get('severity', 'N/A')})"
                context_lines.append(line)

        # Nếu không tìm thấy gì cả ở cả 2 nơi
        if not context_lines:
            context_lines.append("Hệ thống chưa có dữ liệu cụ thể về địa điểm này.")

        response_data["combined_context"] = "\n".join(context_lines)
        return response_data

# Tạo instance
rag_engine = RAGService()