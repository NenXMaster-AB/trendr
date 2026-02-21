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
type JobStatusFilter = "all" | "queued" | "running" | "succeeded" | "failed";
type JobKindFilter = "all" | "ingest" | "generate" | "workflow";
type Template = {
  id: number;
  name: string;
  kind: OutputKind;
  version: number;
};

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
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [artifactQuery, setArtifactQuery] = useState("");
  const [artifactHasContentOnly, setArtifactHasContentOnly] = useState(false);
  const [jobStatusFilter, setJobStatusFilter] = useState<JobStatusFilter>("all");
  const [jobKindFilter, setJobKindFilter] = useState<JobKindFilter>("all");
  const [jobErrorsOnly, setJobErrorsOnly] = useState(false);

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
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);

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
    const query = artifactQuery.trim().toLowerCase();
    return artifacts.filter((artifact) => {
      if (activeTab !== "all" && artifact.kind !== activeTab) return false;
      if (artifactHasContentOnly && !(artifact.content ?? "").trim()) return false;
      if (!query) return true;
      const haystack = `${artifact.kind} ${artifact.title ?? ""} ${artifact.content ?? ""}`.toLowerCase();
      return haystack.includes(query);
    });
  }, [activeTab, artifactHasContentOnly, artifactQuery, artifacts]);

  const filteredJobs = useMemo(() => {
    return jobs.filter((entry) => {
      if (jobStatusFilter !== "all" && entry.status !== jobStatusFilter) return false;
      if (jobKindFilter !== "all" && entry.kind !== jobKindFilter) return false;
      if (jobErrorsOnly && !entry.error) return false;
      return true;
    });
  }, [jobErrorsOnly, jobKindFilter, jobStatusFilter, jobs]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (artifactQuery.trim()) count += 1;
    if (artifactHasContentOnly) count += 1;
    if (jobStatusFilter !== "all") count += 1;
    if (jobKindFilter !== "all") count += 1;
    if (jobErrorsOnly) count += 1;
    return count;
  }, [artifactHasContentOnly, artifactQuery, jobErrorsOnly, jobKindFilter, jobStatusFilter]);

  const selectedOutputKinds = useMemo(
    () =>
      (Object.keys(selectedOutputs) as OutputKind[]).filter(
        (kind) => selectedOutputs[kind],
      ),
    [selectedOutputs],
  );
  const isSingleOutputSelected = selectedOutputKinds.length === 1;

  useEffect(() => {
    if (!isGenerateModalOpen) return;
    if (!isSingleOutputSelected) {
      setTemplates([]);
      setSelectedTemplateId(null);
      return;
    }

    const outputKind = selectedOutputKinds[0];
    let cancelled = false;
    (async () => {
      try {
        const rows = await api.get<Template[]>(`/v1/templates?kind=${outputKind}`);
        if (!cancelled) {
          setTemplates(rows);
          setSelectedTemplateId((prev) => {
            if (prev && rows.some((row) => row.id === prev)) {
              return prev;
            }
            return null;
          });
        }
      } catch {
        if (!cancelled) {
          setTemplates([]);
          setSelectedTemplateId(null);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isGenerateModalOpen, isSingleOutputSelected, selectedOutputKinds]);

  function toggleOutput(kind: OutputKind) {
    setSelectedOutputs((prev) => ({ ...prev, [kind]: !prev[kind] }));
  }

  function clearFilters() {
    setArtifactQuery("");
    setArtifactHasContentOnly(false);
    setJobStatusFilter("all");
    setJobKindFilter("all");
    setJobErrorsOnly(false);
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
        template_id: selectedTemplateId,
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

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setIsFilterModalOpen(true)}
              className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-900"
            >
              Filters{activeFilterCount > 0 ? ` (${activeFilterCount})` : ""}
            </button>
            <button
              onClick={() => setIsGenerateModalOpen(true)}
              className="rounded-xl bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950"
            >
              Generate Posts
            </button>
          </div>
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
        <p className="mt-1 text-xs text-zinc-400">
          Showing {filteredJobs.length} of {jobs.length}
          {activeFilterCount > 0 ? " (filtered)" : ""}.
        </p>
        <div className="mt-3 space-y-2">
          {filteredJobs.map((j) => (
            <div key={j.id} className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
              <div className="text-sm font-medium">
                #{j.id} • {j.kind}
              </div>
              <div className="text-xs text-zinc-400">status: {j.status}</div>
              {j.error ? <div className="mt-1 text-xs text-red-300">{j.error}</div> : null}
            </div>
          ))}
          {jobs.length === 0 ? <div className="text-sm text-zinc-400">No jobs yet.</div> : null}
          {jobs.length > 0 && filteredJobs.length === 0 ? (
            <div className="text-sm text-zinc-400">No jobs match current filters.</div>
          ) : null}
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 p-6">
        <h2 className="text-lg font-semibold">Artifacts</h2>
        <p className="mt-1 text-xs text-zinc-400">
          Showing {filteredArtifacts.length} of {artifacts.length}
          {activeFilterCount > 0 || activeTab !== "all" ? " (filtered)" : ""}.
        </p>

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
            <div className="text-sm text-zinc-400">No artifacts match current tab/filters.</div>
          ) : null}
        </div>
      </div>

      {isFilterModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/70 p-4">
          <div className="w-full max-w-lg rounded-2xl border border-zinc-700 bg-zinc-900 p-6">
            <h2 className="text-lg font-semibold">Project Filters</h2>
            <p className="mt-1 text-xs text-zinc-400">
              Narrow artifacts and jobs for this project detail view.
            </p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-2 block text-xs font-medium text-zinc-300" htmlFor="artifact-query">
                  Artifact search
                </label>
                <input
                  id="artifact-query"
                  type="text"
                  value={artifactQuery}
                  onChange={(e) => setArtifactQuery(e.target.value)}
                  placeholder="Search artifact kind, title, or content..."
                  className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
                />
              </div>

              <label className="flex items-center gap-2 text-sm text-zinc-200">
                <input
                  type="checkbox"
                  checked={artifactHasContentOnly}
                  onChange={(e) => setArtifactHasContentOnly(e.target.checked)}
                  className="h-4 w-4"
                />
                Artifacts with content only
              </label>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-medium text-zinc-300" htmlFor="job-status-filter">
                    Job status
                  </label>
                  <select
                    id="job-status-filter"
                    value={jobStatusFilter}
                    onChange={(e) => setJobStatusFilter(e.target.value as JobStatusFilter)}
                    className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
                  >
                    <option value="all">All statuses</option>
                    <option value="queued">Queued</option>
                    <option value="running">Running</option>
                    <option value="succeeded">Succeeded</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-xs font-medium text-zinc-300" htmlFor="job-kind-filter">
                    Job kind
                  </label>
                  <select
                    id="job-kind-filter"
                    value={jobKindFilter}
                    onChange={(e) => setJobKindFilter(e.target.value as JobKindFilter)}
                    className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
                  >
                    <option value="all">All kinds</option>
                    <option value="ingest">Ingest</option>
                    <option value="generate">Generate</option>
                    <option value="workflow">Workflow</option>
                  </select>
                </div>
              </div>

              <label className="flex items-center gap-2 text-sm text-zinc-200">
                <input
                  type="checkbox"
                  checked={jobErrorsOnly}
                  onChange={(e) => setJobErrorsOnly(e.target.checked)}
                  className="h-4 w-4"
                />
                Jobs with errors only
              </label>
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={clearFilters}
                className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-200"
              >
                Clear filters
              </button>
              <button
                onClick={() => setIsFilterModalOpen(false)}
                className="rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      ) : null}

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
              <label className="mb-2 block text-xs font-medium text-zinc-300" htmlFor="template-select">
                Template
              </label>
              <select
                id="template-select"
                value={selectedTemplateId ?? ""}
                onChange={(e) =>
                  setSelectedTemplateId(
                    e.target.value === "" ? null : Number(e.target.value),
                  )
                }
                disabled={!isSingleOutputSelected}
                className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 disabled:opacity-60"
              >
                <option value="">Built-in template (default)</option>
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name} (v{template.version})
                  </option>
                ))}
              </select>
              {!isSingleOutputSelected ? (
                <p className="mt-2 text-xs text-zinc-400">
                  Select exactly one output to use a saved template.
                </p>
              ) : null}
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
