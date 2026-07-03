# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup
```bash
uv sync                                    # Install dependencies
cp .env.example .env                       # Create env file, add API key
```

### Run
```bash
./run.sh                                   # Start dev server (port 8000)
# or manually:
cd backend && uv run uvicorn app:app --reload --port 8000
```

Access: http://localhost:8000 (UI), http://localhost:8000/docs (API docs)

### Test
No test suite configured. Manual testing via UI or API calls to `/api/query` and `/api/courses`.

## Architecture

Full-stack RAG (Retrieval-Augmented Generation) system for course material Q&A.

### Backend Pipeline

**Entry point**: `backend/app.py` (FastAPI)

Request flow:
1. `POST /api/query` → `RAGSystem.query()`
2. `SessionManager` maintains conversation history (max 2 messages)
3. `VectorStore` (ChromaDB + sentence-transformers) performs semantic search
4. `AIGenerator` (OpenAI-compatible API) synthesizes answer with retrieved context
5. Returns answer + source documents

**Key modules**:
- `rag_system.py` — Orchestrator, coordinates all components
- `document_processor.py` — Parses course files, chunks text (800 chars, 100 overlap)
- `vector_store.py` — ChromaDB wrapper, handles embeddings (all-MiniLM-L6-v2)
- `ai_generator.py` — OpenAI-compatible API calls with tool use
- `session_manager.py` — In-memory conversation state
- `search_tools.py` — Tool definitions for function calling (OpenAI format)
- `config.py` — Environment variables and constants

**Data ingestion**: On startup, `app.py` loads all `docs/course*.txt` files via `RAGSystem.add_course_folder()`.

### Frontend

Static HTML/JS/CSS served from `frontend/` via FastAPI `StaticFiles` mount at `/`.

Single-page chat interface that calls `/api/query` endpoint.

### Data Sources

Course transcripts in `docs/` directory (4 text files, ~100KB each).

## Environment Variables

Required:
- `ANTHROPIC_API_KEY` — API key (used for any OpenAI-compatible provider)

Optional (defaults in `backend/config.py`):
- `ANTHROPIC_BASE_URL` — Custom API endpoint (e.g. `http://localhost:11434/v1` for Ollama, `https://integrate.api.nvidia.com/v1` for NVIDIA NIM)
- `ANTHROPIC_MODEL` — Model name (default: claude-sonnet-4-20250514)
- `EMBEDDING_MODEL` — Sentence-transformers model (default: all-MiniLM-L6-v2)
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `MAX_RESULTS`, `MAX_HISTORY` — RAG parameters
