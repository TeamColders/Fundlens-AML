"""
FundLens — /api/blockchain evidence audit trail endpoints.
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.blockchain.bootstrap import ensure_case_chain
from backend.blockchain.evidence_chain import (
    DEMO_MODE,
    SUPERVISOR_APPROVED,
    get_all_cases,
    get_chain,
    verify_chain,
    write_block,
)
from backend.database.demo_data import get_alert_detail

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain"])


class RecordEvidenceEventBody(BaseModel):
    event_type: str = Field(..., description="e.g. SUPERVISOR_APPROVED")
    actor_id: str = "investigator"
    payload: dict = Field(default_factory=dict)
    notes: str = ""


def _chain_payload(case_id: str, blocks: list) -> dict:
    detail = get_alert_detail(case_id)
    verification = verify_chain(case_id)
    return {
        "case_id": case_id,
        "block_count": len(blocks),
        "blocks": [b.to_dict() for b in blocks],
        "typology": detail.get("typology") if detail else None,
        "risk_level": detail.get("risk_level") if detail else None,
        "mode": "DEMO" if DEMO_MODE else "PRODUCTION",
        "network": verification.network,
        "integrity_label": verification.to_dict()["integrity_label"],
        "valid": verification.valid and len(blocks) > 0,
        "empty": len(blocks) == 0,
    }


@router.get("")
async def list_blockchain_cases():
    """Return all cases with at least one evidence block."""
    cases = get_all_cases()
    summaries = []
    for case_id in cases:
        blocks = get_chain(case_id)
        verification = verify_chain(case_id)
        summaries.append({
            "case_id": case_id,
            "block_count": len(blocks),
            "valid": verification.valid and len(blocks) > 0,
            "last_event": blocks[-1].event_label if blocks else None,
            "last_timestamp": blocks[-1].timestamp if blocks else None,
        })
    return {"cases": summaries, "total": len(summaries)}


@router.get("/{case_id}")
async def blockchain_chain(case_id: str, bootstrap: bool = True):
    """Return the full evidence chain for a case (optionally bootstrap genesis blocks)."""
    if bootstrap:
        ensure_case_chain(case_id)
    blocks = get_chain(case_id)
    if not blocks and not get_alert_detail(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return _chain_payload(case_id, blocks)


@router.get("/{case_id}/verify")
async def blockchain_verify(case_id: str, bootstrap: bool = True):
    """Cryptographically verify the evidence chain."""
    if bootstrap:
        ensure_case_chain(case_id)
    result = verify_chain(case_id)
    return result.to_dict()


@router.get("/{case_id}/export")
async def blockchain_export(case_id: str, bootstrap: bool = True):
    """Download evidence chain + verification as JSON for regulators."""
    if bootstrap:
        ensure_case_chain(case_id)
    detail = get_alert_detail(case_id)
    if not detail and not get_chain(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    verification = verify_chain(case_id)
    export_doc = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "case_summary": {
            "typology": detail.get("typology") if detail else None,
            "risk_level": detail.get("risk_level") if detail else None,
            "total_amount": detail.get("total_amount") if detail else None,
        },
        "verification": verification.to_dict(),
        "chain": _chain_payload(case_id, verification.blocks),
    }
    body = json.dumps(export_doc, indent=2, default=str)
    filename = f"evidence-audit-{case_id}.json"
    return Response(
        content=body.encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{case_id}/events")
async def record_evidence_event(case_id: str, body: RecordEvidenceEventBody):
    """Append a supervisor / investigator evidence event to the chain."""
    if not get_alert_detail(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    ensure_case_chain(case_id)
    payload = {"case_id": case_id, **body.payload}
    metadata = {"notes": body.notes} if body.notes else {}

    try:
        block = write_block(
            case_id=case_id,
            event_type=body.event_type,
            payload=payload,
            actor_id=body.actor_id,
            metadata=metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"success": True, "block": block.to_dict()}


@router.post("/{case_id}/approve")
async def approve_str_evidence(case_id: str, body: RecordEvidenceEventBody | None = None):
    """Record supervisor STR draft approval on the evidence chain."""
    actor = (body.actor_id if body else None) or "supervisor"
    notes = (body.notes if body else None) or ""
    payload = (body.payload if body else None) or {}

    if not get_alert_detail(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    ensure_case_chain(case_id)
    block = write_block(
        case_id=case_id,
        event_type=SUPERVISOR_APPROVED,
        payload={"case_id": case_id, **payload},
        actor_id=actor,
        metadata={"notes": notes, "details": "STR draft reviewed and approved for filing"},
    )
    return {"success": True, "block": block.to_dict()}
