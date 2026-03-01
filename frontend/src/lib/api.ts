/** Typed API client for the AMKG FastAPI backend. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

import type {
  ChatResponse,
  ESGControversy,
  ESGCrossRisk,
  GraphStats,
  Holding,
  LineageResponse,
  OntologySummary,
  OntologyVersionHistory,
  PeerOverlap,
  PortfolioDetail,
  PortfolioSummary,
  ReasoningResult,
  SKOSConceptScheme,
  SparqlResult,
  TaxonomyAlignment,
} from "./types";

export const api = {
  // System
  health: () => fetchAPI<{ status: string; neo4j_connected: boolean }>("/health"),
  stats: () => fetchAPI<GraphStats>("/stats"),

  // Portfolios
  listPortfolios: () => fetchAPI<PortfolioSummary[]>("/api/portfolios/"),
  getPortfolio: (id: string) => fetchAPI<PortfolioDetail>(`/api/portfolios/${id}`),
  getHoldings: (id: string) => fetchAPI<Holding[]>(`/api/portfolios/${id}/holdings`),
  getPeerOverlap: (id: string) => fetchAPI<PeerOverlap[]>(`/api/portfolios/${id}/peer-overlap`),

  // ESG
  esgControversy: (max: number = 2) =>
    fetchAPI<ESGControversy[]>(`/api/esg/controversy?max_controversy=${max}`),
  esgCrossRisk: () => fetchAPI<ESGCrossRisk[]>("/api/esg/cross-portfolio-risk"),
  taxonomyAlignment: () => fetchAPI<TaxonomyAlignment[]>("/api/esg/taxonomy-alignment"),

  // Discovery
  graphOverview: () => fetchAPI<{ label: string; count: number }[]>("/api/discovery/graph-overview"),
  subgraph: (nodeId: number) =>
    fetchAPI<{ source: Record<string, unknown>; relationship: string; target: Record<string, unknown> }[]>(
      `/api/discovery/subgraph/${nodeId}`
    ),
  initialGraph: () =>
    fetchAPI<{ source: Record<string, unknown>; relationship: string; target: Record<string, unknown> }[]>(
      "/api/discovery/initial-graph"
    ),
  searchNodes: (query: string) =>
    fetchAPI<{ id: number; label: string; name: string }[]>(
      `/api/discovery/search-nodes?q=${encodeURIComponent(query)}`
    ),

  // Chat
  chat: (question: string) =>
    fetchAPI<ChatResponse>("/api/chat/", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  // Ontology & Vocabulary
  getOntologySummary: () => fetchAPI<OntologySummary>("/ontology"),
  getVocabulary: (name: string) => fetchAPI<SKOSConceptScheme>(`/api/vocabulary/${name}`),
  getLineage: (label: string, id: string) =>
    fetchAPI<LineageResponse>(`/api/lineage/${label}/${id}`),

  // RDF & SPARQL
  sparqlQuery: (query: string) =>
    fetchAPI<SparqlResult>(`/api/rdf/sparql?query=${encodeURIComponent(query)}`),
  getOntologyVersions: () => fetchAPI<OntologyVersionHistory>("/ontology/versions"),
  getRdfExportUrl: (format: string = "turtle", label?: string) => {
    let url = `${API_BASE}/api/rdf/export?format=${format}`;
    if (label) url += `&label=${label}`;
    return url;
  },

  // Reasoning
  runReasoning: () => fetchAPI<ReasoningResult>("/api/rdf/reasoning"),

  // Document ingestion (uses fetch directly — FormData, not JSON)
  ingestApiUrl: `${API_BASE}/api/ingest/extract`,
};
