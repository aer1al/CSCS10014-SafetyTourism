# rag_engine/llm_client.py
import ollama
from .config import OLLAMA_MODEL

class LLMClient:
    def __init__(self, model_name=None):
        # Nếu không truyền model, lấy mặc định từ config hoặc hardcode
        self.model = model_name if model_name else "gemma3:4b"

    def send_prompt(self, prompt):
        """Gửi prompt tới Ollama và nhận phản hồi text."""
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception as e:
            print(f"❌ Lỗi kết nối Ollama: {str(e)}")
            return None