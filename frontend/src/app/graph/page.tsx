"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

interface GraphNode {
  id: string;
  label: string;
  group: string;
  properties: Record<string, unknown>;
  x?: number;
  y?: number;
}

interface GraphLink {
  source: string;
  target: string;
  label: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

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

export default function GraphExplorerPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const fgRef = useRef<{ zoomToFit: (ms?: number, px?: number) => void } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  useEffect(() => {
    api.graphOverview().then((overview) => {
      const nodes: GraphNode[] = [];
      const links: GraphLink[] = [];
      const nodeIds = new Set<string>();

      overview.forEach((item) => {
        const nodeId = item.label;
        if (!nodeIds.has(nodeId)) {
          nodes.push({
            id: nodeId,
            label: `${item.label} (${item.count})`,
            group: item.label,
            properties: { count: item.count },
          });
          nodeIds.add(nodeId);
        }
      });

      if (nodes.length > 1) {
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            if (Math.random() > 0.5) {
              links.push({ source: nodes[i].id, target: nodes[j].id, label: "RELATED" });
            }
          }
        }
      }

      setGraphData({ nodes, links });
      setActiveFilters(new Set(nodes.map((n) => n.group)));
      setLoading(false);

      setTimeout(() => fgRef.current?.zoomToFit(400, 50), 500);
    }).catch(() => setLoading(false));
  }, []);

  const expandNode = useCallback((nodeId: string) => {
    api.subgraph(nodeId).then((records) => {
      const newNodes = [...graphData.nodes];
      const newLinks = [...graphData.links];
      const existingIds = new Set(newNodes.map((n) => n.id));

      records.forEach((rec) => {
        const entries = Object.entries(rec);
        entries.forEach(([, val]) => {
          if (val && typeof val === "object" && "id" in (val as Record<string, unknown>)) {
            const node = val as { id: string; labels?: string[]; properties?: Record<string, unknown> };
            if (!existingIds.has(String(node.id))) {
              newNodes.push({
                id: String(node.id),
                label: String(node.properties?.name ?? node.id),
                group: node.labels?.[0] ?? "Unknown",
                properties: node.properties ?? {},
              });
              existingIds.add(String(node.id));
              newLinks.push({ source: nodeId, target: String(node.id), label: "CONNECTED" });
            }
          }
        });
      });

      setGraphData({ nodes: newNodes, links: newLinks });
      setActiveFilters((prev) => {
        const next = new Set(prev);
        newNodes.forEach((n) => next.add(n.group));
        return next;
      });
    });
  }, [graphData]);

  const filteredData = {
    nodes: graphData.nodes.filter((n) => activeFilters.has(n.group)),
    links: graphData.links.filter((l) => {
      const srcId = typeof l.source === "object" ? (l.source as GraphNode).id : l.source;
      const tgtId = typeof l.target === "object" ? (l.target as GraphNode).id : l.target;
      const srcNode = graphData.nodes.find((n) => n.id === srcId);
      const tgtNode = graphData.nodes.find((n) => n.id === tgtId);
      return srcNode && tgtNode && activeFilters.has(srcNode.group) && activeFilters.has(tgtNode.group);
    }),
  };

  const groups = [...new Set(graphData.nodes.map((n) => n.group))];

  const getNodeColor = useCallback((node: any) => {
    return NODE_COLORS[node.group] ?? "#64748b";
  }, []);

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node as GraphNode);
    expandNode(node.id);
  }, [expandNode]);

  const renderNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label;
    const fontSize = Math.max(10 / globalScale, 2);
    const nodeR = 5;
    const color = NODE_COLORS[node.group] ?? "#64748b";

    ctx.beginPath();
    ctx.arc(node.x ?? 0, node.y ?? 0, nodeR, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    if (globalScale > 1.5) {
      ctx.font = `${fontSize}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = "#94a3b8";
      ctx.fillText(label, node.x ?? 0, (node.y ?? 0) + nodeR + 2);
    }
  }, []);

  const toggleFilter = (group: string) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(group)) next.delete(group);
      else next.add(group);
      return next;
    });
  };

  return (
    <div className="space-y-4 h-[calc(100vh-4rem)]">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Graph Explorer</h1>
          <p className="text-sm text-slate-500 mt-1">
            Interactive force-directed visualization — click nodes to expand
          </p>
        </div>
        <button
          onClick={() => fgRef.current?.zoomToFit(400, 50)}
          className="px-3 py-1.5 text-xs rounded-lg border border-slate-800 bg-[#0d1321] text-slate-400 hover:text-slate-200 transition-colors"
        >
          Fit View
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {groups.map((group) => (
          <button
            key={group}
            onClick={() => toggleFilter(group)}
            className={`px-3 py-1 rounded-full text-xs transition-all ${
              activeFilters.has(group)
                ? "border border-transparent text-white"
                : "border border-slate-700 text-slate-600"
            }`}
            style={activeFilters.has(group) ? { backgroundColor: NODE_COLORS[group] ?? "#64748b" } : {}}
          >
            {group}
          </button>
        ))}
      </div>

      {/* Graph Container */}
      <div ref={containerRef} className="flex-1 rounded-xl border border-slate-800 bg-[#080c14] overflow-hidden relative" style={{ minHeight: "500px" }}>
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-sm text-slate-600 animate-pulse">Loading graph data...</div>
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
            ref={fgRef as React.RefObject<never>}
            graphData={filteredData}
            width={dimensions.width}
            height={dimensions.height - 20}
            backgroundColor="#080c14"
            nodeLabel="label"
            nodeColor={getNodeColor}
            nodeRelSize={6}
            linkColor={() => "#1e293b"}
            linkWidth={1}
            linkDirectionalArrowLength={3}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            nodeCanvasObject={renderNode}
          />
        )}

        {/* Node Detail Panel */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-64 rounded-xl border border-slate-800 bg-[#0d1321]/95 backdrop-blur p-4">
            <div className="flex justify-between items-start">
              <div>
                <span
                  className="inline-block px-2 py-0.5 rounded text-[10px] font-medium text-white mb-2"
                  style={{ backgroundColor: NODE_COLORS[selectedNode.group] ?? "#64748b" }}
                >
                  {selectedNode.group}
                </span>
                <p className="text-sm font-medium text-slate-200">{selectedNode.label}</p>
              </div>
              <button onClick={() => setSelectedNode(null)} className="text-slate-600 hover:text-slate-400 text-xs">
                ✕
              </button>
            </div>
            {Object.keys(selectedNode.properties).length > 0 && (
              <div className="mt-3 space-y-1.5">
                {Object.entries(selectedNode.properties).slice(0, 6).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-xs">
                    <span className="text-slate-500">{k}</span>
                    <span className="text-slate-300 font-mono truncate ml-2 max-w-[120px]">
                      {String(v)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
