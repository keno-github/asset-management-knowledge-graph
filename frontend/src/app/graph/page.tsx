"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface GraphNode {
  id: number;
  label: string;
  group: string;
  properties: Record<string, unknown>;
  x?: number;
  y?: number;
}

interface GraphLink {
  source: number;
  target: number;
  label: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const NODE_COLORS: Record<string, string> = {
  Portfolio: "#0ea5e9",
  Asset: "#22c55e",
  Benchmark: "#a855f7",
  Sector: "#f59e0b",
  ESGRating: "#ef4444",
  Entity: "#06b6d4",
  FundManager: "#ec4899",
  RatingProvider: "#6366f1",
  Holding: "#84cc16",
  PerformanceRecord: "#f97316",
};

const NODE_SIZES: Record<string, number> = {
  Portfolio: 12,
  Benchmark: 10,
  Sector: 8,
  ESGRating: 6,
  FundManager: 6,
  Entity: 6,
  Asset: 4,
  RatingProvider: 5,
  Holding: 4,
  PerformanceRecord: 4,
};

const LINK_COLORS: Record<string, string> = {
  HOLDS: "#22c55e",
  TRACKS: "#a855f7",
  BELONGS_TO: "#f59e0b",
  HAS_ESG_SCORE: "#ef4444",
  MANAGED_BY: "#ec4899",
  WORKS_FOR: "#06b6d4",
  PEER_OF: "#6366f1",
  COMPOSED_OF: "#84cc16",
};

const LARGE_LABEL_TYPES = new Set(["Portfolio", "Benchmark", "Sector"]);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function linkId(l: GraphLink): string {
  const sId = typeof l.source === "object" ? (l.source as any).id : l.source;
  const tId = typeof l.target === "object" ? (l.target as any).id : l.target;
  return `${sId}-${l.label}-${tId}`;
}

function parseRecord(
  rec: { source: Record<string, unknown>; relationship: string; target: Record<string, unknown> },
  existingIds: Set<number>,
  nodes: GraphNode[],
  links: GraphLink[],
  linkKeys: Set<string>,
) {
  const src = rec.source;
  const tgt = rec.target;
  const srcId = src._id as number;
  const tgtId = tgt._id as number;

  if (!existingIds.has(srcId)) {
    nodes.push({
      id: srcId,
      label: String(src.name ?? src.portfolio_id ?? srcId),
      group: src._label as string,
      properties: Object.fromEntries(Object.entries(src).filter(([k]) => !k.startsWith("_"))),
    });
    existingIds.add(srcId);
  }

  if (!existingIds.has(tgtId)) {
    nodes.push({
      id: tgtId,
      label: String(tgt.name ?? tgt.benchmark_id ?? tgtId),
      group: tgt._label as string,
      properties: Object.fromEntries(Object.entries(tgt).filter(([k]) => !k.startsWith("_"))),
    });
    existingIds.add(tgtId);
  }

  const key = `${srcId}-${rec.relationship}-${tgtId}`;
  if (!linkKeys.has(key)) {
    links.push({ source: srcId, target: tgtId, label: rec.relationship });
    linkKeys.add(key);
  }
}

// ---------------------------------------------------------------------------
// SVG icon paths (inline to avoid dependencies)
// ---------------------------------------------------------------------------

const ChevronIcon = ({ open }: { open: boolean }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    {open ? <polyline points="15 18 9 12 15 6" /> : <polyline points="9 18 15 12 9 6" />}
  </svg>
);

const SearchIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function GraphExplorerPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [controlsOpen, setControlsOpen] = useState(true);

