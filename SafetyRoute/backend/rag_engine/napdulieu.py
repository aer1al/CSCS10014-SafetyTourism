import json
import os
import unicodedata
from neo4j import GraphDatabase

# --- CẤU HÌNH ---
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "12345678") # <--- ĐỔI PASSWORD CỦA BẠN
FILES = {
    "school": "schools.json",
    "tourist": "tourism.json",
    "accident": "accident.json",
    "flood": "flood_points.json"
}

def normalize_name(name):
    """Chuẩn hóa tên đường"""
    if not name or not isinstance(name, str): return "Unknown"
    name = unicodedata.normalize('NFKC', name).title()
    prefixes = ["Đường", "Phố", "Đ.", "Quốc Lộ", "Tỉnh Lộ", "Đại Lộ", "Xa Lộ"]
    for p in prefixes:
        if name.lower().startswith(p.lower() + " "):
            name = name[len(p)+1:].strip()
    return name.strip()

class SemanticGraphBuilder:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def create_constraints(self):
        # Tạo ràng buộc để tránh trùng lặp và tăng tốc độ tìm kiếm
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Street) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:District) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Place) REQUIRE p.name IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (p:Place) ON (p.category)" 
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)
        print("✅ Đã khởi tạo Constraints & Indexes.")

    def import_data(self, file_path, category, relationship_type):
        if not os.path.exists(file_path):
            print(f"⚠️ Không thấy file {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"🔄 Đang xử lý {len(data)} địa điểm loại '{category}'...")

        batch_data = []
        for item in data:
            # 1. Chuẩn hóa tên đường & Quận (Xử lý lỗi Null)
            clean_street = normalize_name(item.get('street'))
            
            raw_district = item.get('district')
            if raw_district and isinstance(raw_district, str) and raw_district.strip():
                district = raw_district.strip()
            else:
                district = "Unknown District"

            # 2. Xử lý Traffic Info (Phức tạp hơn)
            traffic_patterns = []
            
            if 'traffic_info' in item and isinstance(item['traffic_info'], dict):
                t_info = item['traffic_info']
                cause = t_info.get('cause', 'Unknown Cause')

                # CASE A: SCHOOL (Có morning/afternoon)
                if 'morning_peak' in t_info:
                    traffic_patterns.append({
                        "time": t_info['morning_peak'],
                        "session": "morning",
                        "cause": cause,
                        "days": "Mon-Fri", # Mặc định cho trường học
                        "months": "All Year"
                    })
                if 'afternoon_peak' in t_info:
                    traffic_patterns.append({
                        "time": t_info['afternoon_peak'],
                        "session": "afternoon",
                        "cause": cause,
                        "days": "Mon-Fri",
                        "months": "All Year"
                    })

                # CASE B: TOURIST (Có peak_hours, peak_days...)
                if 'peak_hours' in t_info:
                    traffic_patterns.append({
                        "time": t_info['peak_hours'],
                        "session": "full_day", # Hoặc tự đặt
                        "cause": cause,
                        "days": t_info.get('peak_days', 'Everyday'),
                        "months": t_info.get('peak_months', 'All Year')
                    })

            # 3. Đóng gói dữ liệu
            node_data = {
                "name": item.get('name', 'Unknown Name'),
                "category": category,
                "detail_type": item.get('type') or item.get('detail_type', 'General'),
                "street_name": clean_street,
                "district_name": district,
                "lat": item.get('location', {}).get('lat') if 'location' in item else None,
                "lon": item.get('location', {}).get('lon') if 'location' in item else None,
                # Dành cho Hazard
                "desc": item.get('risk_info', {}).get('description') if 'risk_info' in item else "",
                "severity": item.get('risk_info', {}).get('severity') if 'risk_info' in item else "",
                # Danh sách các pattern giao thông
                "traffic_patterns": traffic_patterns
            }
            batch_data.append(node_data)

        # QUERY MỚI: Hỗ trợ TrafficPattern và Hazard
        query = f"""
        UNWIND $batch AS row
        
        // 1. Tạo Khung Quận - Đường
        MERGE (d:District {{name: row.district_name}})
        MERGE (s:Street {{name: row.street_name}})
        MERGE (s)-[:IN_DISTRICT]->(d)
        
        // 2. Tạo Node Place
        MERGE (p:Place {{name: row.name}})
        SET p:{category}, 
            p.category = row.category,
            p.detail_type = row.detail_type,
            p.lat = row.lat,
            p.lon = row.lon,
            p.description = row.desc,
            p.severity = row.severity
            
        // 3. Nối Place vào Đường
        MERGE (p)-[:{relationship_type}]->(s)
        
        // 4. Xử lý Traffic Pattern (Vòng lặp tạo Node Pattern)
        FOREACH (pattern IN row.traffic_patterns | 
            MERGE (tp:TrafficPattern {{
                time_range: pattern.time, 
                days: pattern.days, 
                months: pattern.months,
                session: pattern.session
            }})
            // Tạo quan hệ chứa Nguyên nhân (cause)
            MERGE (p)-[r:CAUSES_CONGESTION]->(tp)
            SET r.cause = pattern.cause
        )
        """

        with self.driver.session() as session:
            # Chia batch 500
            for i in range(0, len(batch_data), 500):
                batch = batch_data[i:i+500]
                session.run(query, batch=batch)
                print(f"   -> Đã nạp {len(batch)} item...")

def run():
    builder = SemanticGraphBuilder(URI, AUTH)
    try:
        builder.create_constraints()
        
        # 1. School (Có Traffic Info kiểu A)
        builder.import_data(FILES['school'], "School", "LOCATED_ON")
        
        # 2. Tourist (Có Traffic Info kiểu B)
        builder.import_data(FILES['tourist'], "Tourist", "LOCATED_ON")
        
        # 3. Hazard (Giữ nguyên logic cũ)
        builder.import_data(FILES['accident'], "Hazard", "AFFECTS")
        builder.import_data(FILES['flood'], "Hazard", "AFFECTS")
        
        print("\n🎉 HOÀN TẤT! Đã nạp dữ liệu với mô hình TrafficPattern mới.")
        
    finally:
        builder.close()

if __name__ == "__main__":
    run()