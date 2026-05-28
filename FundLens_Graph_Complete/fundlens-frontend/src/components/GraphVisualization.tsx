// frontend/src/components/GraphVisualization.tsx
// @react-sigma/core v5 — SigmaContainer receives `graph` prop directly
import type { CSSProperties } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { SigmaContainer, useCamera, useRegisterEvents, useSetSettings, useSigma } from "@react-sigma/core";
import "@react-sigma/core/lib/style.css";
import type { NodeAttrs, EdgeAttrs } from "../hooks/useGraphData";
import { RISK_COLOR, useGraphData } from "../hooks/useGraphData";

interface Props { caseId: string; onNodeClick: (nodeId: string) => void; }
interface TooltipState { visible: boolean; x: number; y: number; accountId: string; riskScore: number; totalAmount: number; isDormant: boolean; riskLevel: string; accountType: string; }
const HIDDEN: TooltipState = { visible: false, x: 0, y: 0, accountId: "", riskScore: 0, totalAmount: 0, isDormant: false, riskLevel: "", accountType: "" };

// Lives inside SigmaContainer — can call Sigma hooks
function GraphController({ onNodeClick, setTooltip, animateFlowRef, animateFlowFn }:
  { onNodeClick: (id: string) => void; setTooltip: React.Dispatch<React.SetStateAction<TooltipState>>; animateFlowRef: React.MutableRefObject<(() => void) | null>; animateFlowFn: ((cb?: (k: string) => void) => void) | null; }
) {
  const sigma = useSigma<NodeAttrs, EdgeAttrs>();
  const registerEvents = useRegisterEvents<NodeAttrs, EdgeAttrs>();
  const setSettings = useSetSettings<NodeAttrs, EdgeAttrs>();
  const { reset } = useCamera();
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    requestAnimationFrame(() => { sigma.refresh(); reset({ duration: 700 }); });
    if (animateFlowFn) animateFlowRef.current = () => animateFlowFn(() => sigma.refresh());
  }, [sigma, reset, animateFlowFn, animateFlowRef]);

  useEffect(() => {
    setSettings({
      defaultNodeColor: "#12244E", defaultEdgeColor: "rgba(0,201,167,0.55)", defaultEdgeType: "arrow",
      renderLabels: true, renderEdgeLabels: true,
      labelColor: { color: "#B0BED0" }, labelSize: 10, labelFont: "DM Sans, sans-serif", labelWeight: "500",
      labelRenderedSizeThreshold: 5, hideEdgesOnMove: false,
      nodeReducer: (_node, data) => {
        const a = data as NodeAttrs;
        return { ...a, color: a.highlighted ? "#FFFFFF" : a.dimmed ? "rgba(176,190,208,0.25)" : a.color, size: a.highlighted ? (a.size ?? 12) * 1.5 : a.dimmed ? (a.size ?? 12) * 0.65 : a.size ?? 12, label: a.label };
      },
      edgeReducer: (_, data) => { const a = data as EdgeAttrs; return { ...a, hidden: !(a.visible ?? true) }; },
    });
  }, [setSettings]);

  useEffect(() => {
    registerEvents({
      enterNode: ({ node, event }) => {
        const g = sigma.getGraph(); g.setNodeAttribute(node, "highlighted", true);
        g.forEachNode((n) => { if (n !== node) g.setNodeAttribute(n, "dimmed", true); });
        sigma.refresh();
        const a = g.getNodeAttributes(node) as NodeAttrs;
        setTooltip({ visible: true, x: event.x, y: event.y, accountId: node, riskScore: a.risk_score, totalAmount: a.total_amount, isDormant: a.is_dormant, riskLevel: a.risk_level, accountType: a.account_type });
      },
      leaveNode: ({ node }) => {
        const g = sigma.getGraph(); g.setNodeAttribute(node, "highlighted", false);
        g.forEachNode((n) => g.setNodeAttribute(n, "dimmed", false));
        sigma.refresh(); setTooltip(HIDDEN);
      },
      clickNode: ({ node }) => onNodeClick(node),
      clickStage: () => reset({ duration: 600 }),
    });
  }, [registerEvents, sigma, setTooltip, onNodeClick, reset]);

  return null;
}