  // Search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<{ id: number; label: string; name: string }[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Graph ref + dimensions
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // -----------------------------------------------------------------------
  // Resize
  // -----------------------------------------------------------------------
  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  // -----------------------------------------------------------------------
  // Initial load
  // -----------------------------------------------------------------------
  useEffect(() => {
    api
      .initialGraph()
      .then((records) => {
        const nodes: GraphNode[] = [];
        const links: GraphLink[] = [];
        const ids = new Set<number>();
        const linkKeys = new Set<string>();
        records.forEach((rec) => parseRecord(rec, ids, nodes, links, linkKeys));
        setGraphData({ nodes, links });
        setActiveFilters(new Set(Object.keys(NODE_COLORS)));
        setLoading(false);
        setTimeout(() => fgRef.current?.zoomToFit(400, 50), 600);
      })
      .catch(() => setLoading(false));
  }, []);

  // -----------------------------------------------------------------------
  // Expand
  // -----------------------------------------------------------------------
  const expandNode = useCallback(
    (nodeId: number) => {
      if (expandedNodes.has(nodeId)) return;
      api.subgraph(nodeId).then((records) => {
        setGraphData((prev) => {
          const nodes = [...prev.nodes];
          const links: GraphLink[] = [...prev.links];
          const linkKeys = new Set(prev.links.map(linkId));
          const ids = new Set(nodes.map((n) => n.id));
          records.forEach((rec) => parseRecord(rec, ids, nodes, links, linkKeys));
          return { nodes, links };
        });
        setExpandedNodes((prev) => new Set(prev).add(nodeId));
      });
    },
    [expandedNodes],
  );

  // -----------------------------------------------------------------------
  // Collapse — clear selectedNode if it gets removed
  // -----------------------------------------------------------------------
  const collapseNode = useCallback(
    (nodeId: number) => {
      setGraphData((prev) => {
        const neighborIds = new Set<number>();
        prev.links.forEach((l) => {
          const sId = typeof l.source === "object" ? (l.source as any).id : l.source;
          const tId = typeof l.target === "object" ? (l.target as any).id : l.target;
          if (sId === nodeId) neighborIds.add(tId);
          if (tId === nodeId) neighborIds.add(sId);
        });

        const toRemove = new Set<number>();
        neighborIds.forEach((nid) => {
          const otherLinks = prev.links.filter((l) => {
            const sId = typeof l.source === "object" ? (l.source as any).id : l.source;
            const tId = typeof l.target === "object" ? (l.target as any).id : l.target;
            return (sId === nid || tId === nid) && sId !== nodeId && tId !== nodeId;
          });
          if (otherLinks.length === 0) toRemove.add(nid);
        });

        // Clear selection if the selected node is being removed
        setSelectedNode((sel) => (sel && toRemove.has(sel.id) ? null : sel));

        return {
          nodes: prev.nodes.filter((n) => !toRemove.has(n.id)),
          links: prev.links.filter((l) => {
            const sId = typeof l.source === "object" ? (l.source as any).id : l.source;
            const tId = typeof l.target === "object" ? (l.target as any).id : l.target;
            return !toRemove.has(sId) && !toRemove.has(tId);
          }),
        };
      });
      setExpandedNodes((prev) => {
        const next = new Set(prev);
        next.delete(nodeId);
        return next;
      });
    },
    [],
  );

