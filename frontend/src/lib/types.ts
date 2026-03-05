/** TypeScript interfaces matching the FastAPI response schemas. */

export interface PortfolioSummary {
  portfolio_id: string;
  name: string;
  asset_class: string | null;
  aum: number | null;
  morningstar_rating: number | null;
  as_of_date: string | null;
  benchmark: string | null;
}

export interface PortfolioDetail extends PortfolioSummary {
  benchmark_id: string | null;
  manager: string | null;
  entity: string | null;
  esg_score: number | null;
  esg_risk: string | null;
}

export interface Holding {
  asset_name: string;
  isin: string | null;
  weight_pct: number;
  as_of_date: string | null;
  sector: string | null;
  country: string | null;
  asset_type: string | null;
}

export interface PeerOverlap {
  peer: string;
  peer_id: string;
  overlap_count: number;
  shared_holdings: string[];
}

export interface ESGControversy {
  portfolio: string;
  portfolio_id: string;
  count: number;
  controversial_assets: string[];
}

export interface ESGCrossRisk {
  asset: string;
  isin: string | null;
  risk: string;
  exposed_portfolios: string[];
  exposure_count: number;
}

export interface TaxonomyAlignment {
  portfolio: string;
  portfolio_id: string;
  taxonomy_pct: number;
  esg_score: number;
}

export interface GraphStats {
  nodes: Record<string, number>;
  relationships: Record<string, number>;
}

export interface ChatResponse {
  question: string;
  cypher_query: string;
  raw_results: Record<string, unknown>[];
  answer: string;
  confidence: number;
}

export interface GraphNode {
  id: string;
  label: string;
  group: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

// Ontology & Vocabulary types

export interface OntologyClass {
  name: string;
  uri: string;
  description: string;
}

export interface OntologyProperty {
  name: string;
  domain: string;
  range: string;
}

export interface OntologySummary {
  namespace: string;
  version: string;
  format: string;
  classes: OntologyClass[];
  object_properties: OntologyProperty[];
  download_url: string;
}

export interface SKOSConcept {
  uri: string;
  pref_label: string;
  alt_labels: string[];
  definition: string | null;
  notation: string | null;
}

export interface SKOSConceptScheme {
  uri: string;
  pref_label: string;
  description: string;
  concepts: SKOSConcept[];
  turtle_download_url: string;
}

export interface LineageResponse {
  node_label: string;
  node_id: string;
  source: string | null;
  ingested_at: string | null;
  pipeline_run_id: string | null;
}

// RDF & SPARQL types

export interface SparqlResult {
  type: string;
  columns?: string[];
  rows?: Record<string, string>[];
  result?: boolean;
  turtle?: string;
}

export interface OntologyVersion {
  version: string;
  date: string;
  changes: string[];
}

export interface OntologyVersionHistory {
  current_version: string;
  versions: OntologyVersion[];
}

// Reasoning types

export interface InferredTriple {
  subject: string;
  predicate: string;
  object: string;
}

export interface ReasoningCategory {
  description: string;
  count: number;
  examples: InferredTriple[];
}

export interface ReasoningResult {
  explicit_triples: number;
  total_triples: number;
  inferred_triples: number;
  categories: {
    type_inheritance: ReasoningCategory;
    domain_range_inference: ReasoningCategory;
    other: ReasoningCategory;
  };
}

// Pipeline types

export interface PipelineStatus {
  running: boolean;
  last_result: Record<string, unknown> | null;
  last_error: string | null;
}

export interface ValuationDate {
  valuation_date: string;
}

// Document ingestion types

export interface ExtractedPortfolio {
  name: string;
  ticker: string | null;
  isin: string | null;
  asset_class: string | null;
  currency: string | null;
  aum: number | null;
  domicile: string | null;
}

export interface ExtractedHolding {
  portfolio_name: string;
  asset_name: string;
  ticker: string | null;
  isin: string | null;
  sector: string | null;
  weight_pct: number | null;
  country: string | null;
}

export interface ExtractedBenchmark {
  name: string;
  ticker: string | null;
  provider: string | null;
  asset_class: string | null;
}

export interface IngestResponse {
  status: string;
  source_type: string;
  text_length: number;
  extraction_model: string;
  entities: {
    portfolios: ExtractedPortfolio[];
    holdings: ExtractedHolding[];
    benchmarks: ExtractedBenchmark[];
  };
  entity_counts: {
    portfolios: number;
    holdings: number;
    benchmarks: number;
  };
  graph_writes: {
    portfolios: number;
    assets: number;
    sectors: number;
    benchmarks: number;
    holds_relationships: number;
    belongs_to_relationships: number;
    tracks_relationships: number;
  };
}
