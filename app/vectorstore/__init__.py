"""
Vector Store Package
====================
Exports the lazily initialized ChromaStore singleton.
"""

from app.vectorstore.chroma_client import ChromaStore

_chroma_store_instance = None

def get_chroma_store() -> ChromaStore:
    """Lazily instantiate and return the ChromaStore singleton."""
    global _chroma_store_instance
    if _chroma_store_instance is None:
        _chroma_store_instance = ChromaStore()
    return _chroma_store_instance

# Alias for ease of use
chroma_store = get_chroma_store()
