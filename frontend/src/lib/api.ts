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
  PeerOverlap,
  PortfolioDetail,
  PortfolioSummary,
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
  subgraph: (nodeId: string) => fetchAPI<Record<string, unknown>[]>(`/api/discovery/subgraph/${nodeId}`),

  // Chat
  chat: (question: string) =>
    fetchAPI<ChatResponse>("/api/chat/", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};
