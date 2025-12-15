import json
import os
import chromadb
from chromadb.utils import embedding_functions

# --- CẤU HÌNH ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, 'dataFilter.json')
DB_PATH = os.path.join(CURRENT_DIR, 'chroma_db')

def build_vector_db():
    print("⚙️  Đang khởi tạo ChromaDB (Vector Database)...")
    
    client = chromadb.PersistentClient(path=DB_PATH)
    collection_name = "safety_knowledge"
    
    # --- SỬA LỖI Ở ĐÂY ---
    # Thay vì delete, ta dùng get_or_create để an toàn hơn
    # Hoặc dùng try-except bắt lỗi NotFoundError
    try:
        client.delete_collection(name=collection_name)
        print(f"🗑️  Đã xóa bộ nhớ cũ '{collection_name}'")
    except Exception: # Bắt tất cả lỗi (kể cả lỗi chưa có DB)
        pass 
        
    collection = client.get_or_create_collection(name=collection_name)
    # ---------------------
    
    # 3. Đọc dữ liệu từ JSON
    if not os.path.exists(DATA_FILE):
        print(f"❌ Lỗi: Không tìm thấy file {DATA_FILE}")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"📂 Đã đọc {len(data)} sự kiện từ file JSON.")
    
    ids = []
    documents = []
    metadatas = []
    
    for item in data:
        ids.append(item['id'])
        # Kết hợp Type + Description
        doc_text = f"{item['type']}. {item['description']}"
        documents.append(doc_text)
        
        # Metadata
        meta = {
            "type": item['type'],
            "severity": item['attributes']['severity'],
            "geometry": json.dumps(item['geometry']),
            "time_start": item['time']['start'],
            "time_end": item['time']['end'],
            "affected_roads": json.dumps(item.get('affected_roads', []))
        }
        metadatas.append(meta)
        
    print("🚀 Đang Vector hóa dữ liệu (Vui lòng đợi)...")
    
    batch_size = 50
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end]
        )
    
    print("-" * 50)
    print(f"✅ HOÀN TẤT! Đã nạp {collection.count()} kiến thức.")
    print(f"💾 Lưu tại: {DB_PATH}")

    # Test
    print("\n🧪 Test thử:")
    test_query = "Tìm chỗ nào vui chơi ồn ào về đêm"
    results = collection.query(query_texts=[test_query], n_results=1)
    print("💡 Tìm thấy:", results['documents'][0][0])

if __name__ == "__main__":
    build_vector_db()