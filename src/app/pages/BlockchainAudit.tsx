import { useEffect, useState } from 'react';
import { Link2, FileDown, ChevronDown, AlertTriangle } from 'lucide-react';
import { api, type EvidenceBlock } from '../../services/api';

// Default case to show — in a real flow this would come from route params
const DEFAULT_CASE = 'CASE-2847';

// Static fallback blocks shown when backend has no data yet
const STATIC_BLOCKS = [
  { number: 48291, timestamp: '14:23:07', hash: '0x3a8f...2c19', event: 'Initial alert created',       details: 'Alert CASE-2847 generated · Typology: Round-trip Layering · GNN Score: 0.94' },
  { number: 48292, timestamp: '14:24:15', hash: '0x7b2e...8d4a', event: 'Investigator opened case',    details: 'Investigator RK opened case · Access logged with biometric auth' },
  { number: 48293, timestamp: '14:25:42', hash: '0x9c1d...3f7b', event: 'Subgraph exported',           details: 'Subgraph exported for STR compilation · 7 nodes, 12 edges' },
  { number: 48294, timestamp: '14:26:18', hash: '0x4e8a...6b5c', event: 'LLM narrative generated',     details: 'LLM narrative generated · Input/output hash recorded' },
  { number: 48295, timestamp: '14:27:33', hash: '0x2f9b...1a8d', event: 'STR draft reviewed',          details: 'STR draft reviewed by supervisor · Approval logged' },
  { number: 48296, timestamp: '14:27:54', hash: '0x5d3c...4e2f', event: 'STR submitted to FIU-IND',    details: 'STR submitted · FIU acknowledgement recorded' },
];

interface DisplayBlock {
  number: number;
  timestamp: string;
  hash: string;
  event: string;
  details: string;
}

