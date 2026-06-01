// ---------------------------------------------------------------------------
// FundLens API service layer
// All requests go through Vite's dev proxy (/api → http://localhost:8000)
// In production, requests go directly to the same domain
// ---------------------------------------------------------------------------

const BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Alert {
  id: number;
  case_id: string;
  typology: string;
  gnn_score: number;
  created_at: string | null;
  payload: Record<string, unknown> | null;
}

export interface Case {
  case_id: string;
  typology: string | null;
  total_amount: number | null;
  status: string;
  created_at: string | null;
}

export interface GraphNode {
  id: string;
  label: string;
  risk_level: string | null;
  amount: number | null;
  account_type: string | null;
  is_hub: boolean;
  is_dormant: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
  amount: number | null;
  timestamp: string | number | null;
  channel: string | null;
  transaction_id: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Entity {
  account_id: string;
  account_type: string | null;
  kyc_tier: string | null;
  is_dormant: boolean;
  total_volume: number | null;
  risk_level: string | null;
  owner: string | null;
}

export interface EvidenceBlock {
  block_type: string;
  payload: Record<string, unknown> | null;
  created_at: string | null;
}

export interface BlockchainData {
  case_id: string;
  blocks: EvidenceBlock[];
}

export interface AnalyticsOverview {
  total_cases: number;
  total_alerts: number;
  risk_breakdown: { low: number; medium: number; high: number };
}

export interface HealthStatus {
  status: { neo4j: boolean; postgres: boolean; redis: boolean };
}

export interface STREvent {
  stage: 'analysing_pattern' | 'compiling_evidence' | 'drafting_narrative' | 'complete';
  message: string;
  progress: number;
  report?: string | {
    case_id?: string;
    summary?: string;
    english_narrative?: string;
    risk_rating?: string;
    recommended_action?: string;
    generation_time_seconds?: number;
  };
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const api = {
  // Alerts
  listAlerts: () => get<{ alerts: Alert[] }>('/alerts'),

  // Cases
  listCases: () => get<{ cases: Case[] }>('/cases'),
  getCase: (caseId: string) => get<Case>(`/cases/${caseId}`),

  // Graph
  getGraph: (caseId: string) => get<GraphData>(`/graph/${caseId}`),

  // Entities
  getEntity: (accountId: string) => get<Entity>(`/entities/${accountId}`),

  // Blockchain
  getCaseEvidence: (caseId: string) => get<BlockchainData>(`/blockchain/case/${caseId}`),

  // Analytics
  getAnalytics: () => get<AnalyticsOverview>('/analytics'),

  // Health
  getHealth: () => get<HealthStatus>('/health'),

  // NL Query
  runQuery: (query: string) => post<{ message: string; query: unknown }>('/query', { query }),

  // STR generation — returns an EventSource URL (SSE)
  strGenerateUrl: (caseId: string) => `${BASE}/str/${caseId}/generate`,

  // STR generation — POST and consume SSE stream
  generateSTR: (caseId: string, onEvent: (e: STREvent) => void): Promise<void> => {
    return new Promise((resolve, reject) => {
      fetch(`${BASE}/str/${caseId}/generate`, { method: 'POST' })
        .then((res) => {
          if (!res.ok || !res.body) {
            reject(new Error(`STR generate failed: ${res.status}`));
            return;
          }
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          const pump = (): Promise<void> =>
            reader.read().then(({ done, value }) => {
              if (done) { resolve(); return; }
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() ?? '';
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const event = JSON.parse(line.slice(6)) as STREvent;
                    onEvent(event);
                  } catch { /* skip malformed */ }
                }
              }
              return pump();
            });

          pump().catch(reject);
        })
        .catch(reject);
    });
  },
};
