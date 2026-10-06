# MINE — Frontend

Next.js 15 application (TypeScript + Tailwind CSS).

## Pages

| Route | Description |
|-------|-------------|
| `/` | GitHub URL input |
| `/analyze/[repoId]` | Analysis status (polling) + concept list |

## Key Files

```
src/
├── app/
│   ├── page.tsx                   # Home page
│   └── analyze/[repoId]/page.tsx  # Analysis + concepts page
├── components/
│   ├── layout/                    # Header, PageShell
│   ├── repo/                      # RepoForm, AnalysisStatus, ConceptList, ConceptCard
│   └── ui/                        # Button (with Spinner), Badge
├── hooks/
│   ├── useRepo.ts                 # Polls /repos/{id} every 2s until terminal status
│   └── useConcepts.ts             # Fetches concepts once status=completed
└── lib/
    ├── api.ts                     # Typed fetch wrapper — all API calls
    ├── types.ts                   # TypeScript interfaces mirroring backend schemas
    └── utils.ts                   # cn() helper
```

## Setup

```bash
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

npm install
npm run dev       # http://localhost:3000
npm run build     # Production build
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | FastAPI backend URL (default: `http://localhost:8000`) |

> No secrets are ever stored in the frontend. All database and API key access goes through the backend.
