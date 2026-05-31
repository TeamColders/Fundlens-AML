import { useMemo } from 'react';
import { useAlertDetail } from '../../hooks/useAlerts';
import { subgraphToLayout } from '../../lib/subgraphLayout';
import GraphNode from './GraphNode';
import FlowArrow from './FlowArrow';

interface MiniFlowGraphProps {
  caseId?: string;
}

export default function MiniFlowGraph({ caseId }: MiniFlowGraphProps) {
  const { detail, loading } = useAlertDetail(caseId || null);
  const { nodes, arrows } = useMemo(
    () => subgraphToLayout(detail?.subgraph, detail?.typology, 'mini'),
    [detail],
  );

  const hubId = detail?.subgraph?.nodes?.find((n) => n.is_hub)?.id;
  const originId = detail?.subgraph?.nodes?.find((n) => n.is_origin)?.id;

  if (loading) {
    return (
      <div
        className="bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center text-gray-500 text-xs"
        style={{ height: '340px' }}
      >
        Loading fund flow…
      </div>
    );
  }

  if (!nodes.length) {
    return (
      <div
        className="bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center text-gray-500 text-xs"
        style={{ height: '340px' }}
      >
        {caseId ? 'No subgraph for this case' : 'Select a case to preview the fund flow'}
      </div>
    );
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 relative" style={{ height: '340px' }}>
      <svg className="w-full h-full">
        <defs>
          <marker id="mini-arrowhead-red" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0,0 L0,8 L8,4 z" fill="#EF4444" opacity="0.7" />
          </marker>
          <marker id="mini-arrowhead-teal" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0,0 L0,8 L8,4 z" fill="#00C9A7" opacity="0.5" />
          </marker>
          <filter id="mini-amber-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="mini-red-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {arrows.map((arrow) => (
          <FlowArrow key={arrow.id} {...arrow} color={arrow.color || 'red'} />
        ))}

        {nodes.map((node) => (
          <GraphNode key={node.id} {...node} />
        ))}
      </svg>

      <div
        className="absolute bottom-2 left-2 right-2 flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-gray-600 bg-white/90 rounded px-2 py-1 border border-gray-100"
        style={{ fontFamily: 'DM Mono' }}
      >
        <span>
          <span className="text-[#F59E0B] font-bold">●</span> Account
        </span>
        {originId && (
          <span>
            <span className="text-[#F59E0B] font-bold">●</span> Origin {originId}
          </span>
        )}
        {hubId && (
          <span>
            <span className="text-[#E31E24] font-bold">●</span> Hub {hubId}
          </span>
        )}
        <span className="text-gray-400">Top flows only · {detail?.accounts_count ?? nodes.length} accts</span>
      </div>
    </div>
  );
}
