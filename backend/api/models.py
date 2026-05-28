"""
FundLens — Pydantic models for all API request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
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
