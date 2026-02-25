"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type ScheduledPost = {
  id: number;
  workspace_id: number;
  project_id?: number | null;
  artifact_id?: number | null;
  platform: string;
  title: string;
  content: string;
  scheduled_at: string;
  status: string;
  meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type StatusFilter = "all" | "draft" | "scheduled" | "ready" | "sent" | "failed" | "cancelled";
type PlatformFilter = "all" | "twitter" | "linkedin" | "blog";

export default function SchedulePage() {
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [platformFilter, setPlatformFilter] = useState<PlatformFilter>("all");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editScheduledAt, setEditScheduledAt] = useState("");

  async function refresh() {
    const data = await api.get<ScheduledPost[]>("/v1/schedule?limit=100");
    setPosts(data);
  }

  useEffect(() => {
    refresh();
  }, []);

  const filteredPosts = useMemo(() => {
    return posts.filter((p) => {
      if (statusFilter !== "all" && p.status !== statusFilter) return false;
      if (platformFilter !== "all" && p.platform !== platformFilter) return false;
      return true;
    });
  }, [posts, statusFilter, platformFilter]);

  const grouped = useMemo(() => {
    const map = new Map<string, ScheduledPost[]>();
    for (const post of filteredPosts) {
      const dateKey = post.scheduled_at.slice(0, 10);
      if (!map.has(dateKey)) map.set(dateKey, []);
      map.get(dateKey)!.push(post);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [filteredPosts]);

  async function cancelPost(id: number) {
    await api.delete(`/v1/schedule/${id}`);
    await refresh();
  }

  async function updateSchedule(id: number) {
    if (!editScheduledAt) return;
    await api.patch(`/v1/schedule/${id}`, {
      scheduled_at: new Date(editScheduledAt).toISOString(),
    });
    setEditingId(null);
    setEditScheduledAt("");
    await refresh();
  }

  const statusColors: Record<string, string> = {
    draft: "text-zinc-400",
    scheduled: "text-blue-400",
    ready: "text-green-400",
    sent: "text-emerald-400",
    failed: "text-red-400",
    cancelled: "text-zinc-500",
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Schedule</h1>
            <p className="mt-1 text-xs text-zinc-400">
              Queue and manage scheduled posts. {filteredPosts.length} post{filteredPosts.length !== 1 ? "s" : ""}.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            >
              <option value="all">All statuses</option>
              <option value="draft">Draft</option>
              <option value="scheduled">Scheduled</option>
              <option value="ready">Ready</option>
              <option value="sent">Sent</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value as PlatformFilter)}
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            >
              <option value="all">All platforms</option>
              <option value="twitter">Twitter</option>
              <option value="linkedin">LinkedIn</option>
              <option value="blog">Blog</option>
            </select>
          </div>
        </div>
      </div>

      {grouped.length === 0 ? (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 text-sm text-zinc-400">
          No scheduled posts yet. Schedule posts from a project&apos;s artifact cards.
        </div>
      ) : null}

      {grouped.map(([date, datePosts]) => (
        <div key={date} className="space-y-2">
          <h2 className="text-sm font-medium text-zinc-300">{date}</h2>
          {datePosts.map((post) => (
            <div
              key={post.id}
              className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">{post.title || `Post #${post.id}`}</span>
                    <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs">{post.platform}</span>
                    <span className={`text-xs ${statusColors[post.status] ?? "text-zinc-400"}`}>
                      {post.status}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-zinc-400">
                    {new Date(post.scheduled_at).toLocaleString()}
                    {post.project_id ? ` · Project #${post.project_id}` : ""}
                  </div>
                  {post.content ? (
                    <pre className="mt-2 max-h-24 overflow-hidden whitespace-pre-wrap text-xs text-zinc-300">
                      {post.content.slice(0, 300)}
                      {post.content.length > 300 ? "..." : ""}
                    </pre>
                  ) : null}
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  {post.status === "scheduled" || post.status === "draft" ? (
                    <>
                      <button
                        onClick={() => {
                          setEditingId(post.id);
                          setEditScheduledAt(post.scheduled_at.slice(0, 16));
                        }}
                        className="rounded-lg border border-zinc-700 px-2 py-1 text-xs text-zinc-200 hover:bg-zinc-900"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => cancelPost(post.id)}
                        className="rounded-lg border border-red-800 px-2 py-1 text-xs text-red-300 hover:bg-red-950/30"
                      >
                        Cancel
                      </button>
                    </>
                  ) : null}
                </div>
              </div>
              {editingId === post.id ? (
                <div className="mt-3 flex items-center gap-2">
                  <input
                    type="datetime-local"
                    value={editScheduledAt}
                    onChange={(e) => setEditScheduledAt(e.target.value)}
                    className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-1 text-sm text-zinc-100"
                  />
                  <button
                    onClick={() => updateSchedule(post.id)}
                    className="rounded-lg bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-950"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditingId(null)}
                    className="rounded-lg border border-zinc-700 px-3 py-1 text-xs text-zinc-200"
                  >
                    Cancel
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
