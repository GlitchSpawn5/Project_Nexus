"""
Ingestion Router
================
POST /file          — Upload a file, create Document + IngestionJob, fire Celery task
GET  /jobs/{job_id} — Check ingestion job status
"""

import os
import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.models.document import Document, DocumentStatus
from app.db.models.ingestion_job import IngestionJob, JobStatus
from app.db.models.chunk import Chunk
from app.worker.tasks.ingest_task import process_document
from app.auth.dependencies import get_current_active_user
from app.auth.kb_access import verify_kb_access
from app.db.models.user import User

router = APIRouter()

# Map common extensions → FileType enum values
_EXT_MAP = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".mp3": "audio",
    ".wav": "audio",
    ".m4a": "audio",
    ".flac": "audio",
    ".ogg": "audio",
    ".aac": "audio",
    ".mp4": "video",
    ".mkv": "video",
    ".avi": "video",
    ".mov": "video",
    ".webm": "video",
}


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    kb_id: str = Query(..., description="Knowledge-base ID to ingest into"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Accept a file upload, persist it, and queue an ingestion job."""
    verify_kb_access(kb_id, current_user, db)

    # ── Resolve file type from extension ───────────────────────────────
    ext = Path(file.filename or "").suffix.lower()
    file_type = _EXT_MAP.get(ext)
    if file_type is None:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file extension: '{ext}'",
        )

    # ── Save file to uploads/ ──────────────────────────────────────────
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    dest = upload_dir / unique_name

    with open(dest, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    # ── Create Document record ─────────────────────────────────────────
    doc = Document(
        kb_id=uuid.UUID(kb_id),
        filename=file.filename,
        file_type=file_type,
        file_path=str(dest),
        status=DocumentStatus.pending,
    )
    db.add(doc)
    db.flush()  # populate doc.id

    # ── Create IngestionJob record ─────────────────────────────────────
    job = IngestionJob(
        document_id=doc.id,
        status=JobStatus.queued,
        progress_pct=0,
    )
    db.add(job)
    db.commit()
    db.refresh(doc)
    db.refresh(job)

    # ── Fire Celery task ───────────────────────────────────────────────
    process_document.delay(
        job_id=str(job.id),
        document_id=str(doc.id),
        kb_id=kb_id,
        file_path=str(dest),
        file_type=file_type,
    )

    return {
        "job_id": str(job.id),
        "document_id": str(doc.id),
        "status": "queued",
    }


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return the current status of an ingestion job."""
    job = db.query(IngestionJob).filter(IngestionJob.id == uuid.UUID(job_id)).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    doc = db.query(Document).filter(Document.id == job.document_id).first()
    if doc:
        verify_kb_access(str(doc.kb_id), current_user, db)
    total_chunks = db.query(Chunk).filter(Chunk.document_id == job.document_id).count()

    return {
        "job_id": str(job.id),
        "document_id": str(job.document_id),
        "status": job.status,
        "progress_pct": job.progress_pct,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "total_chunks": total_chunks,
        "language": doc.language if doc else None,
        "page_count": doc.page_count if doc else None,
    }


@router.get("/documents")
async def list_documents(
    kb_id: str = Query(..., description="Knowledge-base ID to list documents for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return documents that belong to an accessible knowledge base."""
    verify_kb_access(kb_id, current_user, db)

    docs = (
        db.query(Document)
        .filter(Document.kb_id == uuid.UUID(kb_id))
        .order_by(Document.created_at.desc())
        .all()
    )

    return [
        {
            "id": str(doc.id),
            "kb_id": str(doc.kb_id),
            "filename": doc.filename,
            "file_type": doc.file_type.value if hasattr(doc.file_type, "value") else doc.file_type,
            "file_path": doc.file_path,
            "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
            "language": doc.language,
            "page_count": doc.page_count,
            "duration_seconds": doc.duration_seconds,
            "created_at": doc.created_at.isoformat(),
        }
        for doc in docs
    ]


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a document and its chunks from DB and vector store."""
    doc = db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    verify_kb_access(str(doc.kb_id), current_user, db)
        
    # 1. Delete from ChromaDB
    from app.vectorstore import chroma_store
    chroma_store.delete_document(kb_id=str(doc.kb_id), document_id=str(doc.id))
    
    # 2. Delete from PostgreSQL
    # Chunks are typically deleted automatically if there's a CASCADE rule on the FK.
    # Otherwise, we delete chunks first explicitly.
    db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
    
    # Delete IngestionJob manually since it might not cascade
    db.query(IngestionJob).filter(IngestionJob.document_id == doc.id).delete()
    
    # Delete the document
    db.delete(doc)
    db.commit()
    
    # 3. Delete from GraphStore
    from app.graph.graph_store import graph_store
    graph_store.delete_document_nodes(str(doc.id))
    graph_store.save()
    
    # Optionally, delete the physical file
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception:
        pass
        
    return {"status": "deleted", "document_id": str(doc.id)}


@router.get("/{doc_id}/transcript")
async def get_transcript(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Return the full reassembled transcript for an audio/video document.
    Chunks are returned in order with timestamps.
    """
    doc = db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    verify_kb_access(str(doc.kb_id), current_user, db)

    from app.db.models.chunk import Modality

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == doc.id, Chunk.modality == Modality.audio)
        .order_by(Chunk.chunk_index)
        .all()
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No audio transcript found for this document",
        )

    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "duration_seconds": doc.duration_seconds,
        "language": doc.language,
        "chunks": [
            {
                "chunk_index": c.chunk_index,
                "text": c.content_text,
                "timestamp_start": c.timestamp_start,
                "timestamp_end": c.timestamp_end,
            }
            for c in chunks
        ],
    }
