"""
Ingestion Tasks
===============
Celery tasks for async document processing:
  - process_document: orchestrates extraction → chunking → embedding → storage
  - process_image: runs CLIP embedding on uploaded images
  - transcribe_audio: runs Whisper then embeds the transcript
"""
