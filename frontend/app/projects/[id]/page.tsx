"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

type Project = {
  id: number;
  name: string;
  source_type: string;
  source_ref: string;
};

type Job = {
  id: number;
  kind: string;
  status: string;
  project_id?: number | null;
  error?: string | null;
};

type Artifact = {
  id: number;
  kind: string;
  title?: string;
  content?: string;
};

type OutputKind = "tweet" | "linkedin" | "blog";
type ArtifactTab = "all" | "transcript" | "tweet" | "linkedin" | "blog";

const TABS: Array<{ key: ArtifactTab; label: string }> = [
  { key: "all", label: "All" },
  { key: "transcript", label: "Transcript" },
  { key: "tweet", label: "Tweets" },
  { key: "linkedin", label: "LinkedIn" },
  { key: "blog", label: "Blog" },
];

export default function ProjectPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const hasValidProjectId = Number.isFinite(projectId) && projectId > 0;

  const [project, setProject] = useState<Project | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobId, setJobId] = useState<number | null>(null);
  const [job, setJob] = useState<Job | null>(null);

  const [editingArtifactId, setEditingArtifactId] = useState<number | null>(null);
  const [draftContent, setDraftContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const [activeTab, setActiveTab] = useState<ArtifactTab>("all");

  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [selectedOutputs, setSelectedOutputs] = useState<Record<OutputKind, boolean>>({
    tweet: true,
    linkedin: true,
    blog: true,
  });
  const [tone, setTone] = useState("professional");
  const [brandVoice, setBrandVoice] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  async function refresh() {
    if (!hasValidProjectId) return;
    const [projectData, artifactData, jobData] = await Promise.all([
      api.get<Project>(`/v1/projects/${projectId}`),
      api.get<Artifact[]>(`/v1/artifacts?project_id=${projectId}`),
      api.get<Job[]>(`/v1/jobs?project_id=${projectId}&limit=20`),
    ]);
    setProject(projectData);
    setArtifacts(artifactData);
    setJobs(jobData);
  }

  useEffect(() => {
    if (!hasValidProjectId) return;
    refresh();
  }, [projectId, hasValidProjectId]);

  useEffect(() => {
    if (!jobId) return;
    const t = setInterval(async () => {
      const j = await api.get<Job>(`/v1/jobs/${jobId}`);
      setJob(j);
      if (j.status === "succeeded" || j.status === "failed") {
        clearInterval(t);
        refresh();
      }
    }, 1500);
    return () => clearInterval(t);
  }, [jobId]);

  const latestJob = jobs[0] ?? null;
  const headerJobStatus = jobId ? job?.status : latestJob?.status;

  const filteredArtifacts = useMemo(() => {
    if (activeTab === "all") return artifacts;
    return artifacts.filter((artifact) => artifact.kind === activeTab);
  }, [artifacts, activeTab]);

  const selectedOutputKinds = useMemo(
    () =>
      (Object.keys(selectedOutputs) as OutputKind[]).filter(
        (kind) => selectedOutputs[kind],
      ),
    [selectedOutputs],
  );

  function toggleOutput(kind: OutputKind) {
    setSelectedOutputs((prev) => ({ ...prev, [kind]: !prev[kind] }));
  }

  async function generate() {
    if (!hasValidProjectId) return;
    if (selectedOutputKinds.length === 0) {
      setGenerateError("Select at least one output type.");
      return;
    }

    setGenerateError(null);
    setIsGenerating(true);
    setJob(null);

    try {
      const j = await api.post<Job>("/v1/generate", {
        project_id: projectId,
        outputs: selectedOutputKinds,
        tone,
        brand_voice: brandVoice.trim() || null,
      });
      setJobId(j.id);
      setIsGenerateModalOpen(false);
    } finally {
      setIsGenerating(false);
    }
  }

  function startEdit(artifact: Artifact) {
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
      {!hasValidProjectId ? (
        <div className="rounded-2xl border border-red-800 bg-red-950/30 p-6 text-sm text-red-200">
          Invalid project id in route.
        </div>
      ) : null}

      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{project?.name ?? `Project #${projectId}`}</h1>
            <div className="mt-1 text-xs text-zinc-400">
              {project?.source_type ?? "youtube"} •{" "}
              {project?.source_ref?.startsWith("http") ? (
                <a
                  href={project.source_ref}
                  target="_blank"
                  rel="noreferrer"
                  className="text-zinc-200 underline decoration-zinc-600 underline-offset-2"
                >
                  Source link
                </a>
              ) : (
                project?.source_ref ?? "loading..."
              )}
            </div>
            <div className="mt-2 text-xs text-zinc-400">
              Latest job status:{" "}
              <span className="font-medium text-zinc-200">{headerJobStatus ?? "none"}</span>
            </div>
          </div>

          <button
            onClick={() => setIsGenerateModalOpen(true)}
            className="rounded-xl bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950"
          >
            Generate Posts
          </button>
        </div>

        {jobId ? (
          <div className="mt-4 rounded-xl border border-zinc-800 p-3 text-sm">
            <div className="text-zinc-300">
              Job: <span className="text-zinc-100">#{jobId}</span>
            </div>
            <div className="text-zinc-300">
              Status: <span className="text-zinc-100">{job?.status ?? "..."}</span>
            </div>
            {job?.error ? <div className="mt-2 text-red-300">Error: {job.error}</div> : null}
          </div>
        ) : null}
      </div>

      <div className="rounded-2xl border border-zinc-800 p-6">
        <h2 className="text-lg font-semibold">Jobs</h2>
        <div className="mt-3 space-y-2">
          {jobs.map((j) => (
            <div key={j.id} className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
              <div className="text-sm font-medium">
                #{j.id} • {j.kind}
              </div>
              <div className="text-xs text-zinc-400">status: {j.status}</div>
              {j.error ? <div className="mt-1 text-xs text-red-300">{j.error}</div> : null}
            </div>
          ))}
          {jobs.length === 0 ? <div className="text-sm text-zinc-400">No jobs yet.</div> : null}
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 p-6">
        <h2 className="text-lg font-semibold">Artifacts</h2>

        <div className="mt-3 flex flex-wrap gap-2">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`rounded-lg border px-3 py-1 text-xs ${
                  isActive
                    ? "border-zinc-300 bg-zinc-100 text-zinc-950"
                    : "border-zinc-700 text-zinc-300 hover:bg-zinc-900"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="mt-3 space-y-3">
          {filteredArtifacts.map((a) => (
            <div key={a.id} className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-medium">
                  {a.kind} • {a.title || "Untitled"}
                </div>
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

          {artifacts.length === 0 ? (
            <div className="text-sm text-zinc-400">No artifacts yet.</div>
          ) : filteredArtifacts.length === 0 ? (
            <div className="text-sm text-zinc-400">No artifacts in this tab yet.</div>
          ) : null}
        </div>
      </div>

      {isGenerateModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/70 p-4">
          <div className="w-full max-w-lg rounded-2xl border border-zinc-700 bg-zinc-900 p-6">
            <h2 className="text-lg font-semibold">Generate Options</h2>
            <p className="mt-1 text-xs text-zinc-400">
              Select outputs and writing preferences for this generation run.
            </p>

            <div className="mt-4">
              <div className="mb-2 text-xs font-medium text-zinc-300">Outputs</div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {(["tweet", "linkedin", "blog"] as OutputKind[]).map((kind) => (
                  <label
                    key={kind}
                    className="flex items-center gap-2 rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-200"
                  >
                    <input
                      type="checkbox"
                      checked={selectedOutputs[kind]}
                      onChange={() => toggleOutput(kind)}
                      className="h-4 w-4"
                    />
                    <span className="capitalize">{kind}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="mt-4">
              <label className="mb-2 block text-xs font-medium text-zinc-300" htmlFor="tone-select">
                Tone
              </label>
              <select
                id="tone-select"
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
              >
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="authoritative">Authoritative</option>
                <option value="playful">Playful</option>
              </select>
            </div>

            <div className="mt-4">
              <label className="mb-2 block text-xs font-medium text-zinc-300" htmlFor="brand-voice">
                Brand voice
              </label>
              <textarea
                id="brand-voice"
                value={brandVoice}
                onChange={(e) => setBrandVoice(e.target.value)}
                rows={4}
                placeholder="Describe tone, style, phrasing, and constraints."
                className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
              />
            </div>

            {generateError ? (
              <div className="mt-3 rounded-lg border border-red-800 bg-red-950/30 px-3 py-2 text-xs text-red-300">
                {generateError}
              </div>
            ) : null}

            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => {
                  setGenerateError(null);
                  setIsGenerateModalOpen(false);
                }}
                className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-200"
              >
                Cancel
              </button>
              <button
                onClick={generate}
                disabled={isGenerating}
                className="rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950 disabled:opacity-60"
              >
                {isGenerating ? "Starting..." : "Start Generation"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
