import { Repo, RepoStatus } from "@/lib/types";
import { Spinner } from "@/components/ui/Button";

interface AnalysisStatusProps {
  repo: Repo | null;
  isLoading: boolean;
  error: string | null;
}

const STATUS_CONFIG: Record<
  RepoStatus,
  { label: string; description: string; color: string }
> = {
  pending: {
    label: "Queued",
    description: "Repository is queued for analysis.",
    color: "text-zinc-400",
  },
  analyzing: {
    label: "Analyzing",
    description: "Fetching repository data and extracting concepts…",
    color: "text-blue-400",
  },
  completed: {
    label: "Complete",
    description: "Analysis complete. Concepts extracted successfully.",
    color: "text-emerald-400",
  },
  failed: {
    label: "Failed",
    description: "Analysis failed.",
    color: "text-red-400",
  },
};

export function AnalysisStatus({ repo, isLoading, error }: AnalysisStatusProps) {
  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/30 px-6 py-5">
        <p className="text-sm font-medium text-red-400">Error</p>
        <p className="mt-1 text-sm text-red-300">{error}</p>
      </div>
    );
  }

  if (isLoading && !repo) {
    return (
      <div className="flex items-center gap-3 text-zinc-400">
        <Spinner size="md" />
        <span className="text-sm">Loading…</span>
      </div>
    );
  }

  if (!repo) return null;

  const config = STATUS_CONFIG[repo.status];
  const isInProgress = repo.status === "pending" || repo.status === "analyzing";

  return (
    <div className="space-y-4">
      {/* Repo header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100">
            {repo.owner}/{repo.name}
          </h2>
          {repo.description && (
            <p className="mt-1 text-sm text-zinc-400">{repo.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {isInProgress && <Spinner size="sm" className="text-blue-400" />}
          <span className={`text-sm font-medium ${config.color}`}>
            {config.label}
          </span>
        </div>
      </div>

      {/* Status bar */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3">
        <p className="text-sm text-zinc-400">{config.description}</p>
        {repo.status === "failed" && repo.error_message && (
          <p className="mt-1 text-sm text-red-400">{repo.error_message}</p>
        )}
      </div>

      {/* Metadata chips */}
      {(repo.primary_language || repo.topics.length > 0) && (
        <div className="flex flex-wrap gap-2">
          {repo.primary_language && (
            <span className="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
              {repo.primary_language}
            </span>
          )}
          {repo.topics.slice(0, 6).map((topic) => (
            <span
              key={topic}
              className="text-xs px-2 py-1 rounded bg-zinc-900 text-zinc-400 border border-zinc-800"
            >
              {topic}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
