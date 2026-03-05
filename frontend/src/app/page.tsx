"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { GraphStats } from "@/lib/types";

interface HealthData {
  status: string;
  neo4j_connected: boolean;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = useCallback(() => {
    Promise.allSettled([api.health(), api.stats()]).then(([h, s]) => {
      if (h.status === "fulfilled") setHealth(h.value);
      if (s.status === "fulfilled") setStats(s.value);
      setLoading(false);
    });
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Clean up polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
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
      // Poll for completion
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
              setRefreshMsg("Data refreshed successfully");
              loadData();
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

  const nodeEntries = stats ? Object.entries(stats.nodes) : [];
  const relEntries = stats ? Object.entries(stats.relationships) : [];
  const totalNodes = nodeEntries.reduce((sum, [, c]) => sum + c, 0);
  const totalRels = relEntries.reduce((sum, [, c]) => sum + c, 0);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Knowledge graph overview and system status
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
          {refreshing ? "Refreshing..." : "Refresh Data"}
        </button>
      </div>

      {/* Refresh status message */}
      {refreshMsg && (
        <div className={`px-4 py-2.5 rounded-lg text-sm ${
          refreshMsg.startsWith("Error") || refreshMsg.startsWith("Failed")
            ? "bg-red-500/10 text-red-400 border border-red-500/20"
            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
        }`}>
          {refreshMsg}
        </div>
      )}

      {/* Explainer */}
      <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
        This dashboard shows the shape of the knowledge graph stored in Neo4j — how many entities (nodes) and connections (relationships) exist, broken down by type. Use the quick links below to explore portfolios, visualize the graph, or ask questions in natural language.
      </p>

      {/* Status Banner */}
      <div className="flex items-center gap-3 px-4 py-3 rounded-lg border border-slate-800 bg-[#0d1321]">
        <div
          className={`w-2 h-2 rounded-full ${
            health?.neo4j_connected ? "bg-emerald-400" : loading ? "bg-amber-400 animate-pulse" : "bg-red-400"
          }`}
        />
        <span className="text-sm text-slate-400">
          {loading
            ? "Connecting to Neo4j..."
            : health?.neo4j_connected
              ? "Neo4j connected"
              : "Neo4j disconnected — start with docker compose up -d"}
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Nodes" value={totalNodes} loading={loading} />
        <KPICard label="Relationships" value={totalRels} loading={loading} />
        <KPICard label="Node Types" value={nodeEntries.length} loading={loading} />
        <KPICard label="Rel Types" value={relEntries.length} loading={loading} />
      </div>

      {/* Node & Relationship Breakdown */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
          <h2 className="text-sm font-medium text-slate-400 mb-4">Node Labels</h2>
          {loading ? (
            <SkeletonRows count={5} />
          ) : nodeEntries.length === 0 ? (
            <p className="text-sm text-slate-600">No data — run the pipeline first</p>
          ) : (
            <div className="space-y-3">
              {nodeEntries
                .sort((a, b) => b[1] - a[1])
                .map(([label, count]) => (
                  <BarRow key={label} label={label} count={count} max={nodeEntries[0]?.[1] ?? 1} color="sky" />
                ))}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
          <h2 className="text-sm font-medium text-slate-400 mb-4">Relationship Types</h2>
          {loading ? (
            <SkeletonRows count={5} />
          ) : relEntries.length === 0 ? (
            <p className="text-sm text-slate-600">No data — run the pipeline first</p>
          ) : (
            <div className="space-y-3">
              {relEntries
                .sort((a, b) => b[1] - a[1])
                .map(([label, count]) => (
                  <BarRow key={label} label={label} count={count} max={relEntries[0]?.[1] ?? 1} color="violet" />
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid sm:grid-cols-3 gap-4">
        <QuickLink href="/portfolios" title="Portfolios" desc="Browse ETF holdings and peer overlap" />
        <QuickLink href="/graph" title="Graph Explorer" desc="Interactive force-directed visualization" />
        <QuickLink href="/chat" title="AI Chat" desc="Ask questions in natural language" />
      </div>
    </div>
  );
}

function KPICard({ label, value, loading }: { label: string; value: number; loading: boolean }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-5">
      <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
      {loading ? (
        <div className="h-8 w-20 mt-2 rounded bg-slate-800 animate-pulse" />
      ) : (
        <p className="text-2xl font-semibold mt-1 text-slate-100">{value.toLocaleString()}</p>
      )}
    </div>
  );
}

function BarRow({ label, count, max, color }: { label: string; count: number; max: number; color: string }) {
  const pct = Math.max((count / max) * 100, 2);
  const bg = color === "sky" ? "bg-sky-500/20" : "bg-violet-500/20";
  const fill = color === "sky" ? "bg-sky-500" : "bg-violet-500";
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-300 font-mono">{label}</span>
        <span className="text-slate-500">{count.toLocaleString()}</span>
      </div>
      <div className={`h-1.5 rounded-full ${bg}`}>
        <div className={`h-full rounded-full ${fill}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function SkeletonRows({ count }: { count: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="space-y-1.5">
          <div className="flex justify-between">
            <div className="h-3 w-24 rounded bg-slate-800 animate-pulse" />
            <div className="h-3 w-10 rounded bg-slate-800 animate-pulse" />
          </div>
          <div className="h-1.5 rounded-full bg-slate-800 animate-pulse" />
        </div>
      ))}
    </div>
  );
}

function QuickLink({ href, title, desc }: { href: string; title: string; desc: string }) {
  return (
    <Link
      href={href}
      className="block rounded-xl border border-slate-800 bg-[#0d1321] p-5 hover:border-sky-800 hover:bg-sky-950/10 transition-colors"
    >
      <h3 className="text-sm font-medium text-slate-200">{title}</h3>
      <p className="text-xs text-slate-500 mt-1">{desc}</p>
    </Link>
  );
}
