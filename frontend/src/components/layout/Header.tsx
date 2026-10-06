import Link from "next/link";

export function Header() {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950">
      <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-lg font-semibold tracking-tight text-white group-hover:text-zinc-300 transition-colors">
            MINE
          </span>
          <span className="text-xs text-zinc-500 hidden sm:inline">
            Interview Speaking Trainer
          </span>
        </Link>
        <nav className="flex items-center gap-4 text-sm text-zinc-400">
          <Link href="/" className="hover:text-white transition-colors">
            Analyze
          </Link>
        </nav>
      </div>
    </header>
  );
}
