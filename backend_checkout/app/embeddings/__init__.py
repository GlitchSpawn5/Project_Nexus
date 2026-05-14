"""
Embeddings Package
==================
Exports the lazily initialized EmbeddingService singleton.
"""

from app.embeddings.embedding_service import EmbeddingService
from app.embeddings.clip_service import CLIPService

_embedding_service_instance = None
_clip_service_instance = None


class _LazyServiceProxy:
    def __init__(self, factory):
        self._factory = factory

    def __getattr__(self, name):
        return getattr(self._factory(), name)

def get_embedding_service() -> EmbeddingService:
    """Lazily instantiate and return the EmbeddingService singleton."""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance

def get_clip_service() -> CLIPService:
    """Lazily instantiate and return the CLIPService singleton."""
    global _clip_service_instance
    if _clip_service_instance is None:
        _clip_service_instance = CLIPService()
    return _clip_service_instance

# Backwards-compatible aliases that do not load ML models during app import.
embedding_service = _LazyServiceProxy(get_embedding_service)
clip_service = _LazyServiceProxy(get_clip_service)
