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
 * Uses an isPolling guard to prevent overlapping concurrent requests.
 */
export function useRepo(repoId: string | null): UseRepoResult {
  const [repo, setRepo] = useState<Repo | null>(null);
  const [error, setError] = useState<string | null>(null);
  // isLoading initialises to true when a repoId is already known at mount time.
  const [isLoading, setIsLoading] = useState(() => !!repoId);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isPollingRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  /**
   * fetchRepo is called from setInterval (always async) so setState calls
   * inside it do not violate react-hooks/set-state-in-effect.
   */
  const fetchRepo = useCallback(async () => {
    if (!repoId) return;
    if (isPollingRef.current) return; // skip overlapping requests
    isPollingRef.current = true;
    try {
      const data = await getRepo(repoId);
      setRepo(data);
      setError(null);
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
    } finally {
      isPollingRef.current = false;
    }
  }, [repoId, stopPolling]);

  useEffect(() => {
    if (!repoId) return;

    isPollingRef.current = false;

    // Schedule initial fetch as a microtask so setState calls inside fetchRepo
    // are not synchronous within the effect body.
    void Promise.resolve().then(fetchRepo);

    intervalRef.current = setInterval(fetchRepo, POLL_INTERVAL_MS);

    return () => stopPolling();
  }, [repoId, fetchRepo, stopPolling]);

  return { repo, error, isLoading };
}
