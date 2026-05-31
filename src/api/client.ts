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
  BlockchainData, BlockRecord, ChainVerification,
  NLQueryResult, HealthStatus,
  PlatformConfig, MobileDashboard, AuditLogEntry, ConfigUser,
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

export async function addEntityToWatchlist(accountId: string): Promise<{
  account_id: string;
  on_watchlist: boolean;
  enhanced_monitoring: boolean;
  message: string;
}> {
  return apiFetch(`/entities/${accountId}/watchlist`, { method: 'POST' });
}

export async function flagEntityEnhancedMonitoring(accountId: string): Promise<{
  account_id: string;
  on_watchlist: boolean;
  enhanced_monitoring: boolean;
  message: string;
}> {
  return apiFetch(`/entities/${accountId}/enhanced-monitoring`, { method: 'POST' });
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

export async function saveSTRDraft(
  caseId: string,
  payload: {
    full_report_text: string;
    english_narrative?: string;
    hindi_narrative?: string;
    recommended_action?: string;
    regulatory_basis?: string;
    investigator_id?: string;
  },
): Promise<{ success: boolean; case_id: string; saved_at: string }> {
  return apiFetch(`/str/${caseId}/draft`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchSTRDraft(caseId: string): Promise<STRReport> {
  return apiFetch(`/str/${caseId}/draft`);
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

export async function exportBlockchainEvidence(caseId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/blockchain/${caseId}/export`);
  if (!res.ok) {
    throw new Error(`Export failed: ${res.status}`);
  }
  return res.blob();
}

export async function approveStrEvidence(
  caseId: string,
  body: { actor_id?: string; notes?: string } = {},
): Promise<{ success: boolean; block: BlockRecord }> {
  return apiFetch(`/blockchain/${caseId}/approve`, {
    method: 'POST',
    body: JSON.stringify({
      actor_id: body.actor_id || 'supervisor',
      notes: body.notes || '',
      payload: {},
    }),
  });
}


// ── Configuration ──────────────────────────────────────────────────
export async function fetchPlatformConfig(): Promise<PlatformConfig> {
  return apiFetch('/config');
}

export async function updateConfigThresholds(body: {
  velocity_threshold_lakh?: number;
  dormancy_months?: number;
  gnn_confidence_pct?: number;
  actor_id?: string;
}): Promise<{ success: boolean; thresholds: PlatformConfig['thresholds'] }> {
  return apiFetch('/config/thresholds', {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export async function updateFiuSettings(body: {
  endpoint?: string;
  enabled?: boolean;
  auto_submit?: boolean;
  actor_id?: string;
}): Promise<{ success: boolean; fiu: PlatformConfig['fiu'] }> {
  return apiFetch('/config/fiu', {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export async function testFiuConnection(actor_id = 'admin'): Promise<{
  success: boolean;
  status: string;
  message: string;
}> {
  return apiFetch(`/config/fiu/test?actor_id=${encodeURIComponent(actor_id)}`, { method: 'POST' });
}

export async function patchDataSource(
  sourceId: string,
  body: { status?: string; notes?: string },
): Promise<{ success: boolean }> {
  return apiFetch(`/config/data-sources/${sourceId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export async function fetchConfigAuditLog(limit = 40): Promise<{ entries: AuditLogEntry[] }> {
  return apiFetch(`/config/audit-log?limit=${limit}`);
}

export async function saveConfigUsers(users: ConfigUser[]): Promise<{ success: boolean; users: ConfigUser[] }> {
  return apiFetch('/config/users', {
    method: 'PUT',
    body: JSON.stringify({ users, actor_id: 'admin' }),
  });
}

// ── Mobile ─────────────────────────────────────────────────────────
export async function fetchMobileDashboard(caseId?: string | null): Promise<MobileDashboard> {
  const qs = caseId ? `?case_id=${encodeURIComponent(caseId)}` : '';
  return apiFetch(`/mobile/dashboard${qs}`);
}

export async function mobileAcknowledgeCase(
  caseId: string,
  investigatorId = 'RK-001',
): Promise<{ success: boolean; message: string }> {
  return apiFetch(`/mobile/alerts/${caseId}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ investigator_id: investigatorId }),
  });
}

export async function mobileAssignCase(
  caseId: string,
  assigneeId: string,
  investigatorId = 'RK-001',
): Promise<{ success: boolean }> {
  return apiFetch(`/mobile/alerts/${caseId}/assign`, {
    method: 'POST',
    body: JSON.stringify({ assignee_id: assigneeId, investigator_id: investigatorId }),
  });
}

// ── NL Query ─────────────────────────────────────────────────────
export async function queryGraph(query: string, caseId?: string | null): Promise<NLQueryResult> {
  return apiFetch('/query', {
    method: 'POST',
    body: JSON.stringify({ query, case_id: caseId || undefined }),
  });
}
