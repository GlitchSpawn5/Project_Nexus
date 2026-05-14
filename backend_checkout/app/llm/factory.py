import logging
from importlib import import_module
from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import LLMProviderError

logger = logging.getLogger(__name__)

FALLBACK_CHAIN = ["groq", "gemini", "ollama", "openai"]

PROVIDER_FACTORIES = {
    "groq": ("app.llm.providers.groq_provider", "GroqProvider"),
    "gemini": ("app.llm.providers.gemini_provider", "GeminiProvider"),
    "ollama": ("app.llm.providers.ollama_provider", "OllamaProvider"),
    "openai": ("app.llm.providers.openai_provider", "OpenAIProvider"),
}

_provider_cache = {}


def _build_provider_sequence(primary_name: str, auto_fallback: bool) -> list[str]:
    providers = [primary_name]
    if auto_fallback:
        providers.extend(name for name in FALLBACK_CHAIN if name not in providers)
    return providers

def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Instantiate and return the requested provider (or default from settings), caching the instance."""
    name = (provider_name or settings.LLM_PROVIDER).lower()
    
    if name in _provider_cache:
        return _provider_cache[name]

    provider_factory = PROVIDER_FACTORIES.get(name)
    if provider_factory is None:
        raise ValueError(f"Unknown LLM provider: {name}")

    module_name, class_name = provider_factory
    try:
        provider_cls = getattr(import_module(module_name), class_name)
    except ModuleNotFoundError as e:
        raise LLMProviderError(
            provider_name=name,
            original_error=f"Missing optional dependency for {name}: {e.name}",
        ) from e

    provider = provider_cls()
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
    
    providers_to_try = _build_provider_sequence(primary_name, auto_fallback)

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
