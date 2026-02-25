"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

type SummaryItem = {
  kind: string;
  count: number;
};

type TimelinePoint = {
  date: string;
  kind: string;
  count: number;
};

type PeriodOption = 7 | 14 | 30 | 90;

const KIND_COLORS: Record<string, string> = {
  job_completed: "#60a5fa",
  artifact_created: "#34d399",
  media_generated: "#c084fc",
};

const KIND_LABELS: Record<string, string> = {
  job_completed: "Jobs",
  artifact_created: "Artifacts",
  media_generated: "Media",
};

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<SummaryItem[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [period, setPeriod] = useState<PeriodOption>(30);

  useEffect(() => {
    (async () => {
      const [summaryData, timelineData] = await Promise.all([
        api.get<SummaryItem[]>(`/v1/analytics/summary?days=${period}`),
        api.get<TimelinePoint[]>(`/v1/analytics/timeline?days=${period}`),
      ]);
      setSummary(summaryData);
      setTimeline(timelineData);
    })();
  }, [period]);

  const totalEvents = useMemo(() => summary.reduce((acc, s) => acc + s.count, 0), [summary]);

  const chartData = useMemo(() => {
    const map = new Map<string, Record<string, number>>();
    for (const point of timeline) {
      if (!map.has(point.date)) {
        map.set(point.date, {});
      }
      map.get(point.date)![point.kind] = point.count;
    }
    return Array.from(map.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, kinds]) => ({ date, ...kinds }));
  }, [timeline]);

  const uniqueKinds = useMemo(() => {
    const kinds = new Set<string>();
    for (const point of timeline) kinds.add(point.kind);
    return Array.from(kinds).sort();
  }, [timeline]);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Analytics</h1>
            <p className="mt-1 text-xs text-zinc-400">
              Activity overview for the last {period} days.
            </p>
          </div>
          <div className="flex items-center gap-1">
            {([7, 14, 30, 90] as PeriodOption[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`rounded-lg border px-3 py-1 text-xs ${
                  period === p
                    ? "border-zinc-300 bg-zinc-100 text-zinc-950"
                    : "border-zinc-700 text-zinc-300 hover:bg-zinc-900"
                }`}
              >
                {p}d
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
          <div className="text-xs text-zinc-400">Total Events</div>
          <div className="mt-1 text-2xl font-semibold">{totalEvents}</div>
        </div>
        {summary.map((s) => (
          <div key={s.kind} className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
            <div className="text-xs text-zinc-400">{KIND_LABELS[s.kind] ?? s.kind}</div>
            <div className="mt-1 text-2xl font-semibold">{s.count}</div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h2 className="mb-4 text-lg font-semibold">Activity Over Time</h2>
        {chartData.length === 0 ? (
          <div className="text-sm text-zinc-400">No activity data for this period.</div>
        ) : (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis
                dataKey="date"
                tick={{ fill: "#a1a1aa", fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: "#3f3f46" }}
              />
              <YAxis
                tick={{ fill: "#a1a1aa", fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: "#3f3f46" }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181b",
                  border: "1px solid #3f3f46",
                  borderRadius: "0.75rem",
                  fontSize: "0.75rem",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
              {uniqueKinds.map((kind) => (
                <Bar
                  key={kind}
                  dataKey={kind}
                  name={KIND_LABELS[kind] ?? kind}
                  stackId="a"
                  fill={KIND_COLORS[kind] ?? "#71717a"}
                  radius={[2, 2, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
