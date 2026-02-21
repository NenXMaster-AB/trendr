import Link from "next/link";
import { Sparkles } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-zinc-900 bg-zinc-950/60 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between p-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-100 text-zinc-950">
            <Sparkles size={18} />
          </span>
          <span className="text-lg font-semibold">Trendr</span>
        </Link>

        <nav className="flex items-center gap-3 text-sm text-zinc-300">
          <Link className="hover:text-zinc-100" href="/dashboard">Dashboard</Link>
          <Link className="hover:text-zinc-100" href="/templates">Templates</Link>
          <Link className="hover:text-zinc-100" href="/workflows">Workflows</Link>
          <Link className="hover:text-zinc-100" href="/providers">Providers</Link>
          <a className="hover:text-zinc-100" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API</a>
        </nav>
      </div>
    </header>
  );
}
