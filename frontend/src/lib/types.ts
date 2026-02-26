/** TypeScript interfaces matching the FastAPI response schemas. */

export interface PortfolioSummary {
  portfolio_id: string;
  name: string;
  asset_class: string | null;
  aum: number | null;
  morningstar_rating: number | null;
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
