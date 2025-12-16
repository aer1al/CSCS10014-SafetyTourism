# rag_engine/traffic_query.py

from neo4j import GraphDatabase
from .config import NEO4J_URI, NEO4J_AUTH
from .graph_search import GraphSearcher
from .weather_service import WeatherService

class TrafficService:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        self.searcher = GraphSearcher()
        self.weather = WeatherService()

    def close(self):
        self.driver.close()
        self.searcher.close()

    # --- HÀM 1: KIỂM TRA ĐƯỜNG (SỬA LỖI LOGIC TRUY VẤN) ---
    def get_street_status(self, user_input):
        found_node, labels = self.searcher.find_node_by_name(user_input)
        if not found_node or 'Street' not in labels: return None 

        street_name = found_node['name']

        # LOGIC MỚI:
        # 1. Hazard: Lấy name, severity (để fill vào desc nếu desc rỗng)
        # 2. Place: JOIN sang TrafficPattern để lấy time_range, days, session ngay lập tức
        cypher_query = """
        MATCH (s:Street {name: $street_name})
        OPTIONAL MATCH (s)-[:IN_DISTRICT]->(d:District)
        
        // LẤY HAZARD (Tai nạn/Ngập)
        OPTIONAL MATCH (s)<-[:AFFECTS]-(h:Hazard)
        
        // LẤY PLACE & TRAFFIC PATTERN CỦA NÓ
        OPTIONAL MATCH (s)<-[:LOCATED_ON]-(p:Place)
        OPTIONAL MATCH (p)-[r:CAUSES_CONGESTION]->(tp:TrafficPattern)
        
        RETURN 
            s.name AS street,
            d.name AS district,
            collect(DISTINCT {
                name: h.name,               // VD: Điểm đen Tỉnh Lộ 43
                type: h.detail_type,        // VD: Hazard/Accident
                desc: h.description,        // Có thể rỗng
                severity: h.severity        // VD: High
            }) AS hazards,
            collect(DISTINCT {
                name: p.name, 
                type: p.detail_type,        // VD: School
                category: p.category,
                
                // Lấy thông tin pattern (nếu có)
                has_pattern: (tp IS NOT NULL),
                time: tp.time_range,        // VD: 16:30-18:30
                days: tp.days,              // VD: Mon-Fri
                session: tp.session,        // VD: afternoon
                cause: r.cause              // Nguyên nhân từ quan hệ
            }) AS places
        """
        
        with self.driver.session() as session:
            result = session.run(cypher_query, street_name=street_name).single()
            if not result: return None

            # XỬ LÝ DỮ LIỆU HAZARD (FIX LỖI DESC RỖNG)
            clean_hazards = []
            for h in result['hazards']:
                if h['type']: 
                    # Logic sửa lỗi: Nếu desc rỗng, lấy name làm desc
                    description = h['desc']
                    if not description or description.strip() == "":
                        description = h['name'] # Fallback: "Điểm đen Tỉnh Lộ 43"
                    
                    clean_hazards.append({
                        "type": h['type'],
                        "severity": h['severity'],
                        "desc": description # Giờ đây desc sẽ luôn có dữ liệu
                    })

            # XỬ LÝ PLACES (KÈM THÔNG TIN GIỜ GIẤC)
            clean_places = []
            for p in result['places']:
                if p['name']:
                    place_info = {
                        "name": p['name'],
                        "type": p['type'],
                        "category": p['category']
                    }
                    # Nếu địa điểm này có Traffic Pattern, kẹp luôn vào để LLM đọc
                    if p['has_pattern']:
                        place_info["traffic_impact"] = {
                            "time": p['time'],
                            "days": p['days'],
                            "session": p['session'],
                            "cause": p['cause'] if p['cause'] else "Hoạt động thường nhật"
                        }
                    clean_places.append(place_info)

            district_name = result['district'] if result['district'] else "TP.HCM"
            realtime_weather = self.weather.get_current_weather(district_name)

            return {
                "query_type": "street_info",
                "street": result['street'],
                "district": district_name,
                "hazards": clean_hazards,
                "places": clean_places,
                "current_weather": realtime_weather
            }

    # --- HÀM 2: KIỂM TRA ĐỊA ĐIỂM (CŨNG CẬP NHẬT LOGIC TƯƠNG TỰ) ---
    def get_place_info(self, user_input):
        found_node, labels = self.searcher.find_node_by_name(user_input)
        if not found_node or 'Place' not in labels: return None

        place_name = found_node['name']
        
        # Query lấy chi tiết
        cypher_query = """
        MATCH (p:Place {name: $place_name})
        OPTIONAL MATCH (p)-[:LOCATED_ON]->(s:Street)
        OPTIONAL MATCH (s)-[:IN_DISTRICT]->(d:District)
        
        // Lấy Pattern từ quan hệ CAUSES_CONGESTION
        OPTIONAL MATCH (p)-[r:CAUSES_CONGESTION]->(tp:TrafficPattern)
        
        RETURN 
            p.name AS name,
            p.category AS category,
            p.detail_type AS type,
            s.name AS street,
            d.name AS district,
            collect({
                time: tp.time_range,
                days: tp.days,
                session: tp.session,
                // Ưu tiên lấy nguyên nhân từ Relationship (r), nếu không có thì fallback
                cause: coalesce(r.cause, tp.cause, 'Tập trung đông người')
            }) AS traffic_patterns
        """
        
        with self.driver.session() as session:
            result = session.run(cypher_query, place_name=place_name).single()
            if not result: return None
            
            patterns = [t for t in result['traffic_patterns'] if t['time'] is not None]

            district_name = result['district'] if result['district'] else "TP.HCM"
            realtime_weather = self.weather.get_current_weather(district_name)

            return {
                "query_type": "place_info",
                "name": result['name'],
                "category": result['category'],
                "type": result['type'],
                "address": f"{result['street']}, {result['district']}" if result['street'] else "Chưa rõ",
                "traffic_info": patterns,
                "current_weather": realtime_weather
            }