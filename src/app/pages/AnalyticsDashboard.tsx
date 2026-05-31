import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  CheckCircle,
  FileCheck,
  FolderOpen,
  Loader2,
  Minus,
  RefreshCw,
} from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router';
import { useAnalytics } from '../../hooks/useAnalytics';
import {
  buildTrendArea,
  buildTrendPolyline,
  formatCr,
  trendMaxValue,
} from '../../lib/analyticsChart';
import { setStoredCaseId } from '../../lib/selectedCase';
import type { SystemEvent } from '../../api/types';

const TYPOLOGY_COLORS = ['#EF4444', '#F59E0B', '#F59E0B', '#00C9A7', '#3B82F6', '#6B7280', '#8B5CF6', '#64748B'];

function eventIcon(type: string) {
  switch (type) {
    case 'str':
      return FileCheck;
    case 'case':
      return FolderOpen;
    case 'resolved':
      return CheckCircle;
    default:
      return AlertTriangle;
  }
}

export default function AnalyticsDashboard() {
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useAnalytics();

  const typologyData = useMemo(
    () =>
      data?.top_typologies.map((t, i) => ({
        label: t.name,
        value: t.count,
        pct: t.percentage,
        color: TYPOLOGY_COLORS[i % TYPOLOGY_COLORS.length],
      })) ?? [],
    [data],
  );

  const maxTypology = typologyData[0]?.value || 1;
  const trend = data?.daily_trend ?? [];
  const maxTrend = trendMaxValue(trend);
  const alertLine = buildTrendPolyline(trend, 'alerts', maxTrend);
  const alertArea = buildTrendArea(trend, 'alerts', maxTrend);
  const confirmedLine = buildTrendPolyline(trend, 'confirmed', maxTrend);

  const weekChange = data?.alerts_week_change_pct ?? 0;
  const investigators = data?.investigators ?? [];
  const systemEvents = data?.system_events ?? [];

  const updatedLabel = data?.updated_at
    ? new Date(data.updated_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });

  const openCase = (caseId: string) => {
    if (!caseId || caseId.startsWith('STR')) return;
    setStoredCaseId(caseId);
    navigate('/');
  };

  const exportReport = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fundlens-analytics-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#E31E24]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4 p-8">
        <p className="text-red-600 text-sm">{error}</p>
        <button type="button" onClick={() => refetch()} className="px-4 py-2 border rounded text-sm">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white pb-8">
      <div className="h-[64px] bg-white border-b border-gray-200 flex items-center justify-between px-8">
        <div>
          <h1 className="text-gray-900 text-lg font-bold" style={{ fontFamily: 'Syne' }}>
            Analytics Dashboard
          </h1>
          <p className="text-gray-600 text-xs">
            Detection metrics from live case data · Updated {updatedLabel}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => refetch()}
            className="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors rounded text-sm flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            type="button"
            onClick={exportReport}
            disabled={!data}
            className="px-4 py-2 border border-gray-400 text-gray-600 hover:bg-gray-100 transition-colors rounded text-sm disabled:opacity-50"
          >
            Export report
          </button>
        </div>
      </div>

      <div className="p-8">
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">Alerts this week</div>
            <div className="text-gray-900 text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              {data?.alerts_this_week ?? 0}
            </div>
            <div
              className={`flex items-center gap-1 text-xs ${
                weekChange > 0 ? 'text-[#E31E24]' : weekChange < 0 ? 'text-green-600' : 'text-gray-500'
              }`}
            >
              {weekChange > 0 ? (
                <ArrowUp className="w-3 h-3" />
              ) : weekChange < 0 ? (
                <ArrowDown className="w-3 h-3" />
              ) : (
                <Minus className="w-3 h-3" />
              )}
              <span>
                {weekChange > 0 ? '+' : ''}
                {weekChange}% vs prior week
              </span>
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">Critical / confirmed</div>
            <div className="text-[#E31E24] text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              {data?.confirmed_fraud_count ?? data?.critical_count ?? 0}
            </div>
            <div className="text-[#E31E24] text-[11px]">
              {formatCr(data?.total_amount_flagged ?? 0)} flagged volume
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">STRs generated</div>
            <div className="text-[#E31E24] text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              {data?.strs_filed ?? 0}
            </div>
            <div className="text-gray-600 text-[11px]">{data?.total_cases ?? 0} total cases</div>
          </div>

          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">Avg resolution time</div>
            <div className="text-[#E31E24] text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              {data?.avg_resolution_time ?? '—'}
            </div>
            <div className="text-gray-600 text-[11px]">Investigation desk target</div>
          </div>

          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">GNN accuracy</div>
            <div className="text-[#3B82F6] text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              {data?.gnn_accuracy ?? 0}%
            </div>
            <div className="text-gray-600 text-[11px]">
              {((data?.false_positive_rate ?? 0) * 100).toFixed(1)}% est. false positives
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[minmax(280px,460px)_1fr_minmax(280px,360px)] gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-gray-900 text-sm font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              Alert volume by typology
            </h3>
            <div className="text-xs text-gray-600 mb-4">All active cases</div>
            {typologyData.length ? (
              <div className="space-y-4">
                {typologyData.map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span className="truncate pr-2">{item.label}</span>
                      <span className="text-gray-900 font-bold shrink-0">
                        {item.value} ({item.pct}%)
                      </span>
                    </div>
                    <div className="relative h-6 bg-gray-100 rounded overflow-hidden">
                      <div
                        className="absolute h-full rounded"
                        style={{
                          width: `${(item.value / maxTypology) * 100}%`,
                          backgroundColor: item.color,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500">No typology data</p>
            )}

            {data?.channel_breakdown?.length ? (
              <div className="mt-8 pt-6 border-t border-gray-100">
                <h4 className="text-xs font-semibold text-gray-700 mb-3">Channel mix</h4>
                <div className="flex flex-wrap gap-2">
                  {data.channel_breakdown.map((ch) => (
                    <span
                      key={ch.channel}
                      className="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-[10px]"
                      style={{ fontFamily: 'DM Mono' }}
                    >
                      {ch.channel} {ch.percentage}%
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-gray-900 text-sm font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              Daily alert trend
            </h3>
            <div className="text-xs text-gray-600 mb-4">Last 14 days</div>
            <div className="relative h-[280px]">
              {trend.length ? (
                <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="none">
                  {[0, 25, 50, 75, 100].map((pct) => (
                    <line
                      key={pct}
                      x1="8"
                      y1={100 - pct * 0.92 - 4}
                      x2="100"
                      y2={100 - pct * 0.92 - 4}
                      stroke="#e5e7eb"
                      strokeWidth="0.3"
                    />
                  ))}
                  {alertArea && (
                    <polygon points={alertArea} fill="#E31E24" fillOpacity="0.08" />
                  )}
                  {confirmedLine && (
                    <polyline
                      points={confirmedLine}
                      fill="none"
                      stroke="#d4183d"
                      strokeWidth="0.8"
                      strokeDasharray="2 2"
                      vectorEffect="non-scaling-stroke"
                    />
                  )}
                  {alertLine && (
                    <polyline
                      points={alertLine}
                      fill="none"
                      stroke="#E31E24"
                      strokeWidth="1"
                      vectorEffect="non-scaling-stroke"
                    />
                  )}
                </svg>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-gray-500">
                  No dated cases for trend chart
                </div>
              )}
            </div>
            <div className="flex items-center gap-4 mt-4 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-[2px] bg-[#E31E24]" />
                <span className="text-gray-600">Alerts generated</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0 border-t-2 border-dashed border-[#d4183d]" />
                <span className="text-gray-600">Critical risk</span>
              </div>
            </div>
            <div className="flex justify-between text-[10px] text-gray-400 mt-2" style={{ fontFamily: 'DM Mono' }}>
              <span>{trend[0]?.date?.slice(5)}</span>
              <span>{trend[trend.length - 1]?.date?.slice(5)}</span>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="text-gray-900 text-sm font-bold mb-4" style={{ fontFamily: 'Syne' }}>
                Cases by investigator
              </h3>
              {investigators.length ? (
                <div className="space-y-3">
                  {investigators.map((inv, idx) => (
                    <div
                      key={inv.investigator_id}
                      className={`flex items-center gap-3 p-2 rounded transition-colors ${
                        idx === 0 ? 'bg-[#E31E24] text-white' : 'bg-white hover:bg-gray-50'
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                          idx === 0 ? 'bg-white text-[#E31E24]' : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        {inv.initials}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`text-xs font-medium truncate ${idx === 0 ? '' : 'text-gray-900'}`}>
                          {inv.name}
                        </div>
                        <div
                          className={`text-[10px] ${idx === 0 ? 'opacity-90' : 'text-gray-600'}`}
                          style={{ fontFamily: 'DM Mono' }}
                        >
                          {inv.cases} cases · {inv.avg_resolution_display} avg
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500">No investigator assignments in case data</p>
              )}
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="text-gray-900 text-sm font-bold mb-4" style={{ fontFamily: 'Syne' }}>
                System health
              </h3>
              <div className="space-y-3">
                {(data?.system_health ?? []).map((item) => (
                  <div key={item.name} className="flex items-start gap-2">
                    <div
                      className={`w-2 h-2 rounded-full mt-1 ${
                        item.status === 'ok' ? 'bg-green-500' : 'bg-[#F59E0B]'
                      }`}
                    />
                    <div className="flex-1">
                      <div className="text-gray-900 text-xs mb-1">{item.name}</div>
                      <div className="text-gray-600 text-[10px]" style={{ fontFamily: 'DM Mono' }}>
                        {item.detail}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {data?.risk_distribution?.length ? (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-gray-900 text-sm font-bold mb-3" style={{ fontFamily: 'Syne' }}>
                  Risk distribution
                </h3>
                <div className="space-y-2">
                  {data.risk_distribution.map((r) => (
                    <div key={r.level} className="flex items-center gap-2 text-xs">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: r.color }} />
                      <span className="text-gray-700 flex-1">{r.level}</span>
                      <span className="font-bold text-gray-900" style={{ fontFamily: 'DM Mono' }}>
                        {r.count}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3
            className="text-gray-900 text-sm font-bold mb-4 flex items-center gap-2"
            style={{ fontFamily: 'Syne' }}
          >
            <Activity className="w-4 h-4" />
            Recent system events
          </h3>
          <div className="space-y-1 max-h-[240px] overflow-auto">
            {systemEvents.length ? (
              systemEvents.map((event: SystemEvent, idx) => {
                const Icon = eventIcon(event.event_type);
                const clickable = event.ref.startsWith('CASE-');
                return (
                  <div
                    key={`${event.ref}-${idx}`}
                    className={`flex items-center gap-4 py-2 px-3 rounded hover:bg-gray-50 transition-colors ${
                      idx === 0 ? 'border-l-2 border-[#E31E24] bg-gray-50' : ''
                    }`}
                  >
                    <div className="text-gray-600 text-xs w-20 shrink-0" style={{ fontFamily: 'DM Mono' }}>
                      {event.time}
                    </div>
                    <Icon className="w-4 h-4 text-[#E31E24] flex-shrink-0" />
                    <div className="flex-1 text-gray-900 text-xs">{event.description}</div>
                    {clickable ? (
                      <button
                        type="button"
                        onClick={() => openCase(event.ref)}
                        className="text-[#E31E24] hover:underline text-xs shrink-0"
                        style={{ fontFamily: 'DM Mono' }}
                      >
                        {event.ref}
                      </button>
                    ) : (
                      <span className="text-gray-500 text-xs shrink-0" style={{ fontFamily: 'DM Mono' }}>
                        {event.ref}
                      </span>
                    )}
                  </div>
                );
              })
            ) : (
              <p className="text-xs text-gray-500 py-4">No recent events</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
