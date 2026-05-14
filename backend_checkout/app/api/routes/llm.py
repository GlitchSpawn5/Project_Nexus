from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from app.config import settings
from app.llm.factory import FALLBACK_CHAIN, PROVIDER_FACTORIES, get_llm_provider
from app.llm.exceptions import LLMProviderError
from app.auth.dependencies import require_role
from app.db.models.user import User

router = APIRouter()

PROVIDER_ORDER = tuple(PROVIDER_FACTORIES.keys())


def _provider_configured(provider_name: str) -> bool:
    if provider_name == "groq":
        return bool(settings.GROQ_API_KEY)
    if provider_name == "gemini":
        return bool(settings.GEMINI_API_KEY)
    if provider_name == "ollama":
        return bool(settings.OLLAMA_BASE_URL)
    if provider_name == "openai":
        return bool(settings.OPENAI_API_KEY)
    return False


def _probe_provider(provider_name: str) -> dict[str, Any]:
    configured = _provider_configured(provider_name)
    status = "no_api_key" if provider_name in {"groq", "gemini", "openai"} and not configured else "not_tested"

    if not configured:
        return {"configured": False, "status": status}

    try:
        provider = get_llm_provider(provider_name)
        provider.complete(
            system_prompt="You are a helpful assistant.",
            user_prompt="Reply with the word READY only.",
            max_tokens=10,
        )
        return {"configured": True, "status": "ok"}
    except LLMProviderError as e:
        return {"configured": True, "status": f"error: {e.original_error}"}
    except Exception as e:
        return {"configured": True, "status": f"error: {str(e)}"}

@router.get("/status")
def get_llm_status(admin_user: User = Depends(require_role("admin"))) -> Dict[str, Any]:
    """Test every configured LLM provider and return a provider health summary."""
    primary_provider = settings.LLM_PROVIDER.lower()
    auto_fallback = settings.LLM_AUTO_FALLBACK

    providers_config = {
        provider_name: _probe_provider(provider_name)
        for provider_name in PROVIDER_ORDER
    }

    if primary_provider not in providers_config:
        providers_config[primary_provider] = {
            "configured": False,
            "status": f"error: unknown provider '{primary_provider}'",
        }

    primary_status = providers_config[primary_provider]["status"]

    return {
        "primary_provider": primary_provider,
        "primary_status": primary_status,
        "auto_fallback_enabled": auto_fallback,
        "fallback_chain": FALLBACK_CHAIN,
        "providers": providers_config
    }
