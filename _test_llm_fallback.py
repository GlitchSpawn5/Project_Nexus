import os
os.environ["LLM_PROVIDER"] = "groq"
os.environ["LLM_AUTO_FALLBACK"] = "true"
os.environ["GROQ_API_KEY"] = "gsk_invalid"
os.environ["GEMINI_API_KEY"] = "AIza_invalid"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:9999"  # invalid url

from app.config import settings

# Force reload settings
settings.LLM_PROVIDER = "groq"
settings.LLM_AUTO_FALLBACK = True
settings.GROQ_API_KEY = "gsk_invalid"
settings.GEMINI_API_KEY = "AIza_invalid"
settings.OLLAMA_BASE_URL = "http://localhost:9999"
settings.OPENAI_API_KEY = ""

from app.llm.factory import complete_with_fallback, get_llm_provider
from app.llm.exceptions import LLMProviderError

import logging
logging.basicConfig(level=logging.WARNING)

print("=== Testing Auto Fallback ===")
try:
    complete_with_fallback("system", "user", 10)
    print("SUCCESS (unexpected)")
except LLMProviderError as e:
    print(f"EXPECTED FAILURE: {e}")

print("\n=== Testing No Fallback ===")
settings.LLM_AUTO_FALLBACK = False
try:
    complete_with_fallback("system", "user", 10)
    print("SUCCESS (unexpected)")
except LLMProviderError as e:
    print(f"EXPECTED FAILURE: {e}")
