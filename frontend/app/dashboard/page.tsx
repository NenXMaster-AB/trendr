"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type Project = {
  id: number;
  name: string;
  source_type: string;
  source_ref: string;
};

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [url, setUrl] = useState("");
  const [jobId, setJobId] = useState<number | null>(null);
  const [job, setJob] = useState<any>(null);

  async function refresh() {
    const data = await api.get<Project[]>("/v1/projects");
    setProjects(data);
  }

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (!jobId) return;
    const t = setInterval(async () => {
      const j = await api.get(`/v1/jobs/${jobId}`);
      setJob(j);
      if (j.status === "succeeded" || j.status === "failed") {
        clearInterval(t);
        refresh();
      }
    }, 1500);
    return () => clearInterval(t);
  }, [jobId]);

  async function ingestYouTube() {
    setJob(null);
    const j = await api.post("/v1/ingest/youtube", { url });
    setJobId(j.id);
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="mt-2 text-sm text-zinc-300">Paste a YouTube URL to create a Project and run ingestion (stub transcript).</p>

        <div className="mt-4 flex flex-col gap-3 md:flex-row">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm"
          />
          <button
            onClick={ingestYouTube}
            className="rounded-xl bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950"
          >
            Import
          </button>
        </div>

        {jobId && (
          <div className="mt-4 rounded-xl border border-zinc-800 p-3 text-sm">
            <div className="text-zinc-300">Job: <span className="text-zinc-100">#{jobId}</span></div>
            <div className="text-zinc-300">Status: <span className="text-zinc-100">{job?.status ?? "..."}</span></div>
            {job?.error ? <div className="mt-2 text-red-300">Error: {job.error}</div> : null}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-zinc-800 p-6">
        <h2 className="text-lg font-semibold">Projects</h2>
        <div className="mt-3 space-y-2">
          {projects.map((p) => (
            <a
              key={p.id}
              href={`/projects/${p.id}`}
              className="block rounded-xl border border-zinc-800 bg-zinc-950/40 p-3 hover:bg-zinc-950"
            >
              <div className="font-medium">{p.name}</div>
              <div className="text-xs text-zinc-400">{p.source_type} • {p.source_ref}</div>
            </a>
          ))}
          {projects.length === 0 && <div className="text-sm text-zinc-400">No projects yet.</div>}
        </div>
      </div>
    </div>
  );
}
