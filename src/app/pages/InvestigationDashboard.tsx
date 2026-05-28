import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router';
import { AlertTriangle, TrendingUp, Clock, ExternalLink, ChevronRight, Loader2 } from 'lucide-react';
import GraphNode from '../components/GraphNode';
import FlowArrow from '../components/FlowArrow';
import NodeTooltip from '../components/NodeTooltip';
import { useAlerts, useAlertDetail } from '../../hooks/useAlerts';

interface NodeData {
  id: string;
  x: number;
  y: number;
  radius: number;
  label: string;
  sublabel?: string;
  amount?: string;
  timestamp?: string;
  color: 'amber' | 'red' | 'teal' | 'teal-dashed';
  glow?: boolean;
  critical?: boolean;
}

interface ArrowData {
  id: string;
  from: { x: number; y: number };
  to: { x: number; y: number };
  amount: string;
  color?: 'teal' | 'red';
  curved?: boolean;
}

// Format amount for display: 4723000 → "₹47.2L"
function formatAmount(amount: number): string {
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`;
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;
  return `₹${amount}`;
}

// Map risk_level to priority label
function riskToPriority(risk: string): string {
  if (risk === 'critical') return 'critical';
  if (risk === 'high' || risk === 'critical') return 'high';
  return 'medium';
}

// Convert API subgraph to SVG node positions for the visualization
function subgraphToNodes(detail: any): { nodes: NodeData[]; arrows: ArrowData[] } {
  if (!detail?.subgraph?.nodes?.length) {
    return { nodes: [], arrows: [] };
  }

  const apiNodes = detail.subgraph.nodes;
  const apiEdges = detail.subgraph.edges;

  // Compute layout positions based on node roles
  const originNode = apiNodes.find((n: any) => n.is_origin);
  const hubNode = apiNodes.find((n: any) => n.is_hub);
  const others = apiNodes.filter((n: any) => !n.is_origin && !n.is_hub);

  const svgNodes: NodeData[] = [];

  // Place origin at left
  if (originNode) {
    svgNodes.push({
      id: originNode.id,
      x: 15, y: 50, radius: 28,
      label: originNode.id,
      sublabel: originNode.is_dormant ? 'Dormant→Active' : undefined,
      color: 'amber', glow: true,
    });
  }

  // Place intermediaries in a grid
  const leftIntermediaries = others.filter((_, i: number) => i < Math.ceil(others.length / 2));
  const rightIntermediaries = others.filter((_, i: number) => i >= Math.ceil(others.length / 2));

  leftIntermediaries.forEach((node: any, i: number) => {
    const yPos = 35 + (i * 30 / Math.max(leftIntermediaries.length - 1, 1));
    svgNodes.push({
      id: node.id,
      x: 32, y: leftIntermediaries.length === 1 ? 35 : yPos,
      radius: 18,
      label: node.id,
      amount: formatAmount(node.amount),
      color: 'amber',
    });
  });

  // Place hub at center
  if (hubNode) {
    svgNodes.push({
      id: hubNode.id,
      x: 50, y: 50, radius: 26,
      label: hubNode.id,
      amount: `Hub ${formatAmount(hubNode.amount)}`,
      color: 'red', glow: true, critical: true,
    });
  }

  rightIntermediaries.forEach((node: any, i: number) => {
    const yPos = 35 + (i * 30 / Math.max(rightIntermediaries.length - 1, 1));
    svgNodes.push({
      id: node.id,
      x: 68, y: rightIntermediaries.length === 1 ? 35 : yPos,
      radius: 18,
      label: node.id,
      amount: formatAmount(node.amount),
      color: 'amber',
    });
  });

  // Return node at right (for round-trip patterns)
  if (originNode && detail.typology?.includes('Round-trip')) {
    svgNodes.push({
      id: `${originNode.id}-return`,
      x: 85, y: 50, radius: 24,
      label: originNode.id,
      sublabel: 'Origin ← Return',
      color: 'teal-dashed',
    });
  }

  // Build arrows from edges
  const nodeMap: Record<string, NodeData> = {};
  svgNodes.forEach(n => { nodeMap[n.id] = n; });

  const svgArrows: ArrowData[] = [];
  apiEdges.forEach((edge: any, i: number) => {
    const fromNode = nodeMap[edge.source];
    const toNode = nodeMap[edge.target];
    if (fromNode && toNode) {
      svgArrows.push({
        id: `edge-${i}`,
        from: { x: fromNode.x, y: fromNode.y },
        to: { x: toNode.x, y: toNode.y },
        amount: formatAmount(edge.amount),
      });
    }
  });

  return { nodes: svgNodes, arrows: svgArrows };
}

export default function InvestigationDashboard() {
  const navigate = useNavigate();
  const [selectedAlert, setSelectedAlert] = useState<string>('CASE-2847');
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  // Fetch alerts from API
  const { alerts, loading: alertsLoading } = useAlerts();
  // Fetch selected alert detail for subgraph
  const { detail } = useAlertDetail(selectedAlert);

  // Convert API data to SVG visualization
  const { nodes, arrows } = useMemo(() => subgraphToNodes(detail), [detail]);

  // Get the currently selected case data
  const selectedCase = useMemo(() => {
    if (detail) return detail;
    return alerts.find(a => a.case_id === selectedAlert);
  }, [detail, alerts, selectedAlert]);

  const handleNodeHover = (nodeId: string | null, x?: number, y?: number) => {
    setHoveredNode(nodeId);
    if (nodeId && x !== undefined && y !== undefined) {
      setTooltipPosition({ x, y });
    }
  };

  const handleNodeClick = (nodeId: string) => {
    navigate(`/entity/${nodeId}`);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-[#EF4444]';
      case 'high':
        return 'bg-[#F59E0B]';
      case 'medium':
        return 'bg-[#3B82F6]';
      default:
        return 'bg-[#6B7280]';
    }
  };

  const timeAgo = (created: string, idx: number) => {
    const offsets = ['2m ago', '8m ago', '14m ago', '22m ago', '31m ago'];
    return offsets[idx] || `${idx * 5 + 2}m ago`;
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Top Bar */}
      <div className="h-[64px] bg-white border-b border-gray-200 flex items-center justify-between px-8">
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-gray-900 text-lg font-bold" style={{ fontFamily: 'Syne' }}>
              FundLens AML Platform
            </h1>
            <p className="text-gray-600 text-xs">Union Bank of India · Investigation Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-gray-600 text-xs">System Active</span>
          </div>
          <div className="text-gray-600 text-xs" style={{ fontFamily: 'DM Mono' }}>
            {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>

      {/* 3-Column Layout */}
      <div className="flex h-[calc(100vh-64px)]">
        {/* LEFT COLUMN: Alert Queue */}
        <div className="w-[320px] bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-gray-900 font-bold text-sm mb-1" style={{ fontFamily: 'Syne' }}>
              Active Alerts
            </h2>
            <p className="text-gray-600 text-xs">GNN-detected patterns requiring review</p>
          </div>

          <div className="flex-1 overflow-auto">
            {alertsLoading ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
              </div>
            ) : (
              alerts.map((alert, idx) => (
                <div
                  key={alert.case_id}
                  onClick={() => setSelectedAlert(alert.case_id)}
                  className={`p-4 border-b border-gray-200 cursor-pointer transition-colors ${
                    selectedAlert === alert.case_id
                      ? 'bg-gray-50 border-l-2 border-l-[#E31E24]'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${getPriorityColor(riskToPriority(alert.risk_level))}`} />
                      <span
                        className="text-gray-900 text-xs font-bold"
                        style={{ fontFamily: 'DM Mono' }}
                      >
                        {alert.case_id}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-gray-600">
                      <Clock className="w-3 h-3" />
                      <span className="text-xs">{timeAgo(alert.created_at, idx)}</span>
                    </div>
                  </div>

                  <div className="text-gray-900 text-sm mb-2">{alert.typology}</div>

                  <div
                    className="flex items-center justify-between text-xs mb-2"
                    style={{ fontFamily: 'DM Mono' }}
                  >
                    <span className="text-gray-600">{alert.accounts_count} accounts</span>
                    <span className="text-gray-900 font-bold">{formatAmount(alert.total_amount)}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-[#E31E24]" />
                      <span className="text-[#E31E24] text-xs font-bold">
                        {alert.confidence} confidence
                      </span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-600" />
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-600" style={{ fontFamily: 'DM Mono' }}>
              <div className="flex justify-between mb-1">
                <span>Alerts today:</span>
                <span className="text-gray-900">47</span>
              </div>
              <div className="flex justify-between">
                <span>Under review:</span>
                <span className="text-gray-900">{alerts.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* CENTER COLUMN: Graph Visualization */}
        <div className="flex-1 relative bg-gradient-to-br from-gray-50 to-gray-100 border-x border-gray-200">
          <svg className="w-full h-full">
            <defs>
              <marker
                id="arrowhead-teal"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
                markerUnits="strokeWidth"
              >
                <path d="M0,0 L0,6 L9,3 z" fill="#00C9A7" opacity="0.55" />
              </marker>
              <marker
                id="arrowhead-red"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
                markerUnits="strokeWidth"
              >
                <path d="M0,0 L0,6 L9,3 z" fill="#EF4444" opacity="0.7" />
              </marker>

              <filter id="amber-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <filter id="red-glow" x="-50%" y="-50%" width="200%" height="200%">
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

          {hoveredNode && (
            <NodeTooltip nodeId={hoveredNode} x={tooltipPosition.x} y={tooltipPosition.y} />
          )}

          {/* Critical chip for hub node */}
          {nodes.some(n => n.critical) && (
            <div className="absolute left-[50%] top-[calc(50%+40px)] -translate-x-1/2 pointer-events-none">
              <div
                className="px-2 py-1 bg-[#EF4444] text-white text-[10px] font-bold rounded flex items-center gap-1"
                style={{ fontFamily: 'Syne' }}
              >
                <div className="w-1.5 h-1.5 rounded-full bg-white" />
                CRITICAL
              </div>
            </div>
          )}

          {/* Bottom-Left: Typology */}
          <div className="absolute bottom-6 left-6 w-[260px] bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-xs text-gray-600 mb-3">Typology detected</div>
            <div className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-md mb-3">
              <div className="w-2 h-2 rounded-full bg-[#E31E24]" />
              <span className="text-sm text-gray-900 font-medium">
                {selectedCase && 'typology' in selectedCase ? selectedCase.typology : 'Loading...'}
              </span>
            </div>
            <div className="space-y-2 text-xs" style={{ fontFamily: 'DM Mono' }}>
              <div className="text-gray-600">
                <span className="text-gray-900">{selectedCase && 'hops' in selectedCase ? selectedCase.hops : '-'} hops</span> · <span className="text-gray-900">{selectedCase ? formatAmount(selectedCase.total_amount) : '-'}</span> cycled
              </div>
              <div className="text-gray-600">
                <span className="text-gray-900">{selectedCase && 'duration_display' in selectedCase ? (selectedCase as any).duration_display : (selectedCase as any)?.duration || '-'}</span> · GNN confidence{' '}
                <span className="text-[#E31E24] font-bold">{selectedCase?.confidence || '-'}</span>
              </div>
            </div>
          </div>

          {/* Bottom-Right: Legend */}
          <div className="absolute bottom-6 right-6 bg-white border border-gray-200 rounded-lg p-4">
            <div className="space-y-2 text-xs" style={{ fontFamily: 'DM Mono' }}>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#EF4444]" />
                <span className="text-gray-600">Critical</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#F59E0B]" />
                <span className="text-gray-600">Medium</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#E31E24]" />
                <span className="text-gray-600">Origin/clean</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-[1px] border-t border-dashed border-[#E31E24]" />
                <span className="text-gray-600">Return path</span>
              </div>
            </div>
          </div>

          {/* Expand button */}
          <button
            onClick={() => navigate('/graph')}
            className="absolute top-6 right-6 px-3 py-2 bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors rounded text-xs flex items-center gap-2"
          >
            <ExternalLink className="w-3 h-3" />
            Expand view
          </button>
        </div>

        {/* RIGHT COLUMN: Case Details */}
        <div className="w-[340px] bg-white border-l border-gray-200 flex flex-col overflow-auto">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-gray-900 font-bold text-sm" style={{ fontFamily: 'Syne' }}>
                Case Details
              </h2>
              <div className="px-2 py-1 bg-[#E31E24] text-white text-[10px] font-bold rounded">
                {(selectedCase?.risk_level || 'CRITICAL').toUpperCase()}
              </div>
            </div>
            <p
              className="text-gray-600 text-xs"
              style={{ fontFamily: 'DM Mono' }}
            >
              {selectedAlert}
            </p>
          </div>

          <div className="flex-1 p-4 space-y-4">
            {/* Key Metrics */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs text-gray-600 mb-3 font-semibold">Key Metrics</h3>
              <div className="space-y-3 text-sm" style={{ fontFamily: 'DM Mono' }}>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total amount:</span>
                  <span className="text-gray-900 font-bold">₹{selectedCase ? selectedCase.total_amount.toLocaleString('en-IN') : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Accounts:</span>
                  <span className="text-gray-900">{selectedCase?.accounts_count || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Hops:</span>
                  <span className="text-gray-900">{selectedCase?.hops || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Duration:</span>
                  <span className="text-gray-900">{selectedCase && 'duration_display' in selectedCase ? (selectedCase as any).duration_display : (selectedCase as any)?.duration || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Risk score:</span>
                  <span className="text-[#E31E24] font-bold">{selectedCase?.confidence || '-'}</span>
                </div>
              </div>
            </div>

            {/* Accounts Involved */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs text-gray-600 mb-3 font-semibold">Accounts Involved</h3>
              <div className="space-y-2">
                {(detail?.subgraph?.nodes || []).slice(0, 4).map((node: any) => (
                  <div
                    key={node.id}
                    onClick={() => navigate(`/entity/${node.id}`)}
                    className="flex items-center justify-between p-2 bg-white rounded hover:bg-gray-100 cursor-pointer transition-colors border border-gray-100"
                  >
                    <div>
                      <div
                        className="text-gray-900 text-xs font-bold"
                        style={{ fontFamily: 'DM Mono' }}
                      >
                        {node.id}
                      </div>
                      <div className="text-gray-600 text-xs">
                        {node.is_origin ? 'Origin' : node.is_hub ? 'Hub' : 'Intermediary'}
                      </div>
                    </div>
                    <div
                      className={`w-2 h-2 rounded-full ${
                        node.risk_level === 'critical'
                          ? 'bg-[#E31E24]'
                          : node.risk_level === 'high'
                          ? 'bg-[#F59E0B]'
                          : 'bg-[#3B82F6]'
                      }`}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Regulatory Info */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs text-gray-600 mb-3 font-semibold">Regulatory Reference</h3>
              <div className="space-y-2 text-xs" style={{ fontFamily: 'DM Mono' }}>
                <div className="text-gray-900 font-medium">{(detail as any)?.pmla_section || 'PMLA Section 16'}</div>
                <div className="text-gray-900 font-medium">{(detail as any)?.fatf_reference || 'FATF Typology 12'}</div>
                <div className="text-gray-600">{selectedCase?.typology || 'Loading...'}</div>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2">
              <button
                onClick={() => navigate('/str-generation')}
                className="w-full px-4 py-3 bg-[#E31E24] text-white hover:bg-[#d4183d] transition-colors rounded font-bold text-sm"
                style={{ fontFamily: 'Syne' }}
              >
                Generate STR Report
              </button>
              <button
                onClick={() => {
                  const firstNode = detail?.subgraph?.nodes?.[0];
                  navigate(`/entity/${firstNode?.id || 'ACC-0041'}`);
                }}
                className="w-full px-4 py-3 border border-gray-300 text-gray-900 hover:bg-gray-50 transition-colors rounded text-sm"
              >
                View Entity Details
              </button>
              <button className="w-full px-4 py-3 border border-gray-300 text-gray-900 hover:bg-gray-50 transition-colors rounded text-sm">
                Assign to Investigator
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