  // -----------------------------------------------------------------------
  // Search
  // -----------------------------------------------------------------------
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (!value.trim()) {
      setSearchResults([]);
      setSearchOpen(false);
      return;
    }
    searchTimeout.current = setTimeout(() => {
      api.searchNodes(value).then((results) => {
        setSearchResults(results);
        setSearchOpen(results.length > 0);
      });
    }, 300);
  };

  const focusNode = (nodeId: number) => {
    setSearchOpen(false);
    setSearchQuery("");
    const existing = graphData.nodes.find((n) => n.id === nodeId);
    if (existing) {
      fgRef.current?.centerAt(existing.x, existing.y, 500);
      fgRef.current?.zoom(3, 500);
      setSelectedNode(existing);
    }
    expandNode(nodeId);
  };

  // -----------------------------------------------------------------------
  // Filtered data
  // -----------------------------------------------------------------------
  const filteredData = {
    nodes: graphData.nodes.filter((n) => activeFilters.has(n.group)),
    links: graphData.links.filter((l) => {
      const srcId = typeof l.source === "object" ? (l.source as any).id : l.source;
      const tgtId = typeof l.target === "object" ? (l.target as any).id : l.target;
      const srcNode = graphData.nodes.find((n) => n.id === srcId);
      const tgtNode = graphData.nodes.find((n) => n.id === tgtId);
      return srcNode && tgtNode && activeFilters.has(srcNode.group) && activeFilters.has(tgtNode.group);
    }),
  };

  const groups = [...new Set(graphData.nodes.map((n) => n.group))];

  // -----------------------------------------------------------------------
  // Rendering callbacks
  // -----------------------------------------------------------------------
  const handleNodeClick = useCallback(
    (node: any) => {
      setSelectedNode(node as GraphNode);
      expandNode(node.id);
    },
    [expandNode],
  );

  const handleNodeDoubleClick = useCallback(
    (node: any) => collapseNode(node.id),
    [collapseNode],
  );

  const renderNode = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const r = NODE_SIZES[node.group] ?? 4;
      const color = NODE_COLORS[node.group] ?? "#64748b";

      // Selection glow
      if (selectedNode && selectedNode.id === node.id) {
        ctx.beginPath();
        ctx.arc(node.x ?? 0, node.y ?? 0, r + 4, 0, 2 * Math.PI);
        ctx.fillStyle = `${color}22`;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(node.x ?? 0, node.y ?? 0, r + 2, 0, 2 * Math.PI);
        ctx.fillStyle = `${color}44`;
        ctx.fill();
      }

      // Node
      ctx.beginPath();
      ctx.arc(node.x ?? 0, node.y ?? 0, r, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();

      // Expanded ring
      if (expandedNodes.has(node.id)) {
        ctx.strokeStyle = "rgba(255,255,255,0.6)";
        ctx.lineWidth = 1.5 / globalScale;
        ctx.stroke();
      }

      // Labels
      const showLabel = LARGE_LABEL_TYPES.has(node.group) || globalScale > 2;
      if (showLabel) {
        const fontSize = Math.max(10 / globalScale, 2);
        ctx.font = `${fontSize}px Inter, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillStyle = "#cbd5e1";
        ctx.fillText(node.label, node.x ?? 0, (node.y ?? 0) + r + 2);
      }
    },
    [selectedNode, expandedNodes],
  );

  const renderLink = useCallback(
    (link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const src = link.source;
      const tgt = link.target;
      if (!src.x || !tgt.x) return;

      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);
      ctx.strokeStyle = LINK_COLORS[link.label] ?? "#1e293b";
      ctx.lineWidth = 1 / globalScale;
      ctx.stroke();

      // Arrow
      const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
      const arrowLen = 4 / globalScale;
      const tgtR = NODE_SIZES[tgt.group] ?? 4;
      const ax = tgt.x - Math.cos(angle) * (tgtR + 2);
      const ay = tgt.y - Math.sin(angle) * (tgtR + 2);
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax - arrowLen * Math.cos(angle - 0.4), ay - arrowLen * Math.sin(angle - 0.4));
      ctx.lineTo(ax - arrowLen * Math.cos(angle + 0.4), ay - arrowLen * Math.sin(angle + 0.4));
      ctx.closePath();
      ctx.fillStyle = LINK_COLORS[link.label] ?? "#1e293b";
      ctx.fill();

      // Relationship label when zoomed
      if (globalScale > 1.8) {
        const mx = (src.x + tgt.x) / 2;
        const my = (src.y + tgt.y) / 2;
        const fontSize = Math.max(7 / globalScale, 1.5);
        ctx.font = `${fontSize}px Inter, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = "#64748b";
        ctx.fillText(link.label, mx, my);
      }
    },
    [],
  );

  const toggleFilter = (group: string) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(group)) next.delete(group);
      else next.add(group);
      return next;
    });
  };

  // -----------------------------------------------------------------------
  // Relationship counts for detail panel
  // -----------------------------------------------------------------------
  const getRelCounts = (nodeId: number) => {
    const counts: Record<string, number> = {};
    graphData.links.forEach((l) => {
      const sId = typeof l.source === "object" ? (l.source as any).id : l.source;
      const tId = typeof l.target === "object" ? (l.target as any).id : l.target;
      if (sId === nodeId || tId === nodeId) {
        counts[l.label] = (counts[l.label] || 0) + 1;
      }
    });
    return counts;
  };

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------
  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Compact title bar */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold tracking-tight">Graph Explorer</h1>
          <span className="text-[11px] text-slate-500 font-mono tabular-nums">
            {filteredData.nodes.length} nodes &middot; {filteredData.links.length} rels
          </span>
          <span className="text-[11px] text-slate-600 hidden lg:inline">
            — Interactive visualization of the Neo4j knowledge graph. Start with portfolios, click to expand relationships, search to find any entity.
          </span>
        </div>
        <button
          onClick={() => fgRef.current?.zoomToFit(400, 50)}
          className="px-3 py-1 text-xs rounded-lg border border-slate-800 bg-[#0d1321] text-slate-400 hover:text-slate-200 transition-colors"
        >
          Fit View
        </button>
      </div>

      {/* Graph canvas + always-visible detail panel */}
      <div className="flex flex-1 min-h-0 gap-0">
        {/* Graph container with overlaid controls */}
        <div
          ref={containerRef}
          className="flex-1 rounded-xl rounded-r-none border border-slate-800 border-r-0 bg-[#080c14] overflow-hidden relative"
        >
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-sm text-slate-600 animate-pulse">Loading graph...</div>
            </div>
          ) : graphData.nodes.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-slate-500">No graph data available</p>
                <p className="text-xs text-slate-600 mt-1">Run the pipeline to populate Neo4j</p>
              </div>
            </div>
          ) : (
            <ForceGraph2D
              ref={fgRef}
              graphData={filteredData}
              width={dimensions.width}
              height={dimensions.height}
              backgroundColor="#080c14"
              nodeId="id"
              nodeLabel={(node: any) => `${node.group}: ${node.label}`}
              nodeColor={(node: any) => NODE_COLORS[node.group] ?? "#64748b"}
              nodeRelSize={6}
              nodeCanvasObject={renderNode}
              linkCanvasObject={renderLink}
              linkDirectionalArrowLength={0}
              onNodeClick={handleNodeClick}
              onNodeRightClick={handleNodeDoubleClick}
              cooldownTicks={100}
              d3AlphaDecay={0.02}
              d3VelocityDecay={0.3}
            />
          )}

          {/* ---- Floating controls overlay (top-left) ---- */}
          <div className="absolute top-3 left-3 z-10">
            {/* Toggle button */}
            <button
              onClick={() => setControlsOpen((o) => !o)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-700/60 bg-[#0d1321]/90 backdrop-blur text-slate-400 hover:text-slate-200 text-xs transition-colors"
            >
              <ChevronIcon open={controlsOpen} />
              {!controlsOpen && <span>Controls</span>}
            </button>

            {/* Expanded controls panel */}
            {controlsOpen && (
              <div className="mt-2 w-64 rounded-xl border border-slate-700/60 bg-[#0d1321]/90 backdrop-blur p-3 space-y-3">
                {/* Search */}
                <div className="relative">
                  <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-700/50 bg-[#080c14]/60 focus-within:border-slate-600">
                    <SearchIcon />
                    <input
                      type="text"
                      placeholder="Search nodes..."
                      value={searchQuery}
                      onChange={(e) => handleSearch(e.target.value)}
                      onFocus={() => searchResults.length > 0 && setSearchOpen(true)}
                      onBlur={() => setTimeout(() => setSearchOpen(false), 200)}
                      className="flex-1 bg-transparent text-sm text-slate-300 placeholder-slate-600 focus:outline-none"
                    />
                  </div>
                  {searchOpen && (
                    <div className="absolute z-50 top-full mt-1 w-full max-h-52 overflow-y-auto rounded-lg border border-slate-700/60 bg-[#0d1321] shadow-xl">
                      {searchResults.map((r) => (
                        <button
                          key={r.id}
                          onMouseDown={() => focusNode(r.id)}
                          className="w-full text-left px-3 py-2 text-sm hover:bg-slate-800/50 flex items-center gap-2"
                        >
                          <span
                            className="inline-block w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: NODE_COLORS[r.label] ?? "#64748b" }}
                          />
                          <span className="text-slate-300 truncate">{r.name}</span>
                          <span className="text-slate-600 text-[10px] ml-auto">{r.label}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Filter pills */}
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">Node types</p>
                  <div className="flex flex-wrap gap-1">
                    {groups.map((group) => (
                      <button
                        key={group}
                        onClick={() => toggleFilter(group)}
                        className={`px-2 py-0.5 rounded-full text-[10px] transition-all ${
                          activeFilters.has(group)
                            ? "border border-transparent text-white"
                            : "border border-slate-700 text-slate-600"
                        }`}
                        style={
                          activeFilters.has(group) ? { backgroundColor: NODE_COLORS[group] ?? "#64748b" } : {}
                        }
                      >
                        {group}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Hint */}
                <p className="text-[10px] text-slate-600 leading-relaxed">
                  Click to expand &middot; Double-click to collapse
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ---- Detail panel (always visible) ---- */}
        <div className="w-72 shrink-0 rounded-r-xl border border-slate-800 border-l border-l-slate-800/50 bg-[#0d1321] overflow-y-auto">
          {selectedNode ? (
            <div className="p-4">
              {/* Header */}
              <div className="flex justify-between items-start mb-3">
                <div className="min-w-0">
                  <span
                    className="inline-block px-2 py-0.5 rounded text-[10px] font-medium text-white mb-1.5"
                    style={{ backgroundColor: NODE_COLORS[selectedNode.group] ?? "#64748b" }}
                  >
                    {selectedNode.group}
                  </span>
                  <p className="text-sm font-semibold text-slate-200 truncate">{selectedNode.label}</p>
                </div>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-slate-600 hover:text-slate-400 text-sm leading-none ml-2 shrink-0"
                >
                  ✕
                </button>
              </div>

              {/* Properties */}
              {Object.keys(selectedNode.properties).length > 0 && (
                <div className="mb-4">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Properties</p>
                  <div className="space-y-1.5">
                    {Object.entries(selectedNode.properties).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-xs gap-2">
                        <span className="text-slate-500 shrink-0">{k}</span>
                        <span className="text-slate-300 font-mono truncate text-right max-w-[140px]">
                          {String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Relationships */}
              {(() => {
                const counts = getRelCounts(selectedNode.id);
                const entries = Object.entries(counts);
                if (entries.length === 0) return null;
                return (
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Relationships</p>
                    <div className="space-y-1">
                      {entries.map(([rel, count]) => (
                        <div key={rel} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-1.5">
                            <span
                              className="w-2 h-2 rounded-full shrink-0"
                              style={{ backgroundColor: LINK_COLORS[rel] ?? "#475569" }}
                            />
                            <span className="text-slate-400">{rel}</span>
                          </div>
                          <span className="text-slate-500 font-mono">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            /* Placeholder when nothing selected */
            <div className="h-full flex flex-col items-center justify-center p-6 text-center">
              <div className="w-10 h-10 rounded-full border border-slate-800 flex items-center justify-center mb-3">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-600">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
              </div>
              <p className="text-xs text-slate-500">Click a node to inspect</p>
              <p className="text-[10px] text-slate-600 mt-1">Properties and relationships</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
