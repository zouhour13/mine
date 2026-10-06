-- ─────────────────────────────────────────────────────────────────────────────
-- MINE — Database Schema (Milestone 1)
-- Run this in the Supabase SQL Editor for your project.
-- ─────────────────────────────────────────────────────────────────────────────

-- Analysed repositories
CREATE TABLE IF NOT EXISTS repos (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  github_url       TEXT NOT NULL UNIQUE,
  owner            TEXT NOT NULL,
  name             TEXT NOT NULL,
  description      TEXT,
  primary_language TEXT,
  topics           TEXT[],
  readme_excerpt   TEXT,          -- first ~2 000 chars of README, fed to LLM
  status           TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'analyzing', 'completed', 'failed')),
  error_message    TEXT,          -- safe user-facing message only — no secrets/tracebacks
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  analyzed_at      TIMESTAMPTZ
);

-- Extracted technical concepts
CREATE TABLE IF NOT EXISTS concepts (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id           UUID NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
  name              TEXT NOT NULL,
  category          TEXT NOT NULL
                    CHECK (category IN ('language','framework','library','architecture','pattern','tool')),
  description       TEXT NOT NULL,
  difficulty        TEXT NOT NULL
                    CHECK (difficulty IN ('beginner','intermediate','advanced')),
  interview_question TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Prevents the same concept being inserted twice for the same repo
  CONSTRAINT uq_concept_repo_name UNIQUE (repo_id, name)
);

CREATE INDEX IF NOT EXISTS idx_concepts_repo_id ON concepts(repo_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- Future tables (Milestones 2+) — not yet implemented
-- ─────────────────────────────────────────────────────────────────────────────

-- CREATE TABLE IF NOT EXISTS sessions (
--   id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   repo_id    UUID NOT NULL REFERENCES repos(id),
--   started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
--   ended_at   TIMESTAMPTZ
-- );

-- CREATE TABLE IF NOT EXISTS responses (
--   id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
--   concept_id      UUID NOT NULL REFERENCES concepts(id),
--   allotted_secs   INTEGER NOT NULL CHECK (allotted_secs IN (30, 60, 90, 120)),
--   transcript      TEXT,
--   audio_url       TEXT,
--   clarity_score   NUMERIC(3,1) CHECK (clarity_score BETWEEN 0 AND 10),
--   depth_score     NUMERIC(3,1) CHECK (depth_score BETWEEN 0 AND 10),
--   accuracy_score  NUMERIC(3,1) CHECK (accuracy_score BETWEEN 0 AND 10),
--   overall_score   NUMERIC(3,1) CHECK (overall_score BETWEEN 0 AND 10),
--   feedback        TEXT,
--   evaluated_at    TIMESTAMPTZ,
--   created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- );

-- ─────────────────────────────────────────────────────────────────────────────
-- Weakness tracking (future) — derived from responses via a view or query:
--   SELECT concept_id,
--          AVG(overall_score)  AS avg_score,
--          COUNT(*)            AS attempt_count,
--          MAX(created_at)     AS last_practiced_at
--   FROM responses
--   GROUP BY concept_id
--   ORDER BY avg_score, last_practiced_at;
-- ─────────────────────────────────────────────────────────────────────────────
