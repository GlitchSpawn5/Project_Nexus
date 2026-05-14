"""
Ingestion Task
==============
Celery task that processes a single document asynchronously.
"""

import uuid
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.db.models.ingestion_job import IngestionJob, JobStatus
from app.worker.celery_app import celery
from app.processing.document_processor import DocumentProcessor


@celery.task(bind=True, name="process_document", max_retries=2)
def process_document(
    self,
    job_id: str,
    document_id: str,
    kb_id: str,
    file_path: str,
    file_type: str,
) -> dict:
    """Process a document end-to-end using DocumentProcessor."""
    db = SessionLocal()
    try:
        job = db.query(IngestionJob).filter(IngestionJob.id == uuid.UUID(job_id)).first()
        if job is None:
            raise ValueError(f"IngestionJob {job_id} not found")

        # Mark job as processing
        job.status = JobStatus.processing
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        print(f"[process_document] job={job_id} | status=processing")

        # Callback to update progress percentage
        def update_progress(pct: int):
            job.progress_pct = pct
            db.commit()

        # Run the real extraction and chunking pipeline
        processor = DocumentProcessor()
        summary = processor.process(
            document_id=document_id,
            file_path=file_path,
            file_type=file_type,
            kb_id=kb_id,
            db=db,
            progress_callback=update_progress
        )

        # Mark job as complete
        job.status = JobStatus.complete
        job.progress_pct = 100
        job.result_json = summary
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        
        print(f"[process_document] job={job_id} | status=complete | summary={summary}")
        return {"job_id": job_id, "status": "complete", "summary": summary}

    except Exception as exc:
        db.rollback()
        # Try to persist the failure
        try:
            job = db.query(IngestionJob).filter(IngestionJob.id == uuid.UUID(job_id)).first()
            if job:
                job.status = JobStatus.failed
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
        print(f"[process_document] job={job_id} | FAILED: {exc}")
        raise
    finally:
        db.close()
