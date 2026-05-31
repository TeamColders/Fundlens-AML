import { ArrowUp, Activity, AlertTriangle, FileCheck, FolderOpen, RefreshCw, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router';
import { useEffect, useState } from 'react';
import { api } from '../../services/api';

interface HealthStatus {
  neo4j: boolean;
  postgres: boolean;
  redis: boolean;
}

export default function AnalyticsDashboard() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    api.getHealth()
      .then(data => setHealth(data.status))
      .catch(() => {});
  }, []);

  const typologyData = [
    { label: 'Round-trip Layering', value: 47, color: '#EF4444' },
    { label: 'Structuring/Smurfing', value: 38, color: '#F59E0B' },
    { label: 'Dormant Activation', value: 31, color: '#F59E0B' },
    { label: 'Fan-out/Fan-in', value: 24, color: '#00C9A7' },
    { label: 'PEP Linkage', value: 18, color: '#3B82F6' },
    { label: 'Other', value: 12, color: '#6B7280' },
  ];

  const investigators = [
    { initials: 'AK', name: 'Anjali Kapoor', cases: 12, avgTime: '2.3h', isTop: true },
    { initials: 'RS', name: 'Rohan Sharma', cases: 9, avgTime: '3.1h', isTop: false },
    { initials: 'PT', name: 'Priya Thakur', cases: 8, avgTime: '2.8h', isTop: false },
    { initials: 'VM', name: 'Vikram Mehta', cases: 7, avgTime: '4.2h', isTop: false },
    { initials: 'SK', name: 'Sunil Kumar', cases: 5, avgTime: '3.5h', isTop: false },
  ];

  const systemEvents = [
    { time: '14:23:07', icon: AlertTriangle, desc: 'Critical alert triggered', ref: 'CASE-2847' },
    { time: '14:15:22', icon: FileCheck, desc: 'STR submitted to FIU-IND', ref: 'STR-042' },
    { time: '13:48:19', icon: FolderOpen, desc: 'New case opened', ref: 'CASE-2846' },
    { time: '12:32:45', icon: AlertTriangle, desc: 'Alert generated', ref: 'CASE-2845' },
    { time: '11:15:03', icon: RefreshCw, desc: 'GNN model retrained', ref: 'v2.4' },
    { time: '10:42:18', icon: CheckCircle, desc: 'Case resolved', ref: 'CASE-2821' },
    { time: '09:28:55', icon: FileCheck, desc: 'STR submitted to FIU-IND', ref: 'STR-041' },
    { time: '08:17:32', icon: AlertTriangle, desc: 'Alert triggered', ref: 'CASE-2844' },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Top Bar */}
      <div className="h-[64px] bg-white border-b border-gray-200 flex items-center justify-between px-8">
        <div>
          <h1 className="text-gray-900 text-lg font-bold" style={{ fontFamily: 'Syne' }}>
            Analytics Dashboard
          </h1>
          <p className="text-gray-600 text-xs">
            System performance and detection metrics · Updated: {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 border border-gray-400 text-gray-600 hover:bg-gray-100 transition-colors rounded text-sm">
            Export Report
          </button>
        </div>
      </div>

      <div className="p-8">
        {/* KPI Row */}
        <div className="grid grid-cols-5 gap-4 mb-8">
          {/* Alerts this week */}
          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">Alerts this week</div>
            <div className="text-gray-900 text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              47
            </div>
            <div className="flex items-center gap-1 text-[#E31E24] text-xs">
              <ArrowUp className="w-3 h-3" />
              <span>+12% vs last week</span>
            </div>
          </div>

          {/* Confirmed fraud */}
          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">Confirmed fraud</div>
            <div className="text-[#E31E24] text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              8
            </div>
            <div className="text-[#E31E24] text-[11px]">₹3.2 Cr prevented</div>
          </div>

          {/* STRs filed */}
          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">STRs filed</div>
            <div className="text-[#E31E24] text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              3
            </div>
            <div className="text-[#E31E24] text-[11px]">0 missed deadlines</div>
          </div>

          {/* Avg detection time */}
          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">Avg detection time</div>
            <div className="text-[#E31E24] text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              0.8s
            </div>
            <div className="text-gray-600 text-[11px]">Industry avg: 3–5 days</div>
          </div>

          {/* GNN accuracy */}
          <div className="bg-gray-50 rounded-xl p-6">
            <div className="text-xs text-gray-600 mb-2">GNN accuracy</div>
            <div className="text-[#3B82F6] text-[32px] font-bold mb-2" style={{ fontFamily: 'Syne' }}>
              94.2%
            </div>
            <div className="text-gray-600 text-[11px]">Last 30 days · 0.3% false positives</div>
          </div>
        </div>

        {/* Chart Row */}
        <div className="grid grid-cols-[460px_1fr_360px] gap-6 mb-8">
          {/* Left: Typology Bar Chart */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-gray-900 text-sm font-bold mb-6" style={{ fontFamily: 'Syne' }}>
              Alert volume by typology
            </h3>
            <div className="text-xs text-gray-600 mb-4">Last 30 days</div>
            <div className="space-y-4">
              {typologyData.map((item, idx) => (
                <div key={idx}>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>{item.label}</span>
                    <span className="text-gray-900 font-bold">{item.value}</span>
                  </div>
                  <div className="relative h-6 bg-gray-100 rounded overflow-hidden">
                    <div
                      className="absolute h-full rounded"
                      style={{
                        width: `${(item.value / 47) * 100}%`,
                        backgroundColor: item.color,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Center: Line Chart */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-gray-900 text-sm font-bold mb-6" style={{ fontFamily: 'Syne' }}>
              Daily alert trend
            </h3>
            <div className="text-xs text-gray-600 mb-4">Last 30 days</div>
            <div className="relative h-[280px]">
              <svg className="w-full h-full">
                {/* Grid lines */}
                {[0, 20, 40, 60, 80].map((val, idx) => (
                  <g key={idx}>
                    <line
                      x1="0"
                      y1={`${100 - (val / 80) * 100}%`}
                      x2="100%"
                      y2={`${100 - (val / 80) * 100}%`}
                      stroke="#e0e0e0"
                      strokeWidth="1"
                      opacity="0.3"
                    />
                    <text
                      x="0"
                      y={`${100 - (val / 80) * 100}%`}
                      fill="#666666"
                      fontSize="10"
                      dy="4"
                    >
                      {val}
                    </text>
                  </g>
                ))}

                {/* Alert line (Union Bank Red) */}
                <polyline
                  points="10,60 20,45 30,50 40,35 50,40 60,25 70,30 80,20 90,15"
                  fill="none"
                  stroke="#E31E24"
                  strokeWidth="2"
                />
                <polyline
                  points="10,60 20,45 30,50 40,35 50,40 60,25 70,30 80,20 90,15 90,100 10,100"
                  fill="#E31E24"
                  opacity="0.08"
                />

                {/* Confirmed fraud line (darker red dashed) */}
                <polyline
                  points="10,80 20,75 30,70 40,65 50,60 60,50 70,45 80,35 90,30"
                  fill="none"
                  stroke="#d4183d"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                />
              </svg>
            </div>
            <div className="flex items-center gap-4 mt-4 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-[2px] bg-[#E31E24]" />
                <span className="text-gray-600">Alerts generated</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-[2px] bg-[#d4183d] border-dashed" style={{ borderTop: '2px dashed #d4183d', background: 'none' }} />
                <span className="text-gray-600">Confirmed fraud</span>
              </div>
            </div>
          </div>

          {/* Right: Investigators & System Health */}
          <div className="space-y-6">
            {/* Active cases by investigator */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="text-gray-900 text-sm font-bold mb-4" style={{ fontFamily: 'Syne' }}>
                Active cases by investigator
              </h3>
              <div className="space-y-3">
                {investigators.map((inv, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 p-2 rounded transition-colors ${
                      inv.isTop ? 'bg-[#E31E24] border-l-2 border-[#E31E24]' : 'bg-white hover:bg-gray-50'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                      inv.isTop ? 'bg-white text-[#E31E24]' : 'bg-gray-100 text-gray-900'
                    }`}>
                      {inv.initials}
                    </div>
                    <div className="flex-1">
                      <div className={`text-xs font-medium ${
                        inv.isTop ? 'text-white' : 'text-gray-900'
                      }`}>{inv.name}</div>
                      <div className={`text-[10px] ${inv.isTop ? 'text-white text-opacity-90' : 'text-gray-600'}`} style={{ fontFamily: 'DM Mono' }}>
                        {inv.cases} cases · {inv.avgTime} avg
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* System Health */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="text-gray-900 text-sm font-bold mb-4" style={{ fontFamily: 'Syne' }}>
                System health
              </h3>
              <div className="space-y-3">
                {[
                  { key: 'neo4j'    as const, label: 'Neo4j graph',      detail: '12.4M nodes · 89ms avg query' },
                  { key: 'postgres' as const, label: 'PostgreSQL',        detail: 'Cases & alerts store' },
                  { key: 'redis'    as const, label: 'Redis / pub-sub',   detail: 'Real-time alerts channel' },
                ].map(({ key, label, detail }) => {
                  const up = health ? health[key] : null;
                  return (
                    <div key={key} className="flex items-start gap-2">
                      <div className={`w-2 h-2 rounded-full mt-1 ${up === null ? 'bg-gray-300' : up ? 'bg-green-500' : 'bg-red-500'}`} />
                      <div className="flex-1">
                        <div className="text-gray-900 text-xs mb-1">{label}</div>
                        <div className="text-gray-600 text-[10px]" style={{ fontFamily: 'DM Mono' }}>
                          {up === null ? 'Checking…' : up ? detail : 'Unreachable'}
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 rounded-full mt-1 bg-green-500" />
                  <div className="flex-1">
                    <div className="text-gray-900 text-xs mb-1">Kafka ingestion</div>
                    <div className="text-gray-600 text-[10px]" style={{ fontFamily: 'DM Mono' }}>Normal · 42k events/min</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-gray-900 text-sm font-bold mb-4 flex items-center gap-2" style={{ fontFamily: 'Syne' }}>
            <Activity className="w-4 h-4" />
            Recent system events
          </h3>
          <div className="space-y-1 max-h-[200px] overflow-auto">
            {systemEvents.map((event, idx) => {
              const Icon = event.icon;
              return (
              <div
                key={idx}
                className={`flex items-center gap-4 py-2 px-3 rounded hover:bg-gray-50 transition-colors ${
                  idx === 0 ? 'border-l-2 border-[#E31E24] bg-gray-50' : ''
                }`}
              >
                <div className="text-gray-600 text-xs w-20" style={{ fontFamily: 'DM Mono' }}>
                  {event.time}
                </div>
                <Icon className="w-4 h-4 text-[#E31E24] flex-shrink-0" />
                <div className="flex-1 text-gray-900 text-xs">{event.desc}</div>
                <button
                  onClick={() => navigate('/')}
                  className="text-[#E31E24] hover:underline text-xs"
                  style={{ fontFamily: 'DM Mono' }}
                >
                  {event.ref}
                </button>
              </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}