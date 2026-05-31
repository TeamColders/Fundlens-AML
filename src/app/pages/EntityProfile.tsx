import { useEffect, useState } from 'react';
import { ArrowLeft, Plus, Flag, Eye, AlertTriangle } from 'lucide-react';
import { useNavigate, useParams } from 'react-router';
import { api, type Entity } from '../../services/api';

function riskScore(entity: Entity): number {
  if (entity.risk_level === 'high')   return 87;
  if (entity.risk_level === 'medium') return 55;
  return 28;
}

function riskColor(level: string | null) {
  if (level === 'high')   return 'text-[#E31E24]';
  if (level === 'medium') return 'text-[#F59E0B]';
  return 'text-gray-600';
}

function formatVolume(v: number | null): string {
  if (!v) return '—';
  if (v >= 10_000_000) return `₹${(v / 10_000_000).toFixed(2)} Cr`;
  if (v >= 100_000)    return `₹${(v / 100_000).toFixed(2)} L`;
  return `₹${v.toLocaleString('en-IN')}`;
}

function initials(owner: string | null): string {
  if (!owner) return '??';
  return owner.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
}

// Static transactions — backend has no transaction history endpoint yet
const STATIC_TRANSACTIONS = [
  { date: '2026-03-19', time: '14:23', counterparty: 'ACC-0112', amount: '₹7,80,000', channel: 'NEFT', flagged: true },
  { date: '2026-03-19', time: '14:28', counterparty: 'ACC-0203', amount: '₹9,10,000', channel: 'UPI',  flagged: true },
  { date: '2026-03-19', time: '15:12', counterparty: 'ACC-0317', amount: '₹6,45,000', channel: 'IMPS', flagged: true },
  { date: '2026-03-19', time: '16:08', counterparty: 'ACC-0455', amount: '₹8,90,000', channel: 'NEFT', flagged: true },
  { date: '2026-03-19', time: '17:22', counterparty: 'ACC-0089', amount: '₹4,28,000', channel: 'UPI',  flagged: true },
  { date: '2023-12-15', time: '10:45', counterparty: 'Utility Bill',   amount: '₹1,240',  channel: 'Bill Pay', flagged: false },
  { date: '2023-12-08', time: '14:20', counterparty: 'Salary Credit',  amount: '₹45,000', channel: 'NEFT',     flagged: false },
  { date: '2023-11-28', time: '09:15', counterparty: 'Grocery Store',  amount: '₹3,200',  channel: 'UPI',      flagged: false },
];

