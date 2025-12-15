import chromadb
import os
import json

# --- CẤU HÌNH ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, 'chroma_db')

class SafetyRetriever:
    def __init__(self):
        print("🔌 Đang kết nối vào Vector Database...")
        if not os.path.exists(DB_PATH):
            raise Exception(f"❌ Không tìm thấy DB tại {DB_PATH}. Hãy chạy build_db.py trước!")
            
        self.client = chromadb.PersistentClient(path=DB_PATH)
        # Lưu ý: Tên collection phải khớp với lúc build (safety_knowledge)
        self.collection = self.client.get_collection(name="safety_knowledge")
        print("✅ Kết nối thành công! Sẵn sàng tra cứu.")

    def query(self, user_question, n_results=3):
        """
        Tìm kiếm thông tin dựa trên câu hỏi tự nhiên
        """
        print(f"🔍 Đang tìm kiếm: '{user_question}'")
        
        results = self.collection.query(
            query_texts=[user_question],
            n_results=n_results,
            # Chỉ lấy các trường cần thiết
            include=["documents", "metadatas", "distances"] 
        )
        
        # Xử lý kết quả trả về cho đẹp đội hình
        final_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                meta = results['metadatas'][0][i]
                doc = results['documents'][0][i]
                
                # Convert string JSON lại thành List/Dict để code dễ dùng
                try:
                    geometry = json.loads(meta['geometry'])
                    affected_roads = json.loads(meta['affected_roads'])
                except:
                    geometry = {}
                    affected_roads = []

                item = {
                    "name": doc.split('.')[0], # Lấy phần đầu của description làm tên tạm
                    "description": doc,
                    "type": meta['type'],
                    "severity": meta['severity'],
                    "affected_roads": affected_roads,
                    "geometry": geometry,
                    "time_active": f"{meta['time_start']} - {meta['time_end']}"
                }
                final_results.append(item)
        
        return final_results

# --- PHẦN TEST CHẠY THỬ ---
if __name__ == "__main__":
    # Khởi tạo công cụ tìm kiếm
    retriever = SafetyRetriever()
    
    # Giả lập câu hỏi người dùng
    questions = [
        "Chỗ nào hay ngập nước?",
        "Khu vực nào đông đúc kẹt xe?",
        "Tìm chỗ vui chơi về đêm" # Câu này sẽ test cái Bùi Viện bạn vừa thêm (nếu có)
    ]
    
    print("\n" + "="*50)
    for q in questions:
        print(f"❓ User hỏi: {q}")
        answers = retriever.query(q, n_results=1)
        
        if answers:
            top_hit = answers[0]
            print(f"💡 Tìm thấy: {top_hit['description']}")
            print(f"⚠️ Mức độ rủi ro: {top_hit['severity']}")
            print(f"🛣️ Đường bị ảnh hưởng: {top_hit['affected_roads'][:3]}...")
        else:
            print("❌ Không tìm thấy thông tin.")
        print("-" * 30)