// frontend/src/hooks/useGraphData.ts
// Fetches alert subgraph from the API and formats it for Sigma.js / graphology.
// Implements force-directed layout and flow animation helpers.

import { useCallback, useEffect, useRef, useState } from "react";
import Graph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";

const API_BASE = (import.meta as any).env?.VITE_API_URL ?? "http://localhost:8000";

// ── Risk colour map ────────────────────────────────────────────────
export const RISK_COLOR: Record<string, string> = {
  critical: "#FF4D4D",
  high:     "#FF6B6B",
  medium:   "#FFB300",
  low:      "#00C9A7",
  clean:    "#B0BED0",
};

// ── Raw API types ─────────────────────────────────────────────────
export interface RawNode {
  id:           string;
  label:        string;
  risk_level:   string;
  amount:       number;
  account_type: string;
  is_hub:       boolean;
  is_dormant:   boolean;
  is_origin:    boolean;
}

export interface RawEdge {
  source:         string;
  target:         string;
  amount:         number;
  timestamp:      string;
  channel:        string;
  transaction_id: string;
}

export interface RawSubgraph {
  nodes: RawNode[];
  edges: RawEdge[];
}

// ── Node/Edge attributes stored in graphology ────────────────────
export interface NodeAttrs {
  x:            number;
  y:            number;
  size:         number;
  color:        string;     // ring / glow colour
  label:        string;
  // business attrs
  risk_level:   string;
  risk_score:   number;
  total_amount: number;
  account_type: string;
  is_hub:       boolean;
  is_dormant:   boolean;
  is_origin:    boolean;
  // visual state
  highlighted:  boolean;
  dimmed:       boolean;
}

export interface EdgeAttrs {
  size:       number;
  color:      string;
  label:      string;
  // business attrs
  amount:     number;
  timestamp:  string;
  channel:    string;
  // animation state (index in the sorted edge list)
  animIndex:  number;
  visible:    boolean;
}

// ── Hook return type ──────────────────────────────────────────────
export interface UseGraphDataReturn {
  graph:       Graph<NodeAttrs, EdgeAttrs> | null;
  rawEdges:    RawEdge[];   // sorted by timestamp, for animation
  loading:     boolean;
  error:       string | null;
  refetch:     () => void;
  animateFlow: (onEdgeReveal?: (edgeKey: string) => void) => void;
  stopAnimation: () => void;
}

