"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ProjectPage({ params }: { params: { id: string } }) {
  const projectId = Number(params.id);
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [jobId, setJobId] = useState<number | null>(null);
  const [job, setJob] = useState<any>(null);
  const [editingArtifactId, setEditingArtifactId] = useState<number | null>(null);
  const [draftContent, setDraftContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function refresh() {
    const a = await api.get<any[]>(`/v1/artifacts?project_id=${projectId}`);
    setArtifacts(a);
  }

  useEffect(() => {
    refresh();
  }, [projectId]);

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

  async function generate() {
    setJob(null);
    const j = await api.post("/v1/generate", {
      project_id: projectId,
      outputs: ["tweet", "linkedin", "blog"],
      tone: "professional"
    });
    setJobId(j.id);
  }

  function startEdit(artifact: any) {
    setEditingArtifactId(artifact.id);
    setDraftContent(artifact.content ?? "");
  }

  function cancelEdit() {
    setEditingArtifactId(null);
    setDraftContent("");
  }

  async function saveEdit(artifactId: number) {
    setIsSaving(true);
    try {
      await api.patch(`/v1/artifacts/${artifactId}`, { content: draftContent });
      await refresh();
      cancelEdit();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Project #{projectId}</h1>
          <button onClick={generate} className="rounded-xl bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950">
            Generate Posts
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
        <h2 className="text-lg font-semibold">Artifacts</h2>
        <div className="mt-3 space-y-3">
          {artifacts.map((a) => (
            <div key={a.id} className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-medium">{a.kind} • {a.title || "Untitled"}</div>
                {editingArtifactId === a.id ? null : (
                  <button
                    onClick={() => startEdit(a)}
                    className="rounded-lg border border-zinc-700 px-2 py-1 text-xs text-zinc-200 hover:bg-zinc-900"
                  >
                    Edit
                  </button>
                )}
              </div>

              {editingArtifactId === a.id ? (
                <div className="mt-2 space-y-2">
                  <textarea
                    value={draftContent}
                    onChange={(e) => setDraftContent(e.target.value)}
                    rows={8}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-100"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => saveEdit(a.id)}
                      disabled={isSaving}
                      className="rounded-lg bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-950 disabled:opacity-60"
                    >
                      {isSaving ? "Saving..." : "Save"}
                    </button>
                    <button
                      onClick={cancelEdit}
                      disabled={isSaving}
                      className="rounded-lg border border-zinc-700 px-3 py-1 text-xs text-zinc-200 disabled:opacity-60"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : a.content ? (
                <pre className="mt-2 whitespace-pre-wrap text-xs text-zinc-200">{a.content}</pre>
              ) : (
                <div className="mt-2 text-xs text-zinc-400">No content</div>
              )}
            </div>
          ))}
          {artifacts.length === 0 && <div className="text-sm text-zinc-400">No artifacts yet.</div>}
        </div>
      </div>
    </div>
  );
}
