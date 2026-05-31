import {
  Activity,
  Database,
  FileText,
  Link2,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Settings,
  Shield,
  Users,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  patchDataSource,
  saveConfigUsers,
  testFiuConnection,
  updateConfigThresholds,
  updateFiuSettings,
} from '../../api/client';
import type { DataConnection, PlatformConfig } from '../../api/types';
import { usePlatformConfig } from '../../hooks/usePlatformConfig';

const TABS = [
  { id: 'data', label: 'Data connections', icon: Database },
  { id: 'thresholds', label: 'Detection thresholds', icon: Activity },
  { id: 'gnn', label: 'GNN model settings', icon: Settings },
  { id: 'users', label: 'User management', icon: Users },
  { id: 'blockchain', label: 'Blockchain config', icon: Link2 },
  { id: 'fiu', label: 'FIU integration', icon: FileText },
  { id: 'audit', label: 'Audit log', icon: Shield },
] as const;

type TabId = (typeof TABS)[number]['id'];

function statusBadge(status: string) {
  const s = status.toLowerCase();
  if (s === 'connected' || s === 'online')
    return 'bg-[#E31E24] text-white';
  if (s === 'connecting' || s === 'degraded')
    return 'bg-[#F59E0B] text-white';
  return 'bg-gray-500 text-white';
}

function Sparkline({ values, color }: { values: number[]; color: string }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const points = values
    .map((v, i) => {
      const x = (i / (values.length - 1 || 1)) * 100;
      const y = 40 - (v / max) * 35;
      return `${x},${y}`;
    })
    .join(' ');
  return (
    <svg className="w-full h-12" viewBox="0 0 100 40" preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" />
    </svg>
  );
}

