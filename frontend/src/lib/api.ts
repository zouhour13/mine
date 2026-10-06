/**
 * Typed API client.
 *
 * All API calls go through this module.
 * The base URL comes from NEXT_PUBLIC_API_URL — never hardcoded.
 * No secrets are ever sent from the frontend.
 */

import type { ApiError, Concept, ConceptList, Repo } from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const API_PREFIX = `${BASE_URL}/api/v1`;

class APIResponseError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
    this.name = "APIResponseError";
  }
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_PREFIX}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body: ApiError = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
      // response body is not JSON — use default message
    }
    throw new APIResponseError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

// ── Repos ────────────────────────────────────────────────────────────────────

export async function submitRepo(githubUrl: string): Promise<Repo> {
  return request<Repo>("/repos", {
    method: "POST",
    body: JSON.stringify({ github_url: githubUrl }),
  });
}

export async function getRepo(repoId: string): Promise<Repo> {
  return request<Repo>(`/repos/${repoId}`);
}

// ── Concepts ─────────────────────────────────────────────────────────────────

export async function getConcepts(repoId: string): Promise<ConceptList> {
  return request<ConceptList>(`/repos/${repoId}/concepts`);
}

export { APIResponseError };
