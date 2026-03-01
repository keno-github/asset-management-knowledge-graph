import Link from "next/link";

const NODE_COLORS: Record<string, string> = {
  Portfolio: "#0ea5e9",
  Asset: "#22c55e",
  Benchmark: "#a855f7",
  Sector: "#f59e0b",
  ESGRating: "#ef4444",
};

function NodePill({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap"
      style={{ backgroundColor: color + "20", color, border: `1px solid ${color}40` }}
    >
      {label}
    </span>
  );
}

function RelArrow({ label }: { label: string }) {
  return (
    <span className="flex items-center gap-1 text-[10px] text-slate-500 font-mono whitespace-nowrap">
      <span className="w-6 h-px bg-slate-700" />
      {label}
      <span className="w-4 h-px bg-slate-700" />
      <span className="text-slate-600">&#9656;</span>
    </span>
  );
}

function PipelineStep({
  step,
  title,
  desc,
}: {
  step: number;
  title: string;
  desc: string;
}) {
  return (
    <div className="flex-1 min-w-[200px]">
      <div className="flex items-center gap-3 mb-2">
        <span className="w-7 h-7 rounded-full bg-sky-500/15 border border-sky-500/30 text-sky-400 text-xs font-semibold flex items-center justify-center shrink-0">
          {step}
        </span>
        <h3 className="text-sm font-medium text-slate-200">{title}</h3>
      </div>
      <p className="text-xs text-slate-500 leading-relaxed pl-10">{desc}</p>
    </div>
  );
}

function FeatureCard({
  href,
  title,
  desc,
}: {
  href: string;
  title: string;
  desc: string;
}) {
  return (
    <Link
      href={href}
      className="block rounded-xl border border-slate-800 bg-[#0d1321] p-5 hover:border-sky-800 hover:bg-sky-950/10 transition-colors"
    >
      <h3 className="text-sm font-medium text-slate-200">{title}</h3>
      <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{desc}</p>
    </Link>
  );
}

