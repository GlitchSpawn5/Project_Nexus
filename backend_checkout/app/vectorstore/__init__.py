"""
Vector Store Package
====================
Exports the lazily initialized ChromaStore singleton.
"""

from app.vectorstore.chroma_client import ChromaStore

_chroma_store_instance = None


class _LazyStoreProxy:
    def __getattr__(self, name):
        return getattr(get_chroma_store(), name)

def get_chroma_store() -> ChromaStore:
    """Lazily instantiate and return the ChromaStore singleton."""
    global _chroma_store_instance
    if _chroma_store_instance is None:
        _chroma_store_instance = ChromaStore()
    return _chroma_store_instance

# Backwards-compatible alias that avoids opening Chroma during app import.
chroma_store = _LazyStoreProxy()
