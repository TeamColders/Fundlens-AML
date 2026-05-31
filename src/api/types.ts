/**
 * FundLens — TypeScript type definitions matching backend Pydantic models.
 */

// ── Enums ────────────────────────────────────────────────────────
export type AlertStatus = 'active' | 'under_review' | 'confirmed_fraud' | 'dismissed';
export type RiskLevel = 'critical' | 'high' | 'medium' | 'low';
export type STRStage = 'analysing_pattern' | 'compiling_evidence' | 'drafting_narrative' | 'complete' | 'error';

// ── Graph ────────────────────────────────────────────────────────
export interface GraphNode {
  id: string;
  label: string;
  risk_level: string;
  amount: number;
  account_type: string;
  is_hub: boolean;
  is_dormant: boolean;
  is_origin: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
  amount: number;
  timestamp: string;
  channel: string;
  transaction_id: string;
}

export interface Subgraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  hub_id?: string;
}

// ── Alerts ───────────────────────────────────────────────────────
export interface AlertListItem {
  case_id: string;
  typology: string;
  risk_score: number;
  total_amount: number;
  accounts_count: number;
  hops: number;
  duration: string;
  channel: string;
  created_at: string;
  status: string;
  confidence: string;
  risk_level: string;
}

export interface AlertsResponse {
  alerts: AlertListItem[];
  total: number;
  page: number;
}

export interface AlertDetail {
  case_id: string;
  typology: string;
  risk_score: number;
  total_amount: number;
  accounts_count: number;
  hops: number;
  duration_display: string;
  duration_minutes: number;
  channel: string;
  created_at: string;
  status: string;
  confidence: string;
  risk_level: string;
  fatf_reference: string;
  pmla_section: string;
  gnn_score: number;
  subgraph: Subgraph;
  timeline: TimelineEntry[];
}

export interface TimelineEntry {
  timestamp: string;
  sender: string;
  receiver: string;
  amount: number;
  channel: string;
}

// ── STR ──────────────────────────────────────────────────────────
export interface STRReport {
  case_id: string;
  english_narrative: string;
  hindi_narrative: string;
  recommended_action: string;
  regulatory_basis: string;
  full_report_text: string;
  generated_at: string;
  model_used: string;
  generation_time_s: number;
  word_count: number;
  page_estimate: number;
  fallback_reason?: string;
  partial?: boolean;
}

export interface STRProgressEvent {
  stage: STRStage;
  message: string;
  progress: number;
  report?: STRReport;
  error?: string;
}

// ── Entity ───────────────────────────────────────────────────────
export interface PeerComparisonMetric {
  label: string;
  peer: number;
  account: number;
  alert: boolean;
}

export interface InvestigationHistoryItem {
  case_id: string;
  typology: string;
  status: string;
  created_at?: string;
}

export interface EntityProfile {
  account_id: string;
  account_type: string;
  status: string;
  kyc_tier: number;
  created_date: string;
  last_active_date: string;
  declared_income: number;
  home_branch: string;
  is_dormant: boolean;
  is_pep_adjacent: boolean;
  owner_name: string;
  owner_type: string;
  risk_level: string;
  risk_score: number;
  notes: string;
  transactions: EntityTransaction[];
  transaction_total_count?: number;
  primary_case_id?: string | null;
  metrics: EntityMetrics;
  network: NetworkNode[];
  related_entities: RelatedEntity[];
  peer_comparison?: PeerComparisonMetric[];
  investigation_history?: InvestigationHistoryItem[];
  watch_flags?: string[];
  on_watchlist?: boolean;
  enhanced_monitoring?: boolean;
}

export interface EntityTransaction {
  date: string;
  time: string;
  counterparty: string;
  amount: number;
  channel: string;
  flagged: boolean;
  direction: 'in' | 'out';
}

export interface EntityMetrics {
  avg_monthly_volume: number;
  current_month_volume: number;
  baseline_deviation: string;
  counterparties_30d: number;
  inbound_ratio: number;
  outbound_ratio: number;
}

export interface NetworkNode {
  id: string;
  risk_level: string;
}

export interface RelatedEntity {
  name: string;
  relation: string;
  risk_score: number;
  account_id?: string;
}

// ── Analytics ────────────────────────────────────────────────────
export interface AnalyticsData {
  alerts_today: number;
  alerts_this_week: number;
  alerts_week_change_pct?: number;
  total_cases: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  confirmed_fraud_count?: number;
  total_amount_flagged: number;
  false_positive_rate: number;
  avg_resolution_time: string;
  gnn_accuracy?: number;
  strs_filed?: number;
  top_typologies: TypologyCount[];
  channel_breakdown: ChannelCount[];
  daily_trend: DailyTrend[];
  risk_distribution: RiskDistribution[];
  investigators?: InvestigatorWorkload[];
  system_health?: SystemHealthItem[];
  system_events?: SystemEvent[];
  updated_at?: string;
}

