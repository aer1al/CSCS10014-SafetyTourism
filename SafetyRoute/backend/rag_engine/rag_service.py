import sys
import os
import ollama
from dotenv import load_dotenv

# --- CẤU HÌNH PATH & IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from graph_retriever import GraphRetriever 

load_dotenv()

# Cấu hình Ollama (Mặc định localhost và llama3)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Tạo client toàn cục cho Ollama
try:
    ollama_client = ollama.Client(host=OLLAMA_HOST)
except:
    ollama_client = None

class RAGService:
    def __init__(self):
        print(f"🔌 Đang khởi động RAG Engine (Mode: Graph ONLY - Ollama {OLLAMA_MODEL})...")
        self.graph_db = None
        
        # Kết nối Neo4j
        try:
            self.graph_db = GraphRetriever()
        except Exception as e:
            print(f"⚠️ Cảnh báo: Không thể kết nối Neo4j. ({e})")

    def _extract_road_name_with_ai(self, question):
        """
        Dùng Ollama để sửa lỗi chính tả và lấy tên đường chuẩn.
        """
        try:
            if not ollama_client:
                return None

            prompt = f"""
            Nhiệm vụ: Trích xuất tên đường hoặc địa điểm từ câu hỏi và sửa lỗi chính tả (viết hoa chữ cái đầu).
            Chỉ trả về DUY NHẤT tên đường. Nếu không tìm thấy tên đường nào cụ thể, trả về "None".
            
            Câu hỏi: "{question}"
            
            Ví dụ:
            - "ngyễn tất thành có kẹt ko" -> Nguyễn Tất Thành
            - "đường 3/2 ra sao" -> Đường 3 Tháng 2
            - "chỗ nào ngập" -> None
            
            Trả về (Chỉ tên, không giải thích):
            """
            
            response = ollama_client.chat(
                model=OLLAMA_MODEL, 
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0}
            )
            
            cleaned_name = response['message']['content'].strip()
            
            # Xử lý hậu kỳ nếu model trả về thừa lời dẫn
            if ":" in cleaned_name:
                cleaned_name = cleaned_name.split(":")[-1].strip()

            if "None" in cleaned_name or len(cleaned_name) > 50:
                return None
            
            # Xóa các ký tự thừa như dấu chấm
            cleaned_name = cleaned_name.replace(".", "").replace('"', "")
            
            return cleaned_name
            
        except Exception as e:
            print(f"⚠️ Lỗi AI Extract (Ollama): {e}")
            return None
            
    def search(self, question, n_results=3):
        """
        Logic: AI Extract (Ollama) -> Graph Search (Neo4j)
        """
        response_data = {
            "road_name": None,
            "graph_results": [],
            "combined_context": ""
        }

        # 1️⃣ Extract tên đường
        road_name = None
        try:
            road_name = self._extract_road_name_with_ai(question)
        except Exception as e:
            print("⚠️ Extract road failed:", e)

        response_data["road_name"] = road_name

        # 2️⃣ GRAPH SEARCH – CHỈ KHI CÓ ROAD NAME
        if road_name and self.graph_db:
            try:
                print(f"🔍 Graph query: {road_name}")
                response_data["graph_results"] = self.graph_db.find_related_risks(road_name)
            except Exception as e:
                print("⚠️ Graph search failed:", e)

        # 3️⃣ BUILD CONTEXT
        context_lines = []

        if response_data["graph_results"]:
            context_lines.append("=== THÔNG TIN KHU VỰC (GRAPH) ===")
            for item in response_data["graph_results"]:
                
                # Định dạng thời gian
                time_info = ""
                if item.get("time_start") not in [None, "N/A"] or item.get("time_end") not in [None, "N/A"]:
                    ts = item.get("time_start", "?")
                    te = item.get("time_end", "?")
                    time_info = f" (Giờ cao điểm: {ts} - {te})"
                
                # Định dạng chuỗi Context mới
                context_lines.append(
                    f"- [{item['type']}] {item['name']}: {item['description']}{time_info}"
                )

        if not context_lines:
            context_lines.append("Chưa có dữ liệu rủi ro cụ thể cho khu vực này.")

        response_data["combined_context"] = "\n".join(context_lines)
        return response_data

# Tạo instance
rag_engine = RAGService()

# ======================================================
# HÀM TEST CASE
# ======================================================

def test_rag_engine():
    print(f"\n--- BẮT ĐẦU TEST RAG ENGINE (GRAPH ONLY - OLLAMA) ---")

    test_cases = [
        "đường nguyễn tất thành ra sao?", 
        "đường có tắc không",             
        "nguyễn văn linh chỗ nào nguy hiểm", 
    ]

    for i, question in enumerate(test_cases):
        print(f"\n[TEST {i+1}] Câu hỏi: {question}")
        try:
            # Gọi hàm search
            result = rag_engine.search(question)
            
            print(f"  > Road Name (AI Extract): {result['road_name']}")
            
            print("  > Combined Context (Kết quả gửi cho Chatbot):")
            print("-------------------------------------------------")
            print(result['combined_context'])
            print("-------------------------------------------------")
            
            if not result['graph_results'] and result['road_name']:
                 print("  *** Ghi chú: Context rỗng dù AI đã tìm được tên đường. Cần kiểm tra lại dữ liệu trong Neo4j. ***")
            elif not result['road_name']:
                 print("  *** Ghi chú: AI không trích xuất được tên đường cụ thể. Kết quả Context là mặc định. ***")

        except Exception as e:
            print(f"  ❌ LỖI KHI CHẠY TEST CASE: {e}")

if __name__ == '__main__':
    test_rag_engine()
