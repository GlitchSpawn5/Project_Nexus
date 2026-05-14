import groq
from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import LLMProviderError

class GroqProvider(BaseLLMProvider):
    def __init__(self):
        self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMProviderError(provider_name=self.name(), original_error=str(e))
            
    def name(self) -> str:
        return "groq"
