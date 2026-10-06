<div align="center">

# MINE

**AI-Powered Interview Speaking Trainer for Software & AI Engineers**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Tests](https://img.shields.io/badge/tests-42%20passing-brightgreen?style=flat)](#running-tests)

</div>

---

## The Problem

Engineers often **know** technical concepts but struggle to **explain** them clearly and spontaneously under interview pressure. The gap is not knowledge — it is verbal articulation on demand.

MINE solves this by analysing your actual codebase, extracting the concepts an interviewer would ask about, and generating contextual questions for you to practise speaking out loud.

---

## How It Works

```
GitHub URL  ──▶  Repository Analysis  ──▶  Concept Extraction  ──▶  Practice
```

1. Paste a public GitHub repository URL
2. MINE fetches metadata, README, language breakdown, file tree, and key files
3. A Gemini LLM extracts 10–20 high-value interview concepts, contextualised to **your** project
4. You receive structured concepts with interview questions to practise

> **Example question generated from a FastAPI project:**
> *"Why did you choose FastAPI over Flask or Django for this backend, and how does its dependency injection system help structure the codebase?"*

---

## Architecture

```
mine/
├── backend/          # FastAPI · Python 3.11+
│   ├── app/
│   │   ├── core/         # config.py · dependencies.py · exceptions.py · database.py
│   │   ├── routes/       # Thin HTTP handlers — repos.py · concepts.py
│   │   ├── services/     # Business logic — repo_service.py · concept_service.py
│   │   ├── clients/      # External APIs — github_client.py · llm/gemini_client.py
│   │   └── schemas/      # Pydantic models — repo.py · concept.py
│   └── tests/            # 42 unit tests (all passing)
│
├── frontend/         # Next.js 15 · TypeScript · Tailwind CSS
│   └── src/
│       ├── app/          # Pages — / · /analyze/[repoId]
│       ├── components/   # UI · layout · repo components
│       ├── hooks/        # useRepo (polling) · useConcepts
│       └── lib/          # api.ts · types.ts · utils.ts
│
└── database/
    └── schema.sql    # Supabase PostgreSQL schema
```

### Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Thin routes** | Routes only validate input and shape responses. All logic lives in services. |
| **Provider-agnostic LLM** | `LLMClient` is a Python `Protocol`. Add a new provider with one new file. |
| **No secrets in responses** | Domain exceptions map to safe user-facing messages. No stack traces ever reach the API. |
| **Optional GitHub token** | Public repositories work without a token. Token raises rate limit from 60 → 5,000 req/hr. |
| **Scoped analysis** | Only metadata, README, language breakdown, top-level tree, and ≤5 key files are sent to the LLM. No raw codebase dumps. |
| **Async analysis** | `POST /repos` returns `202` immediately. Analysis runs via FastAPI `BackgroundTasks`. Frontend polls every 2s. |

---

## API Reference

**Base URL:** `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/repos` | Submit a GitHub URL — returns `202` immediately |
| `GET` | `/repos/{id}` | Poll analysis status (`pending → analyzing → completed\|failed`) |
| `GET` | `/repos/{id}/concepts` | Fetch extracted concepts (requires `status=completed`) |
| `GET` | `/health` | Health check |

**Interactive docs:** http://localhost:8000/docs

### Example: Submit a repository

```bash
curl -X POST http://localhost:8000/api/v1/repos \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/tiangolo/fastapi"}'
```

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "owner": "tiangolo",
  "name": "fastapi",
  "status": "pending",
  "created_at": "2026-10-06T12:00:00Z"
}
```

### Example: Concept response

```json
{
  "repo_id": "550e8400-...",
  "total": 14,
  "concepts": [
    {
      "name": "Dependency Injection",
      "category": "pattern",
      "difficulty": "intermediate",
      "description": "FastAPI resolves typed dependencies declared in function signatures at request time, enabling clean separation of concerns for auth, DB access, and shared state.",
      "interview_question": "How does FastAPI's dependency injection differ from traditional middleware, and why did you choose it to structure this backend?"
    }
  ]
}
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier works)
- A [Gemini API key](https://aistudio.google.com/app/apikey) (free tier works)
- *(Optional)* A [GitHub Personal Access Token](https://github.com/settings/tokens) — needed only for higher rate limits

---

### Step 1 — Database

Open your Supabase project → **SQL Editor** → paste and run [`database/schema.sql`](database/schema.sql).

---

### Step 2 — Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS / Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Optional — public repos work without this
GITHUB_TOKEN=ghp_...

# Required
GEMINI_API_KEY=your-gemini-api-key
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJh...

# Defaults — change if needed
LLM_PROVIDER=gemini
CORS_ORIGINS=http://localhost:3000
```

```bash
# Start the backend
uvicorn app.main:app --reload --port 8000
```

---

### Step 3 — Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open **http://localhost:3000**

---

## Running Tests

```bash
cd backend

# Windows
.venv\Scripts\python -m pytest tests/ -v

# macOS / Linux
python -m pytest tests/ -v
```

```
42 passed in 0.65s
```

Tests cover:
- **URL parsing** — valid/invalid GitHub URLs, edge cases
- **GitHub client** — all HTTP status codes mapped to domain exceptions, token auth
- **Concept validation** — Pydantic schema enforcement for all LLM outputs
- **Repository service** — status transitions, duplicate handling, error safety
- All external calls are mocked — no real API keys needed

---

## Concept Quality

MINE is designed to generate questions that reveal depth of understanding, not trivia.

| ❌ Shallow | ✅ Contextual |
|-----------|-------------|
| "What is Docker?" | "Why does this project use Docker Compose, and how does it manage the service dependencies?" |
| "What is async/await?" | "Where does this codebase use async I/O and why does it matter for the expected workload?" |
| "What is FastAPI?" | "What trade-offs did you consider when choosing FastAPI over alternatives for this API?" |

---

## Roadmap

### Milestone 2 — Speaking Practice
- [ ] Timed speaking sessions (30 / 60 / 90 / 120 seconds)
- [ ] Microphone recording
- [ ] Speech-to-text transcription
- [ ] AI evaluation with structured feedback (clarity, depth, accuracy)

### Milestone 3 — Progress Tracking
- [ ] Session history
- [ ] Weak-topic identification
- [ ] 70/30 weighted practice (weak concepts prioritised)
- [ ] Performance trends over time

### Future
- [ ] Authentication
- [ ] Multiple repository workspaces
- [ ] Durable job queue (Celery + Redis) replacing BackgroundTasks

---

## Contributing

This project follows a clean architecture — contributions are welcome.

1. Keep routes thin
2. Business logic belongs in services
3. External APIs belong behind clients
4. Never commit `.env` files or secrets

---

<div align="center">
Built with FastAPI · Next.js · Supabase · Gemini
</div>
