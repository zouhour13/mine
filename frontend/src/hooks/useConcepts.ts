"use client";

import { useEffect, useState } from "react";
import { getConcepts } from "@/lib/api";
import type { Concept } from "@/lib/types";

interface UseConceptsResult {
  concepts: Concept[];
  total: number;
  error: string | null;
  isLoading: boolean;
}

/**
 * Fetches concepts for a repo once.
 * Only fires when repoId is set and ready=true.
 */
export function useConcepts(
  repoId: string | null,
  ready: boolean
): UseConceptsResult {
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  // isLoading starts true when we know we're about to fetch; only set to false.
  const [isLoading, setIsLoading] = useState(() => !!(repoId && ready));

  useEffect(() => {
    if (!repoId || !ready) return;

    getConcepts(repoId)
      .then((data) => {
        setConcepts(data.concepts);
        setTotal(data.total);
        setError(null);
      })
      .catch((err: unknown) => {
        const message =
          err instanceof Error ? err.message : "Failed to fetch concepts.";
        setError(message);
      })
      .finally(() => setIsLoading(false));
  }, [repoId, ready]);

  return { concepts, total, error, isLoading };
}
