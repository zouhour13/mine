"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { submitRepo, APIResponseError } from "@/lib/api";
import { Button } from "@/components/ui/Button";

export function RepoForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setError("Please enter a GitHub repository URL.");
      return;
    }

    setIsSubmitting(true);
    try {
      const repo = await submitRepo(trimmed);
      router.push(`/analyze/${repo.id}`);
    } catch (err: unknown) {
      const message =
        err instanceof APIResponseError
          ? err.detail
          : "Failed to submit repository. Please try again.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label
          htmlFor="github-url"
          className="block text-sm font-medium text-zinc-300 mb-2"
        >
          GitHub Repository URL
        </label>
        <input
          id="github-url"
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/owner/repository"
          className="w-full rounded-md bg-zinc-900 border border-zinc-700 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:border-transparent transition"
          disabled={isSubmitting}
          autoFocus
        />
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-400">
          {error}
        </p>
      )}

      <Button
        type="submit"
        size="lg"
        isLoading={isSubmitting}
        disabled={isSubmitting}
        className="w-full"
      >
        {isSubmitting ? "Submitting…" : "Analyze Repository"}
      </Button>
    </form>
  );
}
