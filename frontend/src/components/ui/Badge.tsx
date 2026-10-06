import { cn } from "@/lib/utils";
import { ConceptCategory, ConceptDifficulty } from "@/lib/types";

const CATEGORY_STYLES: Record<ConceptCategory, string> = {
  language: "bg-blue-950 text-blue-300 border-blue-800",
  framework: "bg-violet-950 text-violet-300 border-violet-800",
  library: "bg-cyan-950 text-cyan-300 border-cyan-800",
  architecture: "bg-amber-950 text-amber-300 border-amber-800",
  pattern: "bg-emerald-950 text-emerald-300 border-emerald-800",
  tool: "bg-zinc-800 text-zinc-300 border-zinc-700",
};

const DIFFICULTY_STYLES: Record<ConceptDifficulty, string> = {
  beginner: "bg-emerald-950 text-emerald-400 border-emerald-800",
  intermediate: "bg-amber-950 text-amber-400 border-amber-800",
  advanced: "bg-red-950 text-red-400 border-red-800",
};

interface BadgeProps {
  label: string;
  variant: "category" | "difficulty";
  value: ConceptCategory | ConceptDifficulty;
  className?: string;
}

export function Badge({ label, variant, value, className }: BadgeProps) {
  const style =
    variant === "category"
      ? CATEGORY_STYLES[value as ConceptCategory]
      : DIFFICULTY_STYLES[value as ConceptDifficulty];

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        style,
        className
      )}
    >
      {label}
    </span>
  );
}
