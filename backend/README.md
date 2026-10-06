# MINE — Backend

FastAPI application (Python 3.11+).

## Structure

```
app/
├── main.py              # App factory, CORS, router registration
├── core/
│   ├── config.py        # Settings only (Pydantic BaseSettings)
│   ├── dependencies.py  # Client factories — GitHubClient, LLMClient
│   ├── database.py      # Supabase async client singleton
│   └── exceptions.py    # Domain exceptions with safe user-facing messages
├── routes/
│   ├── repos.py         # POST /repos · GET /repos/{id}
│   └── concepts.py      # GET /repos/{id}/concepts
├── services/
│   ├── repo_service.py  # Analysis pipeline orchestrator
│   └── concept_service.py  # Concept persistence + deduplication
├── clients/
│   ├── github_client.py    # GitHub REST API
│   └── llm/
│       ├── base.py         # LLMClient Protocol
│       └── gemini_client.py # Gemini via REST API (no grpc)
└── schemas/
    ├── repo.py          # RepoCreate · RepoRead · RepoContext
    └── concept.py       # LLMConceptItem · ConceptRead · ConceptList
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env
# Fill in GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Tests

```bash
python -m pytest tests/ -v
# 42 passed
```

## Analysis Flow

```
POST /repos (202 immediately)
        │
        └── BackgroundTask: run_analysis()
                │
                ├── GitHub: fetch metadata, README, languages, tree, key files
                ├── LLM:    extract_concepts() → validated Pydantic list
                └── DB:     bulk_insert_concepts() → status=completed
```

> **BackgroundTasks caveat:** Tasks are in-process and not durable. A server restart during analysis will leave a repo stuck at `analyzing`. Acceptable for MVP — replace with Celery later if needed.

## Adding a New LLM Provider

1. Create `app/clients/llm/<provider>_client.py`
2. Implement `extract_concepts(context, max_concepts, min_concepts)` matching the `LLMClient` Protocol
3. Add a branch in `app/core/dependencies.py` → `_build_llm_client()`
4. Set `LLM_PROVIDER=<provider>` in `.env`
