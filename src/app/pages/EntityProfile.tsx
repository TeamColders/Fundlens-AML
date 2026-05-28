import { ArrowLeft, Plus, Flag, Eye, Loader2 } from 'lucide-react';
import { useNavigate, useParams } from 'react-router';
import { useEntityProfile } from '../../hooks/useEntityProfile';

export default function EntityProfile() {
  const navigate = useNavigate();
  const { accountId } = useParams<{ accountId: string }>();
  const { entity, loading, error } = useEntityProfile(accountId || 'ACC-0041');

  // Derive display values from API data or fallback
  const ownerName = entity?.owner_name || 'Rajesh Kumar';
  const initials = ownerName.split(' ').map((n: string) => n[0]).join('').toUpperCase();
  const riskScore = entity?.risk_score || 87;
  const accountType = entity?.account_type === 'savings' ? 'Savings Account' : 'Current Account';
  const homeBranch = entity?.home_branch || 'SB-Branch Mumbai Central';

  const transactions = entity?.transactions?.length ? entity.transactions.map((txn: any) => ({
    date: txn.date,
    time: txn.time,
    counterparty: txn.counterparty,
    amount: `₹${txn.amount.toLocaleString('en-IN')}`,
    channel: txn.channel,
    flagged: txn.flagged,
  })) : [
    { date: '2026-03-19', time: '14:23', counterparty: 'ACC-0112', amount: '₹7,80,000', channel: 'NEFT', flagged: true },
    { date: '2026-03-19', time: '14:28', counterparty: 'ACC-0203', amount: '₹9,10,000', channel: 'UPI', flagged: true },
    { date: '2026-03-19', time: '15:12', counterparty: 'ACC-0317', amount: '₹6,45,000', channel: 'IMPS', flagged: true },
    { date: '2026-03-19', time: '16:08', counterparty: 'ACC-0455', amount: '₹8,90,000', channel: 'NEFT', flagged: true },
    { date: '2026-03-19', time: '17:22', counterparty: 'ACC-0089', amount: '₹4,28,000', channel: 'UPI', flagged: true },
    { date: '2026-03-19', time: '18:45', counterparty: 'ACC-0112', amount: '₹3,15,000', channel: 'NEFT', flagged: true },
    { date: '2026-03-19', time: '19:30', counterparty: 'ACC-0203', amount: '₹2,95,000', channel: 'IMPS', flagged: true },
    { date: '2026-03-19', time: '20:15', counterparty: 'ACC-0317', amount: '₹4,60,000', channel: 'UPI', flagged: true },
    { date: '2023-12-15', time: '10:45', counterparty: 'Utility Bill', amount: '₹1,240', channel: 'Bill Pay', flagged: false },
    { date: '2023-12-08', time: '14:20', counterparty: 'Salary Credit', amount: '₹45,000', channel: 'NEFT', flagged: false },
    { date: '2023-11-28', time: '09:15', counterparty: 'Grocery Store', amount: '₹3,200', channel: 'UPI', flagged: false },
    { date: '2023-11-20', time: '16:30', counterparty: 'Utility Bill', amount: '₹1,180', channel: 'Bill Pay', flagged: false },
  ];

  const avgVolume = entity?.metrics?.avg_monthly_volume
    ? `₹${entity.metrics.avg_monthly_volume.toLocaleString('en-IN')}`
    : '₹12,400';
  const currentVolume = entity?.metrics?.current_month_volume
    ? `₹${entity.metrics.current_month_volume.toLocaleString('en-IN')}`
    : '₹47,23,000';
  const deviation = entity?.metrics?.baseline_deviation || '3,800%';

  const networkNodes = entity?.network?.length ? entity.network : [
    { id: 'ACC-0112', risk_level: 'medium' },
    { id: 'ACC-0203', risk_level: 'medium' },
    { id: 'ACC-0089', risk_level: 'critical' },
    { id: 'ACC-0317', risk_level: 'medium' },
    { id: 'ACC-0455', risk_level: 'medium' },
  ];

  const relatedEntities = entity?.related_entities?.length ? entity.related_entities : [
    { name: 'Priya Kumar', relation: 'Same address', risk_score: 42 },
    { name: 'Amit Sharma', relation: 'Same mobile', risk_score: 68 },
    { name: 'ACC-0892', relation: 'Shared device login', risk_score: 81 },
  ];

  const netNodePositions = [
    { x: 30, y: 20 }, { x: 70, y: 20 }, { x: 85, y: 50 },
    { x: 70, y: 80 }, { x: 30, y: 80 }, { x: 15, y: 50 },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#E31E24]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white pb-20">
      {/* Top Bar with Breadcrumb */}
      <div className="h-[44px] bg-white border-b border-gray-200 flex items-center px-6">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-700 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="ml-4 text-sm text-gray-700" style={{ fontFamily: 'DM Mono' }}>
          Dashboard → <span className="text-gray-900">CASE-2847</span> → <span className="text-[#E31E24]">{accountId || 'ACC-0041'}</span>
        </div>
      </div>

      {/* Identity Card */}
      <div className="mx-6 mt-6 bg-gray-50 rounded-lg border-l-4 border-[#E31E24] p-6 flex justify-between items-center">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          {/* Initials Circle */}
          <div className="w-[54px] h-[54px] rounded-full bg-[#E31E24] flex items-center justify-center">
            <span className="text-white font-bold text-xl" style={{ fontFamily: 'Syne' }}>
              {initials}
            </span>
          </div>

          {/* Identity Info */}
          <div>
            <h1 className="text-gray-900 text-[18px] font-bold mb-1" style={{ fontFamily: 'Syne' }}>
              {ownerName}
            </h1>
            <div className="text-[13px] text-gray-700 mb-3">
              {accountType} · {homeBranch}
            </div>
            <div className="flex items-center gap-2">
              {entity?.is_dormant && (
                <span className="px-2 py-1 bg-[#F59E0B] text-white rounded text-xs font-semibold">
                  Dormant (26 months)
                </span>
              )}
              <span className="px-2 py-1 bg-[#3B82F6] text-white rounded text-xs font-semibold">
                KYC Tier {entity?.kyc_tier || 2}
              </span>
              {entity?.is_pep_adjacent && (
                <span className="px-2 py-1 bg-[#E31E24] text-white rounded text-xs font-semibold">
                  PEP adjacent
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right Section */}
        <div className="text-right">
          <div className="text-xs text-gray-700 mb-1">Risk Score</div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-[#E31E24] text-4xl font-bold" style={{ fontFamily: 'Syne' }}>
              {riskScore}
            </span>
            <span className="px-3 py-1 bg-[#E31E24] text-white rounded text-sm font-bold">
              {entity?.risk_level === 'critical' ? 'Critical' : 'High'}
            </span>
          </div>
          <div className="text-[11px] text-[#E31E24] mb-1">
            Last active: 14:23 today (after 26mo dormancy)
          </div>
          <div className="text-[11px] text-gray-700">
            Opened: {entity?.created_date || 'March 2019'} · PAN: XXXXX1234X (masked)
          </div>
        </div>
      </div>

      {/* Main 3-Column Layout */}
      <div className="mx-6 mt-6 grid grid-cols-[320px_1fr_320px] gap-6">
        {/* LEFT COLUMN - Account Metrics */}
        <div className="space-y-6">
          <div>
            <h3 className="text-sm text-gray-700 mb-3">Account metrics</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">Avg monthly txn volume</div>
                <div className="text-gray-900 text-lg font-bold" style={{ fontFamily: 'Syne' }}>
                  {avgVolume}
                </div>
              </div>
              <div className="bg-white border border-[#E31E24] rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">Current month</div>
                <div className="text-[#E31E24] text-lg font-bold" style={{ fontFamily: 'Syne' }}>
                  {currentVolume}
                </div>
                <div className="text-xs text-[#E31E24] mt-1">{deviation} over baseline</div>
              </div>
              <div className="bg-white border border-[#F59E0B] rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">Counterparties (30d)</div>
                <div className="text-[#F59E0B] text-lg font-bold" style={{ fontFamily: 'Syne' }}>
                  {entity?.metrics?.counterparties_30d || 8}
                </div>
                <div className="text-xs text-[#F59E0B] mt-1">Unusual for type</div>
              </div>
              <div className="bg-white border border-[#E31E24] rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">In/Out ratio</div>
                <div className="text-[#E31E24] text-lg font-bold" style={{ fontFamily: 'Syne' }}>
                  {entity?.metrics?.inbound_ratio
                    ? `${Math.round(entity.metrics.inbound_ratio * 100)}%/${Math.round(entity.metrics.outbound_ratio * 100)}%`
                    : '97%/3%'}
                </div>
                <div className="text-xs text-[#E31E24] mt-1">Nearly all inbound</div>
              </div>
            </div>
          </div>

          {/* Peer Comparison */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm text-gray-700 mb-4">Peer comparison</h3>
            <div className="space-y-4">
              {[
                { label: 'Txn frequency', peer: 70, account: 85, alert: false },
                { label: 'Avg amount', peer: 60, account: 95, alert: true },
                { label: 'Counterparties', peer: 40, account: 88, alert: true },
                { label: 'Dormancy risk', peer: 20, account: 92, alert: true },
                { label: 'KYC compliance', peer: 85, account: 65, alert: false },
              ].map((metric, idx) => (
                <div key={idx}>
                  <div className="flex justify-between text-xs text-gray-700 mb-1">
                    <span>{metric.label}</span>
                    <span>{metric.account}%</span>
                  </div>
                  <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="absolute h-full bg-[#E31E24] opacity-30 rounded-full"
                      style={{ width: `${metric.peer}%` }}
                    />
                    <div
                      className={`absolute h-full rounded-full ${
                        metric.alert ? 'bg-[#E31E24]' : 'bg-[#E31E24]'
                      }`}
                      style={{ width: `${metric.account}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-3 border-t border-gray-200 text-xs text-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-2 bg-[#E31E24] opacity-30 rounded" />
                <span>Peer average (similar accounts)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-2 bg-[#E31E24] rounded" />
                <span>This account (deviations)</span>
              </div>
            </div>
          </div>
        </div>

        {/* CENTER COLUMN - Transaction History */}
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
                  {transactions.map((txn: any, idx: number) => (
                    <tr
                      key={idx}
                      className={`border-t border-gray-200 hover:bg-gray-50 transition-colors ${
                        txn.flagged ? 'bg-gray-50' : ''
                      }`}
                    >
                      <td className="py-2 px-3">
                        {txn.flagged && <div className="w-2 h-2 rounded-full bg-[#E31E24]" />}
                      </td>
                      <td className="py-2 px-3 text-gray-700">{txn.date}</td>
                      <td className="py-2 px-3 text-gray-700">{txn.time}</td>
                      <td className="py-2 px-3 text-gray-900">{txn.counterparty}</td>
                      <td
                        className={`py-2 px-3 text-right font-bold ${
                          txn.flagged ? 'text-[#E31E24]' : 'text-gray-900'
                        }`}
                      >
                        {txn.amount}
                      </td>
                      <td className="py-2 px-3 text-gray-700">{txn.channel}</td>
                      <td className="py-2 px-3">
                        {txn.flagged && (
                          <span className="px-2 py-1 bg-[#E31E24] text-white rounded text-[10px] font-bold">
                            High
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bg-gray-50 px-4 py-3 text-xs text-gray-700 border-t border-gray-200">
              Showing {transactions.length} of 847 total transactions
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN - Network & Related */}
        <div className="space-y-6">
          {/* Network Connections */}
          <div>
            <h3 className="text-sm text-gray-700 mb-3">Network connections</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <svg className="w-full h-[180px]">
                <defs>
                  <marker id="mini-marker" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L6,3 z" fill="#E31E24" opacity="0.4" />
                  </marker>
                </defs>
                
                {/* Center node (this account) */}
                <circle cx="50%" cy="50%" r="18" fill="white" stroke="#E31E24" strokeWidth="2" />
                <text x="50%" y="50%" textAnchor="middle" dy="0.35em" fill="#333" fontSize="9">
                  {accountId || 'ACC-0041'}
                </text>
                
                {/* Connected nodes */}
                {networkNodes.slice(0, 6).map((node: any, idx: number) => {
                  const pos = netNodePositions[idx] || { x: 50, y: 50 };
                  const color = node.risk_level === 'critical' ? '#E31E24' : node.risk_level === 'high' ? '#F59E0B' : '#666';
                  return (
                    <g key={idx}>
                      <line
                        x1="50%"
                        y1="50%"
                        x2={`${pos.x}%`}
                        y2={`${pos.y}%`}
                        stroke="#E31E24"
                        strokeWidth="1"
                        opacity="0.3"
                        markerEnd="url(#mini-marker)"
                      />
                      <circle cx={`${pos.x}%`} cy={`${pos.y}%`} r="12" fill="white" stroke={color} strokeWidth="2" />
                      <text x={`${pos.x}%`} y={`${pos.y}%`} textAnchor="middle" dy="0.35em" fill="#333" fontSize="8">
                        {node.id.replace('ACC-', '')}
                      </text>
                    </g>
                  );
                })}
              </svg>
              <button
                onClick={() => navigate('/graph')}
                className="w-full mt-3 text-[#E31E24] hover:underline text-xs flex items-center justify-center gap-1"
              >
                <Eye className="w-3 h-3" />
                View in full graph
              </button>
            </div>
          </div>

          {/* Investigation History */}
          <div>
            <h3 className="text-sm text-gray-700 mb-3">Investigation history</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-xs text-gray-700" style={{ fontFamily: 'DM Mono' }}>
                No prior STRs filed
              </div>
              <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                <div className="text-xs">
                  <div className="text-gray-900 mb-1">Watch flags:</div>
                  <div className="text-gray-700">• Added to dormant watch (Oct 2024)</div>
                  <div className="text-gray-700">• KYC review pending (Feb 2026)</div>
                </div>
              </div>
            </div>
          </div>

          {/* Related Entities */}
          <div>
            <h3 className="text-sm text-gray-700 mb-3">Related entities</h3>
            <div className="space-y-2">
              {relatedEntities.map((entity: any, idx: number) => (
                <div key={idx} className="bg-white border border-gray-200 rounded-lg p-3 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="text-gray-900 text-xs font-medium">{entity.name}</div>
                    <div className="text-gray-700 text-[10px]">{entity.relation}</div>
                  </div>
                  <div className={`text-sm font-bold ${entity.risk_score >= 70 ? 'text-[#E31E24]' : 'text-[#F59E0B]'}`}>
                    {entity.risk_score}
                  </div>
                </div>
              ))}
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
        <button className="px-6 py-2 bg-[#E31E24] text-white hover:bg-[#d4183d] transition-colors rounded text-sm font-bold flex items-center gap-2"
          style={{ fontFamily: 'Syne' }}
        >
          Create investigation case ↗
        </button>
      </div>
    </div>
  );
}
