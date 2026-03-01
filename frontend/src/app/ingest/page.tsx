"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { api } from "@/lib/api";
import type { IngestResponse } from "@/lib/types";

type Phase = "idle" | "uploading" | "extracting" | "writing" | "done" | "error";

const STEPS = ["Upload", "Extract", "Write", "Done"] as const;

function StepIndicator({ phase }: { phase: Phase }) {
  const phaseToStep: Record<Phase, number> = {
    idle: -1,
    uploading: 0,
    extracting: 1,
    writing: 2,
    done: 3,
    error: -1,
  };
  const activeStep = phaseToStep[phase];

  return (
    <div className="flex items-center gap-2">
      {STEPS.map((label, i) => {
        const isDone = i < activeStep;
        const isActive = i === activeStep;
        return (
          <div key={label} className="flex items-center gap-2">
            <div
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                isDone
                  ? "bg-emerald-400"
                  : isActive
                    ? "bg-sky-400 animate-pulse"
                    : "bg-slate-700"
              }`}
            />
            <span
              className={`text-xs ${
                isDone
                  ? "text-emerald-400"
                  : isActive
                    ? "text-sky-400"
                    : "text-slate-600"
              }`}
            >
              {label}
            </span>
            {i < STEPS.length - 1 && (
              <div className={`w-8 h-px ${isDone ? "bg-emerald-400/40" : "bg-slate-800"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function LoadingDots({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 py-8 justify-center">
      <div className="flex gap-1">
        <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
      <span className="text-sm text-slate-400">{message}</span>
    </div>
  );
}

export default function IngestPage() {
  const [mode, setMode] = useState<"pdf" | "text">("pdf");
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string>("");
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [textInput, setTextInput] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const phaseMessages: Record<string, string> = {
    uploading: "Uploading document...",
    extracting: "Claude is analyzing the document and extracting entities...",
    writing: "Writing entities and relationships to Neo4j...",
  };

  const reset = () => {
    setPhase("idle");
    setError("");
    setResult(null);
    setSelectedFile(null);
    setTextInput("");
  };

  const handleSubmit = async () => {
    setError("");
    setPhase("uploading");

    const formData = new FormData();
    if (mode === "pdf" && selectedFile) {
      formData.append("file", selectedFile);
    } else if (mode === "text" && textInput.trim()) {
      formData.append("text", textInput.trim());
    } else {
      setError(mode === "pdf" ? "Please select a PDF file." : "Please enter some text.");
      setPhase("error");
      return;
    }

    setPhase("extracting");

    try {
      const res = await fetch(api.ingestApiUrl, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(body.detail || `API error ${res.status}`);
      }

      setPhase("writing");
      const data: IngestResponse = await res.json();
      setResult(data);
      setPhase("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setPhase("error");
    }
  };

  const canSubmit =
    phase === "idle" &&
    ((mode === "pdf" && selectedFile !== null) || (mode === "text" && textInput.trim().length >= 50));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Document Ingestion</h1>
        <p className="text-sm text-slate-400 mt-1">
          Upload a PDF factsheet or paste text to extract financial entities and ingest into the knowledge graph.
        </p>
      </div>

      {/* Step Indicator */}
      {phase !== "idle" && phase !== "error" && (
        <div className="bg-[#0f1729] border border-slate-800 rounded-xl p-4">
          <StepIndicator phase={phase} />
        </div>
      )}

      {/* Input Section */}
      {phase === "idle" && (
        <div className="bg-[#0f1729] border border-slate-800 rounded-xl p-6 space-y-5">
          {/* Mode Toggle */}
          <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1 w-fit">
            <button
              onClick={() => setMode("pdf")}
              className={`px-4 py-1.5 rounded-md text-sm transition-colors ${
                mode === "pdf"
                  ? "bg-sky-500/20 text-sky-400"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Upload PDF
            </button>
            <button
              onClick={() => setMode("text")}
              className={`px-4 py-1.5 rounded-md text-sm transition-colors ${
                mode === "text"
                  ? "bg-sky-500/20 text-sky-400"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Paste Text
            </button>
          </div>

          {/* PDF Upload */}
          {mode === "pdf" && (
            <div>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              <button
                onClick={() => fileRef.current?.click()}
                className="w-full border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-sky-500/50 transition-colors group"
              >
                <svg className="w-8 h-8 mx-auto text-slate-600 group-hover:text-sky-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-sm text-slate-400 mt-2">
                  {selectedFile
                    ? `${selectedFile.name} (${(selectedFile.size / 1024).toFixed(0)} KB)`
                    : "Click to select a PDF file"}
                </p>
              </button>
            </div>
          )}

          {/* Text Input */}
          {mode === "text" && (
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={10}
              placeholder="Paste the content of a financial factsheet, fund summary, or portfolio report here..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-4 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-sky-500/50 resize-none font-mono"
            />
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="px-6 py-2.5 bg-sky-500 text-white rounded-lg text-sm font-medium hover:bg-sky-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Extract & Ingest
          </button>
        </div>
      )}

      {/* Loading State */}
      {(phase === "extracting" || phase === "uploading" || phase === "writing") && (
        <div className="bg-[#0f1729] border border-slate-800 rounded-xl p-6">
          <LoadingDots message={phaseMessages[phase] || "Processing..."} />
        </div>
      )}

      {/* Error State */}
      {phase === "error" && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6 space-y-3">
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={reset}
            className="text-sm text-sky-400 hover:text-sky-300 transition-colors"
          >
            Try again
          </button>
        </div>
      )}

      {/* Results */}
      {phase === "done" && result && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="bg-[#0f1729] border border-slate-800 rounded-xl p-6">
            <h2 className="text-sm font-medium text-slate-200 mb-4">Extraction Summary</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-semibold text-sky-400">{result.entity_counts.portfolios}</p>
                <p className="text-xs text-slate-500 mt-1">Portfolios</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-semibold text-emerald-400">{result.entity_counts.holdings}</p>
                <p className="text-xs text-slate-500 mt-1">Holdings</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-semibold text-amber-400">{result.entity_counts.benchmarks}</p>
                <p className="text-xs text-slate-500 mt-1">Benchmarks</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800">
              <p className="text-xs text-slate-500">
                Source: {result.source_type.toUpperCase()} &middot; {result.text_length.toLocaleString()} chars &middot; Model: {result.extraction_model}
              </p>
            </div>
          </div>

          {/* Extracted Portfolios */}
          {result.entities.portfolios.length > 0 && (
            <div className="bg-[#0f1729] border border-slate-800 rounded-xl p-6">
              <h2 className="text-sm font-medium text-slate-200 mb-3">Portfolios</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-500 border-b border-slate-800">
                      <th className="text-left py-2 pr-4">Name</th>
                      <th className="text-left py-2 pr-4">Ticker</th>
                      <th className="text-left py-2 pr-4">ISIN</th>
                      <th className="text-left py-2 pr-4">Asset Class</th>
                      <th className="text-right py-2">AUM (M)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.entities.portfolios.map((p, i) => (
                      <tr key={i} className="border-b border-slate-800/50 text-slate-300">
                        <td className="py-2 pr-4 font-medium">{p.name}</td>
                        <td className="py-2 pr-4 font-mono text-slate-400">{p.ticker || "—"}</td>
                        <td className="py-2 pr-4 font-mono text-slate-400">{p.isin || "—"}</td>
                        <td className="py-2 pr-4">{p.asset_class || "—"}</td>
                        <td className="py-2 text-right font-mono">{p.aum?.toLocaleString() ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Extracted Holdings */}
          {result.entities.holdings.length > 0 && (
            <div className="bg-[#0f1729] border border-slate-800 rounded-xl p-6">
              <h2 className="text-sm font-medium text-slate-200 mb-3">
                Holdings ({result.entities.holdings.length})
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-500 border-b border-slate-800">
                      <th className="text-left py-2 pr-4">Asset</th>
                      <th className="text-left py-2 pr-4">Ticker</th>
                      <th className="text-left py-2 pr-4">ISIN</th>
                      <th className="text-left py-2 pr-4">Sector</th>
                      <th className="text-right py-2 pr-4">Weight %</th>
                      <th className="text-left py-2">Country</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.entities.holdings.map((h, i) => (
                      <tr key={i} className="border-b border-slate-800/50 text-slate-300">
                        <td className="py-2 pr-4 font-medium">{h.asset_name}</td>
                        <td className="py-2 pr-4 font-mono text-slate-400">{h.ticker || "—"}</td>
                        <td className="py-2 pr-4 font-mono text-slate-400">{h.isin || "—"}</td>
                        <td className="py-2 pr-4">
                          {h.sector ? (
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">{h.sector}</span>
                          ) : "—"}
                        </td>
                        <td className="py-2 pr-4 text-right font-mono">
                          {h.weight_pct !== null ? h.weight_pct.toFixed(2) : "—"}
                        </td>
                        <td className="py-2">{h.country || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Graph Writes */}
          <div className="bg-[#0f1729] border border-slate-800 rounded-xl p-6">
            <h2 className="text-sm font-medium text-slate-200 mb-3">Graph Writes</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Object.entries(result.graph_writes).map(([key, count]) => (
                <div key={key} className="bg-slate-900/50 rounded-lg p-3 text-center">
                  <p className="text-lg font-semibold text-slate-200">{count}</p>
                  <p className="text-[10px] text-slate-500 mt-1">
                    {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Link
              href="/graph"
              className="px-4 py-2 bg-sky-500/10 text-sky-400 rounded-lg text-sm hover:bg-sky-500/20 transition-colors"
            >
              View in Graph Explorer
            </Link>
            <button
              onClick={reset}
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm hover:bg-slate-700 transition-colors"
            >
              Ingest Another Document
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
