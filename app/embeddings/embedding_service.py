"""
Embedding Service
=================
Singleton service for converting text into vector embeddings using sentence-transformers.
"""

from typing import List
from sentence_transformers import SentenceTransformer

from app.config import settings

class EmbeddingService:
    """Wraps sentence-transformers to encode text into embeddings."""
    
    def __init__(self):
        # Load the model specified in the configuration
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
    def embed_text(self, text: str) -> List[float]:
        """
        Encode a single string into a vector.
        Truncates the input to 512 tokens to avoid model overflow.
        
        Args:
            text (str): The text to encode.
            
        Returns:
            List[float]: A flat list of floats representing the embedding.
        """
        # Truncate text to 512 tokens (roughly mapped to words/chars here, 
        # but sentence-transformers automatically handles token truncation if we set max_seq_length)
        self.model.max_seq_length = 512
        
        # Output as a flat float list
        embedding = self.model.encode(text, convert_to_numpy=True).tolist()
        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Encode a list of strings efficiently in batches.
        
        Args:
            texts (List[str]): The list of texts to encode.
            
        Returns:
            List[List[float]]: A list of embedding vectors.
        """
        self.model.max_seq_length = 512
        
        # Batch size of 32 internally
        embeddings = self.model.encode(texts, batch_size=32, convert_to_numpy=True)
        return embeddings.tolist()
