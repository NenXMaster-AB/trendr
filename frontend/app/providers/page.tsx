"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type ProviderSetting = {
  provider: string;
  has_api_key: boolean;
  key_hint?: string | null;
  configured_via?: "workspace" | "environment" | null;
  updated_at?: string | null;
};

export default function ProvidersPage() {
  const [rows, setRows] = useState<ProviderSetting[]>([]);
  const [draftKeys, setDraftKeys] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [savingProvider, setSavingProvider] = useState<string | null>(null);

  async function refresh() {
    const data = await api.get<ProviderSetting[]>("/v1/provider-settings/text");
    setRows(data);
  }

  useEffect(() => {
    refresh().catch((e) => setError(e instanceof Error ? e.message : "Failed to load provider settings."));
  }, []);

  const sortedRows = useMemo(
    () => [...rows].sort((a, b) => a.provider.localeCompare(b.provider)),
    [rows],
  );

  async function saveKey(provider: string) {
    const value = (draftKeys[provider] ?? "").trim();
    if (!value) {
      setError("API key cannot be empty.");
      return;
    }
    setError(null);
    setSavingProvider(provider);
    try {
      await api.put(`/v1/provider-settings/text/${provider}`, { api_key: value });
      setDraftKeys((prev) => ({ ...prev, [provider]: "" }));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save API key.");
    } finally {
      setSavingProvider(null);
    }
  }

  async function removeKey(provider: string) {
    setError(null);
    setSavingProvider(provider);
    try {
      await api.delete(`/v1/provider-settings/text/${provider}`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete API key.");
    } finally {
      setSavingProvider(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h1 className="text-2xl font-semibold">Provider Settings</h1>
        <p className="mt-2 text-sm text-zinc-300">
          Configure workspace-scoped API keys. Secrets are encrypted at rest and only owners/admins can update them.
        </p>
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-800 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <div className="space-y-3">
        {sortedRows.map((row) => {
          const isSaving = savingProvider === row.provider;
          return (
            <div key={row.provider} className="rounded-2xl border border-zinc-800 bg-zinc-900/20 p-5">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="text-base font-semibold capitalize">{row.provider}</div>
                  <div className="text-xs text-zinc-400">
                    Status: {row.has_api_key ? "Configured" : "Not configured"}
                    {row.configured_via ? ` (${row.configured_via})` : ""}
                    {row.key_hint ? ` • ${row.key_hint}` : ""}
                  </div>
                </div>
                {row.updated_at ? (
                  <div className="text-xs text-zinc-500">
                    Updated {new Date(row.updated_at).toLocaleString()}
                  </div>
                ) : null}
              </div>

              <div className="mt-4 flex flex-col gap-2 md:flex-row">
                <input
                  type="password"
                  value={draftKeys[row.provider] ?? ""}
                  onChange={(e) =>
                    setDraftKeys((prev) => ({
                      ...prev,
                      [row.provider]: e.target.value,
                    }))
                  }
                  placeholder={`Enter ${row.provider} API key`}
                  className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => saveKey(row.provider)}
                    disabled={isSaving}
                    className="rounded-xl bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 disabled:opacity-60"
                  >
                    {isSaving ? "Saving..." : "Save"}
                  </button>
                  <button
                    onClick={() => removeKey(row.provider)}
                    disabled={isSaving}
                    className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-200 disabled:opacity-60"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {sortedRows.length === 0 ? (
          <div className="rounded-xl border border-zinc-800 p-4 text-sm text-zinc-400">
            No providers available.
          </div>
        ) : null}
      </div>
    </div>
  );
}
