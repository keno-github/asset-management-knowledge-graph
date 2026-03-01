"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ESGControversy, ESGCrossRisk, TaxonomyAlignment } from "@/lib/types";

export default function ESGPage() {
  const [controversies, setControversies] = useState<ESGControversy[]>([]);
  const [crossRisk, setCrossRisk] = useState<ESGCrossRisk[]>([]);
  const [taxonomy, setTaxonomy] = useState<TaxonomyAlignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"risk" | "controversy" | "taxonomy">("risk");

  useEffect(() => {
    Promise.allSettled([
      api.esgCrossRisk(),
      api.esgControversy(3),
      api.taxonomyAlignment(),
    ]).then(([cr, co, ta]) => {
      if (cr.status === "fulfilled") setCrossRisk(cr.value);
      if (co.status === "fulfilled") setControversies(co.value);
      if (ta.status === "fulfilled") setTaxonomy(ta.value);
      setLoading(false);
    });
  }, []);

  const tabs = [
    { key: "risk" as const, label: "Cross-Portfolio Risk" },
    { key: "controversy" as const, label: "Controversy Exposure" },
    { key: "taxonomy" as const, label: "Taxonomy Alignment" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">ESG Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          Environmental, Social & Governance risk analytics across portfolios
        </p>
      </div>

      {/* Explainer */}
      <p className="text-xs text-slate-500 leading-relaxed max-w-2xl">
        These analytics traverse Portfolio → Asset → ESGRating relationships in the graph to surface sustainability risks that span multiple funds — the kind of multi-hop analysis that&apos;s natural in a knowledge graph but hard in SQL.
      </p>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-lg bg-[#0d1321] border border-slate-800 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${
              activeTab === tab.key
                ? "bg-sky-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 rounded-xl bg-slate-800/50 animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          {activeTab === "risk" && <CrossRiskView data={crossRisk} />}
          {activeTab === "controversy" && <ControversyView data={controversies} />}
          {activeTab === "taxonomy" && <TaxonomyView data={taxonomy} />}
        </>
      )}
    </div>
  );
}

function CrossRiskView({ data }: { data: ESGCrossRisk[] }) {
  if (data.length === 0) {
    return <EmptyState message="No cross-portfolio risk data available" />;
  }

  const riskColors: Record<string, string> = {
    Severe: "bg-red-500/10 text-red-400 border-red-500/20",
    High: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    Medium: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    Low: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    Negligible: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  };

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500 leading-relaxed">
        Assets with High or Severe ESG risk that appear in more than one portfolio — highlighting systemic concentration risk. If one ESG scandal hits, these are the assets that would affect multiple funds simultaneously.
      </p>
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase">Asset</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase">ISIN</th>
            <th className="px-5 py-3 text-center text-xs font-medium text-slate-500 uppercase">Risk Level</th>
            <th className="px-5 py-3 text-center text-xs font-medium text-slate-500 uppercase">Exposed</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase">Portfolios</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, i) => (
            <tr key={i} className="border-b border-slate-800/30 hover:bg-slate-800/20">
              <td className="px-5 py-3 text-slate-200 font-medium">{item.asset}</td>
              <td className="px-5 py-3 text-slate-500 font-mono text-xs">{item.isin ?? "—"}</td>
              <td className="px-5 py-3 text-center">
                <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs border ${riskColors[item.risk] ?? riskColors.Medium}`}>
                  {item.risk}
                </span>
              </td>
              <td className="px-5 py-3 text-center text-slate-300 font-mono">{item.exposure_count}</td>
              <td className="px-5 py-3">
                <div className="flex flex-wrap gap-1">
                  {item.exposed_portfolios.slice(0, 3).map((p) => (
                    <span key={p} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{p}</span>
                  ))}
                  {item.exposed_portfolios.length > 3 && (
                    <span className="text-[10px] text-slate-600">+{item.exposed_portfolios.length - 3}</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    </div>
  );
}

function ControversyView({ data }: { data: ESGControversy[] }) {
  if (data.length === 0) {
    return <EmptyState message="No controversy data available" />;
  }

  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500 leading-relaxed">
        Portfolios ranked by how many controversial assets they hold (controversy score &le; 3 on a 0-5 scale, where 0 is severe). The bar shows relative exposure and the chips list the specific controversial holdings.
      </p>
      <div className="grid gap-4">
      {data.map((item) => (
        <div key={item.portfolio_id} className="rounded-xl border border-slate-800 bg-[#0d1321] p-5">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-sm font-medium text-slate-200">{item.portfolio}</h3>
              <p className="text-xs text-slate-500 font-mono mt-0.5">{item.portfolio_id}</p>
            </div>
            <span className={`text-lg font-semibold ${
              item.count >= 3 ? "text-red-400" : item.count >= 2 ? "text-amber-400" : "text-emerald-400"
            }`}>
              {item.count}
            </span>
          </div>

          <div className="mt-3">
            <div className="h-2 rounded-full bg-slate-800">
              <div
                className={`h-full rounded-full ${
                  item.count >= 3 ? "bg-red-500" : item.count >= 2 ? "bg-amber-500" : "bg-emerald-500"
                }`}
                style={{ width: `${(item.count / maxCount) * 100}%` }}
              />
            </div>
          </div>

          {item.controversial_assets.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {item.controversial_assets.map((asset) => (
                <span key={asset} className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                  {asset}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
    </div>
  );
}

function TaxonomyView({ data }: { data: TaxonomyAlignment[] }) {
  if (data.length === 0) {
    return <EmptyState message="No taxonomy alignment data available" />;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500 leading-relaxed">
        EU Taxonomy alignment measures what percentage of a portfolio&apos;s holdings qualify as environmentally sustainable under the EU taxonomy framework. Higher is better — averaged across each portfolio&apos;s assets.
      </p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {data.map((item) => (
        <div key={item.portfolio_id} className="rounded-xl border border-slate-800 bg-[#0d1321] p-5">
          <h3 className="text-sm font-medium text-slate-200 truncate">{item.portfolio}</h3>
          <p className="text-xs text-slate-600 font-mono">{item.portfolio_id}</p>

          <div className="mt-4 flex items-end justify-between">
            {/* Taxonomy % */}
            <div>
              <p className="text-3xl font-semibold text-sky-400">{item.taxonomy_pct.toFixed(0)}%</p>
              <p className="text-xs text-slate-500 mt-0.5">Taxonomy Aligned</p>
            </div>

            {/* ESG Score */}
            <div className="text-right">
              <p className={`text-lg font-semibold ${
                item.esg_score >= 7 ? "text-emerald-400" : item.esg_score >= 4 ? "text-amber-400" : "text-red-400"
              }`}>
                {item.esg_score.toFixed(1)}
              </p>
              <p className="text-xs text-slate-500">ESG Score</p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-3 h-2 rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-sky-500"
              style={{ width: `${Math.min(item.taxonomy_pct, 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-12 text-center">
      <p className="text-slate-500">{message}</p>
      <p className="text-xs text-slate-600 mt-1">Run the pipeline to populate ESG data</p>
    </div>
  );
}
