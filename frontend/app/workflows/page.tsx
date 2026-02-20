"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";

type OutputKind = "tweet" | "linkedin" | "blog";

type Workflow = {
  id: number;
  workspace_id: number;
  name: string;
  definition_json: Record<string, any>;
  created_at: string;
};

type Project = {
  id: number;
  name: string;
};

type Template = {
  id: number;
  name: string;
  kind: OutputKind;
  version: number;
};

type Job = {
  id: number;
  kind: string;
  status: string;
  error?: string | null;
  output?: Record<string, any>;
};

const STARTER_DEFINITION = {
  nodes: [
    { id: "ingest", type: "task", task: "ingest_youtube" },
    { id: "generate", type: "task", task: "generate_posts" },
  ],
  edges: [{ from: "ingest", to: "generate" }],
};

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newName, setNewName] = useState("YouTube -> Generate");
  const [newDefinitionText, setNewDefinitionText] = useState(
    JSON.stringify(STARTER_DEFINITION, null, 2),
  );
  const [isCreating, setIsCreating] = useState(false);

  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null);
  const selectedWorkflow = useMemo(
    () => workflows.find((item) => item.id === selectedWorkflowId) ?? null,
    [workflows, selectedWorkflowId],
  );

  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [url, setUrl] = useState("");
  const [projectName, setProjectName] = useState("");
  const [tone, setTone] = useState("professional");
  const [brandVoice, setBrandVoice] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [selectedOutputs, setSelectedOutputs] = useState<Record<OutputKind, boolean>>({
    tweet: true,
    linkedin: true,
    blog: true,
  });

  const [runJobId, setRunJobId] = useState<number | null>(null);
  const [runJob, setRunJob] = useState<Job | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const selectedOutputKinds = useMemo(
    () =>
      (Object.keys(selectedOutputs) as OutputKind[]).filter(
        (kind) => selectedOutputs[kind],
      ),
    [selectedOutputs],
  );

  const selectableTemplates = useMemo(() => {
    if (selectedOutputKinds.length !== 1) {
      return [];
    }
    return templates.filter((item) => item.kind === selectedOutputKinds[0]);
  }, [templates, selectedOutputKinds]);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const [workflowRows, projectRows, templateRows] = await Promise.all([
        api.get<Workflow[]>("/v1/workflows"),
        api.get<Project[]>("/v1/projects"),
        api.get<Template[]>("/v1/templates"),
      ]);
      setWorkflows(workflowRows);
      setProjects(projectRows);
      setTemplates(templateRows);

      if (workflowRows.length > 0) {
        setSelectedWorkflowId((prev) => {
          if (prev && workflowRows.some((item) => item.id === prev)) {
            return prev;
          }
          return workflowRows[0].id;
        });
      } else {
        setSelectedWorkflowId(null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load workflows";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (selectedOutputKinds.length !== 1) {
      setSelectedTemplateId("");
      return;
    }
    setSelectedTemplateId((prev) => {
      if (!prev) return "";
      return selectableTemplates.some((item) => String(item.id) === prev) ? prev : "";
    });
  }, [selectableTemplates, selectedOutputKinds]);

  useEffect(() => {
    if (!runJobId) return;
    const t = setInterval(async () => {
      try {
        const data = await api.get<Job>(`/v1/jobs/${runJobId}`);
        setRunJob(data);
        if (data.status === "succeeded" || data.status === "failed") {
          clearInterval(t);
          refresh();
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load workflow job";
        setError(message);
        clearInterval(t);
      }
    }, 1500);
    return () => clearInterval(t);
  }, [runJobId]);

  async function createWorkflow() {
    const trimmedName = newName.trim();
    if (!trimmedName) {
      setError("Workflow name is required.");
      return;
    }

    let parsedDefinition: Record<string, any>;
    try {
      parsedDefinition = JSON.parse(newDefinitionText);
    } catch {
      setError("Workflow definition must be valid JSON.");
      return;
    }

    setIsCreating(true);
    setError(null);
    try {
      await api.post("/v1/workflows", {
        name: trimmedName,
        definition_json: parsedDefinition,
      });
      await refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to create workflow";
      setError(message);
    } finally {
      setIsCreating(false);
    }
  }

  async function runWorkflow() {
    if (!selectedWorkflow) {
      setError("Select a workflow first.");
      return;
    }
    if (selectedOutputKinds.length === 0) {
      setError("Select at least one output.");
      return;
    }

    setIsRunning(true);
    setError(null);
    setRunJob(null);

    try {
      const body = {
        project_id: selectedProjectId ? Number(selectedProjectId) : null,
        url: url.trim() || null,
        project_name: projectName.trim() || null,
        outputs: selectedOutputKinds,
        tone,
        brand_voice: brandVoice.trim() || null,
        template_id: selectedTemplateId ? Number(selectedTemplateId) : null,
      };

      const job = await api.post<Job>(`/v1/workflows/${selectedWorkflow.id}/run`, body);
      setRunJobId(job.id);
      setRunJob(job);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to run workflow";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h1 className="text-2xl font-semibold">Workflows</h1>
        <p className="mt-2 text-sm text-zinc-300">
          Create reusable DAG definitions and run them as a single workflow job.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="space-y-4 rounded-2xl border border-zinc-800 p-4">
          <div className="text-sm font-semibold">Saved workflows</div>
          <div className="space-y-2">
            {workflows.map((item) => (
              <button
                key={item.id}
                onClick={() => setSelectedWorkflowId(item.id)}
                className={`w-full rounded-xl border px-3 py-2 text-left ${
                  selectedWorkflowId === item.id
                    ? "border-zinc-300 bg-zinc-100 text-zinc-950"
                    : "border-zinc-800 bg-zinc-950/40 text-zinc-100 hover:bg-zinc-950"
                }`}
              >
                <div className="text-sm font-medium">{item.name}</div>
                <div className="text-xs opacity-80">id {item.id}</div>
              </button>
            ))}
            {!isLoading && workflows.length === 0 ? (
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2 text-sm text-zinc-400">
                No workflows yet.
              </div>
            ) : null}
          </div>
        </div>

        <div className="space-y-4 rounded-2xl border border-zinc-800 p-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/30 p-4">
            <h2 className="text-sm font-semibold">Create workflow</h2>
            <input
              value={newName}
              onChange={(event) => setNewName(event.target.value)}
              placeholder="Workflow name"
              className="mt-3 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
            />
            <textarea
              value={newDefinitionText}
              onChange={(event) => setNewDefinitionText(event.target.value)}
              rows={14}
              className="mt-3 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-xs"
            />
            <div className="mt-3 flex justify-end">
              <button
                onClick={createWorkflow}
                disabled={isCreating}
                className="rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950 disabled:opacity-60"
              >
                {isCreating ? "Creating..." : "Create"}
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-950/30 p-4">
            <h2 className="text-sm font-semibold">Run workflow</h2>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-zinc-400" htmlFor="project-id">
                  Existing project (optional)
                </label>
                <select
                  id="project-id"
                  value={selectedProjectId}
                  onChange={(event) => setSelectedProjectId(event.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                >
                  <option value="">None</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name} (#{project.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-xs text-zinc-400" htmlFor="tone">
                  Tone
                </label>
                <select
                  id="tone"
                  value={tone}
                  onChange={(event) => setTone(event.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                >
                  <option value="professional">Professional</option>
                  <option value="casual">Casual</option>
                  <option value="authoritative">Authoritative</option>
                  <option value="playful">Playful</option>
                </select>
              </div>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-zinc-400" htmlFor="url">
                  URL (for ingest node)
                </label>
                <input
                  id="url"
                  value={url}
                  onChange={(event) => setUrl(event.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs text-zinc-400" htmlFor="project-name">
                  New project name (optional)
                </label>
                <input
                  id="project-name"
                  value={projectName}
                  onChange={(event) => setProjectName(event.target.value)}
                  placeholder="Workflow Import"
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mt-3">
              <div className="mb-2 text-xs text-zinc-400">Outputs</div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {(["tweet", "linkedin", "blog"] as OutputKind[]).map((kind) => (
                  <label
                    key={kind}
                    className="flex items-center gap-2 rounded-lg border border-zinc-700 px-3 py-2 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={selectedOutputs[kind]}
                      onChange={() =>
                        setSelectedOutputs((prev) => ({ ...prev, [kind]: !prev[kind] }))
                      }
                    />
                    <span className="capitalize">{kind}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-zinc-400" htmlFor="template-id">
                  Template (single-output only)
                </label>
                <select
                  id="template-id"
                  value={selectedTemplateId}
                  onChange={(event) => setSelectedTemplateId(event.target.value)}
                  disabled={selectedOutputKinds.length !== 1}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm disabled:opacity-60"
                >
                  <option value="">Built-in template</option>
                  {selectableTemplates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name} ({template.kind} v{template.version})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-zinc-400" htmlFor="brand-voice">
                  Brand voice (optional)
                </label>
                <input
                  id="brand-voice"
                  value={brandVoice}
                  onChange={(event) => setBrandVoice(event.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={runWorkflow}
                disabled={!selectedWorkflow || isRunning}
                className="rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950 disabled:opacity-60"
              >
                {isRunning ? "Starting..." : "Run Workflow"}
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-950/30 p-4">
            <h2 className="text-sm font-semibold">Latest workflow run</h2>
            {!runJob ? (
              <div className="mt-3 text-sm text-zinc-400">No workflow run yet.</div>
            ) : (
              <div className="mt-3 space-y-2 text-sm">
                <div>
                  Job <span className="font-medium">#{runJob.id}</span> • status <span className="font-medium">{runJob.status}</span>
                </div>
                {runJob.error ? (
                  <div className="rounded-lg border border-red-800 bg-red-950/30 px-3 py-2 text-xs text-red-300">
                    {runJob.error}
                  </div>
                ) : null}
                {Array.isArray(runJob.output?.node_statuses) ? (
                  <div className="space-y-2">
                    {(runJob.output?.node_statuses as Array<Record<string, any>>).map((node) => (
                      <div key={String(node.node_id)} className="rounded-lg border border-zinc-800 px-3 py-2 text-xs">
                        <div className="font-medium">
                          {String(node.node_id)} • {String(node.task)}
                        </div>
                        <div className="text-zinc-400">status: {String(node.status)}</div>
                        {node.error ? <div className="text-red-300">{String(node.error)}</div> : null}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedWorkflow ? (
        <div className="rounded-2xl border border-zinc-800 p-4">
          <h2 className="text-sm font-semibold">Selected definition</h2>
          <pre className="mt-3 overflow-auto rounded-lg border border-zinc-800 bg-zinc-950/40 p-3 text-xs text-zinc-200">
            {JSON.stringify(selectedWorkflow.definition_json, null, 2)}
          </pre>
        </div>
      ) : null}

      {error ? (
        <div className="rounded-xl border border-red-800 bg-red-950/30 p-3 text-sm text-red-200">{error}</div>
      ) : null}
    </div>
  );
}
