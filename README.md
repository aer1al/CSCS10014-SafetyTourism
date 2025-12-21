# OptiRoute:
## 1. Giới thiệu & Mục tiêu
**OptiRoute** là giải pháp chatbot thông minh giúp người dùng tra tìm tuyến đường đi phù hợp nhu cầu nhất, cân nhắc các yếu tô như giao thông, rủi ro đô thị (ngập lụt, tai nạn) và thông tin địa điểm (trường học, khu du lịch). 


---

## 2. Hướng phát triển (Build Approach)
Chatbot:
- **Intent Routing (AI):** Sử dụng LLM để phân tích ngữ nghĩa và phân loại ý định (Hỏi đường, Tra cứu rủi ro, Thông tin địa điểm).
- **Entity Extraction (Fuzzy Matching):** Thay vì dùng AI trích xuất thực thể (dễ sai sót và tốn tài nguyên), hệ thống sử dụng thuật toán so khớp chuỗi để định danh chính xác các Node trong Graph.
- **Graph Retrieval:** Truy vấn dữ liệu đa tầng bằng ngôn ngữ Cypher, lấy ra các thông tin liên đới (Đường -> Rủi ro -> Mẫu ùn tắc).
- **Response Generation:** LLM tổng hợp dữ liệu từ Graph và trả về báo cáo chi tiết dưới định dạng Markdown.

---

## 🛠️ 3. Công nghệ sử dụng
- **Backend:** Python 3.10+
- **Graph Database:** Neo4j (Cypher Query Language)
- **AI/LLM Engine:** Ollama (Local LLM), Google Gemini API (Hybrid)
- **String Matching:** RapidFuzz (Thuật toán Token Set Ratio)
---

## 4. Mô hình dữ liệu (Graph Schema)
Dữ liệu được tổ chức dưới dạng đồ thị để tối ưu hóa việc truy vấn các mối quan hệ phức tạp:

- **Thực thể (Nodes):** `Street`, `District`, `Place` (Trường học, Du lịch), `Hazard` (Điểm đen, Điểm ngập), `TrafficPattern`.
- **Mối quan hệ (Relationships):**
  - `(Place)-[:LOCATED_ON]->(Street)`
  - `(Street)-[:IN_DISTRICT]->(District)`
  - `(Hazard)-[:AFFECTS]->(Street)`
  - `(Place)-[:CAUSES_CONGESTION]->(TrafficPattern)`



---

## 📈 5. Đánh giá hiệu năng Chatbot
Hệ thống đã được kiểm thử với bộ **100 test cases** bao gồm các biến thể lỗi chính tả, viết tắt, và không dấu (VVK, PVD, ng van cu...).

| Tiêu chí | AI Classify Intent (LLM thuần) | Fuzzy Search Entities |
| :--- | :---: | :---: |
| **Độ chính xác** | ~93% | **60%** |
| **Tốc độ xử lý** | 1,59/req | **75ms** |
| **Tài nguyên RAM** | ~2GB | **Rất thấp** |
Dùng LLM để xác định 'Intent' của user khi, phân loại và dán nhãn thành 3 loại: 'STREET, 'PLACE', 'CHAT'
Dùng Fuzzy search để tìm đúng entities xuất hiện trong DB graph.
Có thể chạy các file trong folder test_engine để tìm hiểu test cases rõ hơn.

---

## 6. Hướng dẫn cài đặt

### Bước 1: Chuẩn bị Cơ sở dữ liệu Neo4j
1. Cài đặt **Neo4j Desktop**.
2. Tạo một DBMS mới và ghi lại thông tin đăng nhập, vào file config trong rag_engine để chỉnh đúng thông tin.
3. Chạy script nạp dữ liệu từ các file JSON nguồn, cd vào folder rag_engine:
   ```bash
   python napdulieu.py
4. Tải Ollama, tải và chọn model gemma:2b (có thể thay đổi model, nhưng phải thay đổi luôn trong file config; Khuyên dùng model vừa phải để xác định intent nhanh)
5. Luôn chạy ngầm Neo4j và Ollama
6. Vào link google drive để tải đồ thị TP.HCM và dán vào thư mục backend (vì graph lớn, chạy trên vscode lâu nên tải về sẽ nhanh hơn): https://drive.google.com/drive/folders/1E1UaacZRatcRoGdW585JJk4fKy27aN0C?usp=drive_link
7. cd vào thư mục backend và chạy file app.py
    ```bash
   python app.py
