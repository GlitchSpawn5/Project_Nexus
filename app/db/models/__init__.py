"""
Database Models
===============
Import every model so Alembic can discover them via ``Base.metadata``.
"""

from app.db.models.user import User, UserRole                          # noqa: F401
from app.db.models.knowledge_base import KnowledgeBase                 # noqa: F401
from app.db.models.document import Document, FileType, DocumentStatus  # noqa: F401
from app.db.models.chunk import Chunk, Modality                        # noqa: F401
from app.db.models.ingestion_job import IngestionJob, JobStatus        # noqa: F401
from app.db.models.query_session import QuerySession                   # noqa: F401
