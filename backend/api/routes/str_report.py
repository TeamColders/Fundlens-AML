"""
FundLens — /api/str endpoints with Server-Sent Events streaming.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from backend.api.models import STRStage, STRSubmitRequest, STRSubmitResponse
from backend.blockchain.bootstrap import ensure_case_chain
from backend.blockchain.evidence_chain import (
    LLM_NARRATIVE_GENERATED,
    STR_SUBMITTED,
    SUBGRAPH_EXPORTED,
    INVESTIGATOR_ACTION,
    has_event,
    write_block,
)
from backend.database.demo_data import get_case_data
from backend.database.str_store import init_str_tables, load_report, save_draft, save_generated_report
from backend.llm.str_pdf import build_str_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/str", tags=["STR Generation"])

_str_store: dict[str, dict[str, Any]] = {}
_str_generation_locks: dict[str, asyncio.Lock] = {}


class STRDraftBody(BaseModel):
    full_report_text: str
    english_narrative: str | None = None
    hindi_narrative: str | None = None
    recommended_action: str | None = None
    regulatory_basis: str | None = None
    investigator_id: str = "investigator"


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, default=str)}\n\n"


def _sse_keep_alive() -> str:
    return ": keep-alive\n\n"


def _report_to_dict(report: Any) -> dict[str, Any]:
    if isinstance(report, dict):
        return report
    if hasattr(report, "model_dump"):
        return report.model_dump(mode="json")
    return dict(report)


def _get_report(case_id: str) -> dict[str, Any] | None:
    if case_id in _str_store:
        return _str_store[case_id]
    return load_report(case_id)


async def _str_generation_stream(case_id: str) -> AsyncGenerator[str, None]:
    try:
        yield _sse_event({
            "stage": STRStage.ANALYSING_PATTERN,
            "message": f"Loading case {case_id} and transaction graph...",
            "progress": 20,
        })
        await asyncio.sleep(0.5)

        ensure_case_chain(case_id)

        case_data = get_case_data(case_id)
        if not case_data:
            yield _sse_event({
                "stage": STRStage.ERROR,
                "message": f"Case {case_id} not found",
                "progress": 0,
                "error": f"Case {case_id} not found",
            })
            return

        if not has_event(case_id, SUBGRAPH_EXPORTED):
            try:
                write_block(
                    case_id=case_id,
                    event_type=SUBGRAPH_EXPORTED,
                    payload={"case_id": case_id, "node_count": case_data.get("accounts_count", 0)},
                    actor_id="system",
                )
            except Exception:
                pass

        yield _sse_event({
            "stage": STRStage.COMPILING_EVIDENCE,
            "message": "Compiling timeline, account roles, and regulatory references...",
            "progress": 50,
        })
        await asyncio.sleep(0.4)

        yield _sse_event({
            "stage": STRStage.DRAFTING_NARRATIVE,
            "message": "Gemini drafting personalised STR narrative for this case...",
            "progress": 75,
        })

        from backend.llm.str_generator import generate_str

        llm_task = asyncio.create_task(generate_str(case_data))
        while not llm_task.done():
            await asyncio.sleep(4)
            yield _sse_keep_alive()

        str_report = await llm_task
        str_report = _report_to_dict(str_report)

        if str_report.get("model_used") != "fallback-template" and not has_event(
            case_id, LLM_NARRATIVE_GENERATED
        ):
            try:
                write_block(
                    case_id=case_id,
                    event_type=LLM_NARRATIVE_GENERATED,
                    payload={
                        "case_id": case_id,
                        "model_used": str_report.get("model_used", "unknown"),
                        "word_count": str_report.get("word_count", 0),
                    },
                    actor_id="system",
                )
            except Exception:
                pass
        else:
            logger.warning(
                "STR for %s used fallback template (%s); skipping LLM_NARRATIVE_GENERATED block",
                case_id,
                str_report.get("fallback_reason", "unknown"),
            )

        _str_store[case_id] = str_report
        save_generated_report(case_id, str_report)

        yield _sse_event({
            "stage": STRStage.COMPLETE,
            "message": "STR ready for review",
            "progress": 100,
            "report": str_report,
        })
    except Exception as e:
        logger.exception("STR generation failed for %s", case_id)
        yield _sse_event({
            "stage": STRStage.ERROR,
            "message": str(e),
            "progress": 0,
            "error": str(e),
        })


async def _stream_with_lock(case_id: str) -> AsyncGenerator[str, None]:
    lock = _str_generation_locks.setdefault(case_id, asyncio.Lock())
    if lock.locked():
        cached = _get_report(case_id)
        if cached:
            logger.info("STR already running for %s — returning cached report", case_id)
            yield _sse_event({
                "stage": STRStage.COMPLETE,
                "message": "STR ready (cached — generation already in progress)",
                "progress": 100,
                "report": cached,
            })
            return
        logger.info("STR already in progress for %s — waiting for lock", case_id)
    async with lock:
        async for chunk in _str_generation_stream(case_id):
            yield chunk


@router.post("/{case_id}/generate")
async def generate_str_endpoint(case_id: str):
    """Stream STR generation progress via Server-Sent Events."""
    init_str_tables()
    logger.info("STR generation requested for %s", case_id)
    return StreamingResponse(
        _stream_with_lock(case_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{case_id}")
async def get_str(case_id: str):
    report = _get_report(case_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"No STR found for case {case_id}")
    return report


@router.post("/{case_id}/draft")
async def save_str_draft(case_id: str, body: STRDraftBody):
    existing = _get_report(case_id) or {"case_id": case_id}
    merged = {
        **existing,
        "case_id": case_id,
        "full_report_text": body.full_report_text,
        "english_narrative": body.english_narrative or existing.get("english_narrative", ""),
        "hindi_narrative": body.hindi_narrative or existing.get("hindi_narrative", ""),
        "recommended_action": body.recommended_action or existing.get("recommended_action", ""),
        "regulatory_basis": body.regulatory_basis or existing.get("regulatory_basis", ""),
        "updated_at": datetime.utcnow().isoformat(),
        "is_draft": True,
    }
    _str_store[case_id] = merged
    save_draft(case_id, merged, body.investigator_id)
    try:
        ensure_case_chain(case_id, investigator_id=body.investigator_id)
        write_block(
            case_id=case_id,
            event_type=INVESTIGATOR_ACTION,
            payload={
                "case_id": case_id,
                "word_count": len(body.full_report_text.split()),
                "action": "STR draft saved",
            },
            actor_id=body.investigator_id,
            metadata={"details": "STR draft saved by investigator · edits hash-sealed"},
        )
    except Exception:
        pass
    return {"success": True, "case_id": case_id, "saved_at": merged["updated_at"]}


@router.get("/{case_id}/draft")
async def get_str_draft(case_id: str):
    report = load_report(case_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"No draft for case {case_id}")
    return report


@router.get("/{case_id}/pdf")
async def download_str_pdf(case_id: str):
    report = _get_report(case_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"No STR found for case {case_id}")
    pdf_bytes = build_str_pdf(report)
    filename = f"STR-{case_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{case_id}/download")
async def download_str_text(case_id: str):
    report = _get_report(case_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"No STR found for case {case_id}")
    text = report.get("full_report_text", "")
    filename = f"STR-{case_id}.txt"
    return Response(
        content=text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{case_id}/submit")
async def submit_str(case_id: str, body: STRSubmitRequest):
    report = _get_report(case_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"No STR found for case {case_id}")

    submission_id = f"SUB-{uuid.uuid4().hex[:8].upper()}"
    fiu_reference = f"FIU-IND-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    try:
        block = write_block(
            case_id=case_id,
            event_type=STR_SUBMITTED,
            payload={
                "case_id": case_id,
                "submission_id": submission_id,
                "fiu_reference": fiu_reference,
            },
            actor_id=body.investigator_id,
            metadata={"notes": body.notes},
        )
        blockchain_block = block.block_id
    except Exception:
        blockchain_block = None

    return STRSubmitResponse(
        success=True,
        submission_id=submission_id,
        fiu_reference=fiu_reference,
        blockchain_block=blockchain_block,
        submitted_at=datetime.utcnow(),
    )
