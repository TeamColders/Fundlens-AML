import { ChevronDown, FileDown, Link2, Loader2, RefreshCw, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { approveStrEvidence, exportBlockchainEvidence } from '../../api/client';
import type { BlockRecord } from '../../api/types';
import { useBlockchain } from '../../hooks/useBlockchain';
import { useAlertDetail } from '../../hooks/useAlerts';
import { useSelectedCaseId } from '../../hooks/useSelectedCaseId';
import { usePersistCaseContext } from '../../hooks/useCaseContext';
import { pathWithCase } from '../../lib/selectedCase';
import { useNavigate } from 'react-router';

function integrityBanner(
  verification: { valid?: boolean; empty?: boolean; integrity_label?: string } | null,
  chainEmpty: boolean,
) {
  if (chainEmpty || verification?.empty) {
    return { label: 'NO CHAIN', tone: 'amber' as const, sub: 'No evidence blocks sealed yet' };
  }
  if (verification?.valid === false || verification?.integrity_label === 'COMPROMISED') {
    return { label: 'COMPROMISED', tone: 'red' as const, sub: 'Hash linkage check failed' };
  }
  return { label: 'VERIFIED', tone: 'green' as const, sub: 'SHA-256 chain intact' };
}

export default function BlockchainAudit() {
  const navigate = useNavigate();
  const [expandedBlock, setExpandedBlock] = useState<number | null>(null);
  const [exporting, setExporting] = useState(false);
  const [approving, setApproving] = useState(false);
  const { caseId } = useSelectedCaseId();
  const { detail } = useAlertDetail(caseId || null);
  usePersistCaseContext(caseId || null, detail);
  const { chain, verification, loading, error, refetch } = useBlockchain(caseId || null);

  const blocks: BlockRecord[] = chain?.blocks ?? [];
  const chainEmpty = blocks.length === 0;
  const banner = integrityBanner(verification, chainEmpty);
  const modeLabel = chain?.mode === 'PRODUCTION' ? 'Hyperledger Fabric' : 'FundLens demo ledger (SHA-256)';

  const handleExport = async () => {
    if (!caseId) return;
    setExporting(true);
    try {
      const blob = await exportBlockchainEvidence(caseId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `evidence-audit-${caseId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setExporting(false);
    }
  };

  const handleVerify = () => refetch();

  const handleApprove = async () => {
    if (!caseId) return;
    setApproving(true);
    try {
      await approveStrEvidence(caseId, { actor_id: 'supervisor', notes: 'STR draft approved via audit trail' });
      await refetch();
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setApproving(false);
    }
  };

  if (!caseId) {
    return (
      <div className="min-h-screen bg-white p-8">
        <h1 className="text-gray-900 text-3xl font-bold mb-2" style={{ fontFamily: 'Syne' }}>
          Evidence audit trail
        </h1>
        <p className="text-gray-600 text-sm">Select a case from the investigation dashboard to view its evidence chain.</p>
      </div>
    );
  }

  if (loading && !chain) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#E31E24]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <h1 className="text-gray-900 text-3xl font-bold mb-2" style={{ fontFamily: 'Syne' }}>
            Evidence audit trail
          </h1>
          <p className="text-gray-700 text-sm">
            Case <span style={{ fontFamily: 'DM Mono' }}>{caseId}</span>
            {detail?.typology ? ` · ${detail.typology}` : ''}
            {chain?.risk_level ? ` · ${chain.risk_level} risk` : ''}
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            onClick={() => refetch()}
            className="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded text-sm flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting || chainEmpty}
            className="px-4 py-2 border border-gray-700 text-gray-700 hover:bg-gray-100 disabled:opacity-50 rounded text-sm flex items-center gap-2"
          >
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
            Export JSON
          </button>
          <button
            type="button"
            onClick={handleVerify}
            className="px-4 py-2 border border-[#E31E24] text-[#E31E24] hover:bg-red-50 rounded text-sm flex items-center gap-2"
          >
            <ShieldCheck className="w-4 h-4" />
            Re-verify chain
          </button>
          <button
            type="button"
            onClick={() => navigate(pathWithCase('/str-generation', caseId))}
            className="px-4 py-2 bg-gray-900 text-white rounded text-sm"
          >
            Open STR
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 text-sm rounded-lg">{error}</div>
      )}

      <div className="bg-white border-l-4 border-[#E31E24] rounded-lg p-6 mb-8 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <Link2 className="w-8 h-8 text-[#E31E24]" />
          <div>
            <div className="text-gray-900 font-semibold mb-1" style={{ fontFamily: 'Syne' }}>
              Evidence cryptographically sealed · {modeLabel}
            </div>
            <div className="text-gray-700 text-sm" style={{ fontFamily: 'DM Mono' }}>
              {blocks.length} block{blocks.length === 1 ? '' : 's'}
              {chain?.network ? ` · Network: ${chain.network}` : ''}
            </div>
            <div className="text-gray-500 text-xs mt-1">{banner.sub}</div>
          </div>
        </div>
        <div
          className={`px-6 py-3 rounded-lg border-2 ${
            banner.tone === 'green'
              ? 'bg-green-500 border-green-500 text-white'
              : banner.tone === 'red'
                ? 'bg-red-500 border-red-500 text-white'
                : 'bg-amber-100 border-amber-400 text-amber-900'
          }`}
        >
          <span className="text-xl font-bold" style={{ fontFamily: 'Syne' }}>
            {banner.label}
          </span>
        </div>
      </div>

      {chainEmpty ? (
        <div className="max-w-2xl mx-auto text-center py-16 border border-dashed border-gray-300 rounded-xl">
          <p className="text-gray-700 mb-4">No blocks found. Opening case detail or generating an STR will seal evidence.</p>
          <button type="button" onClick={() => refetch()} className="text-[#E31E24] hover:underline text-sm">
            Initialize trail
          </button>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto">
          <div className="relative">
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-[#E31E24] opacity-30" />
            <div className="space-y-4">
              {blocks.map((block) => (
                <div key={block.block_id} className="relative">
                  <div className="absolute left-8 top-6 w-3 h-3 rounded-full bg-[#E31E24] border-2 border-white transform -translate-x-1/2 z-10" />
                  <div className="ml-16 bg-white border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedBlock(expandedBlock === block.block_id ? null : block.block_id)
                      }
                      className="w-full p-5 text-left hover:bg-gray-50"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3 flex-wrap">
                          <span className="text-[#E31E24] font-bold" style={{ fontFamily: 'DM Mono' }}>
                            Block #{block.block_id}
                          </span>
                          <span
                            className={`px-2 py-1 text-white rounded text-xs font-semibold ${
                              block.verified !== false ? 'bg-green-500' : 'bg-red-500'
                            }`}
                          >
                            {block.verified !== false ? 'Verified' : 'Tampered'}
                          </span>
                          <span className="text-xs text-gray-500">{block.event_type}</span>
                        </div>
                        <span className="text-gray-700 text-xs" style={{ fontFamily: 'DM Mono' }}>
                          {block.display_timestamp || block.timestamp}
                        </span>
                      </div>
                      <div className="text-gray-900 font-semibold mb-1">{block.event_label}</div>
                      <div className="text-gray-700 text-sm">{block.details}</div>
                      <div className="text-gray-500 text-xs mt-2" style={{ fontFamily: 'DM Mono' }}>
                        {block.short_hash} · actor: {block.actor_id || 'system'}
                      </div>
                    </button>
                    {expandedBlock === block.block_id && (
                      <div className="px-5 pb-5 border-t border-gray-100 bg-gray-50 text-xs space-y-3" style={{ fontFamily: 'DM Mono' }}>
                        <div>
                          <div className="text-gray-600 mb-1">Block hash</div>
                          <div className="text-[#E31E24] break-all">{block.block_hash}</div>
                        </div>
                        <div>
                          <div className="text-gray-600 mb-1">Previous hash</div>
                          <div className="break-all">{block.prev_hash}</div>
                        </div>
                        <div>
                          <div className="text-gray-600 mb-1">Payload hash (SHA-256)</div>
                          <div className="break-all">{block.payload_hash}</div>
                        </div>
                        {block.payload_preview && (
                          <div>
                            <div className="text-gray-600 mb-1">Payload preview</div>
                            <pre className="bg-white border border-gray-200 rounded p-2 overflow-x-auto text-[11px]">
                              {JSON.stringify(block.payload_preview, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto mt-8 grid gap-4 md:grid-cols-2">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-gray-900 font-semibold mb-3" style={{ fontFamily: 'Syne' }}>
            Supervisor approval
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Record STR draft review on the evidence chain before FIU submission.
          </p>
          <button
            type="button"
            onClick={handleApprove}
            disabled={approving || chainEmpty}
            className="px-4 py-2 bg-[#E31E24] text-white rounded text-sm font-semibold disabled:opacity-50 flex items-center gap-2"
          >
            {approving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            Record supervisor approval
          </button>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => setExpandedBlock(expandedBlock === -1 ? null : -1)}
            className="w-full p-5 flex items-center justify-between hover:bg-gray-50"
          >
            <span className="text-gray-900 font-semibold" style={{ fontFamily: 'Syne' }}>
              Independent verification
            </span>
            <ChevronDown className={`w-5 h-5 ${expandedBlock === -1 ? 'rotate-180' : ''}`} />
          </button>
          {expandedBlock === -1 && verification && (
            <div className="px-5 pb-5 border-t border-gray-200 text-sm space-y-3">
              <p>
                Verified at: <span style={{ fontFamily: 'DM Mono' }}>{verification.verified_at}</span>
              </p>
              <p>Mode: {verification.mode}</p>
              <p>Blocks checked: {verification.block_count}</p>
              {verification.broken_at_block != null && (
                <p className="text-red-600">Broken at block #{verification.broken_at_block}</p>
              )}
              <div className="bg-gray-50 border rounded p-3 text-xs" style={{ fontFamily: 'DM Mono' }}>
                Recompute: block_hash = SHA-256(block_id | prev_hash | payload_hash | timestamp)
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
