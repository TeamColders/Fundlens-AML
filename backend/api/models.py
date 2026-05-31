"""
FundLens — Pydantic models for all API request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ── ENUMS ────────────────────────────────────────────────────────
class AlertStatus(str, Enum):
    ACTIVE          = "active"
    UNDER_REVIEW    = "under_review"
    CONFIRMED_FRAUD = "confirmed_fraud"
    DISMISSED       = "dismissed"


class STRStage(str, Enum):
    ANALYSING_PATTERN  = "analysing_pattern"
    COMPILING_EVIDENCE = "compiling_evidence"
    DRAFTING_NARRATIVE = "drafting_narrative"
    COMPLETE           = "complete"
    ERROR              = "error"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


# ── ALERT MODELS ─────────────────────────────────────────────────
class AlertDetail(BaseModel):
    """Alert detail from graph query."""
    account_id: str
    risk_level: str
    amount: float
    account_type: str
    is_hub: bool = False
    is_dormant: bool = False
    
    class Config:
        from_attributes = True


class AlertEdge(BaseModel):
    """Edge in alert subgraph."""
    source: str
    target: str
    amount: float
    timestamp: str
    channel: str


class AlertSubgraph(BaseModel):
    """Subgraph for an alert."""
    nodes: List[AlertDetail]
    edges: List[AlertEdge]


class Alert(BaseModel):
    """Alert response model."""
    case_id: str
    typology: str
    risk_score: float = Field(ge=0.0, le=1.0)
    total_amount: float
    accounts_count: int
    hops: int
    duration_minutes: float
    channel: str
    created_at: datetime
    status: str
    confidence: float = Field(ge=0.0, le=1.0)
    subgraph: Optional[AlertSubgraph] = None

    class Config:
        from_attributes = True


class AlertsResponse(BaseModel):
    """Paginated alerts response."""
    alerts: List[Alert]
    total: int
    page: int
    limit: int


class AlertStatusUpdate(BaseModel):
    """Update alert status."""
    status: str
    investigator_id: Optional[str] = None
    notes: Optional[str] = None


# ── GRAPH MODELS ──────────────────────────────────────────────────
class GraphNode(BaseModel):
    """Graph node for visualization."""
    id: str
    label: str
    risk_level: str
    amount: float
    account_type: str
    is_hub: bool = False
    is_dormant: bool = False
    x: Optional[float] = None
    y: Optional[float] = None


class GraphEdge(BaseModel):
    """Graph edge for visualization."""
    source: str
    target: str
    label: str
    amount: float
    timestamp: str
    channel: str
    color: Optional[str] = None


class GraphData(BaseModel):
    """Graph data response."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    center_node: Optional[str] = None


# ── GNN MODELS ────────────────────────────────────────────────────
class NodeFeatures(BaseModel):
    """Node features for GNN."""
    account_id: str
    features: List[float] = Field(min_length=12, max_length=12)


class EdgeFeatures(BaseModel):
    """Edge features for GNN."""
    source: str
    target: str
    features: List[float] = Field(min_length=6, max_length=6)


class SubgraphRequest(BaseModel):
    """GNN scoring request."""
    case_id: str
    nodes: List[NodeFeatures]
    edges: List[EdgeFeatures]


class NodeScore(BaseModel):
    """Per-node fraud score."""
    account_id: str
    score: float = Field(ge=0.0, le=1.0)


class GNNScore(BaseModel):
    """GNN inference response."""
    case_id: str
    fraud_probability: float = Field(ge=0.0, le=1.0)
    node_scores: List[NodeScore]
    inference_time_ms: float
    model_version: str
    threshold_crossed: bool
    risk_level: str


# ── STR MODELS ────────────────────────────────────────────────────
class STRReport(BaseModel):
    """STR (Suspicious Transaction Report) response."""
    case_id: str
    english_narrative: str
    hindi_narrative: Optional[str] = None
    recommended_action: str
    regulatory_basis: str
    generated_at: datetime
    model_used: str
    generation_time_seconds: float
    full_report_text: str


class STRSubmitRequest(BaseModel):
    """Submit STR for filing."""
    case_id: str
    report_text: str
    investigator_id: Optional[str] = None


class STRGenerationEvent(BaseModel):
    """SSE event for STR generation."""
    stage: str
    message: str
    progress: int
    report: Optional[STRReport] = None


# ── ENTITY MODELS ─────────────────────────────────────────────────
class EntityProfile(BaseModel):
    """Entity profile."""
    entity_id: str
    name_hash: str
    kyc_tier: int
    account_ids: List[str]
    total_volume: float
    transaction_count: int
    risk_score: float


# ── ANALYTICS MODELS ──────────────────────────────────────────────
class DailyStats(BaseModel):
    """Daily statistics."""
    date: str
    alerts_created: int
    alerts_resolved: int
    fraud_amount_detected: float
    transactions_processed: int


class AnalyticsData(BaseModel):
    """Analytics response."""
    daily_stats: List[DailyStats]
    typology_distribution: Dict[str, int]
    high_risk_accounts: List[str]
    detection_rate: float


# ── BLOCKCHAIN MODELS ─────────────────────────────────────────────
class BlockchainBlock(BaseModel):
    """Blockchain evidence block."""
    block_id: int
    case_id: str
    event_type: str
    timestamp: str
    actor_id: Optional[str] = None
    payload_hash: str
    block_hash: str


class BlockchainData(BaseModel):
    """Blockchain audit trail."""
    case_id: str
    blocks: List[BlockchainBlock]
    chain_valid: bool


