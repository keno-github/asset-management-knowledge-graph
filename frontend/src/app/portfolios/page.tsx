"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { PortfolioSummary } from "@/lib/types";

export default function PortfoliosPage() {
  const [portfolios, setPortfolios] = useState<PortfolioSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [valuationDates, setValuationDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("all");

  useEffect(() => {
    Promise.allSettled([
      api.listPortfolios(),
      api.getValuationDates(),
    ]).then(([pRes, dRes]) => {
      if (pRes.status === "fulfilled") setPortfolios(pRes.value);
      if (dRes.status === "fulfilled") {
        const dates = dRes.value.map((d) => d.valuation_date).filter(Boolean);
        setValuationDates(dates);
      }
      setLoading(false);
    });
  }, []);

  const filtered = portfolios.filter((p) => {
    const matchesText =
      p.name.toLowerCase().includes(filter.toLowerCase()) ||
      (p.asset_class ?? "").toLowerCase().includes(filter.toLowerCase());
    const matchesDate =
      selectedDate === "all" || p.as_of_date === selectedDate;
    return matchesText && matchesDate;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Portfolios</h1>
        <p className="text-sm text-slate-500 mt-1">Browse ETF portfolios and their holdings</p>
      </div>

      {/* Explainer */}
      <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
        Each row is an ETF portfolio ingested from the data pipeline. Click a portfolio name to see its full holdings, sector allocation, and peer overlap — all derived from graph relationships in Neo4j.
      </p>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Text search */}
        <div className="relative max-w-sm flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Filter by name or asset class..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-slate-800 bg-[#0d1321] text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-sky-700 transition-colors"
          />
        </div>

        {/* Valuation date selector */}
        {valuationDates.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Valuation Date:</span>
            <div className="flex gap-1.5 flex-wrap">
              <button
                onClick={() => setSelectedDate("all")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  selectedDate === "all"
                    ? "bg-sky-600 text-white"
                    : "bg-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                All Dates
              </button>
              {valuationDates.map((date) => (
                <button
                  key={date}
                  onClick={() => setSelectedDate(date)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    selectedDate === date
                      ? "bg-sky-600 text-white"
                      : "bg-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {date}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left">
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Asset Class</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">AUM</th>
              <th className="px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Valuation Date</th>
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
                  <td className="px-5 py-4 text-slate-400 text-xs">
                    <span className={selectedDate !== "all" && p.as_of_date === selectedDate ? "text-sky-400 font-medium" : ""}>
                      {p.as_of_date ?? "—"}
                    </span>
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
