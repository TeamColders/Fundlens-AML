"""
FundLens — /api/mobile endpoints for investigator mobile experience.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.database.demo_data import get_alert_detail, get_alerts, update_alert_status

router = APIRouter(prefix="/api/mobile", tags=["Mobile"])


class MobileActionBody(BaseModel):
    investigator_id: str = "RK-001"
    notes: str = ""


class AssignBody(MobileActionBody):
    assignee_id: str = Field(..., min_length=2)


def _risk_pct(case: dict) -> int:
    gnn = case.get("gnn_score") or case.get("risk_score")
    if gnn is None:
        return 85
    g = float(gnn)
    return round(g * 100) if g <= 1 else round(g)


def _format_alert_summary(case: dict, *, include_graph: bool = False) -> dict:
    detail = get_alert_detail(case["case_id"]) if include_graph else None
    nodes = (detail or {}).get("subgraph", {}).get("nodes") if detail else None
    account_count = (
        len([n for n in nodes if n.get("id") != "EXTERNAL"])
        if nodes
        else case.get("accounts_count")
    )
    created = case.get("created_at")
    return {
        "case_id": case["case_id"],
        "typology": case.get("typology"),
        "risk_level": case.get("risk_level"),
        "risk_pct": _risk_pct(case),
        "total_amount": float(case.get("total_amount") or 0),
        "accounts_count": account_count,
        "channel": case.get("channel"),
        "status": case.get("status"),
        "confidence": case.get("confidence"),
        "created_at": created,
        "duration_display": case.get("duration_display"),
        "investigator_id": case.get("investigator_id"),
        "has_subgraph": bool(nodes),
    }


def _time_ago(created_at: str | None, fallback_idx: int) -> str:
    if not created_at:
        return f"{fallback_idx * 8 + 5}m ago"
    try:
        from backend.database.demo_data import _parse_case_datetime

        dt = _parse_case_datetime(created_at)
        if not dt:
            return f"{fallback_idx * 8 + 5}m ago"
        delta = datetime.now(timezone.utc) - dt
        mins = int(delta.total_seconds() / 60)
        if mins < 1:
            return "just now"
        if mins < 60:
            return f"{mins}m ago"
        hours = mins // 60
        if hours < 24:
            return f"{hours}h ago"
        return f"{hours // 24}d ago"
    except Exception:
        return f"{fallback_idx * 8 + 5}m ago"


@router.get("/dashboard")
async def mobile_dashboard(case_id: str | None = None):
    """Featured alert + recent list for mobile shell."""
    data = get_alerts(limit=20)
    alerts = data.get("alerts") or []
    if not alerts:
        return {
            "featured": None,
            "recent": [],
            "unread_count": 0,
            "critical_count": 0,
        }

    featured_case = None
    if case_id:
        featured_case = next((a for a in alerts if a["case_id"] == case_id), None)
    if not featured_case:
        featured_case = alerts[0]

    critical_count = sum(
        1 for a in alerts if (a.get("risk_level") or "").lower() == "critical"
    )
    recent = []
    for idx, alert in enumerate(alerts[:8]):
        recent.append({
            **_format_alert_summary(alert),
            "time_ago": _time_ago(alert.get("created_at"), idx),
        })

    return {
        "featured": _format_alert_summary(featured_case, include_graph=True),
        "recent": recent,
        "unread_count": len(alerts),
        "critical_count": critical_count,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/alerts/{case_id}")
async def mobile_alert_detail(case_id: str):
    detail = get_alert_detail(case_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    summary = _format_alert_summary(detail, include_graph=True)
    timeline = (detail.get("timeline") or [])[:6]
    nodes = detail.get("subgraph", {}).get("nodes") or []
    return {
        **summary,
        "timeline": timeline,
        "graph_preview": [
            {
                "id": n.get("id"),
                "risk_level": n.get("risk_level"),
                "is_origin": n.get("is_origin"),
                "is_hub": n.get("is_hub"),
            }
            for n in nodes[:8]
            if n.get("id") != "EXTERNAL"
        ],
    }


@router.post("/alerts/{case_id}/acknowledge")
async def mobile_acknowledge(case_id: str, body: MobileActionBody):
    """Mark case as under investigation (mobile quick action)."""
    ok = update_alert_status(case_id, "investigating", body.investigator_id, body.notes)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    try:
        from backend.blockchain.bootstrap import ensure_case_chain
        from backend.blockchain.evidence_chain import CASE_OPENED, has_event, write_block

        ensure_case_chain(case_id, investigator_id=body.investigator_id)
        if not has_event(case_id, CASE_OPENED):
            write_block(
                case_id=case_id,
                event_type=CASE_OPENED,
                payload={"case_id": case_id, "status": "investigating", "source": "mobile"},
                actor_id=body.investigator_id,
                metadata={"details": f"Mobile acknowledge · {body.investigator_id}"},
            )
    except Exception:
        pass

    return {
        "success": True,
        "case_id": case_id,
        "status": "investigating",
        "message": "Case acknowledged — open desktop for full graph",
    }


@router.post("/alerts/{case_id}/assign")
async def mobile_assign(case_id: str, body: AssignBody):
    notes = body.notes or f"Assigned to {body.assignee_id} via mobile"
    ok = update_alert_status(case_id, "assigned", body.investigator_id, notes)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    try:
        from backend.blockchain.evidence_chain import INVESTIGATOR_ACTION, write_block
        from backend.blockchain.bootstrap import ensure_case_chain

        ensure_case_chain(case_id)
        write_block(
            case_id=case_id,
            event_type=INVESTIGATOR_ACTION,
            payload={
                "case_id": case_id,
                "action": "assigned",
                "assignee_id": body.assignee_id,
            },
            actor_id=body.investigator_id,
            metadata={"details": f"Assigned to {body.assignee_id} from mobile"},
        )
    except Exception:
        pass

    return {
        "success": True,
        "case_id": case_id,
        "assignee_id": body.assignee_id,
        "status": "assigned",
    }
