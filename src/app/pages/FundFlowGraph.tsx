import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router';
import { ArrowLeft, Loader2 } from 'lucide-react';
import GraphNode from '../components/GraphNode';
import FlowArrow from '../components/FlowArrow';
import NodeTooltip from '../components/NodeTooltip';
import { useAlertDetail, useAlerts } from '../../hooks/useAlerts';
import { usePersistCaseContext } from '../../hooks/useCaseContext';
import { useSelectedCaseId } from '../../hooks/useSelectedCaseId';
import { pathWithCase } from '../../lib/selectedCase';
import { subgraphToLayout, formatAmount } from '../../lib/subgraphLayout';

export default function FundFlowGraph() {
  const navigate = useNavigate();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const { caseId, setCaseId } = useSelectedCaseId();
  const { alerts } = useAlerts();
  const { detail, loading, error } = useAlertDetail(caseId || null);
  usePersistCaseContext(caseId || null, detail);

  const hoveredGraphNode = useMemo(
    () => detail?.subgraph?.nodes?.find((n) => n.id === hoveredNode),
    [detail, hoveredNode],
  );

  const { nodes, arrows } = useMemo(
    () => subgraphToLayout(detail?.subgraph, detail?.typology, 'full'),
    [detail],
  );

  const sortedEdges = useMemo(() => {
    const edges = detail?.subgraph?.edges || [];
    return [...edges].sort((a, b) => (b.amount || 0) - (a.amount || 0));
  }, [detail]);

  const handleCaseChange = (id: string) => {
    setCaseId(id);
    navigate(pathWithCase('/graph', id), { replace: true });
  };

  const handleNodeHover = (nodeId: string | null, x?: number, y?: number) => {
    setHoveredNode(nodeId);
    if (nodeId && x !== undefined && y !== undefined) {
      setTooltipPosition({ x, y });
    }
  };

  const handleNodeClick = (nodeId: string) => {
    const id = nodeId.replace('-return', '');
    if (id === 'EXTERNAL') return;
    navigate(`/entity/${id}`);
  };

  if (!caseId && !loading) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4 p-8">
        <p className="text-gray-700 text-sm">No cases available. Seed demo data first.</p>
        <button type="button" onClick={() => navigate('/')} className="px-4 py-2 border rounded text-sm">
          Back to dashboard
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#E31E24]" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4 p-8">
        <p className="text-gray-700 text-sm">{error || `Case ${caseId} not found`}</p>
        <button type="button" onClick={() => navigate('/')} className="px-4 py-2 border rounded text-sm">
          Back to dashboard
        </button>
      </div>
    );
  }

  const hubNode = detail.subgraph?.nodes?.find((n) => n.is_hub);

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="h-[64px] bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Back to dashboard"
          >
            <ArrowLeft className="w-5 h-5 text-gray-700" />
          </button>
          <div>
            <h1 className="text-gray-900 text-lg font-bold" style={{ fontFamily: 'Syne' }}>
              Fund Flow Graph
            </h1>
            <p className="text-gray-600 text-xs">{detail.typology}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-gray-500" htmlFor="case-select">
            Case
          </label>
          <select
            id="case-select"
            value={caseId}
            onChange={(e) => handleCaseChange(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white min-w-[160px]"
            style={{ fontFamily: 'DM Mono' }}
          >
            {alerts.map((a) => (
              <option key={a.case_id} value={a.case_id}>
                {a.case_id}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => navigate(pathWithCase('/str-generation', caseId))}
            className="px-3 py-1.5 text-xs bg-[#E31E24] text-white rounded-lg hover:bg-[#c91920]"
          >
            Generate STR
          </button>
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="flex-1 relative bg-gradient-to-br from-gray-50 via-white to-gray-100">
          {nodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500 text-sm">
              No graph nodes for this case.
            </div>
          ) : (
            <svg className="w-full h-full">
              <defs>
                <marker id="arrowhead-teal-g" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L0,6 L9,3 z" fill="#00C9A7" opacity="0.7" />
                </marker>
                <marker id="arrowhead-red-g" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L0,6 L9,3 z" fill="#EF4444" opacity="0.8" />
                </marker>
                <filter id="amber-glow-g" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                  <feMerge>
                    <feMergeNode in="coloredBlur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
                <filter id="red-glow-g" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="6" result="coloredBlur" />
                  <feMerge>
                    <feMergeNode in="coloredBlur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>

              {arrows.map((arrow) => (
                <FlowArrow key={arrow.id} {...arrow} />
              ))}

              {nodes.map((node) => (
                <GraphNode
                  key={node.id}
                  {...node}
                  onHover={handleNodeHover}
                  onClick={handleNodeClick}
                />
              ))}
            </svg>
          )}

          {hoveredNode && (
            <NodeTooltip
              nodeId={hoveredNode}
              x={tooltipPosition.x}
              y={tooltipPosition.y}
              node={hoveredGraphNode}
            />
          )}

          {hubNode && (
            <div className="absolute left-1/2 top-[calc(50%+2.5rem)] -translate-x-1/2 pointer-events-none">
              <div className="px-2 py-1 bg-[#E31E24] text-white text-[10px] font-bold rounded flex items-center gap-1" style={{ fontFamily: 'Syne' }}>
                <div className="w-1.5 h-1.5 rounded-full bg-white" />
                CRITICAL HUB
              </div>
            </div>
          )}
        </div>

        <aside className="w-[300px] border-l border-gray-200 bg-white flex flex-col shrink-0">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-sm font-bold text-gray-900" style={{ fontFamily: 'Syne' }}>
              Transaction flow
            </h2>
            <p className="text-xs text-gray-500 mt-1">
              Top transfers · amounts on largest edges in graph
            </p>
          </div>
          <div className="flex-1 overflow-auto p-3 space-y-2">
            {sortedEdges.slice(0, 15).map((edge, i) => (
              <div
                key={edge.transaction_id || `${edge.source}-${edge.target}-${i}`}
                className="p-2.5 rounded-lg border border-gray-100 bg-gray-50 text-xs"
                style={{ fontFamily: 'DM Mono' }}
              >
                <div className="flex justify-between gap-2 mb-1">
                  <span className="text-[#E31E24] font-bold">{formatAmount(edge.amount)}</span>
                  <span className="text-gray-500">{edge.channel}</span>
                </div>
                <div className="text-gray-700">
                  {edge.source} → {edge.target}
                </div>
                {edge.timestamp && (
                  <div className="text-gray-400 mt-0.5">{String(edge.timestamp).slice(11, 19) || edge.timestamp}</div>
                )}
              </div>
            ))}
          </div>
          <div className="p-4 border-t border-gray-200 text-xs text-gray-600" style={{ fontFamily: 'DM Mono' }}>
            <div>{detail.hops} hops · {formatAmount(detail.total_amount)} total</div>
            <div className="mt-1">GNN {detail.confidence}</div>
          </div>
        </aside>
      </div>
    </div>
  );
}
