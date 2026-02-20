"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";

type TemplateKind = "tweet" | "linkedin" | "blog";
type KindFilter = "all" | TemplateKind;

type Template = {
  id: number;
  workspace_id: number;
  name: string;
  kind: TemplateKind;
  version: number;
  content: string;
  meta: Record<string, any>;
  created_at: string;
};

const VARIABLE_GUIDE: Array<{ token: string; description: string }> = [
  { token: "{tone}", description: "Writing style target for the output." },
  { token: "{brand_voice}", description: "Brand voice or stylistic constraints." },
  { token: "{audience}", description: "Intended audience from generation options." },
  { token: "{transcript}", description: "Full source transcript text." },
  { token: "{segments}", description: "Timestamped transcript segments." },
];

const STARTER_BY_KIND: Record<TemplateKind, string> = {
  tweet: `Write a tweet draft from this source.

Tone: {tone}
Brand voice: {brand_voice}
Audience: {audience}

Use these source facts and avoid generic claims:
{segments}

Full transcript (for context):
{transcript}`,
  linkedin: `Write a LinkedIn post draft from this source.

Tone: {tone}
Brand voice: {brand_voice}
Audience: {audience}

Prioritize specific details and concrete insights.

Source segments:
{segments}

Transcript:
{transcript}`,
  blog: `Write a blog draft from this source.

Tone: {tone}
Brand voice: {brand_voice}
Audience: {audience}

Use a clear structure and reference concrete points from the source.

Source segments:
{segments}

Transcript:
{transcript}`,
};

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [kindFilter, setKindFilter] = useState<KindFilter>("all");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newName, setNewName] = useState("");
  const [newKind, setNewKind] = useState<TemplateKind>("tweet");
  const [newContent, setNewContent] = useState(STARTER_BY_KIND.tweet);
  const [isCreating, setIsCreating] = useState(false);

  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const selectedTemplate = useMemo(
    () => templates.find((item) => item.id === selectedTemplateId) ?? null,
    [templates, selectedTemplateId],
  );

  const [editName, setEditName] = useState("");
  const [editKind, setEditKind] = useState<TemplateKind>("tweet");
  const [editContent, setEditContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const query = kindFilter === "all" ? "" : `?kind=${kindFilter}`;
      const data = await api.get<Template[]>(`/v1/templates${query}`);
      setTemplates(data);
      if (data.length === 0) {
        setSelectedTemplateId(null);
        return;
      }
      if (!selectedTemplateId || !data.some((item) => item.id === selectedTemplateId)) {
        setSelectedTemplateId(data[0].id);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load templates";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [kindFilter]);

  useEffect(() => {
    if (!selectedTemplate) {
      setEditName("");
      setEditKind("tweet");
      setEditContent("");
      return;
    }
    setEditName(selectedTemplate.name);
    setEditKind(selectedTemplate.kind);
    setEditContent(selectedTemplate.content);
  }, [selectedTemplate]);

  async function copyVariable(token: string) {
    try {
      await navigator.clipboard.writeText(token);
      setCopiedToken(token);
      setTimeout(() => setCopiedToken((prev) => (prev === token ? null : prev)), 1200);
    } catch {
      setError("Could not copy variable to clipboard.");
    }
  }

  function appendToken(target: "create" | "edit", token: string) {
    if (target === "create") {
      setNewContent((prev) => (prev.trimEnd() ? `${prev.trimEnd()}\n${token}` : token));
      return;
    }
    setEditContent((prev) => (prev.trimEnd() ? `${prev.trimEnd()}\n${token}` : token));
  }

  async function createTemplate() {
    const trimmedName = newName.trim();
    const trimmedContent = newContent.trim();

    if (!trimmedName) {
      setError("Template name is required.");
      return;
    }
    if (!trimmedContent) {
      setError("Template content is required.");
      return;
    }

    setIsCreating(true);
    setError(null);
    try {
      await api.post("/v1/templates", {
        name: trimmedName,
        kind: newKind,
        content: trimmedContent,
        meta: {},
      });
      setNewName("");
      setNewContent(STARTER_BY_KIND[newKind]);
      await refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to create template";
      setError(message);
    } finally {
      setIsCreating(false);
    }
  }

  async function saveTemplate() {
    if (!selectedTemplate) return;

    const trimmedName = editName.trim();
    const trimmedContent = editContent.trim();
    if (!trimmedName || !trimmedContent) {
      setError("Name and content are required.");
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await api.patch(`/v1/templates/${selectedTemplate.id}`, {
        name: trimmedName,
        kind: editKind,
        content: trimmedContent,
      });
      await refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to update template";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  }

  async function removeTemplate() {
    if (!selectedTemplate) return;
    if (!confirm("Delete this template?")) return;

    setIsDeleting(true);
    setError(null);
    try {
      await api.delete(`/v1/templates/${selectedTemplate.id}`);
      await refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete template";
      setError(message);
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h1 className="text-2xl font-semibold">Template Library</h1>
        <p className="mt-2 text-sm text-zinc-300">
          Create reusable prompt templates by output type. When a generation runs, variable tokens below are replaced with real run values.
        </p>

        <div className="mt-4 grid gap-2 md:grid-cols-2 lg:grid-cols-3">
          {VARIABLE_GUIDE.map((item) => (
            <button
              key={item.token}
              onClick={() => copyVariable(item.token)}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-left hover:bg-zinc-800/60"
              title="Click to copy"
            >
              <div className="font-mono text-xs text-zinc-100">{item.token}</div>
              <div className="mt-1 text-xs text-zinc-400">{item.description}</div>
            </button>
          ))}
        </div>

        <div className="mt-2 text-xs text-zinc-400">
          {copiedToken ? `Copied ${copiedToken}` : "Tip: click a token to copy it."}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="space-y-4 rounded-2xl border border-zinc-800 p-4">
          <div>
            <label className="mb-1 block text-xs text-zinc-400" htmlFor="kind-filter">
              Filter
            </label>
            <select
              id="kind-filter"
              value={kindFilter}
              onChange={(event) => setKindFilter(event.target.value as KindFilter)}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
            >
              <option value="all">All</option>
              <option value="tweet">Tweet</option>
              <option value="linkedin">LinkedIn</option>
              <option value="blog">Blog</option>
            </select>
          </div>

          <div className="space-y-2">
            {templates.map((item) => (
              <button
                key={item.id}
                onClick={() => setSelectedTemplateId(item.id)}
                className={`w-full rounded-xl border px-3 py-2 text-left ${
                  item.id === selectedTemplateId
                    ? "border-zinc-300 bg-zinc-100 text-zinc-950"
                    : "border-zinc-800 bg-zinc-950/40 text-zinc-100 hover:bg-zinc-950"
                }`}
              >
                <div className="text-sm font-medium">{item.name}</div>
                <div className="text-xs opacity-80">
                  {item.kind} v{item.version}
                </div>
              </button>
            ))}
            {!isLoading && templates.length === 0 ? (
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2 text-sm text-zinc-400">No templates yet.</div>
            ) : null}
          </div>
        </div>

        <div className="space-y-4 rounded-2xl border border-zinc-800 p-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/30 p-4">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold">Create template</h2>
              <button
                onClick={() => setNewContent(STARTER_BY_KIND[newKind])}
                className="rounded-lg border border-zinc-700 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-900"
              >
                Use starter
              </button>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <input
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder="Name"
                className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              />
              <select
                value={newKind}
                onChange={(event) => setNewKind(event.target.value as TemplateKind)}
                className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              >
                <option value="tweet">Tweet</option>
                <option value="linkedin">LinkedIn</option>
                <option value="blog">Blog</option>
              </select>
            </div>

            <textarea
              value={newContent}
              onChange={(event) => setNewContent(event.target.value)}
              rows={10}
              className="mt-3 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-xs"
            />

            <div className="mt-2 flex flex-wrap gap-2">
              {VARIABLE_GUIDE.map((item) => (
                <button
                  key={`create-${item.token}`}
                  onClick={() => appendToken("create", item.token)}
                  className="rounded-md border border-zinc-700 px-2 py-1 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                >
                  + {item.token}
                </button>
              ))}
            </div>

            <div className="mt-3 flex justify-end">
              <button
                onClick={createTemplate}
                disabled={isCreating}
                className="rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950 disabled:opacity-60"
              >
                {isCreating ? "Creating..." : "Create"}
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-950/30 p-4">
            <h2 className="text-sm font-semibold">Editor</h2>
            {!selectedTemplate ? (
              <div className="mt-3 text-sm text-zinc-400">Select a template to edit.</div>
            ) : (
              <>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <input
                    value={editName}
                    onChange={(event) => setEditName(event.target.value)}
                    className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                  />
                  <select
                    value={editKind}
                    onChange={(event) => setEditKind(event.target.value as TemplateKind)}
                    className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                  >
                    <option value="tweet">Tweet</option>
                    <option value="linkedin">LinkedIn</option>
                    <option value="blog">Blog</option>
                  </select>
                </div>

                <textarea
                  value={editContent}
                  onChange={(event) => setEditContent(event.target.value)}
                  rows={12}
                  className="mt-3 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-xs"
                />

                <div className="mt-2 flex flex-wrap gap-2">
                  {VARIABLE_GUIDE.map((item) => (
                    <button
                      key={`edit-${item.token}`}
                      onClick={() => appendToken("edit", item.token)}
                      className="rounded-md border border-zinc-700 px-2 py-1 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                    >
                      + {item.token}
                    </button>
                  ))}
                </div>

                <div className="mt-2 text-xs text-zinc-400">
                  version {selectedTemplate.version} • id {selectedTemplate.id}
                </div>

                <div className="mt-3 flex justify-end gap-2">
                  <button
                    onClick={removeTemplate}
                    disabled={isDeleting}
                    className="rounded-lg border border-red-700 px-3 py-2 text-sm text-red-300 disabled:opacity-60"
                  >
                    {isDeleting ? "Deleting..." : "Delete"}
                  </button>
                  <button
                    onClick={saveTemplate}
                    disabled={isSaving}
                    className="rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950 disabled:opacity-60"
                  >
                    {isSaving ? "Saving..." : "Save"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-800 bg-red-950/30 p-3 text-sm text-red-200">{error}</div>
      ) : null}
    </div>
  );
}
