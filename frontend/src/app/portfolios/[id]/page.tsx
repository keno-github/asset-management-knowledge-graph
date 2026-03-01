"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { PortfolioDetail, Holding, PeerOverlap } from "@/lib/types";

export default function PortfolioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [peers, setPeers] = useState<PeerOverlap[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<"weight_pct" | "asset_name">("weight_pct");
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    if (!id) return;
    Promise.allSettled([
      api.getPortfolio(id),
      api.getHoldings(id),
      api.getPeerOverlap(id),
    ]).then(([p, h, pr]) => {
      if (p.status === "fulfilled") setPortfolio(p.value);
      if (h.status === "fulfilled") setHoldings(h.value);
      if (pr.status === "fulfilled") setPeers(pr.value);
      setLoading(false);
    });
  }, [id]);

  const sorted = [...holdings].sort((a, b) => {
    const mul = sortAsc ? 1 : -1;
    if (sortKey === "weight_pct") return mul * (a.weight_pct - b.weight_pct);
    return mul * a.asset_name.localeCompare(b.asset_name);
  });

  const handleSort = (key: "weight_pct" | "asset_name") => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-48 rounded bg-slate-800 animate-pulse" />
        <div className="h-40 rounded-xl bg-slate-800/50 animate-pulse" />
        <div className="h-64 rounded-xl bg-slate-800/50 animate-pulse" />
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="py-20 text-center">
        <p className="text-slate-500">Portfolio not found</p>
        <Link href="/portfolios" className="text-sky-400 text-sm mt-2 inline-block hover:underline">
          Back to portfolios
        </Link>
      </div>
    );
  }

  const sectorCounts: Record<string, number> = {};
  holdings.forEach((h) => {
    const sec = h.sector ?? "Unknown";
    sectorCounts[sec] = (sectorCounts[sec] ?? 0) + h.weight_pct;
  });
  const topSectors = Object.entries(sectorCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Link href="/portfolios" className="hover:text-slate-300">Portfolios</Link>
        <span>/</span>
        <span className="text-slate-300">{portfolio.name}</span>
      </div>

      {/* Explainer */}
      <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
        This view traverses the graph outward from this portfolio — its holdings via HOLDS relationships, sector allocation via BELONGS_TO, benchmark via TRACKS, and peer portfolios that share common assets.
      </p>

      {/* Portfolio Header */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold">{portfolio.name}</h1>
            <p className="text-sm text-slate-500 mt-1">{portfolio.portfolio_id}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 mt-6">
          <InfoItem label="Asset Class" value={portfolio.asset_class} />
          <InfoItem label="AUM" value={portfolio.aum != null ? `$${(portfolio.aum / 1e9).toFixed(2)}B` : null} />
          <InfoItem label="Valuation Date" value={portfolio.as_of_date} />
          <InfoItem label="Benchmark" value={portfolio.benchmark} />
        </div>

        {/* ESG Section */}
        {(portfolio.esg_score != null || portfolio.esg_risk != null) && (
          <div className="mt-6 pt-6 border-t border-slate-800">
            <h2 className="text-xs text-slate-500 uppercase tracking-wider mb-3">ESG Profile</h2>
            <div className="flex gap-8">
              {portfolio.esg_score != null && (
                <div className="flex items-center gap-3">
                  <ESGGauge score={portfolio.esg_score} />
                  <div>
                    <p className="text-lg font-semibold">{portfolio.esg_score.toFixed(1)}</p>
                    <p className="text-xs text-slate-500">ESG Score</p>
                  </div>
                </div>
              )}
              {portfolio.esg_risk != null && (
                <div>
                  <span className={`inline-block px-2.5 py-1 rounded text-xs font-medium ${
                    portfolio.esg_risk === "Low" ? "bg-emerald-500/10 text-emerald-400" :
                    portfolio.esg_risk === "Medium" ? "bg-amber-500/10 text-amber-400" :
                    "bg-red-500/10 text-red-400"
                  }`}>
                    {portfolio.esg_risk} Risk
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Holdings Table */}
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-[#0d1321] overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800 flex justify-between items-center">
            <h2 className="text-sm font-medium text-slate-300">
              Holdings <span className="text-slate-600">({holdings.length})</span>
            </h2>
          </div>
          <div className="max-h-[500px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-[#0d1321]">
                <tr className="border-b border-slate-800">
                  <th
                    className="px-5 py-2.5 text-left text-xs font-medium text-slate-500 uppercase cursor-pointer hover:text-slate-300"
                    onClick={() => handleSort("asset_name")}
                  >
                    Asset {sortKey === "asset_name" ? (sortAsc ? "↑" : "↓") : ""}
                  </th>
                  <th className="px-5 py-2.5 text-left text-xs font-medium text-slate-500 uppercase">Sector</th>
                  <th
                    className="px-5 py-2.5 text-right text-xs font-medium text-slate-500 uppercase cursor-pointer hover:text-slate-300"
                    onClick={() => handleSort("weight_pct")}
                  >
                    Weight {sortKey === "weight_pct" ? (sortAsc ? "↑" : "↓") : ""}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((h, i) => (
                  <tr key={`${h.isin}-${i}`} className="border-b border-slate-800/30 hover:bg-slate-800/20">
                    <td className="px-5 py-2.5">
                      <div className="text-slate-200">{h.asset_name}</div>
                      {h.isin && <div className="text-[10px] text-slate-600 font-mono">{h.isin}</div>}
                    </td>
                    <td className="px-5 py-2.5">
                      {h.sector && (
                        <span className="text-xs text-slate-400">{h.sector}</span>
                      )}
                    </td>
                    <td className="px-5 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1 rounded-full bg-slate-800">
                          <div className="h-full rounded-full bg-sky-500" style={{ width: `${Math.min(h.weight_pct * 10, 100)}%` }} />
                        </div>
                        <span className="text-xs font-mono text-slate-300 w-12 text-right">
                          {h.weight_pct.toFixed(2)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sidebar: Sectors + Peers */}
        <div className="space-y-6">
          {/* Sector Breakdown */}
          <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-5">
            <h2 className="text-sm font-medium text-slate-300 mb-4">Sector Allocation</h2>
            <div className="space-y-3">
              {topSectors.map(([sector, weight]) => (
                <div key={sector}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400 truncate pr-2">{sector}</span>
                    <span className="text-slate-500 font-mono">{weight.toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-800">
                    <div className="h-full rounded-full bg-sky-600" style={{ width: `${Math.min(weight, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Peer Overlap */}
          <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-5">
            <h2 className="text-sm font-medium text-slate-300 mb-4">Peer Overlap</h2>
            {peers.length === 0 ? (
              <p className="text-xs text-slate-600">No peer overlaps found</p>
            ) : (
              <div className="space-y-3">
                {peers.map((peer) => (
                  <Link
                    key={peer.peer_id}
                    href={`/portfolios/${peer.peer_id}`}
                    className="block p-3 rounded-lg border border-slate-800/50 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-sky-400 hover:text-sky-300">{peer.peer}</span>
                      <span className="text-xs text-slate-500">{peer.overlap_count} shared</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {peer.shared_holdings.slice(0, 3).map((h) => (
                        <span key={h} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">{h}</span>
                      ))}
                      {peer.shared_holdings.length > 3 && (
                        <span className="text-[10px] text-slate-600">+{peer.shared_holdings.length - 3}</span>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
      <p className="text-sm text-slate-200 mt-0.5">{value ?? "—"}</p>
    </div>
  );
}

function ESGGauge({ score }: { score: number }) {
  const pct = (score / 10) * 100;
  const color = score >= 7 ? "#22c55e" : score >= 4 ? "#f59e0b" : "#ef4444";
  const circumference = 2 * Math.PI * 18;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <svg width="48" height="48" className="-rotate-90">
      <circle cx="24" cy="24" r="18" fill="none" stroke="#1e293b" strokeWidth="4" />
      <circle
        cx="24" cy="24" r="18" fill="none"
        stroke={color} strokeWidth="4"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
      />
    </svg>
  );
}
