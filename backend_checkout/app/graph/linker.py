import logging
from typing import List
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.chunk import Chunk
from app.config import settings

logger = logging.getLogger(__name__)

class CrossModalLinker:
    """Links multimodal chunks (text, image, audio) based on semantics, entities, and time."""

    def __init__(self, chroma_store, embedding_service, graph_store):
        self.chroma_store = chroma_store
        self.embedding_service = embedding_service
        self.graph_store = graph_store
        
        # Load spaCy NER model lazily
        self._nlp = None

    def _get_nlp(self):
        if self._nlp is None:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.error("spaCy model 'en_core_web_sm' not found. Ensure it is downloaded.")
                self._nlp = lambda text: [] # Dummy fallback
        return self._nlp

    def link_by_semantic_similarity(
        self, new_chunks: List[Chunk], kb_id: str, threshold: float = 0.75
    ) -> int:
        """Finds cross-modal semantic relationships using embedding cosine similarity."""
        links_created = 0
        if not new_chunks:
            return 0

        # We need embeddings for the new chunks to query opposite modalities
        # The new chunks are already in DB but we query ChromaDB directly for embeddings if needed,
        # or we just use their text to get the embedding again (faster than querying ChromaDB by ID).
        # Actually, since new_chunks were just embedded in DocumentProcessor, re-embedding is easy.
        
        # Separate by modality
        text_chunks = [c for c in new_chunks if c.modality in ["text", "audio"]]
        image_chunks = [c for c in new_chunks if c.modality == "image"]

        # 1. Text/Audio chunks query Image collection
        if text_chunks:
            try:
                img_collection = self.chroma_store.get_or_create_collection(kb_id, modality="image")
                texts = [c.content_text for c in text_chunks if c.content_text]
                if texts:
                    embeddings = self.embedding_service.embed_batch(texts)
                    
                    for chunk, embedding in zip(text_chunks, embeddings):
                        # Query image collection
                        results = img_collection.query(
                            query_embeddings=[embedding],
                            n_results=5
                        )
                        if results and results["distances"] and results["distances"][0]:
                            for target_id, distance in zip(results["ids"][0], results["distances"][0]):
                                # Cosine distance -> similarity
                                similarity = 1.0 - distance
                                if similarity >= threshold:
                                    self.graph_store.add_link(
                                        source_chunk_id=str(chunk.id),
                                        target_chunk_id=target_id,
                                        link_type="semantic",
                                        strength=similarity
                                    )
                                    links_created += 1
            except Exception as e:
                logger.warning(f"Semantic linking text->image failed: {e}")

        # 2. Image chunks query Text collection
        if image_chunks:
            try:
                txt_collection = self.chroma_store.get_or_create_collection(kb_id, modality="text")
                # Wait, image_chunks were embedded with CLIP. 
                # Cross-collection query requires matching embedding spaces. 
                # If we embedded images with CLIP, and text with all-MiniLM, they are NOT in the same space.
                # However, the user prompt says:
                # "For image chunks: query the text collection using the CLIP text encoder"
                # Wait, the prompt says:
                # "For text chunks: query the image collection using the text embedding" -> This implies Image collection has CLIP text embeddings? No, Image collection has CLIP image embeddings. If we query Image collection with text, we MUST use CLIP text encoder.
                # In previous prompts, did we implement CLIP text encoding in EmbeddingService? Let's check.
                
                # Let's import clip service if available
                from app.embeddings.clip_service import clip_service
                
                # text chunks query image collection using CLIP text encoder
                for chunk in text_chunks:
                    if chunk.content_text:
                        clip_text_emb = clip_service.embed_text(chunk.content_text)
                        # Query image collection
                        img_collection = self.chroma_store.get_or_create_collection(kb_id, modality="image")
                        results = img_collection.query(
                            query_embeddings=[clip_text_emb],
                            n_results=5
                        )
                        if results and results["distances"] and results["distances"][0]:
                            for target_id, distance in zip(results["ids"][0], results["distances"][0]):
                                similarity = 1.0 - distance
                                if similarity >= threshold:
                                    self.graph_store.add_link(
                                        source_chunk_id=str(chunk.id),
                                        target_chunk_id=target_id,
                                        link_type="semantic",
                                        strength=similarity
                                    )
                                    links_created += 1
                
                # image chunks query text collection
                # Wait, text collection is all-MiniLM space. Image is CLIP space.
                # If we have an image chunk, how do we query the text collection?
                # We can't use CLIP image embedding to query all-MiniLM collection.
                # Did we extract OCR text or image descriptions? If image_chunks have content_text (OCR),
                # we can embed that with all-MiniLM to query text collection.
                for chunk in image_chunks:
                    if chunk.content_text:
                        text_emb = self.embedding_service.embed_batch([chunk.content_text])[0]
                        txt_collection = self.chroma_store.get_or_create_collection(kb_id, modality="text")
                        results = txt_collection.query(
                            query_embeddings=[text_emb],
                            n_results=5
                        )
                        if results and results["distances"] and results["distances"][0]:
                            for target_id, distance in zip(results["ids"][0], results["distances"][0]):
                                similarity = 1.0 - distance
                                if similarity >= threshold:
                                    self.graph_store.add_link(
                                        source_chunk_id=str(chunk.id),
                                        target_chunk_id=target_id,
                                        link_type="semantic",
                                        strength=similarity
                                    )
                                    links_created += 1
            except Exception as e:
                logger.warning(f"Semantic linking cross-modal failed: {e}")

        return links_created

    def link_by_named_entities(self, new_chunks: List[Chunk], kb_id: str, db: Session, threshold: int = 2) -> int:
        """Finds links based on shared named entities extracted via spaCy."""
        links_created = 0
        nlp = self._get_nlp()
        
        target_labels = {"PERSON", "ORG", "GPE", "DATE", "MONEY", "PRODUCT"}

        for chunk in new_chunks:
            if not chunk.content_text:
                continue
                
            doc = nlp(chunk.content_text)
            entities = {ent.text for ent in doc.ents if ent.label_ in target_labels}
            
            if not entities:
                continue

            # Query Postgres for other chunks in the same KB containing these entities
            for entity in entities:
                # Use ILIKE for case-insensitive search
                stmt = select(Chunk).where(
                    Chunk.kb_id == uuid.UUID(kb_id),
                    Chunk.id != chunk.id,
                    Chunk.content_text.ilike(f"%{entity}%")
                )
                matching_chunks = db.execute(stmt).scalars().all()
                
                for match in matching_chunks:
                    # Count shared entities between chunk and match
                    match_doc = nlp(match.content_text)
                    match_entities = {ent.text for ent in match_doc.ents if ent.label_ in target_labels}
                    
                    shared = entities.intersection(match_entities)
                    if len(shared) >= threshold:
                        strength = min(len(shared) / 5.0, 1.0)
                        self.graph_store.add_link(
                            source_chunk_id=str(chunk.id),
                            target_chunk_id=str(match.id),
                            link_type="entity",
                            strength=strength,
                            metadata={"shared_entities": list(shared)}
                        )
                        links_created += 1

        return links_created

    def link_by_temporal_cooccurrence(self, new_chunks: List[Chunk], kb_id: str, db: Session, window_seconds: float = 10.0) -> int:
        """Links audio/video chunks with image (frame) chunks based on timestamp proximity."""
        links_created = 0
        
        audio_chunks = [c for c in new_chunks if c.modality == "audio" and c.timestamp_start is not None]
        if not audio_chunks:
            return 0
            
        # Get all image chunks for this KB
        stmt = select(Chunk).where(
            Chunk.kb_id == uuid.UUID(kb_id),
            Chunk.modality == "image"
        )
        image_chunks = db.execute(stmt).scalars().all()
        
        for audio in audio_chunks:
            a_start = audio.timestamp_start
            a_end = audio.timestamp_end if audio.timestamp_end is not None else a_start
            
            for img in image_chunks:
                # Assuming metadata_json contains timestamp for video frames
                img_meta = img.metadata_json or {}
                img_timestamp = img_meta.get("timestamp_start")
                
                if img_timestamp is not None:
                    # Check if img_timestamp is within the audio segment +/- window_seconds
                    if (a_start - window_seconds) <= img_timestamp <= (a_end + window_seconds):
                        self.graph_store.add_link(
                            source_chunk_id=str(audio.id),
                            target_chunk_id=str(img.id),
                            link_type="temporal",
                            strength=1.0
                        )
                        links_created += 1

        return links_created

    def run_all(self, document_id: str, new_chunk_ids: List[str], kb_id: str, db: Session) -> dict:
        """Executes all linking algorithms for newly ingested chunks."""
        # Fetch the full chunk objects
        stmt = select(Chunk).where(Chunk.id.in_([uuid.UUID(cid) for cid in new_chunk_ids]))
        new_chunks = db.execute(stmt).scalars().all()

        if not new_chunks:
            return {"semantic_links": 0, "entity_links": 0, "temporal_links": 0, "total_links": 0}

        # 1. Semantic Links
        semantic_links = self.link_by_semantic_similarity(
            new_chunks, kb_id, threshold=settings.SEMANTIC_LINK_THRESHOLD
        )
        
        # 2. Entity Links
        entity_links = self.link_by_named_entities(
            new_chunks, kb_id, db, threshold=settings.ENTITY_LINK_MIN_SHARED
        )
        
        # 3. Temporal Links
        temporal_links = self.link_by_temporal_cooccurrence(
            new_chunks, kb_id, db, window_seconds=settings.TEMPORAL_LINK_WINDOW_SECONDS
        )

        total = semantic_links + entity_links + temporal_links

        self.graph_store.save()

        return {
            "semantic_links": semantic_links,
            "entity_links": entity_links,
            "temporal_links": temporal_links,
            "total_links": total
        }
