# MINE — Interview Speaking Trainer

An AI-powered interview speaking trainer for software and AI engineers.

**The core problem:** Engineers often know technical concepts but struggle to explain them clearly and spontaneously during interviews.

MINE analyses a GitHub repository, extracts the most interview-relevant technical concepts, and generates contextual questions for you to practice speaking about.

---

## Architecture

```
mine/
├── backend/      FastAPI (Python 3.11+)
├── frontend/     Next.js 15 (TypeScript + Tailwind CSS)
└── database/     Supabase PostgreSQL schema
```

**Backend layers:**
- `routes/` — Thin HTTP handlers, delegate to services
- `services/` — Business logic (analysis pipeline, concept persistence)
- `clients/` — GitHub REST API client, LLM client (provider-agnostic)
- `schemas/` — Pydantic request/response models
- `core/` — Settings, DB client, dependency injection, exceptions

**LLM abstraction:** The `LLMClient` is a Python `Protocol`. Adding a new LLM provider requires only a new file in `clients/llm/` and a one-line change in `core/dependencies.py`.

---

## Milestone 1 Features

- ✅ GitHub repository URL input
- ✅ Async repository analysis (FastAPI BackgroundTasks)
- ✅ GitHub metadata, README, file tree, and key file fetching
- ✅ Concept extraction via Gemini (REST API, no grpc dependency)
- ✅ Pydantic-validated structured output
- ✅ Status polling (pending → analyzing → completed/failed)
- ✅ Concept display with categories, difficulty, and interview questions
- ✅ Safe error handling — no secrets or stack traces in API responses

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) project
- A [Gemini API key](https://aistudio.google.com)
- (Optional) A GitHub Personal Access Token

### 1. Database

Run `database/schema.sql` in your Supabase project's SQL Editor.

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Copy and fill in your environment variables
cp .env.example .env
```

Edit `.env`:

```env
GITHUB_TOKEN=              # Optional — public repos work without it
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
CORS_ORIGINS=http://localhost:3000
```

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend

# Copy and fill in your environment variables
cp .env.local.example .env.local

npm install
npm run dev
```

Open http://localhost:3000

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/repos` | Submit a GitHub URL for analysis |
| `GET` | `/api/v1/repos/{id}` | Poll analysis status |
| `GET` | `/api/v1/repos/{id}/concepts` | Fetch extracted concepts |
| `GET` | `/health` | Health check |

---

## Running Tests

```bash
cd backend
.venv\Scripts\python -m pytest tests/ -v   # Windows
python -m pytest tests/ -v                  # macOS/Linux
```

42 tests covering: URL parsing, GitHub client, concept schema validation, repository service, duplicate handling.

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| FastAPI BackgroundTasks | Zero infra overhead for MVP. Not durable across restarts — acceptable at this stage. Celery/Redis can replace it later without changing service code. |
| Gemini via REST API | Avoids grpc/native DLL dependencies that may be blocked by system policies. |
| `LLMClient` as Protocol | Structural typing — add providers without inheritance. |
| Supabase service key backend-only | Frontend never touches the DB directly — all access via the API. |
| `UNIQUE(repo_id, name)` on concepts | DB-level deduplication. Upsert with `ignore_duplicates=True` is the application-layer guard. |
| `GITHUB_TOKEN` optional | Public repos work without a token. Provide one for 5 000 req/hr instead of 60. |

---

## Roadmap (Not Yet Implemented)

- [ ] Timed speaking sessions (30/60/90/120s)
- [ ] Microphone recording
- [ ] Speech-to-text
- [ ] AI evaluation and feedback
- [ ] Session history and weak-topic tracking
- [ ] 70/30 weighted practice algorithm (weak concepts vs random)
- [ ] Authentication
