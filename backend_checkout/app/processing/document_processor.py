"""
Document Processor Orchestrator
===============================
Coordinates extraction, chunking, language detection, and database persistence.
"""

import uuid
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.db.models.document import Document, DocumentStatus
from app.db.models.chunk import Chunk, Modality
from app.processing.extractors.text_extractor import TextExtractor
from app.processing.chunker import SemanticChunker
from app.processing.language_detector import detect_language


from app.processing.extractors.image_extractor import ImageExtractor


class DocumentProcessor:
    """Orchestrates document ingestion processing."""

    def process(
        self, 
        document_id: str, 
        file_path: str, 
        file_type: str, 
        kb_id: str, 
        db: Session,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> dict:
        """
        Runs the extraction pipeline and populates the database based on modality.
        """
        # Fetch Document record
        doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found in database.")

        if file_type == "image":
            return self.process_image(doc, file_path, kb_id, db, progress_callback)
        elif file_type in ["pdf", "docx"]:
            return self.process_text_document(doc, file_path, file_type, kb_id, db, progress_callback)
        elif file_type in ["audio", "video"]:
            return self.process_audio(doc, file_path, kb_id, db, progress_callback)
        else:
            raise ValueError(f"Unsupported file_type for processing: {file_type}")

    # ─── AUDIO PIPELINE ───────────────────────────────────────────────────

    def process_audio(
        self,
        doc: Document,
        file_path: str,
        kb_id: str,
        db: Session,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> dict:
        """
        Transcribe an audio/video file, chunk the transcript, embed, and store.
        Audio chunks live in the *text* collection (same embedding model) with modality="audio".
        """
        from app.processing.extractors.audio_extractor import AudioExtractor
        from app.processing.audio_chunker import AudioChunker
        from app.embeddings import embedding_service
        from app.vectorstore import chroma_store

        # ── 1. Metadata extraction (10 %) ─────────────────────────────────
        file_meta = AudioExtractor.extract_metadata(file_path)
        if progress_callback:
            progress_callback(10)

        # ── 2. Transcription (50 %) ───────────────────────────────────────
        extractor = AudioExtractor()
        transcript = extractor.transcribe(file_path)

        doc.language = transcript["language"]
        doc.duration_seconds = transcript["duration_seconds"]
        # Use mutagen duration if Whisper's is 0 (edge-case short clips)
        if (doc.duration_seconds or 0) == 0 and file_meta.get("duration_seconds"):
            doc.duration_seconds = file_meta["duration_seconds"]

        if progress_callback:
            progress_callback(50)

        # ── 3. Chunking (65 %) ────────────────────────────────────────────
        chunks_data = AudioChunker.chunk_segments(transcript["segments"])

        # Fallback: if Whisper detected speech but the chunker found no words
        # (e.g. music-only or very short utterances), create a single chunk
        # from the full transcript.
        if not chunks_data and transcript["full_text"].strip():
            chunks_data = [{
                "chunk_index": 0,
                "text": transcript["full_text"].strip(),
                "timestamp_start": 0.0,
                "timestamp_end": transcript["duration_seconds"],
                "word_count": len(transcript["full_text"].split()),
                "segment_indices": [],
            }]

        if progress_callback:
            progress_callback(65)

        # ── 4. Database persistence (80 %) ────────────────────────────────
        db_chunks = []
        for chunk_dict in chunks_data:
            chunk_metadata = {
                "segment_indices": chunk_dict["segment_indices"],
                "word_count": chunk_dict["word_count"],
                "audio_duration": transcript["duration_seconds"],
                "language": transcript["language"],
            }

            chunk_record = Chunk(
                document_id=doc.id,
                kb_id=uuid.UUID(kb_id),
                chunk_index=chunk_dict["chunk_index"],
                content_text=chunk_dict["text"],
                page_number=None,
                timestamp_start=chunk_dict["timestamp_start"],
                timestamp_end=chunk_dict["timestamp_end"],
                metadata_json=chunk_metadata,
                modality=Modality.audio,
                vector_id=None,
            )
            db.add(chunk_record)
            db_chunks.append(chunk_record)

        db.flush()  # generate UUIDs

        if progress_callback:
            progress_callback(80)

        # ── 5. Embedding + vector store (95 %) ────────────────────────────
        if db_chunks:
            texts = [c.content_text for c in db_chunks]
            chunk_ids = [str(c.id) for c in db_chunks]

            metadatas = []
            for c in db_chunks:
                metadatas.append({
                    "document_id": str(doc.id),
                    "filename": doc.filename,
                    "modality": "audio",
                    "chunk_index": c.chunk_index,
                    "timestamp_start": c.timestamp_start,
                    "timestamp_end": c.timestamp_end,
                    "language": transcript["language"],
                })

            # Audio transcripts are text → use text embedding model → text collection
            embeddings = embedding_service.embed_batch(texts)

            try:
                chroma_store.upsert_chunks(
                    kb_id=kb_id,
                    chunk_ids=chunk_ids,
                    embeddings=embeddings,
                    texts=texts,
                    metadatas=metadatas,
                    modality="text",  # audio shares the text collection
                )

                for c in db_chunks:
                    c.vector_id = str(c.id)

                if progress_callback:
                    progress_callback(95)

            except Exception as e:
                db.rollback()
                raise RuntimeError(f"Failed to upsert audio chunks to vector store: {e}")
        else:
            # No speech detected — skip embedding, jump to 95 %
            if progress_callback:
                progress_callback(95)

        # ── 6. Graph Linking (97 %) ───────────────────────────────────────
        from app.graph.graph_store import graph_store
        from app.graph.linker import CrossModalLinker
        from app.vectorstore import chroma_store
        from app.embeddings import embedding_service

        for c in db_chunks:
            graph_store.add_chunk_node(
                chunk_id=str(c.id),
                kb_id=kb_id,
                modality=c.modality.value,
                document_id=str(doc.id),
                filename=doc.filename,
                text_preview=c.content_text[:100] if c.content_text else "",
                timestamp_start=c.timestamp_start,
                timestamp_end=c.timestamp_end,
                page_number=c.page_number
            )
            
        if progress_callback:
            progress_callback(97)
            
        linker = CrossModalLinker(chroma_store=chroma_store, embedding_service=embedding_service, graph_store=graph_store)
        chunk_ids = [str(c.id) for c in db_chunks]
        link_summary = linker.run_all(str(doc.id), chunk_ids, kb_id, db)
        
        if progress_callback:
            progress_callback(99)

        # ── 7. Finalise (100 %) ───────────────────────────────────────────
        doc.status = DocumentStatus.complete
        db.commit()

        if progress_callback:
            progress_callback(100)

        return {
            "document_id": str(doc.id),
            "language": transcript["language"],
            "duration_seconds": transcript["duration_seconds"],
            "total_chunks": len(db_chunks),
            "full_transcript_length": len(transcript["full_text"]),
            "links": link_summary
        }
            
    def process_image(
        self, 
        doc: Document, 
        file_path: str, 
        kb_id: str, 
        db: Session,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> dict:
        """Processes an image document."""
        # ── 1. Extraction ──────────────────────────────────────────────────
        meta = ImageExtractor.extract(file_path)
        ocr_text = meta.get("ocr_text", "")
        
        if progress_callback:
            progress_callback(30)
            
        # ── 2. Vector Embedding ────────────────────────────────────────────
        from app.embeddings import clip_service
        
        # Embed the image
        embedding = clip_service.embed_image(file_path)
        
        if progress_callback:
            progress_callback(60)
            
        # ── 3. Database Persistence ────────────────────────────────────────
        chunk_record = Chunk(
            document_id=doc.id,
            kb_id=uuid.UUID(kb_id),
            chunk_index=0,
            content_text=ocr_text,
            page_number=None,
            metadata_json=meta,
            modality=Modality.image,
            image_id=str(doc.id), # One image = one chunk, so image_id is doc_id
            vector_id=None
        )
        db.add(chunk_record)
        db.flush()
        
        if progress_callback:
            progress_callback(80)
            
        # ── 4. ChromaDB Storage ────────────────────────────────────────────
        from app.vectorstore import chroma_store
        
        # Truncate OCR text for metadata to 500 chars max
        safe_ocr = ocr_text[:500] + ("..." if len(ocr_text) > 500 else "")
        
        chroma_meta = {
            "document_id": str(doc.id),
            "filename": doc.filename,
            "width": meta.get("width", 0),
            "height": meta.get("height", 0),
            "ocr_text": safe_ocr,
            "modality": "image",
            "language": "unknown" # Images don't use langdetect
        }
        
        try:
            chroma_store.upsert_chunks(
                kb_id=kb_id,
                chunk_ids=[str(chunk_record.id)],
                embeddings=[embedding],
                texts=[ocr_text],
                metadatas=[chroma_meta],
                modality="image"
            )
            
            chunk_record.vector_id = str(chunk_record.id)
            
            if progress_callback:
                progress_callback(95)
                
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Failed to upsert image chunk to vector store: {str(e)}")
            
        # ── 5. Graph Linking (97 %) ────────────────────────────────────────
        from app.graph.graph_store import graph_store
        from app.graph.linker import CrossModalLinker
        from app.vectorstore import chroma_store
        from app.embeddings import embedding_service
        
        graph_store.add_chunk_node(
            chunk_id=str(chunk_record.id),
            kb_id=kb_id,
            modality=chunk_record.modality.value,
            document_id=str(doc.id),
            filename=doc.filename,
            text_preview=chunk_record.content_text[:100] if chunk_record.content_text else "",
            timestamp_start=chunk_record.timestamp_start,
            timestamp_end=chunk_record.timestamp_end,
            page_number=chunk_record.page_number
        )
        
        if progress_callback:
            progress_callback(97)
            
        linker = CrossModalLinker(chroma_store=chroma_store, embedding_service=embedding_service, graph_store=graph_store)
        link_summary = linker.run_all(str(doc.id), [str(chunk_record.id)], kb_id, db)

        if progress_callback:
            progress_callback(99)

        # ── 6. Finalize Document Status ────────────────────────────────────
        doc.status = DocumentStatus.complete
        db.commit()
        
        if progress_callback:
            progress_callback(100)
            
        return {
            "document_id": str(doc.id),
            "chunk_id": str(chunk_record.id),
            "has_ocr_text": bool(ocr_text),
            "dimensions": f"{meta.get('width', 0)}x{meta.get('height', 0)}",
            "links": link_summary
        }

    def process_text_document(
        self, 
        doc: Document, 
        file_path: str, 
        file_type: str, 
        kb_id: str, 
        db: Session,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> dict:

        # ── 1. Extraction ──────────────────────────────────────────────────
        if file_type == "pdf":
            pages_or_sections = TextExtractor.extract_from_pdf(file_path)
            doc.page_count = len(pages_or_sections)
        elif file_type == "docx":
            pages_or_sections = TextExtractor.extract_from_docx(file_path)
            doc.page_count = len(pages_or_sections) # for DOCX, page_count acts as section_count
        else:
            raise ValueError(f"Unsupported file_type for text extraction: {file_type}")
            
        if progress_callback:
            progress_callback(10)

        # ── 2. Language Detection ──────────────────────────────────────────
        # Gather up to first 1000 chars across pages/sections for language detection
        sample_texts = []
        chars_collected = 0
        for item in pages_or_sections:
            text = item.get("text", "")
            sample_texts.append(text)
            chars_collected += len(text)
            if chars_collected >= 1000:
                break
                
        full_sample = "\n".join(sample_texts)
        doc.language = detect_language(full_sample)
        
        # We can flush early to persist page_count and language, but doing it later is fine too
        
        # ── 3. Chunking ────────────────────────────────────────────────────
        chunks_data = SemanticChunker.chunk(pages_or_sections, source_type=file_type)
        
        if progress_callback:
            progress_callback(50)

        # ── 4. Database Persistence ────────────────────────────────────────
        db_chunks = []
        for chunk_dict in chunks_data:
            chunk_metadata = {
                "word_count": chunk_dict["word_count"],
                "section_heading": chunk_dict.get("section_heading"),
                "char_start": chunk_dict["char_start"],
                "char_end": chunk_dict["char_end"],
            }
            
            chunk_record = Chunk(
                document_id=doc.id,
                kb_id=uuid.UUID(kb_id),
                chunk_index=chunk_dict["chunk_index"],
                content_text=chunk_dict["text"],
                page_number=chunk_dict.get("page_number"),
                metadata_json=chunk_metadata,
                modality=Modality.text,
                vector_id=None # To be populated later when embedded
            )
            db.add(chunk_record)
            db_chunks.append(chunk_record)
            
        db.flush() # Ensure chunks have their UUIDs generated
        
        if progress_callback:
            progress_callback(60)
            
        # ── 5. Vector Embedding & Storage ──────────────────────────────────
        from app.embeddings import embedding_service
        from app.vectorstore import chroma_store
        
        texts = [c.content_text for c in db_chunks]
        chunk_ids = [str(c.id) for c in db_chunks]
        
        # Prepare metadata for ChromaDB
        metadatas = []
        for c in db_chunks:
            meta = {
                "document_id": str(doc.id),
                "page_number": c.page_number,
                "section_heading": c.metadata_json.get("section_heading"),
                "modality": c.modality.value,
                "chunk_index": c.chunk_index,
                "language": doc.language,
            }
            metadatas.append(meta)
            
        # Embed batch
        embeddings = embedding_service.embed_batch(texts)
        if progress_callback:
            progress_callback(80)
            
        # Upsert to ChromaDB safely
        try:
            chroma_store.upsert_chunks(
                kb_id=kb_id,
                chunk_ids=chunk_ids,
                embeddings=embeddings,
                texts=texts,
                metadatas=metadatas
            )
            
            # If successful, update the PostgreSQL records with the vector IDs
            for c in db_chunks:
                c.vector_id = str(c.id)
                
            if progress_callback:
                progress_callback(95)
                
        except Exception as e:
            # Upsert failed, do not set vector_id, possibly log error
            # Rollback any pending DB changes (or just the vector_id setting since we didn't commit yet)
            db.rollback()
            raise RuntimeError(f"Failed to upsert chunks to vector store: {str(e)}")
            
        # ── 6. Graph Linking (97 %) ────────────────────────────────────────
        from app.graph.graph_store import graph_store
        from app.graph.linker import CrossModalLinker
        from app.vectorstore import chroma_store
        from app.embeddings import embedding_service
        
        for c in db_chunks:
            graph_store.add_chunk_node(
                chunk_id=str(c.id),
                kb_id=kb_id,
                modality=c.modality.value,
                document_id=str(doc.id),
                filename=doc.filename,
                text_preview=c.content_text[:100] if c.content_text else "",
                timestamp_start=c.timestamp_start,
                timestamp_end=c.timestamp_end,
                page_number=c.page_number
            )
            
        if progress_callback:
            progress_callback(97)
            
        linker = CrossModalLinker(chroma_store=chroma_store, embedding_service=embedding_service, graph_store=graph_store)
        chunk_ids = [str(c.id) for c in db_chunks]
        link_summary = linker.run_all(str(doc.id), chunk_ids, kb_id, db)
        
        if progress_callback:
            progress_callback(99)

        # ── 7. Finalize Document Status ────────────────────────────────────
        doc.status = DocumentStatus.complete
        db.commit()
        
        if progress_callback:
            progress_callback(100)
        
        return {
            "document_id": str(doc.id),
            "language": doc.language,
            "total_chunks": len(chunks_data),
            "page_count": doc.page_count,
            "links": link_summary
        }
