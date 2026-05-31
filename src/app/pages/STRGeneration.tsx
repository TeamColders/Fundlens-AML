import {
  ArrowLeft,
  Check,
  Download,
  ExternalLink,
  Globe,
  Loader2,
  RefreshCw,
  Save,
} from 'lucide-react';
import { useNavigate } from 'react-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import MiniFlowGraph from '../components/MiniFlowGraph';
import { saveSTRDraft, submitSTR } from '../../api/client';
import { useSTRGeneration } from '../../hooks/useSTRGeneration';
import { useBlockchain } from '../../hooks/useBlockchain';
import { useAlertDetail } from '../../hooks/useAlerts';
import { usePersistCaseContext } from '../../hooks/useCaseContext';
import { useSelectedCaseId } from '../../hooks/useSelectedCaseId';
import type { STRReport } from '../../api/types';
import { buildReportText, downloadStrPdf, downloadStrText } from '../../lib/strExport';

export default function STRGeneration() {
  const navigate = useNavigate();
  const { caseId } = useSelectedCaseId();

  const { stage, message, progress, report, error, generating, generate } = useSTRGeneration();
  const { chain } = useBlockchain(caseId || null);
  const { detail, error: detailError } = useAlertDetail(caseId || null);
  usePersistCaseContext(caseId || null, detail);

  const [language, setLanguage] = useState<'EN' | 'HI'>('EN');
  const [draftSaved, setDraftSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState<'pdf' | 'txt' | null>(null);
  const [editedReport, setEditedReport] = useState<STRReport | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const autoGenCaseRef = useRef<string | null>(null);

  useEffect(() => {
    if (!caseId || autoGenCaseRef.current === caseId) return;
    autoGenCaseRef.current = caseId;
    generate(caseId);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- auto-run once per case
  }, [caseId]);

  useEffect(() => {
    if (report) setEditedReport(report);
  }, [report]);

  const activeReport = editedReport || report;

  const fullText = useMemo(
    () =>
      activeReport
        ? buildReportText(activeReport, detail ?? undefined, caseId)
        : '',
    [activeReport, detail, caseId],
  );

  const narrativeText =
    language === 'EN'
      ? activeReport?.english_narrative || ''
      : activeReport?.hindi_narrative || '[Hindi translation pending]';

  const recommendedAction = activeReport?.recommended_action || '';
  const regulatoryBasis = activeReport?.regulatory_basis || '';

  const today = new Date().toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });

  const handleSaveDraft = useCallback(async () => {
    if (!caseId || !activeReport) return;
    setSaving(true);
    try {
      const text = buildReportText(activeReport, detail ?? undefined, caseId);
      await saveSTRDraft(caseId, {
        full_report_text: text,
        english_narrative: activeReport.english_narrative,
        hindi_narrative: activeReport.hindi_narrative,
        recommended_action: activeReport.recommended_action,
        regulatory_basis: activeReport.regulatory_basis,
        investigator_id: 'investigator-001',
      });
      setEditedReport({ ...activeReport, full_report_text: text });
      setDraftSaved(true);
      setTimeout(() => setDraftSaved(false), 3000);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setSaving(false);
    }
  }, [caseId, activeReport, fullText]);

  const handleDownloadPdf = async () => {
    if (!caseId) return;
    setDownloading('pdf');
    try {
      if (activeReport) {
        const text = buildReportText(activeReport, detail ?? undefined, caseId);
        await saveSTRDraft(caseId, {
          full_report_text: text,
          english_narrative: activeReport.english_narrative,
          hindi_narrative: activeReport.hindi_narrative,
          recommended_action: activeReport.recommended_action,
          regulatory_basis: activeReport.regulatory_basis,
        });
      }
      await downloadStrPdf(caseId);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setDownloading(null);
    }
  };

  const handleDownloadTxt = async () => {
    if (!caseId) return;
    setDownloading('txt');
    try {
      if (activeReport) {
        const text = buildReportText(activeReport, detail ?? undefined, caseId);
        await saveSTRDraft(caseId, {
          full_report_text: text,
          english_narrative: activeReport.english_narrative,
          hindi_narrative: activeReport.hindi_narrative,
          recommended_action: activeReport.recommended_action,
          regulatory_basis: activeReport.regulatory_basis,
        });
      }
      await downloadStrText(caseId);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setDownloading(null);
    }
  };

  const handleSubmit = async () => {
    if (!caseId || !fullText) return;
    setSubmitting(true);
    try {
      const result = await submitSTR(caseId, fullText, 'investigator-001');
      alert(`Submitted to FIU-IND\nReference: ${result.fiu_reference}`);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const stages = [
    { label: 'Analysing pattern', key: 'analysing_pattern' },
    { label: 'Compiling evidence', key: 'compiling_evidence' },
    { label: 'Drafting narrative', key: 'drafting_narrative' },
  ];

  const getStageStatus = (stageKey: string) => {
    if (!stage) return 'pending';
    const stageOrder = ['analysing_pattern', 'compiling_evidence', 'drafting_narrative', 'complete'];
    const currentIdx = stageOrder.indexOf(stage);
    const targetIdx = stageOrder.indexOf(stageKey);
    if (currentIdx > targetIdx) return 'complete';
    if (currentIdx === targetIdx) return 'active';
    return 'pending';
  };

  if (!caseId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-sm text-gray-600">Select a case from the investigation dashboard first.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="h-[64px] bg-white border-b border-gray-200 flex items-center justify-between px-8">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">Back to Investigation</span>
        </button>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 mr-2" style={{ fontFamily: 'DM Mono' }}>
            {caseId}
          </span>
          <button
            type="button"
            disabled={generating}
            onClick={() => generate(caseId)}
            className="px-3 py-2 border border-gray-300 rounded text-sm flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            Regenerate
          </button>
          <button
            type="button"
            onClick={handleSaveDraft}
            disabled={!activeReport || saving}
            className={`px-4 py-2 border transition-colors rounded text-sm flex items-center gap-2 ${
              draftSaved ? 'bg-green-50 border-green-500 text-green-700' : 'border-gray-400 text-gray-600 hover:bg-gray-100'
            }`}
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : draftSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {draftSaved ? 'Draft saved' : 'Save draft'}
          </button>
          <button
            type="button"
            onClick={handleDownloadTxt}
            disabled={!activeReport || downloading !== null}
            className="px-4 py-2 border border-gray-400 text-gray-600 hover:bg-gray-100 rounded text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {downloading === 'txt' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Download .txt
          </button>
          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={!activeReport || downloading !== null}
            className="px-4 py-2 border border-[#E31E24] text-[#E31E24] hover:bg-red-50 rounded text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {downloading === 'pdf' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Download PDF
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!activeReport || submitting}
            className="px-6 py-2 bg-[#E31E24] text-white hover:bg-[#d4183d] rounded text-sm font-semibold flex items-center gap-2 disabled:opacity-50"
            style={{ fontFamily: 'Syne' }}
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ExternalLink className="w-4 h-4" />}
            Submit to FIU-IND
          </button>
        </div>
      </div>

      <div className="flex h-[calc(100vh-64px)]">
        <div className="w-1/2 border-r border-gray-200 p-8 overflow-auto">
          <div className="mb-6">
            <h3 className="text-sm text-gray-600 mb-3">Case overview — {caseId}</h3>
            <MiniFlowGraph caseId={caseId} />
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-5 mb-6">
            <h3 className="text-sm text-gray-600 mb-4">Case summary (fed to Gemini)</h3>
            <div className="space-y-3 text-sm" style={{ fontFamily: 'DM Mono' }}>
              <div className="flex justify-between">
                <span className="text-gray-600">Typology:</span>
                <span className="text-gray-900">{detail?.typology || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Amount:</span>
                <span className="text-gray-900">₹{detail?.total_amount?.toLocaleString('en-IN') || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Accounts:</span>
                <span className="text-gray-900">{detail?.accounts_count ?? '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">GNN confidence:</span>
                <span className="text-[#E31E24] font-bold">{detail?.confidence || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Model:</span>
                <span className="text-gray-900">{activeReport?.model_used || (generating ? 'Gemini…' : '—')}</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
            <h3 className="text-sm text-gray-600 mb-4">Evidence chain</h3>
            <div className="space-y-2">
              {(chain?.blocks || []).slice(0, 4).map((block) => (
                <div key={block.block_id} className="flex items-center gap-2 text-xs bg-white border rounded p-2" style={{ fontFamily: 'DM Mono' }}>
                  <Check className="w-3 h-3 text-[#E31E24]" />
                  <span>#{block.block_id} · {block.event_label || block.event_type}</span>
                </div>
              ))}
              {!chain?.blocks?.length && (
                <p className="text-xs text-gray-500">Blocks recorded on generation & submit</p>
              )}
            </div>
          </div>
        </div>

        <div className="w-1/2 p-8 overflow-auto flex flex-col">
          <div className="flex items-center gap-4 mb-6">
            {stages.map((step, idx) => {
              const status = getStageStatus(step.key);
              return (
                <div key={step.key} className="flex items-center gap-2">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      status === 'complete'
                        ? 'bg-[#E31E24]'
                        : status === 'active'
                          ? 'border-2 border-[#E31E24]'
                          : 'border-2 border-gray-300'
                    }`}
                  >
                    {status === 'complete' ? (
                      <Check className="w-4 h-4 text-white" />
                    ) : status === 'active' ? (
                      <div className="w-2 h-2 bg-[#E31E24] rounded-full animate-pulse" />
                    ) : null}
                  </div>
                  <span className={`text-xs ${status === 'pending' ? 'text-gray-400' : 'text-gray-600'}`}>
                    {step.label}
                  </span>
                  {idx < 2 && <div className={`w-6 h-0.5 ${status === 'pending' ? 'bg-gray-300' : 'bg-[#E31E24]'}`} />}
                </div>
              );
            })}
            {generating && (
              <span className="text-xs text-gray-500 ml-2">{progress}% · {message}</span>
            )}
          </div>

          {detailError && !detail && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
              Case summary unavailable ({detailError}). Run{' '}
              <code className="text-xs">python3 backend/database/demo_seed.py --mode local</code>{' '}
              or pick a case from the dashboard.
            </div>
          )}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          {activeReport?.model_used === 'fallback-template' && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-sm">
              <p className="font-semibold mb-1">Template draft only — Gemini did not run</p>
              <p className="text-xs text-amber-800">
                {activeReport.fallback_reason ||
                  'Set a valid GEMINI_API_KEY in .env, install google-genai, and restart the API.'}
              </p>
              <p className="text-xs text-amber-700 mt-2">
                Get a key at{' '}
                <a
                  href="https://aistudio.google.com/apikey"
                  target="_blank"
                  rel="noreferrer"
                  className="underline"
                >
                  Google AI Studio
                </a>
                . If you see quota errors, wait 1–2 minutes before Regenerate.
              </p>
            </div>
          )}
          {activeReport?.partial && activeReport.model_used !== 'fallback-template' && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900 text-sm">
              English STR generated; Hindi section was skipped due to API limits. You can edit the
              Hindi tab manually or click Regenerate later.
            </div>
          )}

          <div className="flex-1 bg-gray-50 border border-[#E31E24] rounded-xl p-6 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-3">
              <div className="px-3 py-1 bg-[#E31E24] text-white rounded text-xs font-bold">STR-01 DRAFT</div>
              <div className="flex items-center gap-2">
                <Globe className="w-3 h-3 text-gray-500" />
                <button
                  type="button"
                  onClick={() => setLanguage('EN')}
                  className={`px-2 py-0.5 rounded text-xs ${language === 'EN' ? 'bg-[#E31E24] text-white' : 'text-gray-600'}`}
                >
                  EN
                </button>
                <button
                  type="button"
                  onClick={() => setLanguage('HI')}
                  className={`px-2 py-0.5 rounded text-xs ${language === 'HI' ? 'bg-[#E31E24] text-white' : 'text-gray-600'}`}
                >
                  HI
                </button>
              </div>
            </div>

            {generating && !activeReport ? (
              <div className="flex-1 flex items-center justify-center gap-2 text-gray-500">
                <Loader2 className="w-6 h-6 animate-spin text-[#E31E24]" />
                <span className="text-sm">{message || 'Gemini is drafting your report…'}</span>
              </div>
            ) : (
              <div className="flex-1 overflow-auto text-[11px] leading-relaxed text-gray-700 space-y-4" style={{ fontFamily: 'DM Mono' }}>
                <div className="font-bold text-sm">FIU-IND FORM STR-01 (DRAFT)</div>
                <div>
                  <div>Report Date: {today}</div>
                  <div>Filing Entity: Union Bank of India</div>
                </div>
                <div className="border-t border-gray-300 pt-3">
                  <div className="font-bold">CASE REF: {caseId}</div>
                  <div>TYPOLOGY: {detail?.typology}</div>
                  <div>RISK SCORE: {detail?.confidence} (GNN)</div>
                  <div>ACCOUNTS: {detail?.accounts_count}</div>
                  <div>TOTAL: ₹{detail?.total_amount?.toLocaleString('en-IN')}</div>
                  <div>PERIOD: {detail?.duration_display}</div>
                </div>
                <div>
                  <div className="font-bold mb-2">NARRATIVE:</div>
                  <textarea
                    className="w-full min-h-[140px] p-2 border border-gray-200 rounded bg-white text-gray-800 resize-y"
                    value={language === 'EN' ? activeReport?.english_narrative || '' : activeReport?.hindi_narrative || ''}
                    onChange={(e) => {
                      if (!activeReport) return;
                      setEditedReport({
                        ...activeReport,
                        ...(language === 'EN'
                          ? { english_narrative: e.target.value }
                          : { hindi_narrative: e.target.value }),
                      });
                    }}
                  />
                </div>
                <div>
                  <div className="font-bold mb-2">RECOMMENDED ACTION:</div>
                  <textarea
                    className="w-full min-h-[60px] p-2 border border-gray-200 rounded bg-white resize-y"
                    value={recommendedAction}
                    onChange={(e) =>
                      activeReport &&
                      setEditedReport({ ...activeReport, recommended_action: e.target.value })
                    }
                  />
                </div>
                <div>
                  <div className="font-bold mb-2">REGULATORY BASIS:</div>
                  <textarea
                    className="w-full min-h-[40px] p-2 border border-gray-200 rounded bg-white resize-y"
                    value={regulatoryBasis}
                    onChange={(e) =>
                      activeReport &&
                      setEditedReport({ ...activeReport, regulatory_basis: e.target.value })
                    }
                  />
                </div>
                <p className="text-[10px] text-gray-500">
                  {activeReport?.word_count ?? 0} words · {activeReport?.page_estimate ?? 1} pages ·{' '}
                  {activeReport?.generation_time_s != null ? `${activeReport.generation_time_s}s` : '—'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
