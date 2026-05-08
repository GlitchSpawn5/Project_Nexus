"""
NEXUS — Database Engine & Session
===================================
SQLAlchemy engine, session factory, declarative base, and FastAPI dependency.
"""

from datetime import datetime

from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)

from app.config import settings

# ---------------------------------------------------------------------------
# Engine & session
# ---------------------------------------------------------------------------
_connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=not settings.DATABASE_URL.startswith("sqlite"),
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Shared declarative base for every ORM model."""
    pass


# ---------------------------------------------------------------------------
# Reusable mixin
# ---------------------------------------------------------------------------
class TimestampMixin:
    """Adds created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """Yield a SQLAlchemy session; auto-closes when the request ends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
