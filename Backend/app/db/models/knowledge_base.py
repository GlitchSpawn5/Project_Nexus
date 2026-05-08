"""KnowledgeBase model — logical container for documents."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin


class KnowledgeBase(TimestampMixin, Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="knowledge_bases")
    documents = relationship(
        "Document", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    chunks = relationship(
        "Chunk", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
