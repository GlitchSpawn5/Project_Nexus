import httpx
from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import LLMProviderError

class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> str:
        try:
            # We enforce a timeout of 120 seconds
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False
                },
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise LLMProviderError(provider_name=self.name(), original_error=str(e))
            
    def name(self) -> str:
        return "ollama"