export default function AboutPage() {
  return (
    <div className="space-y-10">
      {/* Section 1: Hero */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Asset Management Knowledge Graph
        </h1>
        <p className="text-sm text-slate-400 mt-2 max-w-3xl leading-relaxed">
          A full-stack knowledge graph application that models the relationships
          between investment portfolios, their holdings, benchmarks, sectors, and
          ESG ratings — then lets you explore them visually and query them in
          natural language.
        </p>
        <p className="text-xs text-slate-500 mt-4 max-w-3xl leading-relaxed">
          Traditional portfolio analytics lives in spreadsheets and relational
          databases where answering &ldquo;which portfolios share high-risk ESG
          assets?&rdquo; requires complex multi-table joins across 5+ tables. A
          knowledge graph makes these relationship questions natural — you just
          follow the edges. This project builds that graph from real ETF data and
          wraps it in an interactive frontend.
        </p>
      </div>

      {/* Section 2: Graph Schema */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
        <h2 className="text-sm font-medium text-slate-200 mb-5">
          Graph Schema
        </h2>
        <div className="space-y-4 overflow-x-auto">
          {/* Row 1: Portfolio -> Asset -> Sector */}
          <div className="flex items-center gap-2 flex-wrap">
            <NodePill label="Portfolio" color={NODE_COLORS.Portfolio} />
            <RelArrow label="HOLDS" />
            <NodePill label="Asset" color={NODE_COLORS.Asset} />
            <RelArrow label="BELONGS_TO" />
            <NodePill label="Sector" color={NODE_COLORS.Sector} />
          </div>

          {/* Row 2: Portfolio -> Benchmark -> Asset */}
          <div className="flex items-center gap-2 flex-wrap pl-8">
            <span className="text-slate-700 text-xs mr-1">├</span>
            <NodePill label="Portfolio" color={NODE_COLORS.Portfolio} />
            <RelArrow label="TRACKS" />
            <NodePill label="Benchmark" color={NODE_COLORS.Benchmark} />
            <RelArrow label="COMPOSED_OF" />
            <NodePill label="Asset" color={NODE_COLORS.Asset} />
          </div>

          {/* Row 3: Asset -> ESGRating */}
          <div className="flex items-center gap-2 flex-wrap pl-8">
            <span className="text-slate-700 text-xs mr-1">└</span>
            <NodePill label="Asset" color={NODE_COLORS.Asset} />
            <RelArrow label="HAS_ESG_SCORE" />
            <NodePill label="ESGRating" color={NODE_COLORS.ESGRating} />
          </div>
        </div>
      </div>

      {/* Section 3: Pipeline */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
        <h2 className="text-sm font-medium text-slate-200 mb-5">
          How It Works
        </h2>
        <div className="flex flex-col md:flex-row gap-6">
          <PipelineStep
            step={1}
            title="Fetch"
            desc="Downloads holdings CSVs from 8 iShares UCITS ETFs, loads Kaggle ESG ratings, enriches with Yahoo Finance market data."
          />
          <PipelineStep
            step={2}
            title="Transform"
            desc="Parses iShares CSV format, normalizes ESG scores to 0-10 scale, maps countries to ISO codes, generates sector-based ESG for coverage gaps."
          />
          <PipelineStep
            step={3}
            title="Validate"
            desc="Quality checks on weight sums, ISIN formats, duplicates. Pipeline halts if checks fail."
          />
          <PipelineStep
            step={4}
            title="Load"
            desc="Batched idempotent MERGE into Neo4j with uniqueness constraints and indexes."
          />
        </div>
      </div>

      {/* Section 4: Features */}
      <div>
        <h2 className="text-sm font-medium text-slate-200 mb-4">
          What You Can Do
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FeatureCard
            href="/portfolios"
            title="Browse Portfolios"
            desc="Holdings, sector allocation, AUM, and peer overlap."
          />
          <FeatureCard
            href="/esg"
            title="ESG Risk Analysis"
            desc="Cross-portfolio ESG concentration, controversy exposure, EU taxonomy alignment."
          />
          <FeatureCard
            href="/graph"
            title="Graph Explorer"
            desc="Interactive force-directed visualization. Start from portfolios, click to expand relationships, search any entity."
          />
          <FeatureCard
            href="/chat"
            title="AI Chat"
            desc="Ask questions in English, get Cypher-generated answers from Claude."
          />
        </div>
      </div>

      {/* Section 5: Tech Stack */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
        <h2 className="text-sm font-medium text-slate-200 mb-4">Tech Stack</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Backend
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Python 3.10+, FastAPI, Neo4j 5, Pydantic v2, Pandas, Anthropic
              Claude API, yfinance
            </p>
          </div>
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Frontend
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4,
              react-force-graph-2d
            </p>
          </div>
          <div className="md:col-span-2">
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Infrastructure
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Docker Compose (Neo4j), pip-installable package via hatchling
            </p>
          </div>
        </div>
      </div>

      {/* Section 6: Semantic Standards */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1321] p-6">
        <h2 className="text-sm font-medium text-slate-200 mb-4">
          Semantic Standards
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              OWL Ontology
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              The graph schema is formally defined as an OWL/RDF ontology in
              Turtle format. Each node type is declared as an{" "}
              <code className="text-sky-400">owl:Class</code>, relationships as{" "}
              <code className="text-sky-400">owl:ObjectProperty</code> with
              typed domains and ranges, and attributes as{" "}
              <code className="text-sky-400">owl:DatatypeProperty</code> with
              XSD types. Available at{" "}
              <Link
                href="/ontology"
                className="text-sky-400 hover:text-sky-300 underline"
              >
                /ontology
              </Link>
              .
            </p>
          </div>
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              SKOS Vocabularies
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Sector and asset class taxonomies follow SKOS (Simple Knowledge
              Organization System). The GICS sector hierarchy is modelled as a{" "}
              <code className="text-sky-400">skos:ConceptScheme</code> with
              preferred and alternative labels, supporting harmonization of
              variant names across data sources. Available at{" "}
              <Link
                href="/ontology"
                className="text-sky-400 hover:text-sky-300 underline"
              >
                /ontology
              </Link>
              .
            </p>
          </div>
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Data Lineage
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Every node and relationship carries provenance metadata: data
              source tag, ingestion timestamp, and pipeline run ID. This enables
              traceability from any graph entity back to its origin — whether
              iShares CSV, Kaggle ESG data, or yfinance enrichment. Query via{" "}
              <Link
                href="/ontology"
                className="text-sky-400 hover:text-sky-300 underline"
              >
                /ontology
              </Link>
              .
            </p>
          </div>
        </div>
      </div>

      {/* Section 7: The Data */}
      <div>
        <h2 className="text-sm font-medium text-slate-200 mb-3">The Data</h2>
        <p className="text-xs text-slate-500 leading-relaxed max-w-3xl">
          8 real iShares UCITS ETFs covering European, global, ESG-screened, and
          fixed income strategies. ~2,000 unique assets, 11 sectors, ESG ratings
          from Kaggle + sector-based generation. All relationship properties
          carry weights, dates, and scores — not just binary connections.
        </p>
      </div>
    </div>
  );
}
