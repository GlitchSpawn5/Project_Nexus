"""
NEXUS — Multimodal Retrieval-Augmented Generation System
=========================================================
FastAPI entry point.

Initialises the application, registers middleware, mounts routers,
and exposes a /health endpoint for liveness checks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# ---------------------------------------------------------------------------
# Router imports (empty placeholders for now)
# ---------------------------------------------------------------------------
from app.api.routes import ingestion, query, knowledge_base, admin, graph, llm, auth

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="NEXUS",
    description=(
        "Multimodal RAG system — search across PDFs, images, and audio "
        "using a unified vector database and get grounded, citation-backed answers."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])
app.include_router(knowledge_base.router, prefix="/api/v1/kb", tags=["Knowledge Base"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["LLM"])


# ---------------------------------------------------------------------------
# Auto-create tables in development mode
# ---------------------------------------------------------------------------
if settings.APP_ENV == "development":
    import importlib
    from app.db.database import engine, Base
    # Import all models so Base.metadata is populated
    for _m in [
        "app.db.models.user",
        "app.db.models.knowledge_base",
        "app.db.models.document",
        "app.db.models.chunk",
        "app.db.models.ingestion_job",
        "app.db.models.query_session",
    ]:
        importlib.import_module(_m)

    Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Database Seeding (Runs in ALL environments)
# ---------------------------------------------------------------------------
from app.db.database import SessionLocal
from app.auth.security import seed_admin_user
db = SessionLocal()
try:
    seed_admin_user(db)
finally:
    db.close()


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Return basic system status."""
    return {"status": "ok"}
