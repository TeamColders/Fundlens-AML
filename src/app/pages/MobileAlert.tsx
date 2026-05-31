import { Bell, ChevronRight, Loader2, Menu } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { mobileAcknowledgeCase, mobileAssignCase } from '../../api/client';
import { useMobileDashboard } from '../../hooks/useMobileDashboard';
import { useSelectedCaseId } from '../../hooks/useSelectedCaseId';
import { formatAmount } from '../../lib/subgraphLayout';
import { pathWithCase, setStoredCaseId } from '../../lib/selectedCase';

export default function MobileAlert() {
  const navigate = useNavigate();
  const { caseId, setCaseId } = useSelectedCaseId();
  const { data, loading, error, refetch } = useMobileDashboard(caseId);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const featured = data?.featured;
  const recent = data?.recent ?? [];

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const selectCase = (id: string) => {
    setStoredCaseId(id);
    setCaseId(id);
    refetch();
  };

  const handleInvestigate = async () => {
    if (!featured) return;
    setActionLoading('investigate');
    try {
      const res = await mobileAcknowledgeCase(featured.case_id);
      setStoredCaseId(featured.case_id);
      showToast(res.message);
      navigate(pathWithCase('/', featured.case_id));
    } catch (e) {
      showToast((e as Error).message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleAssign = async () => {
    if (!featured) return;
    setActionLoading('assign');
    try {
      await mobileAssignCase(featured.case_id, 'PS-002');
      showToast('Assigned to Priya Sharma (PS-002)');
      refetch();
    } catch (e) {
      showToast((e as Error).message);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div
        className="w-[390px] h-[844px] bg-white relative overflow-hidden shadow-2xl rounded-[2rem] border border-gray-200"
        style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}
      >
        <div className="h-[44px] bg-black flex items-center justify-between px-6 text-white text-xs">
          <div>9:41</div>
          <div className="font-medium opacity-80">FundLens Mobile</div>
        </div>

        <div className="h-[56px] bg-white border-b border-gray-200 flex items-center justify-between px-5">
          <Menu className="w-6 h-6 text-gray-900" />
          <div className="text-gray-900 text-[16px] font-bold" style={{ fontFamily: 'Syne' }}>
            FundLens
          </div>
          <div className="relative">
            <Bell className="w-6 h-6 text-gray-900" />
            {(data?.unread_count ?? 0) > 0 && (
              <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#E31E24] flex items-center justify-center text-white text-[10px] font-bold">
                {Math.min(data!.unread_count, 9)}
              </div>
            )}
          </div>
        </div>

        {toast && (
          <div className="mx-4 mt-2 p-2 bg-gray-900 text-white text-xs rounded-lg text-center">{toast}</div>
        )}

        {loading && !data ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#E31E24]" />
          </div>
        ) : error ? (
          <div className="m-4 p-4 text-sm text-red-700 bg-red-50 rounded-lg">{error}</div>
        ) : featured ? (
          <div className="bg-gray-50 border-l-4 border-[#E31E24] p-4 m-4 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#E31E24] animate-pulse" />
                <span className="text-[#E31E24] text-[10px] font-bold tracking-wide" style={{ fontFamily: 'Syne' }}>
                  {(featured.risk_level || 'critical').toUpperCase()} ALERT
                </span>
              </div>
              <span className="text-gray-700 text-[10px]">Live</span>
            </div>

            <div className="mb-3">
              <div className="text-[#E31E24] text-[48px] font-bold leading-none mb-2" style={{ fontFamily: 'Syne' }}>
                {featured.risk_pct}%
              </div>
              <div className="text-gray-900 text-[18px] font-semibold mb-2" style={{ fontFamily: 'Syne' }}>
                {featured.typology}
              </div>
              <div className="text-gray-700 text-xs mb-1" style={{ fontFamily: 'DM Mono' }}>
                {featured.case_id} · {featured.accounts_count} accounts ·{' '}
                {formatAmount(featured.total_amount)}
              </div>
              <div className="text-gray-700 text-[11px]" style={{ fontFamily: 'DM Mono' }}>
                {featured.channel} · {featured.duration_display || featured.status}
              </div>
            </div>

            <div
              className="bg-white rounded-lg p-3 mb-4 border border-gray-200"
              style={{ minHeight: '100px' }}
            >
              <div className="text-[10px] text-gray-500 mb-2 uppercase tracking-wide">Graph preview</div>
              {featured.has_subgraph ? (
                <div className="flex flex-wrap gap-2">
                  <div className="text-xs text-gray-600 w-full">
                    {data?.critical_count ?? 0} critical · {data?.unread_count ?? 0} in queue
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate(pathWithCase('/graph', featured.case_id))}
                    className="text-[#E31E24] text-xs font-semibold"
                  >
                    Open full graph on desktop →
                  </button>
                </div>
              ) : (
                <div className="text-xs text-gray-400 text-center py-6">Graph loads on desktop view</div>
              )}
            </div>

            <div className="space-y-3">
              <button
                type="button"
                onClick={handleInvestigate}
                disabled={actionLoading !== null}
                className="w-full bg-[#E31E24] text-white rounded-lg py-3 text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-60"
                style={{ fontFamily: 'Syne' }}
              >
                {actionLoading === 'investigate' ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  'Investigate now →'
                )}
              </button>
              <button
                type="button"
                onClick={handleAssign}
                disabled={actionLoading !== null}
                className="w-full border border-gray-900 text-gray-900 rounded-lg py-3 text-sm font-semibold disabled:opacity-60"
              >
                {actionLoading === 'assign' ? 'Assigning…' : 'Assign to team'}
              </button>
            </div>
          </div>
        ) : (
          <div className="m-4 p-6 text-center text-gray-600 text-sm">
            No alerts — run demo seed and start the API.
          </div>
        )}

        <div className="px-4 pb-28 overflow-y-auto max-h-[340px]">
          <div className="text-[#E31E24] text-[10px] tracking-widest font-semibold mb-3 uppercase">
            Recent alerts
          </div>
          <div className="space-y-2">
            {recent.map((alert) => {
              const isSelected = alert.case_id === (featured?.case_id || caseId);
              const dotColor =
                alert.risk_level === 'critical'
                  ? '#E31E24'
                  : alert.risk_level === 'high'
                    ? '#F59E0B'
                    : '#6B7280';
              return (
                <button
                  key={alert.case_id}
                  type="button"
                  onClick={() => selectCase(alert.case_id)}
                  className={`w-full bg-white border rounded-lg p-4 flex items-center justify-between text-left transition-colors ${
                    isSelected ? 'border-[#E31E24] bg-red-50/30' : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: dotColor }} />
                    <div className="min-w-0">
                      <div className="text-gray-900 text-sm font-medium mb-1 truncate">{alert.typology}</div>
                      <div className="text-gray-700 text-xs truncate" style={{ fontFamily: 'DM Mono' }}>
                        {alert.case_id} · {formatAmount(alert.total_amount)} · {alert.time_ago}
                      </div>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-700 shrink-0" />
                </button>
              );
            })}
          </div>
        </div>

        <div
          className="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-200"
          style={{ paddingBottom: 'env(safe-area-inset-bottom, 16px)' }}
        >
          <div className="flex items-center justify-around pt-2 pb-1">
            {[
              { label: 'Dashboard', path: '/', active: false },
              { label: 'Alerts', path: '/mobile', active: true },
              { label: 'Graph', path: '/graph', active: false },
              { label: 'STR', path: '/str-generation', active: false },
              { label: 'Settings', path: '/admin', active: false },
            ].map((tab) => (
              <button
                key={tab.label}
                type="button"
                onClick={() => {
                  if (featured?.case_id) setStoredCaseId(featured.case_id);
                  navigate(caseId && tab.path !== '/mobile' ? pathWithCase(tab.path, caseId) : tab.path);
                }}
                className="flex flex-col items-center gap-1 py-2 px-2"
              >
                <div
                  className={`w-6 h-6 rounded ${tab.active ? 'bg-[#E31E24]' : 'bg-gray-300'}`}
                />
                <span className={`text-[10px] ${tab.active ? 'text-[#E31E24] font-semibold' : 'text-gray-400'}`}>
                  {tab.label}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