export interface TypologyCount {
  name: string;
  count: number;
  percentage: number;
}

export interface ChannelCount {
  channel: string;
  count: number;
  percentage: number;
}

export interface DailyTrend {
  date: string;
  alerts: number;
  confirmed?: number;
}

export interface InvestigatorWorkload {
  investigator_id: string;
  name: string;
  initials: string;
  cases: number;
  avg_resolution_display: string;
}

export interface SystemHealthItem {
  name: string;
  status: 'ok' | 'degraded' | 'down';
  detail: string;
}

export interface SystemEvent {
  time: string;
  event_type: string;
  description: string;
  ref: string;
}

export interface RiskDistribution {
  level: string;
  count: number;
  color: string;
}

// ── Blockchain ───────────────────────────────────────────────────
export interface BlockRecord {
  block_id: number;
  block_hash: string;
  short_hash: string;
  prev_hash: string;
  short_prev: string;
  case_id: string;
  event_type: string;
  event_label: string;
  payload_hash: string;
  timestamp: string;
  display_timestamp?: string;
  actor_id: string | null;
  metadata: Record<string, unknown> | null;
  payload_preview?: Record<string, unknown> | null;
  details?: string;
  verified: boolean;
}

export interface BlockchainData {
  case_id: string;
  block_count: number;
  blocks: BlockRecord[];
  typology?: string | null;
  risk_level?: string | null;
  mode?: string;
  network?: string;
  integrity_label?: string;
  valid?: boolean;
  empty?: boolean;
}

export interface ChainVerification {
  valid: boolean;
  empty?: boolean;
  block_count: number;
  blocks: BlockRecord[];
  broken_at_block: number | null;
  verified_at: string;
  network: string;
  mode: string;
  integrity_label: string;
}

// ── Query ────────────────────────────────────────────────────────
export interface NLQueryResult {
  query: string;
  cypher: string;
  results: Record<string, unknown>[];
  result_count: number;
  execution_ms: number;
  summary?: string;
  narrative?: string;
  source?: 'neo4j' | 'sql' | 'gemini' | 'gemini+sql' | 'neo4j+gemini' | string;
  display_type?: 'table' | 'entity';
  entity?: EntityProfile;
  model_used?: string;
  fallback_reason?: string;
  error?: string;
}

// ── Configuration ────────────────────────────────────────────────
export interface DataConnection {
  id: string;
  name: string;
  vendor: string;
  status: string;
  detail: string;
  progress_pct?: number;
}

export interface PlatformConfig {
  thresholds: {
    structuring_threshold_inr: number;
    velocity_threshold_lakh: number;
    dormancy_months: number;
    gnn_confidence_pct: number;
  };
  data_connections: DataConnection[];
  connection_health: {
    events_per_sec: number;
    graph_write_latency_ms: number;
    gnn_inference_ms: number;
    sparkline_events: number[];
    sparkline_graph: number[];
    sparkline_gnn: number[];
  };
  users: ConfigUser[];
  fiu: FiuSettings;
  blockchain: { mode: string; db_path: string; network: string };
  gnn_model: {
    name: string;
    version: string;
    device: string;
    confidence_threshold_pct: number;
  };
  system_status: { label: string; status: string; detail: string }[];
  analytics_summary: {
    total_cases: number;
    alerts_today: number;
    gnn_accuracy: number;
  };
  updated_at: string;
}

export interface ConfigUser {
  id: string;
  name: string;
  role: string;
  branch: string;
  active: boolean;
}

export interface FiuSettings {
  endpoint: string;
  enabled: boolean;
  auto_submit: boolean;
  last_test_status?: string;
}

export interface AuditLogEntry {
  id: number | string;
  timestamp: string;
  actor_id: string;
  action: string;
  section: string;
  details: string;
  payload?: Record<string, unknown>;
}

export interface MobileAlertSummary {
  case_id: string;
  typology: string;
  risk_level: string;
  risk_pct: number;
  total_amount: number;
  accounts_count: number;
  channel?: string;
  status?: string;
  confidence?: string;
  created_at?: string;
  duration_display?: string;
  investigator_id?: string;
  has_subgraph?: boolean;
  time_ago?: string;
}

export interface MobileDashboard {
  featured: MobileAlertSummary | null;
  recent: MobileAlertSummary[];
  unread_count: number;
  critical_count: number;
  updated_at?: string;
}

// ── Health ────────────────────────────────────────────────────────
export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  services: Record<string, string>;
  endpoints: string[];
}
