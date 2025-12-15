from neo4j import GraphDatabase

# --- CẤU HÌNH KẾT NỐI NEO4J ---
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "12345678")  # <--- KIỂM TRA MẬT KHẨU CỦA BẠN

class GraphRetriever:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(URI, auth=AUTH)
            self.driver.verify_connectivity()
            print("🔌 Graph Retriever: Đã kết nối Neo4j!")
        except Exception as e:
            print(f"❌ Graph Retriever Lỗi kết nối: {e}")

    def close(self):
        self.driver.close()

    def find_related_risks(self, road_name):
        """
        Logic: Tìm đường -> Chỉ lấy Chợ, Trường, Điểm rủi ro nằm trên đường đó.
        """
        # Query này dùng whitelist để CHỈ LẤY những thứ ảnh hưởng giao thông
        query = """
        MATCH (r:Road)
        WHERE toLower(r.name) CONTAINS toLower($road_name)
        
        // Tìm các node kết nối trực tiếp với đường (Market, School, RiskZone...)
        MATCH (r)-[rel]-(place)
        
        // --- BỘ LỌC QUAN TRỌNG (FILTER) ---
        // Chỉ lấy những node có nhãn (Label) nằm trong danh sách này:
        WHERE any(label IN labels(place) WHERE label IN ['Market', 'School', 'University', 'Hospital', 'RiskZone', 'Flood', 'TrafficJam', 'Construction'])
        
        RETURN 
            r.name as road_name,
            labels(place) as place_types,
            place.name as place_name,
            place.description as description,
            type(rel) as relationship
        LIMIT 5
        """
        
        results = []
        print(f"⚡ [NEO4J] Đang tìm các điểm ảnh hưởng trên đường: {road_name}...")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, road_name=road_name)
                for record in result:
                    # Lấy loại địa điểm (Ví dụ: Market, School...)
                    # labels(place) trả về list, ta lấy cái đầu tiên không phải là 'Place' (nếu có logic đó)
                    # Hoặc đơn giản lấy cái đầu tiên
                    types = record["place_types"]
                    main_type = types[0] if types else "Unknown"

                    # Tạo mô tả dễ hiểu cho Chatbot đọc
                    item = {
                        "road_found": record["road_name"],
                        "type": main_type,               # Để Chatbot nhận diện (Market/School)
                        "name": record["place_name"],    # Tên địa điểm (Chợ Xóm Chiếu)
                        "description": record.get("description", "Địa điểm nằm trên tuyến đường này"),
                        "relationship": record["relationship"]
                    }
                    results.append(item)
            
            if len(results) > 0:
                print(f"✅ [NEO4J] Tìm thấy {len(results)} điểm ảnh hưởng (Chợ/Trường/Sự cố).")
            else:
                print(f"⚠️ [NEO4J] Không tìm thấy Chợ/Trường nào trên đường {road_name} (hoặc tên đường chưa khớp DB).")
                
        except Exception as e:
            print(f"❌ Lỗi truy vấn Graph: {e}")
            
        return results