// ── Main hook ─────────────────────────────────────────────────────
export function useGraphData(caseId: string): UseGraphDataReturn {
  const [graph, setGraph]     = useState<Graph<NodeAttrs, EdgeAttrs> | null>(null);
  const [rawEdges, setRawEdges] = useState<RawEdge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const animTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  // ── Fetch + build graph ─────────────────────────────────────────
  const fetchGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/graph/${encodeURIComponent(caseId)}`);
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const data: RawSubgraph = await res.json();
      const { g, sortedEdges } = buildGraph(data);
      setGraph(g);
      setRawEdges(sortedEdges);
    } catch (e) {
      // In dev/demo mode fall back to the hardcoded CASE-2847 data
      if (caseId === "CASE-2847") {
        const { g, sortedEdges } = buildGraph(DEMO_SUBGRAPH);
        setGraph(g);
        setRawEdges(sortedEdges);
        setError(null);
      } else {
        setError(e instanceof Error ? e.message : "Unknown error");
      }
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => { fetchGraph(); }, [fetchGraph]);

  // ── Animation: reveal edges one by one ──────────────────────────
  const animateFlow = useCallback(
    (onEdgeReveal?: (edgeKey: string) => void) => {
      if (!graph) return;

      // Reset all edges to invisible
      graph.forEachEdge((key) => {
        graph.setEdgeAttribute(key, "visible", false);
        graph.setEdgeAttribute(key, "color", "rgba(0,201,167,0.15)");
        graph.setEdgeAttribute(key, "size", 1);
      });

      // Get edge keys sorted by animIndex
      const edgeKeys: string[] = [];
      graph.forEachEdge((key) => { edgeKeys.push(key); });
      edgeKeys.sort((a, b) =>
        (graph.getEdgeAttribute(a, "animIndex") ?? 0) -
        (graph.getEdgeAttribute(b, "animIndex") ?? 0)
      );

      // Clear old timers
      animTimers.current.forEach(clearTimeout);
      animTimers.current = [];

      edgeKeys.forEach((key, i) => {
        // Reveal edge with glow at its turn
        const t1 = setTimeout(() => {
          graph.setEdgeAttribute(key, "visible", true);
          graph.setEdgeAttribute(key, "color", "#00C9A7");   // bright teal
          graph.setEdgeAttribute(key, "size", 3);
          onEdgeReveal?.(key);
        }, i * 400);

        // Dim it after 600ms (so it fades before next edge highlights)
        const t2 = setTimeout(() => {
          graph.setEdgeAttribute(key, "color", "rgba(0,201,167,0.40)");
          graph.setEdgeAttribute(key, "size", 1.5);
        }, i * 400 + 600);

        animTimers.current.push(t1, t2);
      });

      // After all done, restore full opacity
      const tFinal = setTimeout(() => {
        graph.forEachEdge((key) => {
          graph.setEdgeAttribute(key, "color", "rgba(0,201,167,0.55)");
          graph.setEdgeAttribute(key, "size", 1.5);
          graph.setEdgeAttribute(key, "visible", true);
        });
      }, edgeKeys.length * 400 + 800);
      animTimers.current.push(tFinal);
    },
    [graph]
  );

  const stopAnimation = useCallback(() => {
    animTimers.current.forEach(clearTimeout);
    animTimers.current = [];
  }, []);

  return { graph, rawEdges, loading, error, refetch: fetchGraph, animateFlow, stopAnimation };
}

// ── Build graphology graph from raw API data ──────────────────────
function buildGraph(data: RawSubgraph): {
  g: Graph<NodeAttrs, EdgeAttrs>;
  sortedEdges: RawEdge[];
} {
  const g = new Graph<NodeAttrs, EdgeAttrs>({ multi: false, type: "directed" });

  // Max amount for normalising node size
  const maxAmount = Math.max(...data.nodes.map((n) => n.amount), 1);
  const logMax    = Math.log10(maxAmount + 1);

  // ── Add nodes ──────────────────────────────────────────────────
  // Initial positions in a circle — ForceAtlas2 will re-settle them
  data.nodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / data.nodes.length;
    const r     = 5;
    const size  = 8 + (Math.log10(n.amount + 1) / logMax) * 20;

    g.addNode(n.id, {
      x:            r * Math.cos(angle),
      y:            r * Math.sin(angle),
      size,
      color:        RISK_COLOR[n.risk_level] ?? RISK_COLOR.clean,
      label:        n.id,
      risk_level:   n.risk_level,
      risk_score:   _riskScore(n.risk_level),
      total_amount: n.amount,
      account_type: n.account_type,
      is_hub:       n.is_hub,
      is_dormant:   n.is_dormant,
      is_origin:    n.is_origin,
      highlighted:  false,
      dimmed:       false,
    });
  });

  // ── Sort edges by timestamp ────────────────────────────────────
  const sortedEdges = [...data.edges].sort((a, b) =>
    a.timestamp.localeCompare(b.timestamp)
  );

  // Max edge amount for size normalisation
  const maxEdgeAmount = Math.max(...sortedEdges.map((e) => e.amount), 1);

  // ── Add edges ──────────────────────────────────────────────────
  sortedEdges.forEach((e, i) => {
    // key unused — graphology generates edge key automatically
    const edgeSize = 1 + (e.amount / maxEdgeAmount) * 3;
    const amountLabel = `₹${(e.amount / 100000).toFixed(1)}L`;

    if (!g.hasNode(e.source) || !g.hasNode(e.target)) return;
    if (g.hasEdge(e.source, e.target)) return; // skip multi-edges

    g.addEdge(e.source, e.target, {
      size:      edgeSize,
      color:     "rgba(0,201,167,0.55)",
      label:     amountLabel,
      amount:    e.amount,
      timestamp: e.timestamp,
      channel:   e.channel,
      animIndex: i,
      visible:   true,
    });
  });

  // ── Force-directed layout ──────────────────────────────────────
  // First pass: random positions are settled by ForceAtlas2
  if (g.order > 1) {
    forceAtlas2.assign(g, {
      iterations:   120,
      settings: {
        gravity:          1,
        scalingRatio:     4,
        strongGravityMode: false,
        barnesHutOptimize: g.order > 10,
      },
    });
  }

  return { g, sortedEdges };
}

// ── Helpers ───────────────────────────────────────────────────────
function _riskScore(risk: string): number {
  return { critical: 94, high: 80, medium: 60, low: 30, clean: 10 }[risk] ?? 50;
}

// ── Demo data: CASE-2847 ─────────────────────────────────────────
export const DEMO_SUBGRAPH: RawSubgraph = {
  nodes: [
    { id:"ACC-0041", label:"ACC-0041", risk_level:"high",     amount:4723000, account_type:"savings", is_hub:false, is_dormant:true,  is_origin:true  },
    { id:"ACC-0112", label:"ACC-0112", risk_level:"medium",   amount:780000,  account_type:"savings", is_hub:false, is_dormant:false, is_origin:false },
    { id:"ACC-0203", label:"ACC-0203", risk_level:"medium",   amount:910000,  account_type:"savings", is_hub:false, is_dormant:false, is_origin:false },
    { id:"ACC-0089", label:"ACC-0089", risk_level:"critical", amount:3420000, account_type:"current", is_hub:true,  is_dormant:false, is_origin:false },
    { id:"ACC-0317", label:"ACC-0317", risk_level:"medium",   amount:840000,  account_type:"savings", is_hub:false, is_dormant:false, is_origin:false },
    { id:"ACC-0455", label:"ACC-0455", risk_level:"medium",   amount:890000,  account_type:"savings", is_hub:false, is_dormant:false, is_origin:false },
    { id:"ACC-0043", label:"ACC-0043", risk_level:"high",     amount:1730000, account_type:"current", is_hub:false, is_dormant:false, is_origin:false },
  ],
  edges: [
    { source:"ACC-0041", target:"ACC-0112", amount:780000,  timestamp:"09:16:22", channel:"NEFT",  transaction_id:"T001" },
    { source:"ACC-0041", target:"ACC-0203", amount:910000,  timestamp:"09:16:22", channel:"UPI",   transaction_id:"T002" },
    { source:"ACC-0112", target:"ACC-0089", amount:780000,  timestamp:"10:02:11", channel:"NEFT",  transaction_id:"T003" },
    { source:"ACC-0203", target:"ACC-0089", amount:910000,  timestamp:"10:02:11", channel:"IMPS",  transaction_id:"T004" },
    { source:"ACC-0089", target:"ACC-0317", amount:840000,  timestamp:"11:44:55", channel:"NEFT",  transaction_id:"T005" },
    { source:"ACC-0089", target:"ACC-0455", amount:890000,  timestamp:"11:44:55", channel:"UPI",   transaction_id:"T006" },
    { source:"ACC-0317", target:"ACC-0043", amount:840000,  timestamp:"15:28:07", channel:"UPI",   transaction_id:"T007" },
    { source:"ACC-0455", target:"ACC-0043", amount:890000,  timestamp:"15:28:07", channel:"IMPS",  transaction_id:"T008" },
  ],
};
