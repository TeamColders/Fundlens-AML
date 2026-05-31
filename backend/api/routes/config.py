"""
FundLens — /api/config platform configuration endpoints.
"""
from __future__ import annotations

import os
import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.blockchain.evidence_chain import DEMO_MODE, DB_PATH as EVIDENCE_DB_PATH
from backend.database.config_store import (
    append_audit_log,
    get_audit_log,
    get_data_source_overrides,
    get_fiu_settings,
    get_thresholds,
    get_users,
    update_data_source,
    update_fiu_settings,
    update_thresholds,
    update_users,
)
from backend.database.demo_data import DEMO_DB_PATH, _load_all_cases, get_analytics

router = APIRouter(prefix="/api/config", tags=["Configuration"])


class ThresholdsUpdate(BaseModel):
    velocity_threshold_lakh: int | None = Field(None, ge=10, le=50)
    dormancy_months: int | None = Field(None, ge=3, le=24)
    gnn_confidence_pct: int | None = Field(None, ge=60, le=95)
    actor_id: str = "admin"


class FiuUpdate(BaseModel):
    endpoint: str | None = None
    enabled: bool | None = None
    auto_submit: bool | None = None
    actor_id: str = "admin"


class DataSourcePatch(BaseModel):
    status: str | None = None
    notes: str | None = None
    actor_id: str = "admin"


class UserRecord(BaseModel):
    id: str
    name: str
    role: str
    branch: str
    active: bool = True


class UsersUpdate(BaseModel):
    users: list[UserRecord]
    actor_id: str = "admin"


def _service_status(name: str) -> tuple[str, str]:
    if name == "kafka":
        broker = os.getenv("KAFKA_BROKER", "localhost:9092")
        return ("online", f"Broker {broker}") if broker else ("offline", "KAFKA_BROKER not set")
    if name == "neo4j":
        try:
            from backend.graph.neo4j_client import get_client

            if get_client().verify_connection():
                return ("online", "Graph connected")
            return ("degraded", "Unreachable — demo SQL fallback active")
        except Exception as exc:
            return ("degraded", str(exc)[:80])
    if name == "postgres":
        try:
            from backend.database.demo_data import get_dict_db

            if get_dict_db is None:
                return ("degraded", "psycopg2 not installed")
            with get_dict_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return ("online", "Primary case store")
        except Exception:
            return ("degraded", "Using SQLite demo fallback")
    if name == "gemini":
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            return ("degraded", "GEMINI_API_KEY not set")
        return ("online", os.getenv("GEMINI_STR_MODEL", "gemini-2.0-flash"))
    if name == "blockchain":
        return ("online", f"{'Demo ledger' if DEMO_MODE else 'Fabric'} · {EVIDENCE_DB_PATH.name}")
    return ("unknown", "")


