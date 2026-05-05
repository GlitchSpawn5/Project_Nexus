# NEXUS
# Multimodal Retrieval-Augmented Generation System

A multimodal RAG system that searches across PDFs, images, and audio
using a unified vector database and returns grounded, citation-backed answers.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env
# Edit .env with your actual API keys and settings

# 4. Start infrastructure (PostgreSQL, Redis, ChromaDB)
docker-compose up -d postgres redis chromadb

# 5. Run the application
uvicorn app.main:app --reload

# 6. Visit http://localhost:8000/health
# 7. Swagger docs at http://localhost:8000/docs
```

## Project Structure

```
nexus/
├── app/
│   ├── api/            # FastAPI routers and dependencies
│   │   └── routes/     # Endpoint modules (ingestion, query, kb, admin)
│   ├── core/           # Logging, exceptions, security
│   ├── db/             # SQLAlchemy engine, session, base
│   ├── ingestion/      # Extractors (PDF, DOCX, image, audio) + chunker
│   ├── models/         # ORM models (document, chunk, query_log)
│   ├── rag/            # Retriever, reranker, prompt builder, generator
│   ├── schemas/        # Pydantic request/response models
│   ├── services/       # Embedding, LLM, vector store services
│   ├── tasks/          # Celery async tasks
│   ├── config.py       # Pydantic BaseSettings configuration
│   └── main.py         # FastAPI entry point
├── tests/              # Pytest test suite
├── uploads/            # Uploaded file storage (gitignored)
├── .env.example        # Environment variable template
├── docker-compose.yml  # Local dev infrastructure
├── requirements.txt    # Python dependencies
└── README.md
```
