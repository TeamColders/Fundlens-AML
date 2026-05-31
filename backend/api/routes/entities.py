"""
FundLens — /api/entities endpoints.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.blockchain.evidence_chain import INVESTIGATOR_ACTION, write_block
from backend.database.demo_data import (
    get_entity,
    set_account_enhanced_monitoring,
    set_account_watchlist,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/entities", tags=["Entities"])


class EntityActionResponse(BaseModel):
    account_id: str
    on_watchlist: bool
    enhanced_monitoring: bool
    message: str


@router.get("/{account_id}")
async def entity_profile(account_id: str):
    """Full entity profile: metrics, transactions, network, investigation history."""
    entity = get_entity(account_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return entity


def _log_entity_evidence(account_id: str, action: str, case_id: str | None) -> None:
    if not case_id:
        return
    try:
        from backend.blockchain.bootstrap import ensure_case_chain

        ensure_case_chain(case_id)
        write_block(
            case_id=case_id,
            event_type=INVESTIGATOR_ACTION,
            payload={"account_id": account_id, "action": action, "case_id": case_id},
            actor_id="investigator",
            metadata={"details": f"{action} on {account_id} · recorded on case {case_id}"},
        )
    except Exception as exc:
        logger.warning("Evidence block for entity action failed: %s", exc)


@router.post("/{account_id}/watchlist", response_model=EntityActionResponse)
async def add_to_watchlist(account_id: str):
    result = set_account_watchlist(account_id, True)
    if not result:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    entity = get_entity(account_id)
    _log_entity_evidence(account_id, "Watchlist added", entity.get("primary_case_id"))
    return EntityActionResponse(
        account_id=account_id,
        on_watchlist=result["on_watchlist"],
        enhanced_monitoring=result["enhanced_monitoring"],
        message=f"{account_id} added to watchlist",
    )


@router.delete("/{account_id}/watchlist", response_model=EntityActionResponse)
async def remove_from_watchlist(account_id: str):
    result = set_account_watchlist(account_id, False)
    if not result:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return EntityActionResponse(
        account_id=account_id,
        on_watchlist=result["on_watchlist"],
        enhanced_monitoring=result["enhanced_monitoring"],
        message=f"{account_id} removed from watchlist",
    )


@router.post("/{account_id}/enhanced-monitoring", response_model=EntityActionResponse)
async def flag_enhanced_monitoring(account_id: str):
    result = set_account_enhanced_monitoring(account_id, True)
    if not result:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    entity = get_entity(account_id)
    _log_entity_evidence(account_id, "Enhanced monitoring flagged", entity.get("primary_case_id"))
    return EntityActionResponse(
        account_id=account_id,
        on_watchlist=result["on_watchlist"],
        enhanced_monitoring=result["enhanced_monitoring"],
        message=f"{account_id} flagged for enhanced monitoring",
    )