def _build_data_connections(analytics: dict) -> list[dict]:
    overrides = get_data_source_overrides()
    txn_count = 0
    try:
        from backend.database.demo_data import get_dict_db

        if get_dict_db:
            with get_dict_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) AS cnt FROM transactions")
                    txn_count = int(cur.fetchone()["cnt"])
    except Exception:
        pass
    if txn_count == 0 and DEMO_DB_PATH.exists():
        import sqlite3

        con = sqlite3.connect(DEMO_DB_PATH)
        txn_count = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        con.close()

    events_per_min = max(1200, min(txn_count // 10, 42000)) if txn_count else 0
    base = [
        {
            "id": "cbs",
            "name": "Core Banking System",
            "vendor": "Infosys Finacle",
            "default_status": "connected",
            "detail": f"Branch: All · Events/min: {events_per_min:,}" if events_per_min else "Branch: All",
        },
        {
            "id": "rtgs",
            "name": "RTGS / NEFT",
            "vendor": "RBI SFMS connector",
            "default_status": "connected",
            "detail": "Real-time · Last sync: < 5s",
        },
        {
            "id": "upi",
            "name": "UPI / IMPS",
            "vendor": "NPCI switch",
            "default_status": "connecting",
            "detail": "NPCI switch connection",
            "progress_pct": 67,
        },
        {
            "id": "swift",
            "name": "SWIFT",
            "vendor": "SWIFT Alliance",
            "default_status": "not_configured",
            "detail": "Required for cross-border monitoring",
        },
    ]
    out = []
    for src in base:
        ov = overrides.get(src["id"], {})
        status = ov.get("status") or src["default_status"]
        out.append({
            **src,
            "status": status,
            "detail": ov.get("notes") or src["detail"],
            "progress_pct": ov.get("progress_pct", src.get("progress_pct")),
        })
    return out


def _connection_health(analytics: dict) -> dict:
    cases = analytics.get("total_cases") or 0
    base_events = 400 + cases * 12
    return {
        "events_per_sec": base_events + random.randint(0, 80),
        "graph_write_latency_ms": 72 + random.randint(0, 40),
        "gnn_inference_ms": 120 + random.randint(0, 50),
        "sparkline_events": [base_events + random.randint(-20, 30) for _ in range(12)],
        "sparkline_graph": [80 + random.randint(-15, 25) for _ in range(12)],
        "sparkline_gnn": [130 + random.randint(-20, 20) for _ in range(12)],
    }


@router.get("")
async def get_platform_config():
    """Full configuration snapshot for admin UI."""
    analytics = get_analytics()
    services = {
        "kafka": _service_status("kafka"),
        "neo4j": _service_status("neo4j"),
        "postgres": _service_status("postgres"),
        "gemini": _service_status("gemini"),
        "blockchain": _service_status("blockchain"),
        "api": ("online", "FundLens API"),
    }
    system_status = [
        {"label": label.replace("_", " ").title(), "status": st, "detail": det}
        for label, (st, det) in services.items()
    ]
    return {
        "thresholds": get_thresholds(),
        "data_connections": _build_data_connections(analytics),
        "connection_health": _connection_health(analytics),
        "users": get_users(),
        "fiu": get_fiu_settings(),
        "blockchain": {
            "mode": "demo" if DEMO_MODE else "production",
            "db_path": str(EVIDENCE_DB_PATH),
            "network": "UBI-Fabric-Private" if not DEMO_MODE else "FundLens-Demo-Ledger",
        },
        "gnn_model": {
            "name": "FraudGAT",
            "version": os.getenv("FUNDLENS_GNN_VERSION", "gnn_v1"),
            "device": "cuda" if os.getenv("FUNDLENS_FORCE_CPU") != "1" else "cpu",
            "confidence_threshold_pct": get_thresholds()["gnn_confidence_pct"],
        },
        "system_status": system_status,
        "analytics_summary": {
            "total_cases": analytics.get("total_cases", 0),
            "alerts_today": analytics.get("alerts_today", 0),
            "gnn_accuracy": analytics.get("gnn_accuracy", 0),
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/thresholds")
async def patch_thresholds(body: ThresholdsUpdate):
    updates = body.model_dump(exclude={"actor_id"}, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No threshold fields provided")
    merged = update_thresholds(updates, actor_id=body.actor_id)
    return {"success": True, "thresholds": merged}


@router.patch("/fiu")
async def patch_fiu(body: FiuUpdate):
    updates = body.model_dump(exclude={"actor_id"}, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No FIU fields provided")
    merged = update_fiu_settings(updates, actor_id=body.actor_id)
    return {"success": True, "fiu": merged}


@router.post("/fiu/test")
async def test_fiu_connection(actor_id: str = "admin"):
    fiu = get_fiu_settings()
    status = "ok" if fiu.get("enabled") else "disabled"
    append_audit_log(
        actor_id=actor_id,
        action="fiu_test",
        section="fiu",
        details=f"FIU connectivity test: {status}",
    )
    return {
        "success": status == "ok",
        "status": status,
        "message": "FIU endpoint reachable (demo)" if status == "ok" else "FIU integration disabled",
        "tested_at": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/data-sources/{source_id}")
async def patch_data_source(source_id: str, body: DataSourcePatch):
    patch = body.model_dump(exclude={"actor_id"}, exclude_none=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = update_data_source(source_id, patch, actor_id=body.actor_id)
    return {"success": True, "source_id": source_id, "connection": updated}


@router.put("/users")
async def put_users(body: UsersUpdate):
    users = [u.model_dump() for u in body.users]
    saved = update_users(users, actor_id=body.actor_id)
    return {"success": True, "users": saved}


@router.get("/audit-log")
async def config_audit_log(limit: int = 40):
    logs = get_audit_log(limit=limit)
    case_events = []
    for case in _load_all_cases()[:5]:
        case_events.append({
            "id": f"case-{case.get('case_id')}",
            "timestamp": case.get("created_at"),
            "actor_id": "system",
            "action": "alert_created",
            "section": "cases",
            "details": f"{case.get('typology')} · {case.get('case_id')}",
            "payload": {"case_id": case.get("case_id")},
        })
    combined = logs + case_events
    combined.sort(key=lambda x: str(x.get("timestamp") or ""), reverse=True)
    return {"entries": combined[:limit], "total": len(combined)}


@router.get("/health-metrics")
async def config_health_metrics():
    analytics = get_analytics()
    return _connection_health(analytics)
