# rag_engine/chatbot.py
import sys
import os


from .intent_router import IntentRouter
from .traffic_query import TrafficService
from .response_gen import ResponseGenerator

class TrafficChatbot:
    def __init__(self):
        print("🚀 Đang khởi động các module...")
        self.router = IntentRouter()
        self.traffic_service = TrafficService()
        self.generator = ResponseGenerator()
        print("✅ Chatbot đã sẵn sàng!")

    def chat(self, user_input):
        # 1. Router: Hiểu ý định
        intent, entity = self.router.detect_intent(user_input)
        print(f"   [Debug] Intent: {intent} | Entity: {entity}")

        # 2. Retriever: Lấy dữ liệu (Nếu cần)
        context_data = None
        if intent == "STREET" and entity:
            context_data = self.traffic_service.get_street_status(entity)
        elif intent == "PLACE" and entity:
            context_data = self.traffic_service.get_place_info(entity)
        
        # LOG
        if context_data:
            print(f"🔍 [DEBUG DATA TỪ NEO4J]: {context_data}")

            return self.generator.generate(user_input, context_data)

    def close(self):
        self.traffic_service.close()

if __name__ == "__main__":
    bot = TrafficChatbot()
    print("\n--- SAFETY TOURISM BOT (Modular Version) ---")
    while True:
        text = input("\nBạn: ")
        if text.lower() in ["exit", "quit"]: break
        response = bot.chat(text)
        print(f"Bot: {response}")
    bot.close()