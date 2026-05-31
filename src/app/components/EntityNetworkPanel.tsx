import { Eye } from 'lucide-react';

interface NetworkNode {
  id: string;
  risk_level: string;
}

interface EntityNetworkPanelProps {
  accountId: string;
  nodes: NetworkNode[];
  onOpenAccount: (id: string) => void;
  onViewGraph: () => void;
}

const POSITIONS = [
  { x: 30, y: 18 },
  { x: 72, y: 18 },
  { x: 88, y: 50 },
  { x: 72, y: 82 },
  { x: 30, y: 82 },
  { x: 12, y: 50 },
];

function strokeForRisk(level: string): string {
  if (level === 'critical') return '#E31E24';
  if (level === 'high') return '#F59E0B';
  return '#6B7280';
}

export default function EntityNetworkPanel({
  accountId,
  nodes,
  onOpenAccount,
  onViewGraph,
}: EntityNetworkPanelProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <svg className="w-full h-[180px]">
        <defs>
          <marker id="entity-net-arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="#E31E24" opacity="0.4" />
          </marker>
        </defs>

        <circle cx="50%" cy="50%" r="20" fill="white" stroke="#E31E24" strokeWidth="2.5" />
        <text x="50%" y="50%" textAnchor="middle" dy="0.35em" fill="#1a1a1a" fontSize="9" fontFamily="DM Mono" fontWeight="bold">
          {accountId}
        </text>

        {nodes.slice(0, 6).map((node, idx) => {
          const pos = POSITIONS[idx] || { x: 50, y: 50 };
          const color = strokeForRisk(node.risk_level);
          return (
            <g
              key={node.id}
              className="cursor-pointer"
              onClick={() => onOpenAccount(node.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onOpenAccount(node.id)}
            >
              <line
                x1="50%"
                y1="50%"
                x2={`${pos.x}%`}
                y2={`${pos.y}%`}
                stroke="#E31E24"
                strokeWidth="1"
                opacity="0.35"
                markerEnd="url(#entity-net-arrow)"
              />
              <circle cx={`${pos.x}%`} cy={`${pos.y}%`} r="14" fill="white" stroke={color} strokeWidth="2" />
              <text
                x={`${pos.x}%`}
                y={`${pos.y}%`}
                textAnchor="middle"
                dy="0.35em"
                fill="#333"
                fontSize="8"
                fontFamily="DM Mono"
              >
                {node.id}
              </text>
            </g>
          );
        })}
      </svg>
      {nodes.length === 0 && (
        <p className="text-center text-xs text-gray-500 -mt-16 mb-12">No counterparties in loaded transactions</p>
      )}
      <button
        type="button"
        onClick={onViewGraph}
        className="w-full mt-3 text-[#E31E24] hover:underline text-xs flex items-center justify-center gap-1"
      >
        <Eye className="w-3 h-3" />
        View in full graph
      </button>
    </div>
  );
}
