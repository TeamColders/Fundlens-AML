"""
FundLens — /api/query endpoint (NL to Cypher / SQL / Gemini).
"""
import logging
import time

from fastapi import APIRouter

from backend.api.models import NLQueryRequest
from backend.database.query_engine import (
    build_query_context,
    execute_nl_query_local,
    should_use_gemini_answer,
)
from backend.llm.str_generator import answer_nl_query, nl_to_cypher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["NL Query"])


def _neo4j_unavailable(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in ("connection refused", "couldn't connect", "serviceunavailable", "failed to establish")
    )


async def _apply_gemini_answer(
    query: str,
    payload: dict,
    *,
    case_id: str | None,
    neo4j_records: list | None = None,
) -> dict:
    context = build_query_context(
        query,
        case_id=case_id,
        sql_payload=payload,
        neo4j_records=neo4j_records,
    )
    gemini = await answer_nl_query(query, context)
    payload["summary"] = gemini["summary"]
    if gemini.get("narrative"):
        payload["narrative"] = gemini["narrative"]
    payload["model_used"] = gemini.get("model_used")
    if gemini.get("fallback_reason"):
        payload["fallback_reason"] = gemini["fallback_reason"]

    handler = payload.get("handler", "fallback")
    if neo4j_records is not None:
        payload["source"] = "neo4j+gemini"
    elif handler != "fallback":
        payload["source"] = "gemini+sql"
    else:
        payload["source"] = "gemini"
    return payload


@router.post("")
async def nl_query(body: NLQueryRequest):
    """NL query: Neo4j+Cypher when available; SQL patterns; Gemini for analysis / open questions."""
    start = time.time()
    query_text = body.query.strip()
    case_id = body.case_id

    # 1) Neo4j + Gemini Cypher
    try:
        from backend.graph.neo4j_client import get_session

        cypher = await nl_to_cypher(query_text)
        with get_session() as session:
            result = session.run(cypher)
            records = [r.data() for r in result]

        elapsed = round((time.time() - start) * 1000, 1)
        payload = {
            "query": query_text,
            "cypher": cypher,
            "results": records,
            "result_count": len(records),
            "execution_ms": elapsed,
            "summary": f"Neo4j returned {len(records)} record(s).",
            "source": "neo4j",
            "display_type": "table",
            "handler": "neo4j",
        }

        if should_use_gemini_answer(query_text, "neo4j"):
            try:
                payload = await _apply_gemini_answer(
                    query_text, payload, case_id=case_id, neo4j_records=records
                )
            except Exception as exc:
                logger.warning("Gemini narrative for Neo4j query failed: %s", exc)

        payload["execution_ms"] = round((time.time() - start) * 1000, 1)
        return payload
    except Exception as exc:
        if not _neo4j_unavailable(exc):
            logger.warning("Neo4j/LLM query path failed, using SQL/Gemini fallback: %s", exc)

    # 2) SQL pattern store
    payload = execute_nl_query_local(query_text, case_id=case_id)
    handler = payload.get("handler", "fallback")

    # 3) Gemini investigative answer (same stack as STR)
    if should_use_gemini_answer(query_text, handler):
        try:
            payload = await _apply_gemini_answer(query_text, payload, case_id=case_id)
        except Exception as exc:
            logger.warning("Gemini NL query answer failed: %s", exc)
            if handler == "fallback":
                payload["summary"] = (
                    f"{payload.get('summary', '')} "
                    "(Set GEMINI_API_KEY in .env for AI answers to open-ended questions.)"
                ).strip()

    payload["execution_ms"] = round((time.time() - start) * 1000, 1)
    return payload
