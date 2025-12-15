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

    def find_related_risks(self, road_name: str):
        query = """
        MATCH (r:Road)-[rel]-(p)
        WHERE toLower(r.name) CONTAINS toLower($road_name)
          AND NOT p:Road  // Không trả về các node Road khác
        RETURN labels(p) AS labels,
            p.name AS name,
            p.description AS description,
            p.time_start AS time_start,  // <--- THÊM TRƯỜNG TIME START
            p.time_end AS time_end       // <--- THÊM TRƯỜNG TIME END
        LIMIT 10
        """

        results = []
        with self.driver.session() as session:
            for record in session.run(query, road_name=road_name):
                node_type = record["labels"][0] if record["labels"] else "Unknown"
                
                if node_type in ["Road", "Route", "Location"]:
                    continue

                # CẢI THIỆN: Dùng record.get("name") và cung cấp giá trị mặc định ("N/A")
                # để giải quyết lỗi 'None' nếu dữ liệu thiếu name.
                results.append({
                    "type": node_type,
                    "name": record.get("name", "N/A"), 
                    "description": record.get("description", ""),
                    "time_start": record.get("time_start", "N/A"), # Lấy dữ liệu time
                    "time_end": record.get("time_end", "N/A")     # Lấy dữ liệu time
                })
        return results
