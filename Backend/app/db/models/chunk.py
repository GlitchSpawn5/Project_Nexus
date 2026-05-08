"""Chunk model — individual embedding units stored in ChromaDB."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Modality(str, enum.Enum):
    text = "text"
    image = "image"
    audio = "audio"


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id"), nullable=False
    )
    kb_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id"), nullable=False
    )
    modality: Mapped[str] = mapped_column(
        Enum(Modality, name="modality", create_constraint=True), nullable=False
    )
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp_end: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vector_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")
    knowledge_base = relationship("KnowledgeBase", back_populates="chunks")