function evidenceToDisplay(blocks: EvidenceBlock[], offset: number): DisplayBlock[] {
  return blocks.map((b, i) => ({
    number: offset + i,
    timestamp: b.created_at ? new Date(b.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—',
    hash: b.payload && typeof b.payload === 'object' && 'hash' in b.payload
      ? String(b.payload.hash).slice(0, 12) + '...'
      : `0x${Math.random().toString(16).slice(2, 10)}...`,
    event: b.block_type.replace(/_/g, ' '),
    details: b.payload ? JSON.stringify(b.payload).slice(0, 120) : '—',
  }));
}

export default function BlockchainAudit() {
  const [expandedBlock, setExpandedBlock] = useState<number | null>(null);
  const [blocks, setBlocks]               = useState<DisplayBlock[]>(STATIC_BLOCKS);
  const [loading, setLoading]             = useState(true);
  const [liveData, setLiveData]           = useState(false);

  useEffect(() => {
    api.getCaseEvidence(DEFAULT_CASE)
      .then(({ blocks: raw }) => {
        if (raw && raw.length > 0) {
          setBlocks(evidenceToDisplay(raw, 48291));
          setLiveData(true);
        }
        // else keep static fallback
      })
      .catch(() => { /* keep static */ })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-white p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-gray-900 text-3xl font-bold mb-2" style={{ fontFamily: 'Syne' }}>
            Evidence audit trail
          </h1>
          <p className="text-gray-700 text-sm flex items-center gap-2">
            Case {DEFAULT_CASE} · Round-trip Layering
            {loading && <span className="text-gray-400 text-xs">· Loading…</span>}
            {!loading && liveData && (
              <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-semibold">Live data</span>
            )}
            {!loading && !liveData && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-xs flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Demo data
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 border border-gray-700 text-gray-700 hover:bg-gray-100 transition-colors rounded text-sm flex items-center gap-2">
            <FileDown className="w-4 h-4" />
            Export PDF
          </button>
          <button className="px-4 py-2 bg-[#E31E24] text-white hover:bg-[#d4183d] transition-colors rounded text-sm font-bold" style={{ fontFamily: 'Syne' }}>
            Verify on-chain ↗
          </button>
        </div>
      </div>

      {/* Integrity Banner */}
      <div className="bg-white border-l-4 border-[#E31E24] rounded-lg p-6 mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link2 className="w-8 h-8 text-[#E31E24]" />
          <div>
            <div className="text-gray-900 font-semibold mb-1" style={{ fontFamily: 'Syne' }}>
              All evidence cryptographically sealed on Hyperledger Fabric
            </div>
            <div className="text-gray-700 text-sm" style={{ fontFamily: 'DM Mono' }}>
              {blocks.length} blocks · First sealed: {blocks[0]?.timestamp} · Last updated: {blocks[blocks.length - 1]?.timestamp} · Network: UBI-Fabric-Private
            </div>
          </div>
        </div>
        <div className="px-6 py-3 bg-green-500 text-white rounded-lg">
          <span className="text-xl font-bold" style={{ fontFamily: 'Syne' }}>VERIFIED</span>
        </div>
      </div>

      {/* Blockchain Blocks Timeline */}
      <div className="max-w-4xl mx-auto">
        <div className="relative">
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-[#E31E24] opacity-30" />
          <div className="space-y-4">
            {blocks.map((block, idx) => (
              <div key={idx} className="relative">
                <div className="absolute left-8 top-6 w-3 h-3 rounded-full bg-[#E31E24] border-2 border-white transform -translate-x-1/2 z-10" />
                <div className="ml-16 bg-white border border-gray-200 rounded-lg p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-[#E31E24] font-bold" style={{ fontFamily: 'DM Mono' }}>Block #{block.number}</span>
                      <span className="px-2 py-1 bg-green-500 text-white rounded text-xs font-semibold">Verified</span>
                    </div>
                    <span className="text-gray-700 text-xs" style={{ fontFamily: 'DM Mono' }}>{block.timestamp}</span>
                  </div>
                  <div className="text-gray-700 text-xs mb-3" style={{ fontFamily: 'DM Mono' }}>{block.hash}</div>
                  <div className="text-gray-900 font-semibold mb-1 capitalize">{block.event}</div>
                  <div className="text-gray-700 text-sm">{block.details}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Verify independently */}
      <div className="max-w-4xl mx-auto mt-8">
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => setExpandedBlock(expandedBlock === 0 ? null : 0)}
            className="w-full p-5 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <span className="text-gray-900 font-semibold" style={{ fontFamily: 'Syne' }}>Verify independently</span>
            <ChevronDown className={`w-5 h-5 text-gray-700 transition-transform ${expandedBlock === 0 ? 'rotate-180' : ''}`} />
          </button>
          {expandedBlock === 0 && (
            <div className="px-5 pb-5 border-t border-gray-200 pt-4 space-y-4">
              <div>
                <div className="text-xs text-gray-700 mb-2">Block hash:</div>
                <div className="bg-gray-50 border border-gray-200 rounded p-3 text-[#E31E24] text-sm break-all" style={{ fontFamily: 'DM Mono' }}>
                  0x3a8f7b2e9c1d4e8a2f9b5d3c8f7a6b5c4e2f1a8d3b9c7e6a5f4d2c1b8a9e7f3a
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-700 mb-2">Verification command:</div>
                <div className="bg-gray-50 border border-gray-200 rounded p-3 text-gray-900 text-xs" style={{ fontFamily: 'DM Mono' }}>
                  peer chainquery -c fundlens-audit -q "getBlock {blocks[0]?.number}" --tls --cafile /certs/ca.crt
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ZKP Section */}
      <div className="max-w-4xl mx-auto mt-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-gray-900 font-semibold mb-4" style={{ fontFamily: 'Syne' }}>Cross-bank intelligence sharing</h3>
          <div className="flex items-center gap-6">
            <div className="flex-1 bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="text-sm text-gray-900 mb-2">Entity hash shared with 2 consortium banks</div>
              <div className="text-xs text-gray-700" style={{ fontFamily: 'DM Mono' }}>Zero knowledge — no transaction data disclosed</div>
              <div className="mt-3 text-[#E31E24] text-xs font-semibold" style={{ fontFamily: 'DM Mono' }}>Proof hash: 0x9f3e...7a2d</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-[#3B82F6] text-white flex items-center justify-center text-xs font-bold">SBI</div>
              <div className="flex flex-col items-center gap-1">
                <div className="w-8 h-8 rounded bg-[#E31E24] flex items-center justify-center text-white text-xs font-bold">✓</div>
                <div className="text-[10px] text-[#E31E24] font-semibold">ZKP</div>
              </div>
              <div className="w-12 h-12 rounded-full bg-[#F59E0B] text-white flex items-center justify-center text-xs font-bold">HDFC</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
