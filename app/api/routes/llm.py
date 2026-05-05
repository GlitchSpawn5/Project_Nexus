from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.config import settings
from app.llm.factory import get_llm_provider, FALLBACK_CHAIN
from app.llm.exceptions import LLMProviderError
from fastapi import Depends
from app.auth.dependencies import require_role
from app.db.models.user import User

router = APIRouter()

@router.get("/status")
def get_llm_status(admin_user: User = Depends(require_role("admin"))) -> Dict[str, Any]:
    """Test the configured primary LLM provider and return system status."""
    primary_provider = settings.LLM_PROVIDER.lower()
    auto_fallback = settings.LLM_AUTO_FALLBACK
    
    # Check configurations
    providers_config = {
        "groq": {"configured": bool(settings.GROQ_API_KEY), "status": "not_tested"},
        "gemini": {"configured": bool(settings.GEMINI_API_KEY), "status": "not_tested"},
        "ollama": {"configured": bool(settings.OLLAMA_BASE_URL), "status": "not_tested"},
        "openai": {"configured": bool(settings.OPENAI_API_KEY), "status": "no_api_key" if not settings.OPENAI_API_KEY else "not_tested"}
    }
    
    primary_status = "error"
    
    # Only test the primary provider
    if providers_config.get(primary_provider, {}).get("configured", False):
        try:
            provider = get_llm_provider(primary_provider)
            # Test call
            response = provider.complete(
                system_prompt="You are a helpful assistant.",
                user_prompt="Reply with the word READY only.",
                max_tokens=10
            )
            # If we get here without an exception, it worked
            primary_status = "ok"
            providers_config[primary_provider]["status"] = "ok"
        except LLMProviderError as e:
            primary_status = f"error: {e.original_error}"
            providers_config[primary_provider]["status"] = "error"
        except Exception as e:
            primary_status = f"error: {str(e)}"
            providers_config[primary_provider]["status"] = "error"
    else:
        primary_status = "no_api_key"
        providers_config[primary_provider]["status"] = "no_api_key"

    return {
        "primary_provider": primary_provider,
        "primary_status": primary_status,
        "auto_fallback_enabled": auto_fallback,
        "fallback_chain": FALLBACK_CHAIN,
        "providers": providers_config
    }
