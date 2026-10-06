import { Concept } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";

interface ConceptCardProps {
  concept: Concept;
  index: number;
}

export function ConceptCard({ concept, index }: ConceptCardProps) {
  return (
    <article
      className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 space-y-4 hover:border-zinc-700 transition-colors"
      aria-label={`Concept: ${concept.name}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-zinc-600 w-5 shrink-0">
            {String(index + 1).padStart(2, "0")}
          </span>
          <h3 className="text-sm font-semibold text-zinc-100 leading-snug">
            {concept.name}
          </h3>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Badge
            label={concept.category}
            variant="category"
            value={concept.category}
          />
          <Badge
            label={concept.difficulty}
            variant="difficulty"
            value={concept.difficulty}
          />
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-zinc-400 leading-relaxed pl-8">
        {concept.description}
      </p>

      {/* Interview question */}
      <div className="ml-8 rounded-md border border-zinc-700 bg-zinc-800/50 px-4 py-3">
        <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide mb-1">
          Interview question
        </p>
        <p className="text-sm text-zinc-200 leading-relaxed">
          {concept.interview_question}
        </p>
      </div>
    </article>
  );
}
