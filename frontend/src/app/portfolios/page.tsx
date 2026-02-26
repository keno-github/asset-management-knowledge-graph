"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { PortfolioSummary } from "@/lib/types";

export default function PortfoliosPage() {
  const [portfolios, setPortfolios] = useState<PortfolioSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.listPortfolios().then((data) => {
      setPortfolios(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filtered = portfolios.filter(
    (p) =>
      p.name.toLowerCase().includes(filter.toLowerCase()) ||
      (p.asset_class ?? "").toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Portfolios</h1>
        <p className="text-sm text-slate-500 mt-1">Browse ETF portfolios and their holdings</p>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <input
          type="text"
          placeholder="Filter by name or asset class..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full px-4 py-2.5 rounded-lg border border-slate-800 bg-[#0d1321] text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-sky-700 transition-colors"
        />
      </div>

      {/* Table */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left">
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Asset Class</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">AUM</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider text-center">Rating</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Benchmark</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <tr key={i} className="border-b border-slate-800/50">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <td key={j} className="px-5 py-4">
                      <div className="h-4 rounded bg-slate-800 animate-pulse" style={{ width: `${60 + j * 10}%` }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-12 text-center text-slate-600">
                  {portfolios.length === 0 ? "No portfolios loaded — run the pipeline first" : "No matches"}
                </td>
              </tr>
            ) : (
              filtered.map((p) => (
                <tr key={p.portfolio_id} className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                  <td className="px-5 py-4">
                    <Link href={`/portfolios/${p.portfolio_id}`} className="text-sky-400 hover:text-sky-300 font-medium">
                      {p.name}
                    </Link>
                  </td>
                  <td className="px-5 py-4 text-slate-400">
                    {p.asset_class && (
                      <span className="inline-block px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300">
                        {p.asset_class}
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-right text-slate-300 font-mono text-xs">
                    {p.aum != null ? `$${(p.aum / 1e9).toFixed(1)}B` : "—"}
                  </td>
                  <td className="px-5 py-4 text-center">
                    {p.morningstar_rating != null ? (
                      <span className="text-amber-400 text-xs">{"★".repeat(p.morningstar_rating)}</span>
                    ) : (
                      <span className="text-slate-700">—</span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-slate-500 text-xs truncate max-w-[200px]">
                    {p.benchmark ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