export default function EntityProfile() {
  const navigate = useNavigate();
  const { accountId } = useParams<{ accountId: string }>();

  const [entity, setEntity]   = useState<Entity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    if (!accountId) return;
    setLoading(true);
    setError(null);
    api.getEntity(accountId)
      .then(setEntity)
      .catch(() => setError('Entity not found in graph database'))
      .finally(() => setLoading(false));
  }, [accountId]);

  const score = entity ? riskScore(entity) : null;

  return (
    <div className="min-h-screen bg-white pb-20">
      {/* Breadcrumb */}
      <div className="h-[44px] bg-white border-b border-gray-200 flex items-center px-6">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-gray-700 hover:text-gray-900 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="ml-4 text-sm text-gray-700" style={{ fontFamily: 'DM Mono' }}>
          Dashboard → <span className="text-[#E31E24]">{accountId}</span>
        </div>
      </div>

      {/* Loading / Error */}
      {loading && (
        <div className="mx-6 mt-6 p-6 bg-gray-50 rounded-lg text-center text-gray-400 text-sm">
          Loading entity data…
        </div>
      )}
      {error && (
        <div className="mx-6 mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-sm text-red-600">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {error} — showing static data below
        </div>
      )}

      {/* Identity Card */}
      <div className="mx-6 mt-6 bg-gray-50 rounded-lg border-l-4 border-[#E31E24] p-6 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="w-[54px] h-[54px] rounded-full bg-[#E31E24] flex items-center justify-center">
            <span className="text-white font-bold text-xl" style={{ fontFamily: 'Syne' }}>
              {entity ? initials(entity.owner) : (accountId?.slice(0, 2).toUpperCase() ?? '??')}
            </span>
          </div>
          <div>
            <h1 className="text-gray-900 text-[18px] font-bold mb-1" style={{ fontFamily: 'Syne' }}>
              {entity?.owner ?? accountId ?? 'Unknown'}
            </h1>
            <div className="text-[13px] text-gray-700 mb-3">
              {entity?.account_type ?? 'Account'} · {accountId}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {entity?.is_dormant && (
                <span className="px-2 py-1 bg-[#F59E0B] text-white rounded text-xs font-semibold">Dormant</span>
              )}
              {entity?.kyc_tier && (
                <span className="px-2 py-1 bg-[#3B82F6] text-white rounded text-xs font-semibold">
                  KYC {entity.kyc_tier}
                </span>
              )}
              {entity?.risk_level === 'high' && (
                <span className="px-2 py-1 bg-[#E31E24] text-white rounded text-xs font-semibold">High Risk</span>
              )}
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className="text-xs text-gray-700 mb-1">Risk Score</div>
          <div className="flex items-center gap-3 mb-2">
            <span className={`text-4xl font-bold ${riskColor(entity?.risk_level ?? null)}`} style={{ fontFamily: 'Syne' }}>
              {score ?? '—'}
            </span>
            {entity?.risk_level && (
              <span className={`px-3 py-1 text-white rounded text-sm font-bold capitalize ${
                entity.risk_level === 'high' ? 'bg-[#E31E24]' :
                entity.risk_level === 'medium' ? 'bg-[#F59E0B]' : 'bg-gray-400'
              }`}>
                {entity.risk_level}
              </span>
            )}
          </div>
          <div className="text-[11px] text-gray-700">
            Total volume: <span className="font-bold">{formatVolume(entity?.total_volume ?? null)}</span>
          </div>
        </div>
      </div>

      {/* Main 3-Column Layout */}
      <div className="mx-6 mt-6 grid grid-cols-[320px_1fr_320px] gap-6">

        {/* LEFT: Account Metrics */}
        <div className="space-y-6">
          <div>
            <h3 className="text-sm text-gray-700 mb-3">Account metrics</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">Account type</div>
                <div className="text-gray-900 text-sm font-bold" style={{ fontFamily: 'Syne' }}>
                  {entity?.account_type ?? '—'}
                </div>
              </div>
              <div className="bg-white border border-[#E31E24] rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">Total volume</div>
                <div className="text-[#E31E24] text-sm font-bold" style={{ fontFamily: 'Syne' }}>
                  {formatVolume(entity?.total_volume ?? null)}
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">KYC tier</div>
                <div className="text-gray-900 text-sm font-bold" style={{ fontFamily: 'Syne' }}>
                  {entity?.kyc_tier ?? '—'}
                </div>
              </div>
              <div className={`bg-white rounded-lg p-4 border ${entity?.is_dormant ? 'border-[#F59E0B]' : 'border-gray-200'}`}>
                <div className="text-xs text-gray-700 mb-1">Dormant</div>
                <div className={`text-sm font-bold ${entity?.is_dormant ? 'text-[#F59E0B]' : 'text-gray-900'}`} style={{ fontFamily: 'Syne' }}>
                  {entity ? (entity.is_dormant ? 'Yes' : 'No') : '—'}
                </div>
              </div>
            </div>
          </div>

          {/* Peer Comparison */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm text-gray-700 mb-4">Peer comparison</h3>
            <div className="space-y-4">
              {[
                { label: 'Txn frequency', peer: 70, account: 85 },
                { label: 'Avg amount',    peer: 60, account: 95 },
                { label: 'Counterparties',peer: 40, account: 88 },
                { label: 'Dormancy risk', peer: 20, account: entity?.is_dormant ? 92 : 15 },
                { label: 'KYC compliance',peer: 85, account: 65 },
              ].map((metric, idx) => (
                <div key={idx}>
                  <div className="flex justify-between text-xs text-gray-700 mb-1">
                    <span>{metric.label}</span>
                    <span>{metric.account}%</span>
                  </div>
                  <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div className="absolute h-full bg-[#E31E24] opacity-30 rounded-full" style={{ width: `${metric.peer}%` }} />
                    <div className="absolute h-full bg-[#E31E24] rounded-full" style={{ width: `${metric.account}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CENTER: Transaction History (static — no backend endpoint yet) */}
        <div>
          <h3 className="text-sm text-gray-700 mb-3">Transaction history</h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs" style={{ fontFamily: 'DM Mono' }}>
                <thead>
                  <tr className="bg-gray-50 text-gray-700 text-left">
                    <th className="py-3 px-3 w-4"></th>
                    <th className="py-3 px-3">Date</th>
                    <th className="py-3 px-3">Time</th>
                    <th className="py-3 px-3">Counterparty</th>
                    <th className="py-3 px-3 text-right">Amount</th>
                    <th className="py-3 px-3">Channel</th>
                    <th className="py-3 px-3">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {STATIC_TRANSACTIONS.map((txn, idx) => (
                    <tr key={idx} className={`border-t border-gray-200 hover:bg-gray-50 transition-colors ${txn.flagged ? 'bg-gray-50' : ''}`}>
                      <td className="py-2 px-3">{txn.flagged && <div className="w-2 h-2 rounded-full bg-[#E31E24]" />}</td>
                      <td className="py-2 px-3 text-gray-700">{txn.date}</td>
                      <td className="py-2 px-3 text-gray-700">{txn.time}</td>
                      <td className="py-2 px-3 text-gray-900">{txn.counterparty}</td>
                      <td className={`py-2 px-3 text-right font-bold ${txn.flagged ? 'text-[#E31E24]' : 'text-gray-900'}`}>{txn.amount}</td>
                      <td className="py-2 px-3 text-gray-700">{txn.channel}</td>
                      <td className="py-2 px-3">
                        {txn.flagged && <span className="px-2 py-1 bg-[#E31E24] text-white rounded text-[10px] font-bold">High</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bg-gray-50 px-4 py-3 text-xs text-gray-500 border-t border-gray-200">
              Showing recent transactions · Full history requires transaction endpoint
            </div>
          </div>
        </div>

        {/* RIGHT: Network & Related */}
        <div className="space-y-6">
          <div>
            <h3 className="text-sm text-gray-700 mb-3">Network connections</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <svg className="w-full h-[180px]">
                <defs>
                  <marker id="mini-marker" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L6,3 z" fill="#E31E24" opacity="0.4" />
                  </marker>
                </defs>
                <circle cx="50%" cy="50%" r="18" fill="white" stroke="#E31E24" strokeWidth="2" />
                <text x="50%" y="50%" textAnchor="middle" dy="0.35em" fill="#333" fontSize="9">{accountId?.slice(-4)}</text>
                {[
                  { x: 30, y: 20, label: '0112', color: '#F59E0B' },
                  { x: 70, y: 20, label: '0203', color: '#F59E0B' },
                  { x: 85, y: 50, label: '0089', color: '#E31E24' },
                  { x: 70, y: 80, label: '0317', color: '#F59E0B' },
                  { x: 30, y: 80, label: '0455', color: '#F59E0B' },
                  { x: 15, y: 50, label: '0521', color: '#666' },
                ].map((node, idx) => (
                  <g key={idx}>
                    <line x1="50%" y1="50%" x2={`${node.x}%`} y2={`${node.y}%`} stroke="#E31E24" strokeWidth="1" opacity="0.3" markerEnd="url(#mini-marker)" />
                    <circle cx={`${node.x}%`} cy={`${node.y}%`} r="12" fill="white" stroke={node.color} strokeWidth="2" />
                    <text x={`${node.x}%`} y={`${node.y}%`} textAnchor="middle" dy="0.35em" fill="#333" fontSize="8">{node.label}</text>
                  </g>
                ))}
              </svg>
              <button onClick={() => navigate('/graph')} className="w-full mt-3 text-[#E31E24] hover:underline text-xs flex items-center justify-center gap-1">
                <Eye className="w-3 h-3" />
                View in full graph
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-sm text-gray-700 mb-3">Investigation history</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-xs text-gray-700" style={{ fontFamily: 'DM Mono' }}>No prior STRs filed</div>
              <div className="mt-3 pt-3 border-t border-gray-200 space-y-1 text-xs text-gray-700">
                <div>• Added to dormant watch (Oct 2024)</div>
                <div>• KYC review pending (Feb 2026)</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 h-[56px] bg-white border-t border-gray-200 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 border border-gray-700 text-gray-700 hover:bg-gray-100 transition-colors rounded text-sm flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add to watchlist
          </button>
          <button className="px-4 py-2 border border-gray-700 text-gray-700 hover:bg-gray-100 transition-colors rounded text-sm flex items-center gap-2">
            <Flag className="w-4 h-4" />
            Flag for enhanced monitoring
          </button>
        </div>
        <button
          onClick={() => navigate('/str-generation')}
          className="px-6 py-2 bg-[#E31E24] text-white hover:bg-[#d4183d] transition-colors rounded text-sm font-bold"
          style={{ fontFamily: 'Syne' }}
        >
          Create investigation case ↗
        </button>
      </div>
    </div>
  );
}
