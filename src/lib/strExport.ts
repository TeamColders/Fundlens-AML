import type { STRReport } from '../api/types';
import { getApiBase } from './apiBase';

export interface CaseDetailForStr {
  typology?: string;
  total_amount?: number;
  accounts_count?: number;
  duration_display?: string;
  confidence?: string;
  fatf_reference?: string;
  pmla_section?: string;
}

/** Build exportable STR text from current report fields (respects user edits). */
export function buildReportText(
  report: STRReport,
  detail?: CaseDetailForStr,
  caseId?: string,
): string {
  const today = new Date().toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
  const ref = caseId || report.case_id;
  const fatf = detail?.fatf_reference || report.regulatory_basis?.split('|').pop()?.trim() || 'FATF Typology';
  const pmla = detail?.pmla_section || 'Section 12 and Section 16';

  return `FIU-IND FORM STR-01 (DRAFT)
Report Date: ${today}
Filing Entity: Union Bank of India

CASE REF: ${ref}
TYPOLOGY: ${detail?.typology || ''}
RISK SCORE: ${detail?.confidence || ''} (GNN confidence)
ACCOUNTS INVOLVED: ${detail?.accounts_count ?? ''}
TOTAL AMOUNT: ₹${detail?.total_amount?.toLocaleString('en-IN') ?? ''}
PERIOD: ${detail?.duration_display || ''}

NARRATIVE:
${report.english_narrative || ''}

RECOMMENDED ACTION:
${report.recommended_action || ''}

REGULATORY BASIS:
PMLA 2002, ${pmla} | ${fatf}`;
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function downloadStrPdf(caseId: string): Promise<void> {
  const res = await fetch(`${getApiBase()}/str/${encodeURIComponent(caseId)}/pdf`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'PDF download failed');
  }
  const blob = await res.blob();
  downloadBlob(blob, `STR-${caseId}.pdf`);
}

export async function downloadStrText(caseId: string): Promise<void> {
  const res = await fetch(`${getApiBase()}/str/${encodeURIComponent(caseId)}/download`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Download failed');
  }
  const blob = await res.blob();
  downloadBlob(blob, `STR-${caseId}.txt`);
}
