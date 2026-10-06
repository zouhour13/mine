import type { Metadata } from "next";
import { PageShell } from "@/components/layout/PageShell";
import { RepoForm } from "@/components/repo/RepoForm";

export const metadata: Metadata = {
  title: "MINE — Analyze a Repository",
  description:
    "Enter a GitHub repository URL to extract technical interview concepts and start practicing.",
};

export default function HomePage() {
  return (
    <PageShell>
      <div className="max-w-xl mx-auto">
        {/* Hero */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-100 mb-3">
            Interview Speaking Trainer
          </h1>
          <p className="text-zinc-400 leading-relaxed">
            Paste a public GitHub repository URL. MINE will analyse the codebase,
            extract the technical concepts that matter in an engineering interview,
            and generate contextual questions for you to practise out loud.
          </p>
        </div>

        {/* Form card */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
          <RepoForm />
        </div>

        {/* How it works */}
        <div className="mt-10 grid grid-cols-3 gap-4">
          {[
            {
              step: "01",
              title: "Paste a repo URL",
              desc: "Any public GitHub repository works.",
            },
            {
              step: "02",
              title: "AI analyses it",
              desc: "MINE reads the code structure and identifies key concepts.",
            },
            {
              step: "03",
              title: "Practice speaking",
              desc: "Get contextual interview questions and practise your explanations.",
            },
          ].map(({ step, title, desc }) => (
            <div key={step} className="space-y-1">
              <span className="text-xs font-mono text-zinc-600">{step}</span>
              <p className="text-sm font-medium text-zinc-300">{title}</p>
              <p className="text-xs text-zinc-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </PageShell>
  );
}
