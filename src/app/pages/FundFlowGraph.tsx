import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router';
import { ArrowLeft, Download, ExternalLink, Loader2 } from 'lucide-react';
import GraphNode from '../components/GraphNode';
import FlowArrow from '../components/FlowArrow';
import NodeTooltip from '../components/NodeTooltip';
import { useGraphData } from '../../hooks/useGraphData';
import { useAlertDetail } from '../../hooks/useAlerts';

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

// Map risk_level to node style
function getNodeStyle(node: any): { color: NodeData['color'], radius: number, glow?: boolean, critical?: boolean } {
  if (node.is_hub) return { color: 'red', radius: 32, glow: true, critical: true };
  if (node.is_origin) return { color: 'amber', radius: 34, glow: true };
  if (node.risk_level === 'critical') return { color: 'red', radius: 26 };
  return { color: 'amber', radius: 22 };
}

export default function FundFlowGraph() {
  const navigate = useNavigate();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const caseId = 'CASE-2847';
  const { graphData, loading } = useGraphData(caseId);
  const { detail } = useAlertDetail(caseId);

  // Define node positions based on API graph data
  const { nodes, arrows } = useMemo(() => {
    if (!graphData?.nodes?.length) {
      return { nodes: [], arrows: [] };
    }

    const apiNodes = graphData.nodes;
    const apiEdges = graphData.edges;

    const originNode = apiNodes.find((n: any) => n.is_origin);
    const hubNode = apiNodes.find((n: any) => n.is_hub);
    const others = apiNodes.filter((n: any) => !n.is_origin && !n.is_hub);

    const svgNodes: NodeData[] = [];

    // Place origin at left
    if (originNode) {
      svgNodes.push({
        id: originNode.id,
        x: 15, y: 50, ...getNodeStyle(originNode),
        label: originNode.label,
        sublabel: originNode.is_dormant ? 'Dormant→Active' : undefined,
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
        ...getNodeStyle(node),
        label: node.id,
        amount: formatAmount(node.amount),
      });
    });

    // Place hub at center
    if (hubNode) {
      svgNodes.push({
        id: hubNode.id,
        x: 50, y: 50, ...getNodeStyle(hubNode),
        label: hubNode.id,
        amount: `Hub ${formatAmount(hubNode.amount)}`,
      });
    }

    rightIntermediaries.forEach((node: any, i: number) => {
      const yPos = 35 + (i * 30 / Math.max(rightIntermediaries.length - 1, 1));
      svgNodes.push({
        id: node.id,
        x: 68, y: rightIntermediaries.length === 1 ? 35 : yPos,
        ...getNodeStyle(node),
        label: node.id,
        amount: formatAmount(node.amount),
      });
    });

    // Return node at right
    if (originNode && detail?.typology?.includes('Round-trip')) {
      svgNodes.push({
        id: `${originNode.id}-return`,
        x: 85, y: 50, radius: 30,
        label: originNode.id,
        sublabel: 'Origin ← Return',
        color: 'teal-dashed',
      });
    }

    // Build arrows
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

    // If round-trip, add back arrow
    if (hubNode && originNode && detail?.typology?.includes('Round-trip')) {
      svgArrows.push({
        id: 'edge-return',
        from: nodeMap[hubNode.id],
        to: nodeMap[`${originNode.id}-return`],
        amount: formatAmount(originNode.amount * 0.6), // mock logic
        color: 'red',
        curved: true,
      });
    }

    return { nodes: svgNodes, arrows: svgArrows };
  }, [graphData, detail]);
  const handleNodeClick = (nodeId: string) => {
    // If it's a return node, extract original id
    const id = nodeId.replace('-return', '');
    navigate(`/entity/${id}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#E31E24]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white relative">
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

      {/* Graph Canvas */}
      <div className="relative h-[calc(100vh-64px)] overflow-hidden bg-gradient-to-br from-gray-50 via-white to-gray-100">
        <svg className="w-full h-full">
          <defs>
            {/* Arrow markers */}
            <marker
              id="arrowhead-teal"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M0,0 L0,6 L9,3 z" fill="#E31E24" opacity="0.55" />
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
              <path d="M0,0 L0,6 L9,3 z" fill="#E31E24" opacity="0.7" />
            </marker>

            {/* Glow filters */}
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

          {/* Arrows (render first, behind nodes) */}
          {arrows.map((arrow) => (
            <FlowArrow key={arrow.id} {...arrow} />
          ))}

          {/* Nodes */}
          {nodes.map((node) => (
            <GraphNode
              key={node.id}
              {...node}
              onHover={handleNodeHover}
              onClick={handleNodeClick}
            />
          ))}
        </svg>

        {/* Tooltip */}
        {hoveredNode && (
          <NodeTooltip
            nodeId={hoveredNode}
            x={tooltipPosition.x}
            y={tooltipPosition.y}
          />
        )}

        {/* Critical chip for ACC-0089 */}
        <div className="absolute left-[50%] top-[calc(50%+50px)] -translate-x-1/2 pointer-events-none">
          <div className="px-2 py-1 bg-[#E31E24] text-white text-[10px] font-bold rounded flex items-center gap-1"
            style={{ fontFamily: 'Syne' }}
          >
            <div className="w-1.5 h-1.5 rounded-full bg-white" />
            CRITICAL
          </div>
        </div>

        {/* Bottom-Left Panel: Typology */}
        <div className="absolute bottom-6 left-6 w-[280px] bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-xs text-gray-700 mb-3">Typology detected</div>
          <div className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-md mb-4">
            <div className="w-2 h-2 rounded-full bg-[#E31E24]" />
            <span className="text-sm text-gray-900 font-medium">{detail?.typology || 'Round-trip Layering'}</span>
          </div>
          <div className="space-y-2 mb-4 text-xs" style={{ fontFamily: 'DM Mono' }}>
            <div className="text-gray-700">
              <span className="text-gray-900">{detail?.hops || 3} hops</span> · <span className="text-gray-900">₹{detail ? (detail.total_amount/100000).toFixed(1) : '47.2'}L</span> cycled
            </div>
            <div className="text-gray-700">
              <span className="text-gray-900">{detail?.duration_display || '6h 14m'}</span> · GNN confidence{' '}
              <span className="text-[#E31E24]">{detail?.confidence || '94%'}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="flex-1 px-3 py-2 border border-gray-700 text-gray-700 hover:bg-gray-100 transition-colors rounded text-xs">
              Trace origin
            </button>
            <button className="flex-1 px-3 py-2 border border-gray-700 text-gray-700 hover:bg-gray-100 transition-colors rounded text-xs">
              Trace destination
            </button>
          </div>
        </div>

        {/* Bottom-Right: Legend */}
        <div className="absolute bottom-6 right-6 bg-white border border-gray-200 rounded-lg p-4">
          <div className="space-y-2 text-xs" style={{ fontFamily: 'DM Mono' }}>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#E31E24]" />
              <span className="text-gray-700">Critical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#F59E0B]" />
              <span className="text-gray-700">Medium</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#E31E24]" />
              <span className="text-gray-700">Origin/clean</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-[1px] border-t border-dashed border-[#E31E24]" />
              <span className="text-gray-700">Return path</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}