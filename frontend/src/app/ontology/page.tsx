"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type {
  LineageResponse,
  OntologySummary,
  OntologyVersionHistory,
  ReasoningResult,
  SKOSConceptScheme,
  SparqlResult,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const NODE_COLORS: Record<string, string> = {
  Portfolio: "#0ea5e9",
  Asset: "#22c55e",
  Benchmark: "#a855f7",
  Sector: "#f59e0b",
  ESGRating: "#ef4444",
};

function ClassPill({ name }: { name: string }) {
  const color = NODE_COLORS[name] || "#64748b";
  return (
    <span
      className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap"
      style={{
        backgroundColor: color + "20",
        color,
        border: `1px solid ${color}40`,
      }}
    >
      {name}
    </span>
  );
}

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-slate-800/60 ${className}`}
    />
  );
}

function DownloadButton({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={`${API_BASE}${href}`}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-400 hover:text-sky-400 hover:border-sky-800 transition-colors"
    >
      <svg
        className="w-3.5 h-3.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
        />
      </svg>
      {label}
    </a>
  );
}

// ── Section A: OWL Ontology ─────────────────────────────────────────────────

function OntologySection() {
  const [data, setData] = useState<OntologySummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getOntologySummary().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-6">
        <p className="text-xs text-red-400">Failed to load ontology: {error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6 space-y-4">
        <Skeleton className="h-5 w-48" />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-sm font-medium text-slate-200">OWL Ontology</h2>
          <p className="text-xs text-slate-500 mt-1">
            {data.format} &middot; v{data.version}
          </p>
          <p className="text-xs text-slate-600 mt-0.5 font-mono">
            {data.namespace}
          </p>
        </div>
        <DownloadButton href={data.download_url} label="Download .ttl" />
      </div>

      {/* Classes */}
      <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
        Classes
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        {data.classes.map((cls) => (
          <div
            key={cls.uri}
            className="rounded-lg border border-slate-800/60 bg-slate-900/30 p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <ClassPill name={cls.name} />
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              {cls.description}
            </p>
            <p className="text-[10px] text-slate-700 font-mono mt-1.5">
              {cls.uri}
            </p>
          </div>
        ))}
      </div>

      {/* Object Properties */}
      <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
        Object Properties
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-slate-500 border-b border-slate-800">
              <th className="text-left py-2 pr-4 font-medium">Property</th>
              <th className="text-left py-2 pr-4 font-medium">Domain</th>
              <th className="text-left py-2 pr-4 font-medium" />
              <th className="text-left py-2 font-medium">Range</th>
            </tr>
          </thead>
          <tbody>
            {data.object_properties.map((prop) => (
              <tr
                key={prop.name}
                className="border-b border-slate-800/50"
              >
                <td className="py-2.5 pr-4 font-mono text-sky-400">
                  {prop.name}
                </td>
                <td className="py-2.5 pr-4">
                  <ClassPill name={prop.domain} />
                </td>
                <td className="py-2.5 pr-4">
                  <span className="flex items-center gap-1 text-slate-600">
                    <span className="w-6 h-px bg-slate-700" />
                    <span>&#9656;</span>
                  </span>
                </td>
                <td className="py-2.5">
                  <ClassPill name={prop.range} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Section B/C: SKOS Vocabulary ────────────────────────────────────────────

function VocabularySection({
  name,
  title,
}: {
  name: string;
  title: string;
}) {
  const [data, setData] = useState<SKOSConceptScheme | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getVocabulary(name).then(setData).catch((e) => setError(e.message));
  }, [name]);

  if (error) {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-6">
        <p className="text-xs text-red-400">
          Failed to load vocabulary: {error}
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6 space-y-4">
        <Skeleton className="h-5 w-48" />
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-sm font-medium text-slate-200">{title}</h2>
          <p className="text-xs text-slate-500 mt-1">{data.description}</p>
          <p className="text-[10px] text-slate-700 font-mono mt-0.5">
            {data.uri}
          </p>
        </div>
        <DownloadButton
          href={data.turtle_download_url}
          label="Download .ttl"
        />
      </div>

      <div className="space-y-0 divide-y divide-slate-800/60">
        {data.concepts.map((concept) => (
          <div key={concept.uri} className="py-3 first:pt-0 last:pb-0">
            <div className="flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-slate-200">
                    {concept.pref_label}
                  </span>
                  {concept.notation && (
                    <span className="font-mono text-xs text-sky-400">
                      {concept.notation}
                    </span>
                  )}
                </div>
                {concept.definition && (
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    {concept.definition}
                  </p>
                )}
                {concept.alt_labels.length > 0 && (
                  <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                    <span className="text-[10px] text-slate-600 mr-0.5">
                      alt:
                    </span>
                    {concept.alt_labels.map((alt) => (
                      <span
                        key={alt}
                        className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400"
                      >
                        {alt}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <p className="text-[10px] text-slate-600 mt-4">
        {data.concepts.length} concepts
      </p>
    </div>
  );
}

// ── Section D: Data Lineage ─────────────────────────────────────────────────

function LineageSection() {
  const [data, setData] = useState<LineageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    api
      .getLineage("Portfolio", "SWDA")
      .then(setData)
      .catch((e) => {
        if (e.message.includes("404")) {
          setNotFound(true);
        } else {
          setError(e.message);
        }
      });
  }, []);

  const LINEAGE_PROPS = [
    {
      name: "_source",
      desc: "Identifies the data origin — e.g. ishares_api, kaggle_esg, yfinance.",
    },
    {
      name: "_ingested_at",
      desc: "ISO 8601 timestamp of when this entity was written to the graph.",
    },
    {
      name: "_pipeline_run_id",
      desc: "Unique identifier for the ETL pipeline execution that created or updated this node.",
    },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
      <h2 className="text-sm font-medium text-slate-200 mb-1">
        Data Lineage
      </h2>
      <p className="text-xs text-slate-500 mb-5">
        Every node carries provenance metadata for traceability back to the
        original data source.
      </p>

      {/* Property descriptions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {LINEAGE_PROPS.map((prop) => (
          <div key={prop.name} className="rounded-lg border border-slate-800/60 bg-slate-900/30 p-3">
            <p className="font-mono text-xs text-sky-400 mb-1">{prop.name}</p>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {prop.desc}
            </p>
          </div>
        ))}
      </div>

      {/* Example lineage */}
      <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
        Example: Portfolio SWDA
      </h3>

      {error && (
        <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
          <p className="text-xs text-red-400">Failed to load lineage: {error}</p>
        </div>
      )}

      {notFound && (
        <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-4">
          <p className="text-xs text-amber-400">
            No lineage data found. Run the ETL pipeline first to populate
            provenance metadata.
          </p>
        </div>
      )}

      {!data && !error && !notFound && (
        <Skeleton className="h-20 w-full" />
      )}

      {data && (
        <div className="rounded-lg border border-slate-800/60 bg-slate-900/30 p-4">
          <div className="flex items-center gap-2 mb-3">
            <ClassPill name={data.node_label} />
            <span className="font-mono text-xs text-slate-400">
              {data.node_id}
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <p className="text-slate-600 mb-0.5">_source</p>
              <p className="font-mono text-slate-300">
                {data.source || "—"}
              </p>
            </div>
            <div>
              <p className="text-slate-600 mb-0.5">_ingested_at</p>
              <p className="font-mono text-slate-300">
                {data.ingested_at || "—"}
              </p>
            </div>
            <div>
              <p className="text-slate-600 mb-0.5">_pipeline_run_id</p>
              <p className="font-mono text-slate-300">
                {data.pipeline_run_id || "—"}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Section E: RDF Export ────────────────────────────────────────────────────

const RDF_FORMATS = [
  { id: "turtle", label: "Turtle (.ttl)" },
  { id: "json-ld", label: "JSON-LD" },
  { id: "n-triples", label: "N-Triples (.nt)" },
  { id: "xml", label: "RDF/XML" },
];

const NODE_LABELS = ["All", "Portfolio", "Asset", "Benchmark", "Sector", "ESGRating"];

function RdfExportSection() {
  const [format, setFormat] = useState("turtle");
  const [label, setLabel] = useState("All");

  const downloadUrl = api.getRdfExportUrl(
    format,
    label === "All" ? undefined : label
  );

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
      <h2 className="text-sm font-medium text-slate-200 mb-1">RDF Export</h2>
      <p className="text-xs text-slate-500 mb-5">
        Export the Neo4j graph as RDF triples using the AMKG ontology namespace.
        Each node becomes a typed resource with datatype properties mapped to
        their OWL definitions.
      </p>

      <div className="flex flex-wrap items-end gap-4 mb-4">
        <div>
          <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">
            Format
          </label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-700"
          >
            {RDF_FORMATS.map((f) => (
              <option key={f.id} value={f.id}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">
            Filter by label
          </label>
          <select
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-700"
          >
            {NODE_LABELS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </div>
        <a
          href={downloadUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-sky-600/20 border border-sky-600/30 text-xs text-sky-400 hover:bg-sky-600/30 transition-colors"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
            />
          </svg>
          Download RDF
        </a>
      </div>

      <div className="rounded-lg border border-slate-800/60 bg-slate-900/30 p-3">
        <p className="text-[10px] text-slate-600 leading-relaxed">
          <span className="text-slate-500">URI pattern:</span>{" "}
          <code className="text-sky-400">
            amkg:&#123;Label&#125;_&#123;primary_key&#125;
          </code>{" "}
          &mdash; e.g.{" "}
          <code className="text-sky-400">amkg:Portfolio_SWDA</code>,{" "}
          <code className="text-sky-400">amkg:Asset_IE00B4L5Y983</code>
        </p>
      </div>
    </div>
  );
}

// ── Section F: SPARQL Query ─────────────────────────────────────────────────

const SPARQL_PREFIX = `PREFIX amkg: <https://w3id.org/amkg/ontology#>`;

