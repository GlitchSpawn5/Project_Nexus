"""
ChromaDB Client
===============
Provides connection to the local ChromaDB vector store.
Manages collections per knowledge base and handles upserts, queries, and deletions.
"""

from typing import List, Dict, Optional
import concurrent.futures
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

class ChromaStore:
    """Wraps ChromaDB for persistent local vector storage."""
    
    def __init__(self):
        # Connect to ChromaDB in persistent client mode pointing to CHROMA_PERSIST_PATH
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
    def get_or_create_collection(self, kb_id: str, modality: str = "text") -> chromadb.Collection:
        """
        Gets an existing collection or creates a new one for a knowledge base and modality.
        Collections use cosine similarity for distance metrics.
        Legacy collection without suffix is treated as text collection.
        
        Args:
            kb_id (str): The knowledge base UUID string.
            modality (str): "text" or "image".
            
        Returns:
            chromadb.Collection: The collection instance.
        """
        if modality == "text":
            # Legacy fallback: Check if the un-suffixed collection exists
            legacy_name = f"nexus_kb_{kb_id}"
            try:
                collection = self.client.get_collection(name=legacy_name)
                return collection
            except Exception:
                pass
            collection_name = f"nexus_kb_{kb_id}_text"
        else:
            collection_name = f"nexus_kb_{kb_id}_{modality}"
            
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        return collection

    def upsert_chunks(
        self, 
        kb_id: str, 
        chunk_ids: List[str], 
        embeddings: List[List[float]], 
        texts: List[str], 
        metadatas: List[Dict],
        modality: str = "text"
    ) -> None:
        """
        Upsert a batch of chunks into the correct collection.
        
        Args:
            kb_id (str): Knowledge base ID.
            chunk_ids (List[str]): List of UUID strings from the DB Chunk table.
            embeddings (List[List[float]]): List of embedding vectors.
            texts (List[str]): List of raw text chunks.
            metadatas (List[Dict]): List of metadata dictionaries.
            modality (str): The modality collection to upsert to.
        """
        collection = self.get_or_create_collection(kb_id, modality=modality)
        
        # Clean metadata (ChromaDB doesn't accept nested dicts or None values)
        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if v is not None:
                    # Convert any UUIDs or complex objects to strings if needed
                    clean_meta[k] = str(v) if not isinstance(v, (str, int, float, bool)) else v
            clean_metadatas.append(clean_meta)
            
        collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=clean_metadatas
        )

    def _query_single_collection(
        self,
        kb_id: str,
        modality: str,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """Helper to query a single collection."""
        try:
            collection = self.get_or_create_collection(kb_id, modality=modality)
        except Exception:
            return []
            
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
        except Exception:
            return []
            
        formatted_results = []
        
        if not results["ids"] or not results["ids"][0]:
            return formatted_results
            
        ids = results["ids"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else []
        documents = results["documents"][0] if "documents" in results and results["documents"] else []
        metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
        
        for i in range(len(ids)):
            distance = distances[i] if i < len(distances) else 1.0
            score = 1.0 - distance
            
            formatted_results.append({
                "chunk_id": ids[i],
                "text": documents[i] if i < len(documents) else "",
                "score": float(score),
                "metadata": metadatas[i] if i < len(metadatas) else {}
            })
            
        return formatted_results

    def query(
        self, 
        kb_id: str, 
        query_embedding_dict: Dict[str, List[float]], 
        top_k: int = 10, 
        filters: Optional[Dict] = None,
        modality: str = "text"
    ) -> List[Dict]:
        """
        Run a cosine similarity search against the collection(s).
        
        Args:
            kb_id (str): Knowledge base ID.
            query_embedding_dict (Dict[str, List[float]]): Dict containing query embeddings per modality.
                e.g., {"text": [0.1, 0.2, ...], "image": [0.3, 0.4, ...]}
            top_k (int): Number of results to return.
            filters (Dict, optional): Metadata filters for ChromaDB.
            modality (str): "text", "image", or "all".
            
        Returns:
            List[Dict]: List of result dicts: {"chunk_id": str, "text": str, "score": float, "metadata": dict}
        """
        results = []
        
        if modality == "all":
            # Concurrent query against both collections
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                if "text" in query_embedding_dict:
                    futures.append(executor.submit(
                        self._query_single_collection, kb_id, "text", query_embedding_dict["text"], top_k, filters
                    ))
                if "image" in query_embedding_dict:
                    futures.append(executor.submit(
                        self._query_single_collection, kb_id, "image", query_embedding_dict["image"], top_k, filters
                    ))
                    
                for future in concurrent.futures.as_completed(futures):
                    try:
                        results.extend(future.result())
                    except Exception as e:
                        pass # Ignore if a collection fails
                        
            # Merge and sort descending
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
            
        elif modality in query_embedding_dict:
            results = self._query_single_collection(kb_id, modality, query_embedding_dict[modality], top_k, filters)
            
        return results

    def delete_document(self, kb_id: str, document_id: str) -> None:
        """
        Delete all vectors from all collections where metadata.document_id == document_id.
        
        Args:
            kb_id (str): Knowledge base ID.
            document_id (str): Document ID to delete.
        """
        # Delete from text collection
        try:
            col_text = self.get_or_create_collection(kb_id, modality="text")
            col_text.delete(where={"document_id": document_id})
        except Exception:
            pass
            
        # Delete from image collection
        try:
            col_image = self.get_or_create_collection(kb_id, modality="image")
            col_image.delete(where={"document_id": document_id})
        except Exception:
            pass
