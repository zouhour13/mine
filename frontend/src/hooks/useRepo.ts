"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getRepo } from "@/lib/api";
import type { Repo, RepoStatus } from "@/lib/types";

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES: RepoStatus[] = ["completed", "failed"];

interface UseRepoResult {
  repo: Repo | null;
  error: string | null;
  isLoading: boolean;
}

/**
 * Polls GET /repos/{repoId} every 2 seconds until status is completed or failed.
 * Automatically stops polling on terminal status or component unmount.
 */
export function useRepo(repoId: string | null): UseRepoResult {
  const [repo, setRepo] = useState<Repo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const fetchRepo = useCallback(async () => {
    if (!repoId) return;
    try {
      const data = await getRepo(repoId);
      setRepo(data);
      if (TERMINAL_STATUSES.includes(data.status)) {
        stopPolling();
        setIsLoading(false);
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch repository status.";
      setError(message);
      stopPolling();
      setIsLoading(false);
    }
  }, [repoId, stopPolling]);

  useEffect(() => {
    if (!repoId) return;

    setIsLoading(true);
    setError(null);
    fetchRepo();

    intervalRef.current = setInterval(fetchRepo, POLL_INTERVAL_MS);

    return () => stopPolling();
  }, [repoId, fetchRepo, stopPolling]);

  return { repo, error, isLoading };
}
