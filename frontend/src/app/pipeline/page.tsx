"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { PipelineRun } from "@/lib/types";

export default function PipelinePage() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadHistory = useCallback(() => {
    api.getPipelineHistory().then(setRuns).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const res = await api.refreshPipeline();
      if (res.status === "already_running") {
        setRefreshMsg("Pipeline is already running");
        setRefreshing(false);
        return;
      }
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.pipelineStatus();
          if (!status.running) {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            setRefreshing(false);
            if (status.last_error) {
              setRefreshMsg(`Error: ${status.last_error}`);
            } else {
              setRefreshMsg("Pipeline completed successfully");
              loadHistory();
            }
          }
        } catch {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setRefreshing(false);
          setRefreshMsg("Failed to check pipeline status");
        }
      }, 3000);
    } catch {
      setRefreshing(false);
      setRefreshMsg("Failed to start pipeline");
    }
  };

  const lastRun = runs[0] ?? null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Pipeline</h1>
          <p className="text-sm text-slate-500 mt-1">
            Data pipeline monitoring and run history
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          {refreshing && (
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          {refreshing ? "Running..." : "Refresh Data"}
        </button>
      </div>

      {/* Refresh status */}
      {refreshMsg && (
        <div className={`px-4 py-2.5 rounded-lg text-sm ${
          refreshMsg.startsWith("Error") || refreshMsg.startsWith("Failed")
            ? "bg-red-500/10 text-red-400 border border-red-500/20"
            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
        }`}>
          {refreshMsg}
        </div>
      )}

      {/* Current Status Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          label="Last Run"
          value={lastRun ? formatDate(lastRun.started_at) : "—"}
          loading={loading}
        />
        <StatusCard
          label="Status"
          value={lastRun?.status ?? "—"}
          loading={loading}
          badge={lastRun?.status}
        />
        <StatusCard
          label="Duration"
          value={lastRun ? formatDuration(lastRun.duration_seconds) : "—"}
          loading={loading}
        />
        <StatusCard
          label="Schedule"
          value="Daily 06:00 UTC"
          loading={false}
          muted
        />
      </div>

      {/* Run History Table */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800">
          <h2 className="text-sm font-medium text-slate-300">Run History</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left">
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Date</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Duration</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Assets</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Holdings</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Sectors</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">ESG</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Val. Date</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <tr key={i} className="border-b border-slate-800/50">
                  {Array.from({ length: 8 }).map((_, j) => (
                    <td key={j} className="px-5 py-4">
                      <div className="h-4 rounded bg-slate-800 animate-pulse" style={{ width: `${50 + j * 5}%` }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : runs.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-5 py-12 text-center text-slate-600">
                  No pipeline runs yet — click &quot;Refresh Data&quot; to run the pipeline
                </td>
              </tr>
            ) : (
              runs.map((run) => (
                <RunRow
                  key={run.run_id}
                  run={run}
                  expanded={expandedRunId === run.run_id}
                  onToggle={() => setExpandedRunId(expandedRunId === run.run_id ? null : run.run_id)}
                />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Metrics Over Time */}
      {runs.length > 1 && (
        <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
          <h2 className="text-sm font-medium text-slate-300 mb-4">Entity Counts Over Time</h2>
          <div className="space-y-4">
            <MetricBars label="Assets" runs={runs} accessor={(r) => r.load_assets} color="sky" />
            <MetricBars label="Holdings" runs={runs} accessor={(r) => r.load_holds} color="violet" />
            <MetricBars label="ESG Ratings" runs={runs} accessor={(r) => r.load_esg_ratings} color="emerald" />
            <MetricBars label="Portfolios" runs={runs} accessor={(r) => r.load_portfolios} color="amber" />
          </div>
        </div>
      )}
    </div>
  );
}

function StatusCard({ label, value, loading, badge, muted }: {
  label: string;
  value: string;
  loading: boolean;
  badge?: string;
  muted?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-5">
      <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
      {loading ? (
        <div className="h-7 w-20 mt-2 rounded bg-slate-800 animate-pulse" />
      ) : badge ? (
        <span className={`inline-block mt-2 px-2.5 py-1 rounded text-sm font-medium ${
          badge === "success"
            ? "bg-emerald-500/10 text-emerald-400"
            : "bg-red-500/10 text-red-400"
        }`}>
          {badge}
        </span>
      ) : (
        <p className={`text-lg font-semibold mt-1 ${muted ? "text-slate-500 text-sm" : "text-slate-100"}`}>
          {value}
        </p>
      )}
    </div>
  );
}

function RunRow({ run, expanded, onToggle }: {
  run: PipelineRun;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr
        onClick={onToggle}
        className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors cursor-pointer"
      >
        <td className="px-5 py-3.5 text-slate-300 text-xs font-mono">
          {formatDate(run.started_at)}
        </td>
        <td className="px-5 py-3.5">
          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
            run.status === "success"
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-red-500/10 text-red-400"
          }`}>
            {run.status}
          </span>
        </td>
        <td className="px-5 py-3.5 text-slate-400 text-xs">
          {formatDuration(run.duration_seconds)}
        </td>
        <td className="px-5 py-3.5 text-right text-slate-300 font-mono text-xs">
          {run.load_assets.toLocaleString()}
        </td>
        <td className="px-5 py-3.5 text-right text-slate-300 font-mono text-xs">
          {run.load_holds.toLocaleString()}
        </td>
        <td className="px-5 py-3.5 text-right text-slate-300 font-mono text-xs">
          {run.load_sectors.toLocaleString()}
        </td>
        <td className="px-5 py-3.5 text-right text-slate-300 font-mono text-xs">
          {run.load_esg_ratings.toLocaleString()}
        </td>
        <td className="px-5 py-3.5 text-slate-400 text-xs">
          {run.valuation_date ?? "—"}
        </td>
      </tr>
      {expanded && (
        <tr className="border-b border-slate-800/50">
          <td colSpan={8} className="px-5 py-4 bg-slate-900/30">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
              <DetailGroup title="Fetch" items={[
                ["Files", run.fetch_files],
                ["Records", run.fetch_records],
              ]} />
              <DetailGroup title="Transform" items={[
                ["ETFs", run.transform_etfs],
                ["Assets", run.transform_assets],
                ["Holdings", run.transform_holdings],
              ]} />
              <DetailGroup title="Validate" items={[
                ["Pass Rate", run.validate_pass_rate],
                ["Warnings", run.validate_warnings],
                ["Errors", run.validate_errors],
              ]} />
              <DetailGroup title="Load" items={[
                ["Portfolios", run.load_portfolios],
                ["Assets", run.load_assets],
                ["Sectors", run.load_sectors],
                ["Holds", run.load_holds],
                ["ESG Ratings", run.load_esg_ratings],
              ]} />
            </div>
            {run.error_message && (
              <div className="mt-3 px-3 py-2 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
                {run.error_message}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

function DetailGroup({ title, items }: { title: string; items: [string, string | number][] }) {
  return (
    <div>
      <p className="text-slate-500 font-medium mb-1.5">{title}</p>
      <div className="space-y-1">
        {items.map(([label, value]) => (
          <div key={label} className="flex justify-between">
            <span className="text-slate-500">{label}</span>
            <span className="text-slate-300 font-mono">{typeof value === "number" ? value.toLocaleString() : value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MetricBars({ label, runs, accessor, color }: {
  label: string;
  runs: PipelineRun[];
  accessor: (r: PipelineRun) => number;
  color: string;
}) {
  const recent = [...runs].reverse().slice(-10);
  const max = Math.max(...recent.map(accessor), 1);
  const colorMap: Record<string, { bg: string; fill: string }> = {
    sky: { bg: "bg-sky-500/10", fill: "bg-sky-500" },
    violet: { bg: "bg-violet-500/10", fill: "bg-violet-500" },
    emerald: { bg: "bg-emerald-500/10", fill: "bg-emerald-500" },
    amber: { bg: "bg-amber-500/10", fill: "bg-amber-500" },
  };
  const c = colorMap[color] ?? colorMap.sky;

  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-500 font-mono">{accessor(runs[0]).toLocaleString()} latest</span>
      </div>
      <div className="flex items-end gap-1 h-8">
        {recent.map((run) => {
          const val = accessor(run);
          const pct = Math.max((val / max) * 100, 4);
          return (
            <div
              key={run.run_id}
              className={`flex-1 rounded-sm ${c.fill} opacity-80 hover:opacity-100 transition-opacity`}
              style={{ height: `${pct}%` }}
              title={`${formatDate(run.started_at)}: ${val.toLocaleString()}`}
            />
          );
        })}
      </div>
      <div className={`h-0.5 rounded-full ${c.bg} mt-1`} />
    </div>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}
