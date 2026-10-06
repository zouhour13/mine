"use client";

import { use } from "react";
import Link from "next/link";
import { PageShell } from "@/components/layout/PageShell";
import { AnalysisStatus } from "@/components/repo/AnalysisStatus";
import { ConceptList } from "@/components/repo/ConceptList";
import { useRepo } from "@/hooks/useRepo";
import { useConcepts } from "@/hooks/useConcepts";

interface AnalyzePageProps {
  params: Promise<{ repoId: string }>;
}

export default function AnalyzePage({ params }: AnalyzePageProps) {
  const { repoId } = use(params);
  const { repo, error: repoError, isLoading: repoLoading } = useRepo(repoId);

  const isCompleted = repo?.status === "completed";
  const {
    concepts,
    total,
    error: conceptsError,
    isLoading: conceptsLoading,
  } = useConcepts(repoId, isCompleted);

  return (
    <PageShell>
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Back link */}
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <span aria-hidden>←</span> Analyse another repository
        </Link>

        {/* Analysis status panel */}
        <AnalysisStatus
          repo={repo}
          isLoading={repoLoading}
          error={repoError}
        />

        {/* Concepts panel — only shown when completed */}
        {isCompleted && (
          <ConceptList
            concepts={concepts}
            total={total}
            isLoading={conceptsLoading}
            error={conceptsError}
          />
        )}

        {/* Failed state retry */}
        {repo?.status === "failed" && (
          <div className="text-center">
            <Link
              href="/"
              className="text-sm text-zinc-400 hover:text-zinc-200 underline underline-offset-4 transition-colors"
            >
              Try a different repository
            </Link>
          </div>
        )}
      </div>
    </PageShell>
  );
}
