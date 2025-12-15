import json
import os
from neo4j import GraphDatabase

# --- CẤU HÌNH NEO4J (Bạn nhớ sửa password cho đúng máy bạn) ---
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "12345678") # <--- SỬA PASSWORD CỦA BẠN Ở ĐÂY

# Đường dẫn file dữ liệu
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, 'dataFilter.json')

class KnowledgeGraphBuilder:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(URI, auth=AUTH)
            self.driver.verify_connectivity()
            print("🔌 Đã kết nối thành công với Neo4j!")
        except Exception as e:
            print(f"❌ Lỗi kết nối Neo4j: {e}")
            print("👉 Hãy chắc chắn bạn đã bật Neo4j Desktop và điền đúng Password.")
            raise e

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Xóa sạch DB cũ để nạp mới (Reset)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("🗑️  Đã dọn sạch Database cũ.")

    def create_indexes(self):
        """Tạo index để tìm kiếm cho nhanh"""
        with self.driver.session() as session:
            # Tìm nhanh theo tên đường
            session.run("CREATE INDEX road_name_idx IF NOT EXISTS FOR (r:Road) ON (r.name)")
            # Tìm nhanh theo loại rủi ro
            session.run("CREATE INDEX risk_type_idx IF NOT EXISTS FOR (z:RiskZone) ON (z.type)")
            print("⚡ Đã tạo Index tìm kiếm.")

    def ingest_data(self, data):
        """Nạp dữ liệu và tạo mối quan hệ"""
        print("🚀 Đang nạp dữ liệu vào đồ thị...")
        
        with self.driver.session() as session:
            for item in data:
                # 1. Tạo Node Rủi Ro (RiskZone)
                # Dùng MERGE để đảm bảo không tạo trùng
                query_zone = """
                MERGE (z:RiskZone {id: $id})
                SET z.description = $desc,
                    z.type = $type,
                    z.severity = $severity,
                    z.lat = $lat,
                    z.lng = $lng,
                    z.radius = $radius,
                    z.time_start = $t_start,
                    z.time_end = $t_end
                """
                session.run(query_zone, 
                            id=item['id'],
                            desc=item['description'],
                            type=item['type'],
                            severity=item['attributes']['severity'],
                            lat=item['geometry']['lat'],
                            lng=item['geometry']['lng'],
                            radius=item['geometry']['radius'],
                            t_start=item['time']['start'],
                            t_end=item['time']['end']
                )

                # 2. Tạo Node Con Đường (Road) và nối dây (Relationship)
                affected_roads = item.get('affected_roads', [])
                if affected_roads:
                    for road_name in affected_roads:
                        query_relation = """
                        MATCH (z:RiskZone {id: $id})
                        MERGE (r:Road {name: $road_name})
                        MERGE (z)-[:AFFECTS {severity: $severity}]->(r)
                        """
                        session.run(query_relation, 
                                    id=item['id'], 
                                    road_name=road_name,
                                    severity=item['attributes']['severity'])

        print(f"✅ Đã nạp xong {len(data)} vùng rủi ro vào Graph!")

def main():
    if not os.path.exists(DATA_FILE):
        print("❌ Không tìm thấy file dataFilter.json")
        return

    # Load file JSON
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Chạy Builder
    builder = KnowledgeGraphBuilder()
    builder.clear_database() # Xóa cũ
    builder.create_indexes() # Tạo index
    builder.ingest_data(data) # Nạp mới
    builder.close()

if __name__ == "__main__":
    main()