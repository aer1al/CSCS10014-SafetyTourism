# rag_engine/graph_search.py

import unicodedata
from neo4j import GraphDatabase
from .config import NEO4J_URI, NEO4J_AUTH

class GraphSearcher:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    def close(self):
        self.driver.close()

    def _normalize_string(self, text):
        """Chuyển tiếng Việt có dấu về không dấu để so sánh."""
        if not text: return ""
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
        return text.lower()

    def _clean_search_term(self, term):
        """Lọc bỏ từ rác (stopwords)."""
        term = term.lower()
        stopwords = [
            "đường", "phố", "quốc lộ", "tỉnh lộ", "đại lộ", "hẻm", "ngõ", 
            "trường", "đại học", "cao đẳng", "trung học", "tiểu học",
            "tại", "ở", "gần", "khu", "quận", "huyện", "phường", "xã",
            "duong", "pho", "truong", "dai hoc", "quan", "huyen"
        ]
        for word in stopwords:
            if term.startswith(word + " "):
                term = term[len(word):].strip()
        return term

    def find_node_by_name(self, search_term):
        """
        Tìm kiếm Node thông minh (Smart Fuzzy Search).
        Trả về: (Node object, List[Labels])
        """
        original_term = search_term
        cleaned_term = self._clean_search_term(search_term)
        if not cleaned_term: cleaned_term = search_term

        # 1. Tạo Query Fuzzy (~1)
        lucene_query = " AND ".join([f"{word.strip()}~1" for word in cleaned_term.split() if word.strip()])

        query = """
        CALL db.index.fulltext.queryNodes('search_index', $lucene_query)
        YIELD node, score
        WHERE score > 1.0
        RETURN node, score
        ORDER BY score DESC
        LIMIT 5
        """
        
        with self.driver.session() as session:
            try:
                results = session.run(query, lucene_query=lucene_query).fetch(5)
            except Exception as e:
                print(f"Error: {e}")
                return None, None

            # 2. Post-Validation
            search_keywords = self._normalize_string(cleaned_term).split()
            
            for record in results:
                node = record["node"]
                node_name_norm = self._normalize_string(node.get('name', ''))
                
                matched_words = 0
                for kw in search_keywords:
                    if kw in node_name_norm: 
                        matched_words += 1
                
                if len(search_keywords) > 0:
                    match_ratio = matched_words / len(search_keywords)
                else:
                    match_ratio = 0

                if match_ratio >= 0.6:
                    return node, list(node.labels)
            

            return None, None
