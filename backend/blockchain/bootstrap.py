"""
Bootstrap and sync evidence chains for investigation cases.
"""
from __future__ import annotations

import logging
from typing import Optional

from backend.blockchain.evidence_chain import (
    CASE_OPENED,
    LLM_NARRATIVE_GENERATED,
    SUBGRAPH_EXPORTED,
    get_chain,
    has_event,
    seal_case,
    write_block,
)
from backend.database.demo_data import get_alert_detail

logger = logging.getLogger(__name__)


def _gnn_fraction(detail: dict) -> float:
    score = detail.get("gnn_score")
    if score is None:
        score = detail.get("risk_score", 0.0)
    score = float(score or 0.0)
    return score / 100.0 if score > 1 else score


def _existing_event_types(case_id: str) -> set[str]:
    return {b.event_type for b in get_chain(case_id)}


def sync_str_evidence_blocks(case_id: str) -> None:
    """Backfill chain blocks when STR was generated before blocks were written."""
    try:
        from backend.database.str_store import load_report
    except Exception:
        return

    report = load_report(case_id)
    if not report:
        return

    existing = _existing_event_types(case_id)
    case_data = get_alert_detail(case_id)

    if case_data and not has_event(case_id, SUBGRAPH_EXPORTED):
        try:
            write_block(
                case_id=case_id,
                event_type=SUBGRAPH_EXPORTED,
                payload={
                    "case_id": case_id,
                    "node_count": case_data.get("accounts_count", 0),
                    "synced": True,
                },
                actor_id="system",
                metadata={"source": "evidence_sync"},
            )
        except Exception as exc:
            logger.warning("Could not sync SUBGRAPH_EXPORTED for %s: %s", case_id, exc)

    if report.get("model_used") != "fallback-template" and not has_event(
        case_id, LLM_NARRATIVE_GENERATED
    ):
        try:
            write_block(
                case_id=case_id,
                event_type=LLM_NARRATIVE_GENERATED,
                payload={
                    "case_id": case_id,
                    "model_used": report.get("model_used", "unknown"),
                    "word_count": report.get("word_count", 0),
                    "synced": True,
                },
                actor_id="system",
                metadata={"source": "evidence_sync"},
            )
        except Exception as exc:
            logger.warning("Could not sync LLM block for %s: %s", case_id, exc)


def ensure_case_chain(case_id: str, *, investigator_id: Optional[str] = None) -> list:
    """
    Ensure a case has at least ALERT_CREATED (and CASE_OPENED when applicable).
    Sync STR-related blocks if a report already exists.
    """
    chain = get_chain(case_id)
    if chain:
        sync_str_evidence_blocks(case_id)
        return get_chain(case_id)

    detail = get_alert_detail(case_id)
    if not detail:
        return []

    try:
        seal_case(
            case_id=case_id,
            gnn_score=_gnn_fraction(detail),
            typology=str(detail.get("typology") or "Suspicious pattern"),
            total_amount=float(detail.get("total_amount") or 0),
            accounts_count=int(detail.get("accounts_count") or 0),
            actor_id="system",
        )
    except Exception as exc:
        logger.warning("Failed to seal case %s: %s", case_id, exc)
        return get_chain(case_id)

    status = str(detail.get("status") or "").lower()
    if status in ("investigating", "open", "in_progress", "active", "new") and not has_event(
        case_id, CASE_OPENED
    ):
        actor = investigator_id or "investigator"
        try:
            write_block(
                case_id=case_id,
                event_type=CASE_OPENED,
                payload={
                    "case_id": case_id,
                    "status": detail.get("status"),
                    "typology": detail.get("typology"),
                },
                actor_id=actor,
                metadata={"source": "case_bootstrap"},
            )
        except Exception as exc:
            logger.warning("Failed CASE_OPENED block for %s: %s", case_id, exc)

    sync_str_evidence_blocks(case_id)
    return get_chain(case_id)