// Main component
export default function GraphVisualization({ caseId, onNodeClick }: Props) {
  const { graph, loading, error, animateFlow, stopAnimation, refetch } = useGraphData(caseId);
  const [tooltip, setTooltip] = useState<TooltipState>(HIDDEN);
  const [animDone, setAnimDone] = useState(false);
  const animateFlowRef = useRef<(() => void) | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!graph || animDone) return;
    const t = setTimeout(() => { animateFlowRef.current?.(); setAnimDone(true); }, 900);
    return () => clearTimeout(t);
  }, [graph, animDone]);

  useEffect(() => () => stopAnimation(), [stopAnimation]);

  const tooltipStyle = useCallback((): CSSProperties => {
    const pad = 14, tw = 224, th = 130;
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return { left: tooltip.x + pad, top: tooltip.y + pad };
    let left = tooltip.x - rect.left + pad; let top = tooltip.y - rect.top + pad;
    if (left + tw > rect.width) left -= tw + pad * 2;
    if (top + th > rect.height) top -= th + pad * 2;
    return { left, top };
  }, [tooltip.x, tooltip.y]);

  return (
    <div ref={containerRef} style={{ position: "relative", width: "100%", height: "100%", background: "#060C1E", overflow: "hidden", borderRadius: 8 }}>

      {loading && (
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, background: "#060C1E", zIndex: 20 }}>
          <Spinner />
          <span style={{ color: "#8899AA", fontSize: 13 }}>Loading fund flow graph…</span>
        </div>
      )}

      {error && !loading && (
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, background: "#060C1E", zIndex: 20 }}>
          <div style={{ fontSize: 32, color: "#FF4D4D" }}>⚠</div>
          <div style={{ color: "#FF4D4D", fontSize: 13 }}>{error}</div>
          <button onClick={refetch} style={{ background: "#12244E", border: "1px solid #00C9A7", color: "#00C9A7", padding: "6px 20px", borderRadius: 6, cursor: "pointer", fontSize: 12 }}>Retry</button>
        </div>
      )}

      {graph && !loading && (
        <>
          <SigmaContainer<NodeAttrs, EdgeAttrs> graph={graph} style={{ width: "100%", height: "100%", background: "#060C1E" }} settings={{ defaultEdgeType: "arrow" }}>
            <GraphController onNodeClick={onNodeClick} setTooltip={setTooltip} animateFlowRef={animateFlowRef} animateFlowFn={animateFlow} />
          </SigmaContainer>

          {/* Toolbar */}
          <div style={{ position: "absolute", top: 12, right: 12 }}>
            <button onClick={() => { setAnimDone(false); setTimeout(() => { animateFlowRef.current?.(); setAnimDone(true); }, 50); }}
              style={{ background: "rgba(6,12,30,0.9)", border: "1px solid #1D3060", color: "#B0BED0", padding: "5px 14px", borderRadius: 6, cursor: "pointer", fontSize: 11, backdropFilter: "blur(6px)" }}>
              ▶ Replay flow
            </button>
          </div>

          {/* Legend */}
          <div style={{ position: "absolute", bottom: 52, right: 12, background: "rgba(6,12,30,0.9)", border: "1px solid #12244E", borderRadius: 8, padding: "10px 14px", display: "flex", flexDirection: "column", gap: 6, backdropFilter: "blur(6px)" }}>
            {([["Critical", RISK_COLOR.critical], ["High", RISK_COLOR.high], ["Medium", RISK_COLOR.medium], ["Clean/origin", RISK_COLOR.low]] as [string,string][]).map(([l, c]) => (
              <div key={l} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: c, flexShrink: 0 }} />
                <span style={{ color: "#8899AA", fontSize: 10 }}>{l}</span>
              </div>
            ))}
          </div>

          {/* Typology badge */}
          <div style={{ position: "absolute", bottom: 12, left: 12, background: "rgba(6,12,30,0.9)", border: "1px solid #12244E", borderRadius: 6, padding: "6px 12px", display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "#B0BED0", backdropFilter: "blur(6px)" }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#FF4D4D", flexShrink: 0, boxShadow: "0 0 6px #FF4D4D", display: "inline-block" }} />
            Round-trip Layering · 3 hops · ₹47.2L · GNN 94%
          </div>

          {/* Tooltip */}
          {tooltip.visible && (
            <div style={{ position: "absolute", background: "rgba(18,36,78,0.97)", border: "1px solid #00C9A7", borderRadius: 10, padding: "12px 14px", minWidth: 210, zIndex: 100, pointerEvents: "none", backdropFilter: "blur(8px)", boxShadow: "0 4px 24px rgba(0,0,0,0.5)", ...tooltipStyle() }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span style={{ fontFamily: "DM Mono, monospace", fontSize: 13, fontWeight: 600, color: "#F0F4F8" }}>{tooltip.accountId}</span>
                <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 20, background: (RISK_COLOR[tooltip.riskLevel] ?? "#888") + "22", color: RISK_COLOR[tooltip.riskLevel] ?? "#888", border: `1px solid ${RISK_COLOR[tooltip.riskLevel] ?? "#888"}` }}>
                  {tooltip.riskLevel.toUpperCase()}
                </span>
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <tbody>
                  {([["Risk score", `${tooltip.riskScore}%`, RISK_COLOR[tooltip.riskLevel]], ["Amount", `₹${(tooltip.totalAmount/100000).toFixed(2)}L`, "#F0F4F8"], ["Account", tooltip.accountType, "#B0BED0"], ["Dormant", tooltip.isDormant ? "Yes ⚠" : "No", tooltip.isDormant ? "#FFB300" : "#B0BED0"]] as [string,string,string][]).map(([k,v,c]) => (
                    <tr key={k}>
                      <td style={{ color: "#8899AA", fontSize: 11, padding: "3px 0", paddingRight: 14 }}>{k}</td>
                      <td style={{ fontSize: 11, fontWeight: 500, textAlign: "right", color: c }}>{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ marginTop: 10, fontSize: 9, color: "#00C9A7", textAlign: "center", fontStyle: "italic" }}>Click to open entity profile →</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <div style={{ position: "relative", width: 40, height: 40 }}>
      {[0,60,120,180,240,300].map((deg) => (
        <div key={deg} style={{ position: "absolute", top: "50%", left: "50%", width: 5, height: 5, borderRadius: "50%", background: "#00C9A7", transformOrigin: "0 0", transform: `rotate(${deg}deg) translateY(-16px)`, animation: "spin-fade 1s infinite ease-in-out", animationDelay: `${(deg/360).toFixed(2)}s` }} />
      ))}
    </div>
  );
}
