import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { AlertTriangle, TrendingUp, Clock, ExternalLink, ChevronRight, RefreshCw } from 'lucide-react';
import GraphNode from '../components/GraphNode';
import FlowArrow from '../components/FlowArrow';
import NodeTooltip from '../components/NodeTooltip';
import { api, type Alert, type Case } from '../../services/api';

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

// Priority derived from gnn_score
function scoreToPriority(score: number): 'critical' | 'high' | 'medium' {
  if (score >= 0.9) return 'critical';
  if (score >= 0.75) return 'high';
  return 'medium';
}

function priorityColor(priority: string) {
  switch (priority) {
    case 'critical': return 'bg-[#EF4444]';
    case 'high':     return 'bg-[#F59E0B]';
    default:         return 'bg-[#3B82F6]';
  }
}

function formatAmount(amount: number | null | undefined): string {
  if (!amount) return '—';
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(1)}Cr`;
  if (amount >= 100_000)    return `₹${(amount / 100_000).toFixed(1)}L`;
  return `₹${amount.toLocaleString('en-IN')}`;
}

function timeAgo(iso: string | null): string {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

// Static graph for the centre panel (layout requires x/y which backend doesn't provide)
const STATIC_NODES: NodeData[] = [
  { id: 'ACC-0041', x: 15, y: 50, radius: 28, label: 'ACC-0041', sublabel: 'Dormant→Active', timestamp: '14:23', color: 'amber', glow: true },
  { id: 'ACC-0112', x: 32, y: 35, radius: 18, label: 'ACC-0112', amount: '₹7.8L', timestamp: '14:28', color: 'amber' },
  { id: 'ACC-0203', x: 32, y: 65, radius: 18, label: 'ACC-0203', amount: '₹9.1L', timestamp: '14:31', color: 'amber' },
  { id: 'ACC-0089', x: 50, y: 50, radius: 26, label: 'ACC-0089', amount: 'Hub ₹46.8L', timestamp: '14:45', color: 'red', glow: true, critical: true },
  { id: 'ACC-0317', x: 68, y: 35, radius: 18, label: 'ACC-0317', amount: '₹8.4L', timestamp: '14:52', color: 'amber' },
  { id: 'ACC-0455', x: 68, y: 65, radius: 18, label: 'ACC-0455', amount: '₹8.9L', timestamp: '14:55', color: 'amber' },
  { id: 'ACC-0041-return', x: 85, y: 50, radius: 24, label: 'ACC-0041', sublabel: 'Origin ← Return', timestamp: '15:02', color: 'teal-dashed' },
];

const STATIC_ARROWS: ArrowData[] = [
  { id: 'a1', from: STATIC_NODES[0], to: STATIC_NODES[1], amount: '₹7.8L' },
  { id: 'a2', from: STATIC_NODES[0], to: STATIC_NODES[2], amount: '₹9.1L' },
  { id: 'a3', from: STATIC_NODES[1], to: STATIC_NODES[3], amount: '₹7.8L' },
  { id: 'a4', from: STATIC_NODES[2], to: STATIC_NODES[3], amount: '₹9.1L' },
  { id: 'a5', from: STATIC_NODES[3], to: STATIC_NODES[4], amount: '₹8.4L' },
  { id: 'a6', from: STATIC_NODES[3], to: STATIC_NODES[5], amount: '₹8.9L' },
  { id: 'a7', from: STATIC_NODES[4], to: STATIC_NODES[6], amount: '₹8.4L' },
  { id: 'a8', from: STATIC_NODES[5], to: STATIC_NODES[6], amount: '₹8.9L' },
  { id: 'a9', from: STATIC_NODES[3], to: STATIC_NODES[6], amount: '₹29.5L', color: 'red', curved: true },
];

export default function InvestigationDashboard() {
  const navigate = useNavigate();

  const [alerts, setAlerts]               = useState<Alert[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [caseDetail, setCaseDetail]       = useState<Case | null>(null);
  const [loading, setLoading]             = useState(true);
  const [error, setError]                 = useState<string | null>(null);
  const [hoveredNode, setHoveredNode]     = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  // Load alerts on mount
  useEffect(() => {
    setLoading(true);
    api.listAlerts()
      .then(({ alerts: data }) => {
        setAlerts(data);
        if (data.length > 0) setSelectedCaseId(data[0].case_id);
      })
      .catch(() => setError('Could not load alerts'))
      .finally(() => setLoading(false));
  }, []);

  // Load case detail when selection changes
  useEffect(() => {
    if (!selectedCaseId) return;
    setCaseDetail(null);
    api.getCase(selectedCaseId)
      .then(setCaseDetail)
      .catch(() => { /* case may not exist yet */ });
  }, [selectedCaseId]);

  const handleNodeHover = (nodeId: string | null, x?: number, y?: number) => {
    setHoveredNode(nodeId);
    if (nodeId && x !== undefined && y !== undefined) setTooltipPosition({ x, y });
  };

  const handleNodeClick = (nodeId: string) => navigate(`/entity/${nodeId}`);

  const selectedAlert = alerts.find(a => a.case_id === selectedCaseId) ?? null;
  const priority = selectedAlert ? scoreToPriority(selectedAlert.gnn_score) : 'medium';

  return (
    <div className="min-h-screen bg-white">
      {/* Top Bar */}
      <div className="h-[64px] bg-white border-b border-gray-200 flex items-center justify-between px-8">
        <div>
          <h1 className="text-gray-900 text-lg font-bold" style={{ fontFamily: 'Syne' }}>
            FundLens AML Platform
          </h1>
          <p className="text-gray-600 text-xs">Union Bank of India · Investigation Dashboard</p>
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

        {/* LEFT: Alert Queue */}
        <div className="w-[320px] bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-gray-900 font-bold text-sm" style={{ fontFamily: 'Syne' }}>Active Alerts</h2>
              <p className="text-gray-600 text-xs">GNN-detected patterns requiring review</p>
            </div>
            <button
              onClick={() => {
                setLoading(true);
                api.listAlerts()
                  .then(({ alerts: data }) => { setAlerts(data); })
                  .catch(() => {})
                  .finally(() => setLoading(false));
              }}
              className="text-gray-400 hover:text-gray-700 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="flex-1 overflow-auto">
            {loading && alerts.length === 0 && (
              <div className="p-6 text-center text-gray-400 text-xs">Loading alerts…</div>
            )}
            {error && (
              <div className="p-4 text-xs text-red-500 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> {error}
              </div>
            )}
            {!loading && !error && alerts.length === 0 && (
              <div className="p-6 text-center text-gray-400 text-xs">No alerts yet</div>
            )}
            {alerts.map((alert) => {
              const p = scoreToPriority(alert.gnn_score);
              return (
                <div
                  key={alert.id}
                  onClick={() => setSelectedCaseId(alert.case_id)}
                  className={`p-4 border-b border-gray-200 cursor-pointer transition-colors ${
                    selectedCaseId === alert.case_id
                      ? 'bg-gray-50 border-l-2 border-l-[#E31E24]'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${priorityColor(p)}`} />
                      <span className="text-gray-900 text-xs font-bold" style={{ fontFamily: 'DM Mono' }}>
                        {alert.case_id}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-gray-600">
                      <Clock className="w-3 h-3" />
                      <span className="text-xs">{timeAgo(alert.created_at)}</span>
                    </div>
                  </div>
                  <div className="text-gray-900 text-sm mb-2">{alert.typology}</div>
                  <div className="flex items-center justify-between text-xs mb-2" style={{ fontFamily: 'DM Mono' }}>
                    <span className="text-gray-600">
                      {alert.payload && typeof alert.payload === 'object' && 'accounts' in alert.payload
                        ? `${alert.payload.accounts} accounts`
                        : 'case alert'}
                    </span>
                    <span className="text-gray-900 font-bold">
                      {alert.payload && typeof alert.payload === 'object' && 'total_amount' in alert.payload
                        ? formatAmount(alert.payload.total_amount as number)
                        : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-[#E31E24]" />
                      <span className="text-[#E31E24] text-xs font-bold">
                        {Math.round(alert.gnn_score * 100)}% confidence
                      </span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-600" />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-600" style={{ fontFamily: 'DM Mono' }}>
              <div className="flex justify-between mb-1">
                <span>Alerts loaded:</span>
                <span className="text-gray-900">{alerts.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Critical:</span>
                <span className="text-[#E31E24]">
                  {alerts.filter(a => scoreToPriority(a.gnn_score) === 'critical').length}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* CENTER: Graph Visualization */}
        <div className="flex-1 relative bg-gradient-to-br from-gray-50 to-gray-100 border-x border-gray-200">
          <svg className="w-full h-full">
            <defs>
              <marker id="arrowhead-teal" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#00C9A7" opacity="0.55" />
              </marker>
              <marker id="arrowhead-red" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#EF4444" opacity="0.7" />
              </marker>
              <filter id="amber-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
              <filter id="red-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="6" result="coloredBlur" />
                <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
            </defs>
            {STATIC_ARROWS.map(arrow => <FlowArrow key={arrow.id} {...arrow} />)}
            {STATIC_NODES.map(node => (
              <GraphNode key={node.id} {...node} onHover={handleNodeHover} onClick={handleNodeClick} />
            ))}
          </svg>

          {hoveredNode && <NodeTooltip nodeId={hoveredNode} x={tooltipPosition.x} y={tooltipPosition.y} />}

          <div className="absolute left-[50%] top-[calc(50%+40px)] -translate-x-1/2 pointer-events-none">
            <div className="px-2 py-1 bg-[#EF4444] text-white text-[10px] font-bold rounded flex items-center gap-1" style={{ fontFamily: 'Syne' }}>
              <div className="w-1.5 h-1.5 rounded-full bg-white" />
              CRITICAL
            </div>
          </div>

          <div className="absolute bottom-6 left-6 w-[260px] bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-xs text-gray-600 mb-3">Typology detected</div>
            <div className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-md mb-3">
              <div className="w-2 h-2 rounded-full bg-[#E31E24]" />
              <span className="text-sm text-gray-900 font-medium">
                {selectedAlert?.typology ?? 'Round-trip Layering'}
              </span>
            </div>
            <div className="space-y-1 text-xs" style={{ fontFamily: 'DM Mono' }}>
              <div className="text-gray-600">
                GNN confidence{' '}
                <span className="text-[#E31E24] font-bold">
                  {selectedAlert ? `${Math.round(selectedAlert.gnn_score * 100)}%` : '—'}
                </span>
              </div>
            </div>
          </div>

          <div className="absolute bottom-6 right-6 bg-white border border-gray-200 rounded-lg p-4">
            <div className="space-y-2 text-xs" style={{ fontFamily: 'DM Mono' }}>
              <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#EF4444]" /><span className="text-gray-600">Critical</span></div>
              <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#F59E0B]" /><span className="text-gray-600">Medium</span></div>
              <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#00C9A7]" /><span className="text-gray-600">Origin/clean</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-[1px] border-t border-dashed border-[#E31E24]" /><span className="text-gray-600">Return path</span></div>
            </div>
          </div>

          <button
            onClick={() => navigate('/graph')}
            className="absolute top-6 right-6 px-3 py-2 bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors rounded text-xs flex items-center gap-2"
          >
            <ExternalLink className="w-3 h-3" />
            Expand view
          </button>
        </div>

        {/* RIGHT: Case Details */}
        <div className="w-[340px] bg-white border-l border-gray-200 flex flex-col overflow-auto">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-gray-900 font-bold text-sm" style={{ fontFamily: 'Syne' }}>Case Details</h2>
              {selectedAlert && (
                <div className={`px-2 py-1 text-white text-[10px] font-bold rounded uppercase ${priorityColor(priority)}`}>
                  {priority}
                </div>
              )}
            </div>
            <p className="text-gray-600 text-xs" style={{ fontFamily: 'DM Mono' }}>
              {selectedCaseId ?? '—'}
            </p>
          </div>

          <div className="flex-1 p-4 space-y-4">
            {/* Key Metrics — live from /api/cases/:id */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs text-gray-600 mb-3 font-semibold">Key Metrics</h3>
              {!caseDetail && selectedCaseId && (
                <div className="text-xs text-gray-400">Loading…</div>
              )}
              {caseDetail && (
                <div className="space-y-3 text-sm" style={{ fontFamily: 'DM Mono' }}>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total amount:</span>
                    <span className="text-gray-900 font-bold">{formatAmount(caseDetail.total_amount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Typology:</span>
                    <span className="text-gray-900">{caseDetail.typology ?? '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className="text-gray-900 capitalize">{caseDetail.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Created:</span>
                    <span className="text-gray-900">{timeAgo(caseDetail.created_at)}</span>
                  </div>
                  {selectedAlert && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Risk score:</span>
                      <span className="text-[#E31E24] font-bold">{Math.round(selectedAlert.gnn_score * 100)}%</span>
                    </div>
                  )}
                </div>
              )}
              {!caseDetail && !selectedCaseId && (
                <div className="text-xs text-gray-400">Select an alert to view details</div>
              )}
            </div>

            {/* Regulatory Info */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs text-gray-600 mb-3 font-semibold">Regulatory Reference</h3>
              <div className="space-y-2 text-xs" style={{ fontFamily: 'DM Mono' }}>
                <div className="text-gray-900 font-medium">PMLA Section 16</div>
                <div className="text-gray-900 font-medium">FATF Typology 12</div>
                <div className="text-gray-600">Round-trip Layering Pattern</div>
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
                onClick={() => navigate('/graph')}
                className="w-full px-4 py-3 border border-gray-300 text-gray-900 hover:bg-gray-50 transition-colors rounded text-sm"
              >
                View Fund Flow Graph
              </button>
              <button
                onClick={() => navigate('/entity/ACC-0041')}
                className="w-full px-4 py-3 border border-gray-300 text-gray-900 hover:bg-gray-50 transition-colors rounded text-sm"
              >
                View Entity Details
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
