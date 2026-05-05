import logging
from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import LLMProviderError
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

FALLBACK_CHAIN = ["groq", "gemini", "ollama"]

_provider_cache = {}

def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Instantiate and return the requested provider (or default from settings), caching the instance."""
    name = (provider_name or settings.LLM_PROVIDER).lower()
    
    if name in _provider_cache:
        return _provider_cache[name]
        
    if name == "groq":
        provider = GroqProvider()
    elif name == "gemini":
        provider = GeminiProvider()
    elif name == "ollama":
        provider = OllamaProvider()
    elif name == "openai":
        provider = OpenAIProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {name}")
        
    _provider_cache[name] = provider
    return provider

def complete_with_fallback(system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> tuple[str, str]:
    """
    Generate a response with the configured primary LLM.
    If LLM_AUTO_FALLBACK=true, on failure, it will cascade down the FALLBACK_CHAIN.
    Returns (answer_text, provider_name_that_succeeded).
    """
    primary_name = settings.LLM_PROVIDER.lower()
    auto_fallback = settings.LLM_AUTO_FALLBACK
    
    # Create the sequence of providers to try
    providers_to_try = [primary_name]
    if auto_fallback:
        for fallback in FALLBACK_CHAIN:
            if fallback not in providers_to_try:
                providers_to_try.append(fallback)
                
    failures = []
    
    for provider_name in providers_to_try:
        try:
            provider = get_llm_provider(provider_name)
            response = provider.complete(system_prompt, user_prompt, max_tokens=max_tokens)
            return response, provider_name
        except LLMProviderError as e:
            failures.append(str(e))
            if auto_fallback:
                logger.warning(f"[LLM] {provider_name} failed: {e.original_error}. Trying next provider.")
            else:
                raise e
        except Exception as e:
            # Catch initialization errors if any (e.g. missing API keys causing ValueError)
            failures.append(f"[{provider_name}] failed: {str(e)}")
            if auto_fallback:
                logger.warning(f"[LLM] {provider_name} failed to initialize or execute: {str(e)}. Trying next provider.")
            else:
                raise LLMProviderError(provider_name=provider_name, original_error=str(e))
                
    # If we exhaust the list without returning
    raise LLMProviderError(
        provider_name="all", 
        original_error="All LLM providers failed. Failures: " + " | ".join(failures)
    )
