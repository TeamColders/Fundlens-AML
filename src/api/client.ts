/**
 * FundLens — API client for FastAPI backend.
 *
 * All endpoint functions, error handling, and SSE streaming.
 * Uses native fetch (no axios dependency needed).
 */
import type {
  AlertsResponse, AlertDetail, Subgraph,
  STRReport, STRProgressEvent,
  EntityProfile, AnalyticsData,
  BlockchainData, ChainVerification,
  NLQueryResult, HealthStatus,
} from './types';

// ── Configuration ────────────────────────────────────────────────
const API_BASE = '/api';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}


// ── Health ────────────────────────────────────────────────────────
export async function fetchHealth(): Promise<HealthStatus> {
  return apiFetch('/health');
}


// ── Alerts ───────────────────────────────────────────────────────
export async function fetchAlerts(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<AlertsResponse> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.limit) qs.set('limit', String(params.limit));
  if (params?.offset) qs.set('offset', String(params.offset));
  const query = qs.toString() ? `?${qs}` : '';
  return apiFetch(`/alerts${query}`);
}

export async function fetchAlert(caseId: string): Promise<AlertDetail> {
  return apiFetch(`/alerts/${caseId}`);
}

export async function updateAlertStatus(
  caseId: string, status: string, investigatorId: string, notes?: string,
): Promise<void> {
  await apiFetch(`/alerts/${caseId}/status`, {
    method: 'POST',
    body: JSON.stringify({ status, investigator_id: investigatorId, notes }),
  });
}


// ── Graph ────────────────────────────────────────────────────────
export async function fetchGraph(caseId: string): Promise<Subgraph> {
  return apiFetch(`/graph/${caseId}`);
}


// ── Entities ─────────────────────────────────────────────────────
export async function fetchEntity(accountId: string): Promise<EntityProfile> {
  return apiFetch(`/entities/${accountId}`);
}


// ── STR Generation (SSE streaming) ───────────────────────────────
export function streamSTRGeneration(
  caseId: string,
  onEvent: (event: STRProgressEvent) => void,
  onError?: (error: Error) => void,
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/str/${caseId}/generate`, {
        method: 'POST',
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`STR generation failed: ${res.status}`);
      if (!res.body) throw new Error('No response body');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const chunk of lines) {
          if (chunk.startsWith('data: ')) {
            try {
              const data = JSON.parse(chunk.slice(6)) as STRProgressEvent;
              onEvent(data);
            } catch {
              // skip malformed events
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        onError?.(err as Error);
      }
    }
  })();

  return () => controller.abort();
}

export async function fetchSTR(caseId: string): Promise<STRReport> {
  return apiFetch(`/str/${caseId}`);
}

export async function submitSTR(
  caseId: string, reportText: string, investigatorId: string, notes?: string,
): Promise<{ success: boolean; submission_id: string; fiu_reference: string }> {
  return apiFetch(`/str/${caseId}/submit`, {
    method: 'POST',
    body: JSON.stringify({ report_text: reportText, investigator_id: investigatorId, notes }),
  });
}


// ── Analytics ────────────────────────────────────────────────────
export async function fetchAnalytics(): Promise<AnalyticsData> {
  return apiFetch('/analytics');
}


// ── Blockchain ───────────────────────────────────────────────────
export async function fetchBlockchain(caseId: string): Promise<BlockchainData> {
  return apiFetch(`/blockchain/${caseId}`);
}

export async function verifyBlockchain(caseId: string): Promise<ChainVerification> {
  return apiFetch(`/blockchain/${caseId}/verify`);
}


// ── NL Query ─────────────────────────────────────────────────────
export async function queryGraph(query: string): Promise<NLQueryResult> {
  return apiFetch('/query', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}
