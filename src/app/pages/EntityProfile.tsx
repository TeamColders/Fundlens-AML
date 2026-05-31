import { useCallback, useState } from 'react';
import {
  ArrowLeft,
  Plus,
  Flag,
  ExternalLink,
  Loader2,
  Check,
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router';
import {
  addEntityToWatchlist,
  flagEntityEnhancedMonitoring,
} from '../../api/client';
import { useEntityProfile } from '../../hooks/useEntityProfile';
import { useSelectedCaseId } from '../../hooks/useSelectedCaseId';
import { formatAmount } from '../../lib/subgraphLayout';
import { pathWithCase, setStoredCaseId } from '../../lib/selectedCase';
import EntityNetworkPanel from '../components/EntityNetworkPanel';

function riskLabel(level: string): string {
  const map: Record<string, string> = {
    critical: 'Critical',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  };
  return map[level] || 'Medium';
}

export default function EntityProfile() {
  const navigate = useNavigate();
  const { accountId } = useParams<{ accountId: string }>();
  const { caseId } = useSelectedCaseId();
  const { entity, loading, error, refetch } = useEntityProfile(accountId || null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const activeCaseId = entity?.primary_case_id || caseId;

  const runAction = useCallback(
    async (fn: () => Promise<{ message: string }>) => {
      setActionLoading(true);
      setActionMsg(null);
      try {
        const res = await fn();
        setActionMsg(res.message);
        await refetch();
        setTimeout(() => setActionMsg(null), 4000);
      } catch (e) {
        setActionMsg((e as Error).message);
      } finally {
        setActionLoading(false);
      }
    },
    [refetch],
  );

  const openCase = useCallback(() => {
    if (!activeCaseId) {
      navigate('/');
      return;
    }
    setStoredCaseId(activeCaseId);
    navigate('/');
  }, [activeCaseId, navigate]);

  const openGraph = useCallback(() => {
    if (activeCaseId) {
      navigate(pathWithCase('/graph', activeCaseId));
      return;
    }
    navigate('/graph');
  }, [activeCaseId, navigate]);

  const openCounterparty = useCallback(
    (id: string) => {
      if (id.startsWith('ACC-')) {
        navigate(`/entity/${id}`);
      }
    },
    [navigate],
  );

  if (!accountId) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4 p-8">
        <p className="text-gray-700 text-sm">Open an account from the investigation graph or dashboard.</p>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="px-4 py-2 border border-gray-300 rounded text-sm"
        >
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

  if (error || !entity) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4 p-8">
        <p className="text-gray-700 text-sm">{error || `Account ${accountId} not found`}</p>
        <button type="button" onClick={() => navigate('/')} className="px-4 py-2 border rounded text-sm">
          Back to dashboard
        </button>
      </div>
    );
  }

  const ownerName = entity.owner_name;
  const initials = ownerName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
  const accountType =
    entity.account_type === 'savings' ? 'Savings Account' : entity.account_type === 'current' ? 'Current Account' : entity.account_type;
  const inboundPct = Math.round((entity.metrics.inbound_ratio || 0) * 100);
  const outboundPct = Math.round((entity.metrics.outbound_ratio || 0) * 100);
  const peerMetrics = entity.peer_comparison || [];

  return (
    <div className="min-h-screen bg-white pb-24">
      <div className="h-[44px] bg-white border-b border-gray-200 flex items-center px-6">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-700 hover:text-gray-900 transition-colors"
          aria-label="Back to dashboard"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="ml-4 text-sm text-gray-700 flex items-center gap-1" style={{ fontFamily: 'DM Mono' }}>
          <button type="button" onClick={() => navigate('/')} className="hover:text-gray-900">
            Dashboard
          </button>
          <span>→</span>
          {activeCaseId ? (
            <button type="button" onClick={openCase} className="text-gray-900 hover:underline">
              {activeCaseId}
            </button>
          ) : (
            <span className="text-gray-900">—</span>
          )}
          <span>→</span>
          <span className="text-[#E31E24]">{accountId}</span>
        </div>
      </div>

      {actionMsg && (
        <div className="mx-6 mt-3 px-4 py-2 bg-green-50 border border-green-200 rounded-lg text-green-800 text-xs flex items-center gap-2">
          <Check className="w-4 h-4 shrink-0" />
          {actionMsg}
        </div>
      )}

      <div className="mx-6 mt-6 bg-gray-50 rounded-lg border-l-4 border-[#E31E24] p-6 flex justify-between items-center flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="w-[54px] h-[54px] rounded-full bg-[#E31E24] flex items-center justify-center">
            <span className="text-white font-bold text-xl" style={{ fontFamily: 'Syne' }}>
              {initials}
            </span>
          </div>
          <div>
            <h1 className="text-gray-900 text-[18px] font-bold mb-1" style={{ fontFamily: 'Syne' }}>
              {ownerName}
            </h1>
            <div className="text-[13px] text-gray-700 mb-3">
              {accountType} · {entity.home_branch}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {entity.is_dormant && (
                <span className="px-2 py-1 bg-[#F59E0B] text-white rounded text-xs font-semibold">
                  Dormant account
                </span>
              )}
              <span className="px-2 py-1 bg-[#3B82F6] text-white rounded text-xs font-semibold">
                KYC Tier {entity.kyc_tier}
              </span>
              {entity.is_pep_adjacent && (
                <span className="px-2 py-1 bg-[#E31E24] text-white rounded text-xs font-semibold">
                  PEP adjacent
                </span>
              )}
              {entity.on_watchlist && (
                <span className="px-2 py-1 bg-gray-800 text-white rounded text-xs font-semibold">
                  Watchlist
                </span>
              )}
              {entity.enhanced_monitoring && (
                <span className="px-2 py-1 bg-[#E31E24]/90 text-white rounded text-xs font-semibold">
                  Enhanced monitoring
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className="text-xs text-gray-700 mb-1">Risk Score</div>
          <div className="flex items-center gap-3 mb-2 justify-end">
            <span className="text-[#E31E24] text-4xl font-bold" style={{ fontFamily: 'Syne' }}>
              {entity.risk_score}
            </span>
            <span className="px-3 py-1 bg-[#E31E24] text-white rounded text-sm font-bold">
              {riskLabel(entity.risk_level)}
            </span>
          </div>
          <div className="text-[11px] text-gray-700" style={{ fontFamily: 'DM Mono' }}>
            Last active: {entity.last_active_date}
          </div>
          <div className="text-[11px] text-gray-600" style={{ fontFamily: 'DM Mono' }}>
            Opened: {entity.created_date} · Status: {entity.status}
          </div>
        </div>
      </div>

      <div className="mx-6 mt-6 grid grid-cols-1 xl:grid-cols-[320px_1fr_320px] gap-6">
        <div className="space-y-6">
          <div>
            <h3 className="text-sm text-gray-700 mb-3">Account metrics</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">Avg monthly txn volume</div>
                <div className="text-gray-900 text-lg font-bold" style={{ fontFamily: 'Syne' }}>
                  {formatAmount(entity.metrics.avg_monthly_volume)}
                </div>
              </div>
              <div className="bg-white border border-[#E31E24] rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">Case-linked flow</div>
                <div className="text-[#E31E24] text-lg font-bold" style={{ fontFamily: 'Syne' }}>
                  {formatAmount(entity.metrics.current_month_volume)}
                </div>
                <div className="text-xs text-[#E31E24] mt-1">
                  {entity.metrics.baseline_deviation} vs declared income
                </div>
              </div>
              <div className="bg-white border border-[#F59E0B] rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">Counterparties</div>
                <div className="text-[#F59E0B] text-lg font-bold" style={{ fontFamily: 'Syne' }}>
                  {entity.metrics.counterparties_30d}
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="text-xs text-gray-700 mb-1">In / Out ratio</div>
                <div className="text-gray-900 text-lg font-bold" style={{ fontFamily: 'Syne' }}>
                  {inboundPct}% / {outboundPct}%
                </div>
              </div>
            </div>
          </div>

          {peerMetrics.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm text-gray-700 mb-4">Peer comparison</h3>
              <div className="space-y-4">
                {peerMetrics.map((metric) => (
                  <div key={metric.label}>
                    <div className="flex justify-between text-xs text-gray-700 mb-1">
                      <span>{metric.label}</span>
                      <span className={metric.alert ? 'text-[#E31E24] font-bold' : ''}>{metric.account}%</span>
                    </div>
                    <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="absolute h-full bg-gray-400 opacity-40 rounded-full"
                        style={{ width: `${metric.peer}%` }}
                      />
                      <div
                        className={`absolute h-full rounded-full ${metric.alert ? 'bg-[#E31E24]' : 'bg-[#F59E0B]'}`}
                        style={{ width: `${metric.account}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div>
          <h3 className="text-sm text-gray-700 mb-3">Transaction history</h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="overflow-x-auto max-h-[520px] overflow-y-auto">
              <table className="w-full text-xs" style={{ fontFamily: 'DM Mono' }}>
                <thead className="sticky top-0 bg-gray-50 z-10">
                  <tr className="text-gray-700 text-left">
                    <th className="py-3 px-3 w-4" />
                    <th className="py-3 px-3">Date</th>
                    <th className="py-3 px-3">Time</th>
                    <th className="py-3 px-3">Counterparty</th>
                    <th className="py-3 px-3">Dir</th>
                    <th className="py-3 px-3 text-right">Amount</th>
                    <th className="py-3 px-3">Channel</th>
                  </tr>
                </thead>
                <tbody>
                  {entity.transactions.map((txn, idx) => (
                    <tr
                      key={`${txn.date}-${txn.time}-${idx}`}
                      className={`border-t border-gray-200 hover:bg-gray-50 ${txn.flagged ? 'bg-red-50/40' : ''}`}
                    >
                      <td className="py-2 px-3">
                        {txn.flagged && <div className="w-2 h-2 rounded-full bg-[#E31E24]" />}
                      </td>
                      <td className="py-2 px-3 text-gray-700">{txn.date}</td>
                      <td className="py-2 px-3 text-gray-700">{txn.time}</td>
                      <td className="py-2 px-3">
                        {txn.counterparty?.startsWith('ACC-') ? (
                          <button
                            type="button"
                            onClick={() => openCounterparty(txn.counterparty)}
                            className="text-[#E31E24] hover:underline font-medium"
                          >
                            {txn.counterparty}
                          </button>
                        ) : (
                          <span className="text-gray-900">{txn.counterparty}</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-gray-600">{txn.direction === 'in' ? 'IN' : 'OUT'}</td>
                      <td
                        className={`py-2 px-3 text-right font-bold ${
                          txn.flagged ? 'text-[#E31E24]' : 'text-gray-900'
                        }`}
                      >
                        {formatAmount(txn.amount)}
                      </td>
                      <td className="py-2 px-3 text-gray-700">{txn.channel}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bg-gray-50 px-4 py-3 text-xs text-gray-700 border-t border-gray-200">
              Showing {entity.transactions.length} of {entity.transaction_total_count ?? entity.transactions.length}{' '}
              transactions
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-sm text-gray-700 mb-3">Network connections</h3>
            <EntityNetworkPanel
              accountId={accountId}
              nodes={entity.network}
              onOpenAccount={openCounterparty}
              onViewGraph={openGraph}
            />
          </div>

          <div>
            <h3 className="text-sm text-gray-700 mb-3">Investigation history</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              {entity.investigation_history?.length ? (
                <ul className="space-y-2 text-xs" style={{ fontFamily: 'DM Mono' }}>
                  {entity.investigation_history.map((item) => (
                    <li key={item.case_id} className="border-b border-gray-100 pb-2 last:border-0">
                      <button
                        type="button"
                        onClick={() => {
                          setStoredCaseId(item.case_id);
                          navigate('/');
                        }}
                        className="text-[#E31E24] font-bold hover:underline"
                      >
                        {item.case_id}
                      </button>
                      <div className="text-gray-700">{item.typology}</div>
                      <div className="text-gray-500">
                        {item.status}
                        {item.created_at ? ` · ${item.created_at.slice(0, 10)}` : ''}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-gray-600">No linked investigation cases</p>
              )}
              {(entity.watch_flags?.length ?? 0) > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200 space-y-1">
                  <div className="text-xs font-semibold text-gray-900">Watch flags</div>
                  {entity.watch_flags!.map((flag, i) => (
                    <div key={i} className="text-xs text-gray-700">
                      • {flag}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <h3 className="text-sm text-gray-700 mb-3">Related entities</h3>
            <div className="space-y-2">
              {entity.related_entities.length ? (
                entity.related_entities.map((rel, idx) => (
                  <div
                    key={`${rel.name}-${idx}`}
                    className="bg-white border border-gray-200 rounded-lg p-3 flex items-center justify-between"
                  >
                    <div className="flex-1 min-w-0">
                      {rel.account_id ? (
                        <button
                          type="button"
                          onClick={() => openCounterparty(rel.account_id!)}
                          className="text-gray-900 text-xs font-medium hover:text-[#E31E24] truncate block w-full text-left"
                        >
                          {rel.name}
                        </button>
                      ) : (
                        <div className="text-gray-900 text-xs font-medium truncate">{rel.name}</div>
                      )}
                      <div className="text-gray-700 text-[10px] truncate">{rel.relation}</div>
                    </div>
                    <div
                      className={`text-sm font-bold shrink-0 ml-2 ${
                        rel.risk_score >= 70 ? 'text-[#E31E24]' : 'text-[#F59E0B]'
                      }`}
                    >
                      {rel.risk_score}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-gray-500 bg-white border border-gray-200 rounded-lg p-3">
                  No related parties identified
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 h-[56px] bg-white border-t border-gray-200 flex items-center justify-between px-6 z-30">
        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={actionLoading || entity.on_watchlist}
            onClick={() => runAction(() => addEntityToWatchlist(accountId))}
            className="px-4 py-2 border border-gray-700 text-gray-700 hover:bg-gray-100 transition-colors rounded text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {actionLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : entity.on_watchlist ? (
              <Check className="w-4 h-4 text-green-600" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            {entity.on_watchlist ? 'On watchlist' : 'Add to watchlist'}
          </button>
          <button
            type="button"
            disabled={actionLoading || entity.enhanced_monitoring}
            onClick={() => runAction(() => flagEntityEnhancedMonitoring(accountId))}
            className="px-4 py-2 border border-gray-700 text-gray-700 hover:bg-gray-100 transition-colors rounded text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {actionLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : entity.enhanced_monitoring ? (
              <Check className="w-4 h-4 text-green-600" />
            ) : (
              <Flag className="w-4 h-4" />
            )}
            {entity.enhanced_monitoring ? 'Enhanced monitoring on' : 'Flag for enhanced monitoring'}
          </button>
        </div>
        <button
          type="button"
          onClick={openCase}
          className="px-6 py-2 bg-[#E31E24] text-white hover:bg-[#d4183d] transition-colors rounded text-sm font-bold flex items-center gap-2"
          style={{ fontFamily: 'Syne' }}
        >
          {activeCaseId ? `Open case ${activeCaseId}` : 'Open dashboard'}
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
