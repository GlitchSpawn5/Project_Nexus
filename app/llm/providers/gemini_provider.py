import google.generativeai as genai
from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import LLMProviderError

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> str:
        try:
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            # Gemini Python SDK uses max_output_tokens in generation_config
            response = self.model.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                )
            )
            return response.text
        except Exception as e:
            raise LLMProviderError(provider_name=self.name(), original_error=str(e))
            
    def name(self) -> str:
        return "gemini"
