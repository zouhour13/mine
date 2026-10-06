/**
 * Shared TypeScript types mirroring backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/
 */

export type RepoStatus = "pending" | "analyzing" | "completed" | "failed";

export type ConceptCategory =
  | "language"
  | "framework"
  | "library"
  | "architecture"
  | "pattern"
  | "tool";

export type ConceptDifficulty = "beginner" | "intermediate" | "advanced";

export interface Repo {
  id: string;
  github_url: string;
  owner: string;
  name: string;
  description: string | null;
  primary_language: string | null;
  topics: string[];
  status: RepoStatus;
  error_message: string | null;
  created_at: string;
  analyzed_at: string | null;
}

export interface Concept {
  id: string;
  repo_id: string;
  name: string;
  category: ConceptCategory;
  description: string;
  difficulty: ConceptDifficulty;
  interview_question: string;
  created_at: string;
}

export interface ConceptList {
  repo_id: string;
  total: number;
  concepts: Concept[];
}

export interface ApiError {
  detail: string;
}