export default function AdminConfig() {
  const [activeTab, setActiveTab] = useState<TabId>('data');
  const { config, auditLog, loading, error, refetch, setConfig } = usePlatformConfig();
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const [velocityThreshold, setVelocityThreshold] = useState(15);
  const [dormancyPeriod, setDormancyPeriod] = useState(6);
  const [gnnConfidence, setGnnConfidence] = useState(70);
  const [fiuEndpoint, setFiuEndpoint] = useState('');
  const [fiuEnabled, setFiuEnabled] = useState(true);
  const [fiuAutoSubmit, setFiuAutoSubmit] = useState(false);

  useEffect(() => {
    if (!config) return;
    setVelocityThreshold(config.thresholds.velocity_threshold_lakh);
    setDormancyPeriod(config.thresholds.dormancy_months);
    setGnnConfidence(config.thresholds.gnn_confidence_pct);
    setFiuEndpoint(config.fiu.endpoint);
    setFiuEnabled(config.fiu.enabled);
    setFiuAutoSubmit(config.fiu.auto_submit);
  }, [config]);

  const notify = (text: string) => {
    setMessage(text);
    setTimeout(() => setMessage(null), 3000);
  };

  const saveThresholds = async () => {
    setSaving(true);
    try {
      const res = await updateConfigThresholds({
        velocity_threshold_lakh: velocityThreshold,
        dormancy_months: dormancyPeriod,
        gnn_confidence_pct: gnnConfidence,
      });
      setConfig((prev) =>
        prev ? { ...prev, thresholds: res.thresholds } : prev,
      );
      notify('Thresholds saved');
      refetch();
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const saveFiu = async () => {
    setSaving(true);
    try {
      await updateFiuSettings({
        endpoint: fiuEndpoint,
        enabled: fiuEnabled,
        auto_submit: fiuAutoSubmit,
      });
      notify('FIU settings saved');
      refetch();
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const connectSource = async (source: DataConnection) => {
    try {
      await patchDataSource(source.id, { status: 'connected', notes: 'Marked connected by admin' });
      notify(`${source.name} connected`);
      refetch();
    } catch (e) {
      notify((e as Error).message);
    }
  };

  const activeMeta = TABS.find((t) => t.id === activeTab)!;

  if (loading && !config) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#E31E24]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex">
      <div className="w-[220px] bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="h-[72px] flex items-center justify-center border-b border-gray-200">
          <div className="text-gray-900 text-xl font-bold" style={{ fontFamily: 'Syne' }}>
            FundLens
          </div>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {TABS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveTab(item.id)}
                className={`w-full h-[40px] px-4 flex items-center gap-3 text-sm transition-colors ${
                  isActive
                    ? 'bg-[#E31E24] text-white border-l-2 border-[#E31E24]'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
                style={{ fontFamily: 'Syne' }}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-left truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-700 mb-3 font-semibold" style={{ fontFamily: 'Syne' }}>
            System status
          </div>
          <div className="space-y-2">
            {(config?.system_status ?? []).slice(0, 5).map((sys) => (
              <div key={sys.label} className="flex items-center gap-2 text-xs">
                <div
                  className={`w-2 h-2 rounded-full ${
                    sys.status === 'online' ? 'bg-green-500' : 'bg-amber-500'
                  }`}
                />
                <span className="text-gray-700 truncate" title={sys.detail}>
                  {sys.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 p-8 overflow-auto min-w-0">
        <div className="flex items-start justify-between mb-6 gap-4 flex-wrap">
          <div>
            <h1 className="text-gray-900 text-3xl font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              {activeMeta.label}
            </h1>
            <p className="text-gray-700 text-sm">
              {activeTab === 'data' && 'Connect FundLens to your bank transaction systems'}
              {activeTab === 'thresholds' && 'Tune AML detection sensitivity (persisted to config store)'}
              {activeTab === 'gnn' && 'Graph neural network scoring parameters'}
              {activeTab === 'users' && 'Investigator roster for assignments'}
              {activeTab === 'blockchain' && 'Evidence chain deployment mode'}
              {activeTab === 'fiu' && 'FIU-IND STR submission integration'}
              {activeTab === 'audit' && 'Configuration and case activity log'}
            </p>
          </div>
          <button
            type="button"
            onClick={() => refetch()}
            className="px-3 py-2 border border-gray-300 rounded text-sm flex items-center gap-2 hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-800 text-sm rounded">{error}</div>
        )}
        {message && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-800 text-sm rounded">{message}</div>
        )}

        {activeTab === 'data' && config && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 max-w-[700px]">
              {config.data_connections.map((src) => (
                <div
                  key={src.id}
                  className="bg-gray-50 border border-gray-200 rounded-lg p-5 min-h-[140px] flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-gray-900 font-semibold mb-1" style={{ fontFamily: 'Syne' }}>
                        {src.name}
                      </h3>
                      <div
                        className={`inline-block px-2 py-1 rounded text-xs font-semibold ${statusBadge(src.status)}`}
                      >
                        {src.status.replace(/_/g, ' ').toUpperCase()}
                      </div>
                    </div>
                  </div>
                  <div className="text-gray-700 text-xs mt-3" style={{ fontFamily: 'DM Mono' }}>
                    {src.vendor} · {src.detail}
                  </div>
                  {src.progress_pct != null && (
                    <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#F59E0B] rounded-full"
                        style={{ width: `${src.progress_pct}%` }}
                      />
                    </div>
                  )}
                  {src.status === 'not_configured' && (
                    <button
                      type="button"
                      onClick={() => connectSource(src)}
                      className="mt-2 text-[#E31E24] hover:underline text-xs text-left"
                    >
                      Configure ↗
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              type="button"
              className="px-4 py-2 border border-[#E31E24] text-[#E31E24] rounded flex items-center gap-2 text-sm font-semibold opacity-60 cursor-not-allowed"
              title="Demo — add connectors via backend config"
            >
              <Plus className="w-4 h-4" />
              Add data source
            </button>
          </>
        )}

        {(activeTab === 'thresholds' || activeTab === 'gnn') && config && (
          <div className="max-w-[800px] space-y-6">
            {activeTab === 'thresholds' && (
              <>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
                  <div className="flex justify-between mb-2">
                    <div>
                      <div className="font-semibold text-gray-900">Structuring threshold</div>
                      <div className="text-xs text-gray-600">PMLA default — locked</div>
                    </div>
                    <div className="text-[#E31E24] font-bold" style={{ fontFamily: 'DM Mono' }}>
                      ₹{config.thresholds.structuring_threshold_inr.toLocaleString('en-IN')}
                    </div>
                  </div>
                </div>
                {[
                  {
                    label: 'Alert on velocity (per 24h)',
                    hint: '₹10L – ₹50L',
                    value: velocityThreshold,
                    set: setVelocityThreshold,
                    min: 10,
                    max: 50,
                    display: `₹${velocityThreshold}L`,
                  },
                  {
                    label: 'Dormancy period (months)',
                    hint: '3 – 24',
                    value: dormancyPeriod,
                    set: setDormancyPeriod,
                    min: 3,
                    max: 24,
                    display: String(dormancyPeriod),
                  },
                  {
                    label: 'GNN confidence threshold',
                    hint: '60% – 95%',
                    value: gnnConfidence,
                    set: setGnnConfidence,
                    min: 60,
                    max: 95,
                    display: `${gnnConfidence}%`,
                  },
                ].map((slider) => (
                  <div key={slider.label} className="bg-gray-50 border border-gray-200 rounded-lg p-5">
                    <div className="flex justify-between mb-3">
                      <div>
                        <div className="font-semibold text-gray-900">{slider.label}</div>
                        <div className="text-xs text-gray-600">{slider.hint}</div>
                      </div>
                      <div className="text-[#E31E24] font-bold" style={{ fontFamily: 'DM Mono' }}>
                        {slider.display}
                      </div>
                    </div>
                    <input
                      type="range"
                      min={slider.min}
                      max={slider.max}
                      value={slider.value}
                      onChange={(e) => slider.set(Number(e.target.value))}
                      className="w-full accent-[#E31E24]"
                    />
                  </div>
                ))}
                <button
                  type="button"
                  onClick={saveThresholds}
                  disabled={saving}
                  className="px-5 py-2 bg-[#E31E24] text-white rounded font-semibold text-sm flex items-center gap-2 disabled:opacity-50"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save thresholds
                </button>
              </>
            )}
            {activeTab === 'gnn' && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600 text-xs">Model</div>
                    <div className="font-semibold">{config.gnn_model.name}</div>
                  </div>
                  <div>
                    <div className="text-gray-600 text-xs">Version</div>
                    <div className="font-mono">{config.gnn_model.version}</div>
                  </div>
                  <div>
                    <div className="text-gray-600 text-xs">Device</div>
                    <div className="font-semibold uppercase">{config.gnn_model.device}</div>
                  </div>
                  <div>
                    <div className="text-gray-600 text-xs">Avg accuracy (cases)</div>
                    <div className="font-semibold">{config.analytics_summary.gnn_accuracy}%</div>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  Confidence threshold is shared with Detection thresholds ({config.gnn_model.confidence_threshold_pct}%).
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'users' && config && (
          <UsersPanel users={config.users} onSaved={() => { notify('Users saved'); refetch(); }} />
        )}

        {activeTab === 'blockchain' && config && (
          <div className="max-w-lg bg-gray-50 border border-gray-200 rounded-lg p-6 space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Mode</span>
              <span className="font-mono font-semibold uppercase">{config.blockchain.mode}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Network</span>
              <span className="font-mono">{config.blockchain.network}</span>
            </div>
            <div>
              <div className="text-gray-600 text-xs mb-1">Ledger database</div>
              <div className="font-mono text-xs break-all">{config.blockchain.db_path}</div>
            </div>
            <p className="text-gray-600 text-xs pt-2">
              Set <code className="bg-white px-1">FUNDLENS_BLOCKCHAIN_MODE=production</code> for Hyperledger Fabric.
            </p>
          </div>
        )}

        {activeTab === 'fiu' && config && (
          <div className="max-w-lg space-y-4">
            <label className="block text-sm">
              <span className="text-gray-700 font-medium">FIU endpoint</span>
              <input
                type="url"
                value={fiuEndpoint}
                onChange={(e) => setFiuEndpoint(e.target.value)}
                className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono"
              />
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={fiuEnabled} onChange={(e) => setFiuEnabled(e.target.checked)} />
              Integration enabled
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={fiuAutoSubmit} onChange={(e) => setFiuAutoSubmit(e.target.checked)} />
              Auto-submit after supervisor approval
            </label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={saveFiu}
                disabled={saving}
                className="px-4 py-2 bg-[#E31E24] text-white rounded text-sm font-semibold disabled:opacity-50"
              >
                Save FIU settings
              </button>
              <button
                type="button"
                onClick={async () => {
                  const res = await testFiuConnection();
                  notify(res.message);
                }}
                className="px-4 py-2 border border-gray-400 rounded text-sm"
              >
                Test connection
              </button>
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="max-w-3xl border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="p-3 font-semibold">Time</th>
                  <th className="p-3 font-semibold">Actor</th>
                  <th className="p-3 font-semibold">Section</th>
                  <th className="p-3 font-semibold">Details</th>
                </tr>
              </thead>
              <tbody>
                {auditLog.map((entry) => (
                  <tr key={String(entry.id)} className="border-t border-gray-100">
                    <td className="p-3 font-mono text-xs whitespace-nowrap">
                      {String(entry.timestamp).slice(11, 19) || entry.timestamp}
                    </td>
                    <td className="p-3">{entry.actor_id}</td>
                    <td className="p-3">{entry.section}</td>
                    <td className="p-3 text-gray-700">{entry.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!auditLog.length && (
              <p className="p-6 text-center text-gray-500 text-sm">No audit entries yet — save settings to log changes.</p>
            )}
          </div>
        )}
      </div>

      {config && (
        <div className="w-[300px] bg-white border-l border-gray-200 p-6 shrink-0 hidden lg:block">
          <h3 className="text-gray-900 text-sm font-bold mb-4" style={{ fontFamily: 'Syne' }}>
            Connection health
          </h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2 text-xs">
                <span className="text-gray-700">Events/sec</span>
                <span className="font-mono font-bold">{config.connection_health.events_per_sec}</span>
              </div>
              <Sparkline values={config.connection_health.sparkline_events} color="#E31E24" />
            </div>
            <div>
              <div className="flex justify-between mb-2 text-xs">
                <span className="text-gray-700">Graph write latency</span>
                <span className="font-mono font-bold">{config.connection_health.graph_write_latency_ms}ms</span>
              </div>
              <Sparkline values={config.connection_health.sparkline_graph} color="#3B82F6" />
            </div>
            <div>
              <div className="flex justify-between mb-2 text-xs">
                <span className="text-gray-700">GNN inference</span>
                <span className="font-mono font-bold">{config.connection_health.gnn_inference_ms}ms</span>
              </div>
              <Sparkline values={config.connection_health.sparkline_gnn} color="#F59E0B" />
            </div>
          </div>
          <div className="mt-8 pt-6 border-t text-xs text-gray-600">
            <div>{config.analytics_summary.total_cases} open cases</div>
            <div>{config.analytics_summary.alerts_today} alerts today</div>
          </div>
        </div>
      )}
    </div>
  );
}

function UsersPanel({
  users: initial,
  onSaved,
}: {
  users: PlatformConfig['users'];
  onSaved: () => void;
}) {
  const [users, setUsers] = useState(initial);
  const [saving, setSaving] = useState(false);

  useEffect(() => setUsers(initial), [initial]);

  const toggleActive = (id: string) => {
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, active: !u.active } : u)));
  };

  const save = async () => {
    setSaving(true);
    try {
      await saveConfigUsers(users);
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-3">
      {users.map((user) => (
        <div
          key={user.id}
          className="flex items-center justify-between border border-gray-200 rounded-lg p-4 bg-gray-50"
        >
          <div>
            <div className="font-semibold text-gray-900">{user.name}</div>
            <div className="text-xs text-gray-600 font-mono">
              {user.id} · {user.role} · {user.branch}
            </div>
          </div>
          <button
            type="button"
            onClick={() => toggleActive(user.id)}
            className={`px-3 py-1 rounded text-xs font-semibold ${
              user.active ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-600'
            }`}
          >
            {user.active ? 'Active' : 'Inactive'}
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={save}
        disabled={saving}
        className="px-4 py-2 bg-[#E31E24] text-white rounded text-sm font-semibold flex items-center gap-2"
      >
        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        Save roster
      </button>
    </div>
  );
}
