import { Concept } from "@/lib/types";
import { ConceptCard } from "./ConceptCard";
import { Spinner } from "@/components/ui/Button";

interface ConceptListProps {
  concepts: Concept[];
  total: number;
  isLoading: boolean;
  error: string | null;
}

export function ConceptList({ concepts, total, isLoading, error }: ConceptListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-3 text-zinc-400 py-8">
        <Spinner size="md" />
        <span className="text-sm">Loading concepts…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/30 px-6 py-5">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    );
  }

  if (concepts.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-6 py-10 text-center">
        <p className="text-sm text-zinc-500">No concepts were extracted for this repository.</p>
      </div>
    );
  }

  return (
    <section aria-label="Extracted concepts">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-medium text-zinc-400">
          {total} concept{total !== 1 ? "s" : ""} extracted
        </h2>
      </div>
      <div className="space-y-3">
        {concepts.map((concept, i) => (
          <ConceptCard key={concept.id} concept={concept} index={i} />
        ))}
      </div>
    </section>
  );
}
