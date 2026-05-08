# NEXUS
# Multimodal Retrieval-Augmented Generation System

A secure, multimodal RAG system that searches across Text, PDFs, Images, and Audio using a unified vector database. It returns grounded, citation-backed answers with automated evidence chaining and role-based access control.

## Key Features

- **Multi-Modal Ingestion**: Extract and embed content from Text/PDFs (Sentence-Transformers), Images (CLIP), and Audio (Whisper).
- **Semantic Evidence Chaining**: Automatically links conceptually related text chunks, images, and audio segments across documents using a NetworkX graph layer.
- **Answer Generation Layer**: Generates LLM responses directly grounded in the retrieved chunks, including inline citations.
- **Provider Fallback Chain**: Robust multi-provider LLM integration (Groq → Gemini → Ollama → OpenAI) to ensure maximum uptime and rate-limit handling.
- **Multi-Tenancy & RBAC**: Full JWT-based authentication. Users securely manage their own Knowledge Bases (KBs), with strict Admin-level override and oversight capabilities.
- **Celery Task Queue**: Asynchronous processing for long-running document chunking, embedding, and cross-modal linking tasks.

## Quick Start (Local Development)

The current local development setup operates entirely without Docker by leveraging SQLite databases and local file persistence.

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Install dependencies
# NOTE: Requires PyTorch, which is included in the requirements.
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env
# Edit .env with your LLM API keys (Groq, Gemini, etc.)
# Note: You don't need all keys; the fallback chain will use what is available.

# 4. Start the Celery Worker (In a separate terminal)
# Make sure your virtual environment is active
celery -A app.worker.celery_app worker --loglevel=info --pool=solo

# 5. Run the application
uvicorn app.main:app --reload

# 6. Access the Application
# - Health check: http://localhost:8000/health
# - Swagger docs: http://localhost:8000/docs
```

## Security & First Boot

On initial boot, NEXUS automatically seeds a system administrator account.
- **Default Admin Email**: `admin@nexus.local`
- **Default Admin Password**: `changeme123`

*(You can customize these defaults via the `.env` file before booting).*

## Project Structure

```
nexus/
├── app/
│   ├── api/            # FastAPI routers (auth, admin, ingest, query, kb, graph, llm)
│   ├── auth/           # JWT creation, decoding, RBAC, and KB isolation rules
│   ├── db/             # SQLAlchemy engine, session, and ORM models
│   ├── embeddings/     # SentenceTransformers and CLIP integration services
│   ├── graph/          # NetworkX persistence and semantic/entity/temporal linking
│   ├── ingestion/      # Multi-modal extractors (PDF, Image, Audio) & chunking logic
│   ├── llm/            # Answer generation, citation parsing, and Provider definitions
│   ├── worker/         # Celery App and asynchronous background tasks
│   ├── config.py       # Pydantic BaseSettings configuration
│   └── main.py         # FastAPI entry point & global seeder
├── tests/              # Pytest test suite
├── uploads/            # Uploaded physical file storage (gitignored)
├── chroma_data/        # Local ChromaDB Vector persistence (gitignored)
├── graph_data/         # NetworkX JSON database (gitignored)
├── *.db                # SQLite databases for App, Celery Broker, and Celery Backend (gitignored)
├── .env.example        # Environment variable template
├── requirements.txt    # Python dependencies
└── README.md
```
