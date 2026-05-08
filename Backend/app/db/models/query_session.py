import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    Boolean,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class QuerySession(Base):
    __tablename__ = "query_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kb_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    llm_provider: Mapped[str] = mapped_column(String, nullable=False)
    raw_llm_response: Mapped[str] = mapped_column(Text, nullable=False)
    final_answer: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    insufficient_evidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Store retrieved chunks as JSON so we don't need a complex many-to-many relationship just for history
    retrieved_chunk_ids: Mapped[list | dict] = mapped_column(JSON, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
