"""
FundLens — /api/alerts endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.blockchain.bootstrap import ensure_case_chain
from backend.database.demo_data import get_alerts, get_alert_detail, update_alert_status
from backend.blockchain.evidence_chain import write_block, CASE_OPENED

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("")
async def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Return list of active alerts sorted by risk score descending."""
    return get_alerts(status=status, limit=limit, offset=offset)


@router.get("/{case_id}")
async def alert_detail(case_id: str):
    """Return full alert detail including subgraph and timeline."""
    detail = get_alert_detail(case_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    try:
        ensure_case_chain(case_id)
    except Exception as e:
        logger.warning("Evidence chain bootstrap failed for %s: %s", case_id, e)
    return detail


@router.post("/{case_id}/status")
async def update_status(case_id: str, body: dict):
    """Update alert status and write blockchain block."""
    status = body.get("status", "")
    investigator_id = body.get("investigator_id", "unknown")
    notes = body.get("notes", "")

    success = update_alert_status(case_id, status, investigator_id, notes)
    if not success:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Write blockchain block on status change
    try:
        write_block(
            case_id=case_id,
            event_type=CASE_OPENED,
            payload={"case_id": case_id, "new_status": status, "investigator": investigator_id},
            actor_id=investigator_id,
            metadata={"notes": notes},
        )
    except Exception as e:
        logger.warning(f"Failed to write blockchain block: {e}")

    return {"success": True, "case_id": case_id, "new_status": status}
