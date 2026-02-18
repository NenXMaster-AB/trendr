import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h1 className="text-3xl font-semibold">Trendr</h1>
        <p className="mt-2 text-zinc-300">
          Import a YouTube video → generate tweets, LinkedIn posts, and blog drafts. This is a runnable skeleton.
        </p>
        <div className="mt-4 flex gap-3">
          <Link className="rounded-xl bg-zinc-100 px-4 py-2 text-zinc-950" href="/dashboard">Open Dashboard</Link>
          <a className="rounded-xl border border-zinc-700 px-4 py-2 text-zinc-100" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            API Docs
          </a>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-zinc-800 p-5">
          <h2 className="text-lg font-medium">Ingest</h2>
          <p className="mt-2 text-sm text-zinc-300">YouTube import endpoint + background job + transcript artifact.</p>
        </div>
        <div className="rounded-2xl border border-zinc-800 p-5">
          <h2 className="text-lg font-medium">Generate</h2>
          <p className="mt-2 text-sm text-zinc-300">Generate bundle drafts using pluggable text provider (stub).</p>
        </div>
        <div className="rounded-2xl border border-zinc-800 p-5">
          <h2 className="text-lg font-medium">Plugins</h2>
          <p className="mt-2 text-sm text-zinc-300">Provider registry ready for OpenAI/NanoBanana integrations.</p>
        </div>
      </div>
    </div>
  );
}
