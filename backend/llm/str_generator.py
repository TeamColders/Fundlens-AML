"""
FundLens — STR report generation using Anthropic Claude API.
Falls back to a template-based STR if the API is unavailable.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

import anthropic

from backend.llm.prompts import (
    build_str_prompt,
    build_hindi_translation_prompt,
    DEFAULT_GRAPH_SCHEMA,
)
from backend.api.models import STRReport

logger = logging.getLogger(__name__)

# ── Anthropic client — initialised lazily ────────────────────────
_client: Optional[anthropic.AsyncAnthropic] = None

def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env
    return _client


# ── MAIN STR GENERATOR ───────────────────────────────────────────
async def generate_str(case_data: dict) -> STRReport:
    """
    Generate a complete bilingual STR report.
    Returns an STRReport Pydantic model.
    Retries once on API failure, then falls back to a template STR.
    """
    start = time.time()
    model_used = "claude-opus-4-5"

    try:
        english_report, narrative_only = await _generate_english_str(case_data, model_used)
        hindi_narrative = await _translate_to_hindi(narrative_only, model_used)
    except anthropic.APIError as e:
        logger.warning(f"Anthropic API error on first attempt: {e}. Retrying in 2s...")
        await asyncio.sleep(2)
        try:
            english_report, narrative_only = await _generate_english_str(case_data, model_used)
            hindi_narrative = await _translate_to_hindi(narrative_only, model_used)
        except anthropic.APIError as e2:
            logger.error(f"Anthropic API failed after retry: {e2}. Using fallback STR.")
            return _fallback_str(case_data, start)

    elapsed = time.time() - start
    word_count = len(english_report.split())
    page_estimate = max(1, round(word_count / 300))

    # Parse sections out of the full report text
    recommended_action = _extract_section(english_report, "RECOMMENDED ACTION:")
    regulatory_basis = _extract_section(english_report, "REGULATORY BASIS:")

    return STRReport(
        case_id=case_data.get("case_id", "UNKNOWN"),
        english_narrative=narrative_only,
        hindi_narrative=hindi_narrative,
        recommended_action=recommended_action,
        regulatory_basis=regulatory_basis,
        full_report_text=english_report,
        generated_at=datetime.utcnow(),
        model_used=model_used,
        generation_time_s=round(elapsed, 2),
        word_count=word_count,
        page_estimate=page_estimate,
    )


async def _generate_english_str(case_data: dict, model: str) -> tuple[str, str]:
    """Call Claude to generate the full English STR. Returns (full_text, narrative_only)."""
    system_prompt, user_prompt = build_str_prompt(case_data)
    client = get_client()

    message = await client.messages.create(
        model=model,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    full_text = message.content[0].text
    narrative_only = _extract_section(full_text, "NARRATIVE:")
    logger.info(f"STR generated for {case_data.get('case_id')} — {len(full_text.split())} words")
    return full_text, narrative_only


async def _translate_to_hindi(english_narrative: str, model: str) -> str:
    """Translate the narrative section to Hindi."""
    system_prompt, user_prompt = build_hindi_translation_prompt(english_narrative)
    client = get_client()

    message = await client.messages.create(
        model=model,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def _extract_section(text: str, header: str) -> str:
    """Extract text after a section header until the next all-caps header."""
    lines = text.split("\n")
    capturing = False
    captured = []
    for line in lines:
        if line.strip().startswith(header):
            capturing = True
            # Include anything on the same line after the header
            rest = line.strip()[len(header):].strip()
            if rest:
                captured.append(rest)
            continue
        if capturing:
            # Stop at next section header (all-caps line ending in colon)
            if line.strip() and line.strip().isupper() and line.strip().endswith(":"):
                break
            if line.strip() and len(line.strip()) > 20 and line.strip() == line.strip().upper():
                break
            captured.append(line)
    return "\n".join(captured).strip()


def _fallback_str(case_data: dict, start: float) -> STRReport:
    """Template-based fallback STR when the API is unavailable."""
    from datetime import date
    today = date.today().strftime("%d %b %Y")
    case_id = case_data.get("case_id", "UNKNOWN")
    typology = case_data.get("typology_name", "Suspicious Pattern")
    amount = case_data.get("total_amount", 0)
    score = round(case_data.get("gnn_score", 0) * 100, 1)

    full_text = f"""FIU-IND FORM STR-01 (DRAFT) [MANUAL REVIEW REQUIRED]
Report Date: {today}
Filing Entity: Union Bank of India

CASE REF: {case_id}
TYPOLOGY: {typology}
RISK SCORE: {score}% (GNN confidence)
ACCOUNTS INVOLVED: {case_data.get("accounts_count", 0)}
TOTAL AMOUNT: ₹{amount:,.0f}
PERIOD: {case_data.get("duration_hours", 0):.1f} hours

NARRATIVE:
FundLens detected a {typology.lower()} pattern with a GNN confidence score of {score}%.
The pattern involved {case_data.get("accounts_count", 0)} accounts with a total fund \
flow of ₹{amount:,.0f} over {case_data.get("duration_hours", 0):.1f} hours.
This report requires manual review as AI narrative generation was unavailable.

RECOMMENDED ACTION:
Review flagged accounts immediately. Consider freezing implicated accounts pending investigation.

REGULATORY BASIS:
PMLA 2002, Section 12 and Section 16 | {case_data.get("typology_fatf_reference", "FATF Typology")}"""

    return STRReport(
        case_id=case_id,
        english_narrative="[Manual review required — AI generation unavailable]",
        hindi_narrative="[मैन्युअल समीक्षा आवश्यक]",
        recommended_action="Review flagged accounts immediately.",
        regulatory_basis="PMLA 2002, Section 12 and Section 16",
        full_report_text=full_text,
        generated_at=datetime.utcnow(),
        model_used="fallback-template",
        generation_time_s=round(time.time() - start, 2),
        word_count=len(full_text.split()),
        page_estimate=1,
    )


# ── NL TO CYPHER ─────────────────────────────────────────────────
async def nl_to_cypher(query: str) -> str:
    """Convert natural language question to Neo4j Cypher query."""
    from backend.llm.prompts import build_cypher_prompt
    system_prompt, user_prompt = build_cypher_prompt(query, DEFAULT_GRAPH_SCHEMA)
    client = get_client()

    message = await client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    cypher = message.content[0].text.strip()

    # Safety check — reject any write operations
    write_ops = ["CREATE", "MERGE", "SET ", "DELETE", "REMOVE", "DROP"]
    cypher_upper = cypher.upper()
    for op in write_ops:
        if op in cypher_upper:
            raise ValueError(
                f"Generated Cypher contains unsafe operation '{op}'. Query rejected."
            )

    return cypher