const EXAMPLE_QUERIES = [
  {
    label: "List all portfolios",
    query: `${SPARQL_PREFIX}

SELECT ?portfolio ?name WHERE {
  ?portfolio a amkg:Portfolio ;
             amkg:name ?name .
}`,
  },
  {
    label: "Assets in Energy sector",
    query: `${SPARQL_PREFIX}

SELECT ?asset ?name WHERE {
  ?asset a amkg:Asset ;
         amkg:name ?name ;
         amkg:sector "Energy" .
}`,
  },
  {
    label: "Portfolio holdings count",
    query: `${SPARQL_PREFIX}

SELECT ?pname (COUNT(?asset) AS ?holdings) WHERE {
  ?p a amkg:Portfolio ;
     amkg:name ?pname ;
     amkg:holds ?asset .
} GROUP BY ?pname ORDER BY DESC(?holdings)`,
  },
  {
    label: "High ESG scores (>8)",
    query: `${SPARQL_PREFIX}

SELECT ?asset ?score WHERE {
  ?asset a amkg:Asset ;
         amkg:hasESGScore ?rating .
  ?rating amkg:overallScore ?score .
  FILTER(?score > 8)
}`,
  },
];

function SparqlSection() {
  const [query, setQuery] = useState(EXAMPLE_QUERIES[0].query);
  const [result, setResult] = useState<SparqlResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runQuery = () => {
    setLoading(true);
    setError(null);
    setResult(null);
    api
      .sparqlQuery(query)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
      <h2 className="text-sm font-medium text-slate-200 mb-1">
        SPARQL Query
      </h2>
      <p className="text-xs text-slate-500 mb-4">
        Query the knowledge graph using SPARQL. The graph is exported to RDF
        in-memory and queried with rdflib — no external triplestore required.
      </p>

      {/* Example buttons */}
      <div className="flex flex-wrap gap-2 mb-3">
        {EXAMPLE_QUERIES.map((ex) => (
          <button
            key={ex.label}
            onClick={() => setQuery(ex.query)}
            className="px-2.5 py-1 rounded text-[11px] border border-slate-700 text-slate-400 hover:text-sky-400 hover:border-sky-800 transition-colors"
          >
            {ex.label}
          </button>
        ))}
      </div>

      {/* Query editor */}
      <div className="relative mb-4">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={8}
          spellCheck={false}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 pb-10 text-xs font-mono text-slate-300 focus:outline-none focus:border-sky-700 resize-y"
          placeholder="Enter SPARQL query..."
        />
        <button
          onClick={runQuery}
          disabled={loading || !query.trim()}
          className="absolute bottom-3 right-3 px-3 py-1.5 rounded-lg bg-sky-600 text-xs text-white font-medium hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Running..." : "Run"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-3 mb-4">
          <p className="text-xs text-red-400 font-mono break-all">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && result.type === "select" && result.columns && result.rows && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800">
                {result.columns.map((col) => (
                  <th
                    key={col}
                    className="text-left py-2 pr-4 font-medium text-slate-400"
                  >
                    ?{col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.rows.map((row, i) => (
                <tr key={i} className="border-b border-slate-800/50">
                  {result.columns!.map((col) => (
                    <td
                      key={col}
                      className="py-2 pr-4 font-mono text-slate-300 max-w-xs truncate"
                    >
                      {row[col]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-[10px] text-slate-600 mt-2">
            {result.rows.length} result{result.rows.length !== 1 ? "s" : ""}
          </p>
        </div>
      )}

      {result && result.type === "ask" && (
        <div className="rounded-lg border border-slate-800/60 bg-slate-900/30 p-3">
          <p className="text-xs text-slate-300">
            Result:{" "}
            <span className={result.result ? "text-green-400" : "text-red-400"}>
              {result.result ? "true" : "false"}
            </span>
          </p>
        </div>
      )}

      {result && result.type === "construct" && result.turtle && (
        <div className="rounded-lg border border-slate-800/60 bg-slate-900/30 p-3">
          <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap overflow-x-auto max-h-60">
            {result.turtle}
          </pre>
        </div>
      )}
    </div>
  );
}

// ── Section G: Ontology Versions ────────────────────────────────────────────

function VersionsSection() {
  const [data, setData] = useState<OntologyVersionHistory | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getOntologyVersions().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-6">
        <p className="text-xs text-red-400">Failed to load versions: {error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6 space-y-3">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
      <div className="flex items-center gap-3 mb-5">
        <h2 className="text-sm font-medium text-slate-200">
          Ontology Versions
        </h2>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-sky-500/15 text-sky-400 border border-sky-500/30">
          v{data.current_version}
        </span>
      </div>

      <div className="space-y-0 divide-y divide-slate-800/60">
        {data.versions.map((v) => (
          <div key={v.version} className="py-4 first:pt-0 last:pb-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-mono text-xs text-slate-200">
                v{v.version}
              </span>
              <span className="text-[10px] text-slate-600">{v.date}</span>
            </div>
            <ul className="space-y-1 pl-4">
              {v.changes.map((change, i) => (
                <li
                  key={i}
                  className="text-xs text-slate-500 leading-relaxed list-disc"
                >
                  {change}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Section H: OWL Reasoning ───────────────────────────────────────────────

function ReasoningSection() {
  const [data, setData] = useState<ReasoningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api
      .runReasoning()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const toggleCategory = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  if (error) {
    const isEmpty = error.includes("500") || error.includes("Reasoning failed");
    if (isEmpty) {
      return (
        <div className="rounded-xl border border-amber-900/50 bg-amber-950/20 p-6">
          <h2 className="text-sm font-medium text-amber-400 mb-1">OWL-RL Reasoning</h2>
          <p className="text-xs text-amber-400/70">
            Run the data pipeline first to populate the graph, then reasoning can infer new triples.
          </p>
        </div>
      );
    }
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-6">
        <p className="text-xs text-red-400">Failed to run reasoning: {error}</p>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6 space-y-4">
        <Skeleton className="h-5 w-48" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  const categories = [
    { key: "type_inheritance", data: data.categories.type_inheritance, color: "sky" },
    { key: "domain_range_inference", data: data.categories.domain_range_inference, color: "emerald" },
    { key: "other", data: data.categories.other, color: "amber" },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
      <h2 className="text-sm font-medium text-slate-200 mb-1">OWL-RL Reasoning</h2>
      <p className="text-xs text-slate-500 mb-5">
        Deductive closure over the OWL ontology and live graph data — new triples
        inferred from class hierarchies, domain/range declarations, and property axioms.
      </p>

      {/* Triple counts */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="rounded-lg border border-slate-800/60 bg-slate-900/30 p-4 text-center">
          <p className="text-2xl font-semibold text-slate-200">{data.explicit_triples.toLocaleString()}</p>
          <p className="text-[10px] text-slate-500 mt-1">Explicit Triples</p>
        </div>
        <div className="rounded-lg border border-sky-800/40 bg-sky-900/10 p-4 text-center">
          <p className="text-2xl font-semibold text-sky-400">+{data.inferred_triples.toLocaleString()}</p>
          <p className="text-[10px] text-slate-500 mt-1">Inferred Triples</p>
        </div>
        <div className="rounded-lg border border-slate-800/60 bg-slate-900/30 p-4 text-center">
          <p className="text-2xl font-semibold text-slate-200">{data.total_triples.toLocaleString()}</p>
          <p className="text-[10px] text-slate-500 mt-1">Total After Reasoning</p>
        </div>
      </div>

      {/* Categories */}
      <div className="space-y-3">
        {categories.map(({ key, data: cat, color }) => (
          <div
            key={key}
            className="rounded-lg border border-slate-800/60 bg-slate-900/30"
          >
            <button
              onClick={() => toggleCategory(key)}
              className="w-full flex items-center justify-between p-4 text-left"
            >
              <div className="flex items-center gap-3">
                <span className={`text-sm font-medium text-${color}-400`}>
                  {cat.count}
                </span>
                <span className="text-xs text-slate-400">
                  {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              </div>
              <svg
                className={`w-4 h-4 text-slate-600 transition-transform ${expanded[key] ? "rotate-180" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {expanded[key] && (
              <div className="px-4 pb-4">
                <p className="text-xs text-slate-500 mb-3">{cat.description}</p>
                {cat.examples.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-slate-500 border-b border-slate-800">
                          <th className="text-left py-1.5 pr-4 font-medium">Subject</th>
                          <th className="text-left py-1.5 pr-4 font-medium">Predicate</th>
                          <th className="text-left py-1.5 font-medium">Object</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cat.examples.map((triple, i) => (
                          <tr key={i} className="border-b border-slate-800/30">
                            <td className="py-1.5 pr-4 font-mono text-slate-300">{triple.subject}</td>
                            <td className="py-1.5 pr-4 font-mono text-sky-400">{triple.predicate}</td>
                            <td className="py-1.5 font-mono text-slate-300">{triple.object}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-600 italic">No examples in this category</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function OntologyPage() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Ontology &amp; Vocabularies
        </h1>
        <p className="text-sm text-slate-400 mt-2 max-w-3xl leading-relaxed">
          The formal semantic layer that gives the knowledge graph its meaning —
          OWL classes and properties, SKOS controlled vocabularies with
          alternative labels for data harmonization, and provenance metadata for
          full data lineage.
        </p>
      </div>

      <OntologySection />
      <VocabularySection name="sectors" title="SKOS Sector Vocabulary" />
      <VocabularySection name="asset-classes" title="SKOS Asset Class Vocabulary" />
      <LineageSection />
      <RdfExportSection />
      <SparqlSection />
      <ReasoningSection />
      <VersionsSection />
    </div>
  );
}