# ── QUERY MODELS ──────────────────────────────────────────────────
class QueryRequest(BaseModel):
    """Natural language query request."""
    query: str


class QueryResult(BaseModel):
    """Query execution result."""
    cypher: str
    results: List[Dict[str, Any]]
    execution_time_ms: float


# ── HEALTH CHECK ──────────────────────────────────────────────────
class ServiceHealth(BaseModel):
    """Service health status."""
    status: str
    neo4j: bool
    postgres: bool
    redis: bool
    timestamp: datetime
# ── GRAPH MODELS ─────────────────────────────────────────────────
class GraphNode(BaseModel):
    id:           str
    label:        str
    risk_level:   str
    amount:       float
    account_type: str
    is_hub:       bool = False
    is_dormant:   bool = False
    is_origin:    bool = False

class GraphEdge(BaseModel):
    source:         str
    target:         str
    amount:         float
    timestamp:      str
    channel:        str
    transaction_id: str

class Subgraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# ── CASE / ALERT MODELS ──────────────────────────────────────────
class CaseData(BaseModel):
    case_id:                  str
    typology_name:            str
    typology_fatf_reference:  str
    total_amount:             float
    accounts_count:           int
    hop_count:                int
    duration_hours:           float
    gnn_score:                float
    channel:                  str
    subgraph:                 Optional[Subgraph] = None
    timeline:                 Optional[List[dict]] = None
    created_at:               Optional[datetime] = None

class AlertListItem(BaseModel):
    case_id:        str
    typology:       str
    risk_score:     float
    total_amount:   float
    accounts_count: int
    hops:           int
    duration:       str
    channel:        str
    created_at:     str
    status:         str
    confidence:     str
    risk_level:     str = "critical"

class AlertsResponse(BaseModel):
    alerts: List[AlertListItem]
    total:  int
    page:   int = 1

class AlertDetail(BaseModel):
    case_id:        str
    typology:       str
    risk_score:     float
    total_amount:   float
    accounts_count: int
    hops:           int
    duration:       str
    channel:        str
    created_at:     str
    status:         str
    confidence:     str
    risk_level:     str
    fatf_reference: str
    pmla_section:   str
    subgraph:       Subgraph
    timeline:       List[dict]

class AlertStatusUpdate(BaseModel):
    status:          str
    investigator_id: str
    notes:           Optional[str] = None


# ── STR MODELS ───────────────────────────────────────────────────
class STRReport(BaseModel):
    case_id:             str
    english_narrative:   str
    hindi_narrative:     str
    recommended_action:  str
    regulatory_basis:    str
    full_report_text:    str
    generated_at:        datetime
    model_used:          str
    generation_time_s:   float
    word_count:          int
    page_estimate:       int

class STRProgressEvent(BaseModel):
    stage:    STRStage
    message:  str
    progress: int                    # 0-100
    report:   Optional[STRReport] = None
    error:    Optional[str]      = None

class STRSubmitRequest(BaseModel):
    report_text:     str
    investigator_id: str
    notes:           Optional[str] = None

class STRSubmitResponse(BaseModel):
    success:          bool
    submission_id:    str
    fiu_reference:    Optional[str]
    blockchain_block: Optional[int]
    submitted_at:     datetime


# ── BLOCKCHAIN MODELS ────────────────────────────────────────────
class BlockRecord(BaseModel):
    block_id:     int
    block_hash:   str
    prev_hash:    str
    case_id:      str
    event_type:   str
    payload_hash: str
    timestamp:    str
    actor_id:     Optional[str]
    metadata:     Optional[dict]

class ChainVerification(BaseModel):
    valid:           bool
    block_count:     int
    blocks:          List[BlockRecord]
    broken_at_block: Optional[int] = None
    verified_at:     datetime


# ── ENTITY MODELS ────────────────────────────────────────────────
class EntityProfile(BaseModel):
    account_id:       str
    account_type:     str
    status:           str
    kyc_tier:         int
    created_date:     str
    last_active_date: str
    declared_income:  float
    home_branch:      str
    is_dormant:       bool
    is_pep_adjacent:  bool
    owner_name:       str
    owner_type:       str
    risk_level:       str
    notes:            str
    risk_score:       int = 0
    transactions:     List[dict] = []
    metrics:          dict = {}
    network:          List[dict] = []
    related_entities: List[dict] = []

class EntityListItem(BaseModel):
    account_id:   str
    owner_name:   str
    account_type: str
    risk_level:   str
    is_dormant:   bool


# ── ANALYTICS MODELS ─────────────────────────────────────────────
class AnalyticsData(BaseModel):
    alerts_today:       int
    alerts_this_week:   int
    total_cases:        int
    critical_count:     int
    high_count:         int
    medium_count:       int
    total_amount_flagged: float
    false_positive_rate: float
    avg_resolution_time: str
    top_typologies:     List[dict]
    channel_breakdown:  List[dict]
    daily_trend:        List[dict]
    risk_distribution:  List[dict]


# ── QUERY MODELS ─────────────────────────────────────────────────
class NLQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    case_id: Optional[str] = Field(None, description="Active investigation case for context")

class NLQueryResponse(BaseModel):
    query:        str
    cypher:       str
    results:      List[dict]
    result_count: int
    execution_ms: float


# ── GNN SCORING MODELS ───────────────────────────────────────────
class GNNScoreRequest(BaseModel):
    case_id:  str
    subgraph: Subgraph

class GNNScoreResponse(BaseModel):
    case_id:           str
    fraud_probability: float
    node_scores:       dict
    inference_time_ms: float
    model_version:     str
    threshold_crossed: bool
    risk_level:        str
