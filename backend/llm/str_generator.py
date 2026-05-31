"""
FundLens — STR report generation using Google Gemini API.
Falls back to a template-based STR if the API is unavailable.
"""
import asyncio
import logging
import os
import time
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client = None

# flash-lite often shows limit: 0 on free tier; prefer flash / 2.5 with fallbacks.
_DEFAULT_MODEL = "gemini-2.0-flash"
_MODEL_FALLBACKS = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
)


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment")
        from google import genai

        _client = genai.Client(api_key=api_key)
    return _client


def _model_chain() -> list[str]:
    chain: list[str] = []
    primary = os.getenv("GEMINI_STR_MODEL", _DEFAULT_MODEL).strip()
    if primary:
        chain.append(primary)
    for model in _MODEL_FALLBACKS:
        if model not in chain:
            chain.append(model)
    return chain


def _hindi_separate() -> bool:
    return os.getenv("GEMINI_STR_HINDI_SEPARATE", "").lower() in ("1", "true", "yes")


def _report_dict(
    case_data: dict,
    *,
    english_narrative: str,
    hindi_narrative: str,
    recommended_action: str,
    regulatory_basis: str,
    full_report_text: str,
    model_used: str,
    elapsed: float,
    fallback_reason: str | None = None,
    partial: bool = False,
) -> dict:
    word_count = len(full_report_text.split())
    out = {
        "case_id": case_data.get("case_id", "UNKNOWN"),
        "english_narrative": english_narrative,
        "hindi_narrative": hindi_narrative,
        "recommended_action": recommended_action,
        "regulatory_basis": regulatory_basis,
        "full_report_text": full_report_text,
        "generated_at": datetime.utcnow().isoformat(),
        "model_used": model_used,
        "generation_time_s": round(elapsed, 2),
        "word_count": word_count,
        "page_estimate": max(1, round(word_count / 300)),
    }
    if fallback_reason:
        out["fallback_reason"] = fallback_reason
    if partial:
        out["partial"] = True
    return out


def _error_kind(exc: Exception) -> str:
    text = str(exc).lower()
    if "429" in text or "resource_exhausted" in text or "quota" in text:
        return "quota"
    if "api key not valid" in text or "api_key_invalid" in text:
        return "auth"
    if "503" in text or "500" in text or "timeout" in text or "unavailable" in text:
        return "retryable"
    return "other"


async def _generate_content(model: str, system_prompt: str, user_prompt: str, max_tokens: int):
    client = get_client()
    try:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=0.35,
        )
    except Exception:
        config = {
            "system_instruction": system_prompt,
            "max_output_tokens": max_tokens,
            "temperature": 0.35,
        }

    return await client.aio.models.generate_content(
        model=model,
        contents=user_prompt,
        config=config,
    )


async def generate_str(case_data: dict) -> dict:
    """Generate a complete bilingual STR report dict for API + frontend."""
    start = time.time()
    last_error: Exception | None = None

    for model_used in _model_chain():
        try:
            english_report, narrative_only, hindi_narrative = await _generate_bilingual_str(
                case_data, model_used
            )
            break
        except Exception as e:
            last_error = e
            kind = _error_kind(e)
            logger.warning("Gemini STR failed on %s (%s): %s", model_used, kind, e)
            if kind == "quota":
                continue
            if kind == "retryable":
                await asyncio.sleep(3)
                try:
                    english_report, narrative_only, hindi_narrative = await _generate_bilingual_str(
                        case_data, model_used
                    )
                    break
                except Exception as e2:
                    last_error = e2
                    logger.warning("Gemini STR retry failed on %s: %s", model_used, e2)
                    continue
            return _fallback_str(case_data, start, reason=str(e))
    else:
        return _fallback_str(case_data, start, reason=str(last_error) if last_error else None)

    elapsed = time.time() - start
    partial_reason = None
    if hindi_narrative.startswith("[") and "unavailable" in hindi_narrative.lower():
        partial_reason = hindi_narrative

    return _report_dict(
        case_data,
        english_narrative=narrative_only,
        hindi_narrative=hindi_narrative,
        recommended_action=_extract_section(english_report, "RECOMMENDED ACTION:"),
        regulatory_basis=_extract_section(english_report, "REGULATORY BASIS:"),
        full_report_text=english_report,
        model_used=model_used,
        elapsed=elapsed,
        partial=bool(partial_reason),
        fallback_reason=partial_reason,
    )


async def _generate_bilingual_str(
    case_data: dict, model: str
) -> tuple[str, str, str]:
    """One Gemini call for EN report (+ HI in same response unless GEMINI_STR_HINDI_SEPARATE)."""
    english_report, narrative_only = await _generate_english_str(case_data, model)

    hindi_narrative = _extract_section(english_report, "HINDI NARRATIVE:")
    if hindi_narrative and not _hindi_separate():
        return english_report, narrative_only, hindi_narrative

    if not _hindi_separate():
        return english_report, narrative_only, "[Hindi section not returned by model]"

    try:
        hindi_narrative = await _translate_to_hindi(narrative_only, model)
    except Exception as e:
        if _error_kind(e) == "quota":
            logger.warning("Hindi translation skipped (quota): %s", e)
            hindi_narrative = "[Hindi translation skipped — API quota limit]"
        else:
            raise
    return english_report, narrative_only, hindi_narrative


async def _generate_english_str(case_data: dict, model: str) -> tuple[str, str]:
    from backend.llm.prompts import build_str_prompt

    system_prompt, user_prompt = build_str_prompt(case_data)
    response = await _generate_content(model, system_prompt, user_prompt, max_tokens=3072)

    full_text = (response.text or "").strip()
    if not full_text:
        raise RuntimeError("Empty response from Gemini")
    narrative_only = _extract_section(full_text, "NARRATIVE:") or full_text
    logger.info("STR generated for %s (%s words)", case_data.get("case_id"), len(full_text.split()))
    return full_text, narrative_only


async def _translate_to_hindi(english_narrative: str, model: str) -> str:
    from backend.llm.prompts import build_hindi_translation_prompt

    if not english_narrative.strip():
        return "[अनुवाद उपलब्ध नहीं]"
    system_prompt, user_prompt = build_hindi_translation_prompt(english_narrative)
    response = await _generate_content(model, system_prompt, user_prompt, max_tokens=1536)
    return (response.text or "").strip()


def _normalize_header(line: str) -> str:
    return line.strip().lstrip("#").strip().rstrip(":").upper()


def _is_section_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("##"):
        return True
    norm = _normalize_header(stripped)
    known = (
        "FIU-IND FORM STR-01 (DRAFT)",
        "NARRATIVE",
        "RECOMMENDED ACTION",
        "REGULATORY BASIS",
        "CASE REF",
        "TYPOLOGY",
        "RISK SCORE",
        "ACCOUNTS INVOLVED",
        "TOTAL AMOUNT",
        "PERIOD",
        "REPORT DATE",
        "FILING ENTITY",
    )
    return norm in known or (norm.isupper() and len(norm) < 50 and ":" in stripped)


def _extract_section(text: str, header: str) -> str:
    target = header.rstrip(":").upper()
    lines = text.split("\n")
    capturing = False
    captured = []
    for line in lines:
        if _normalize_header(line) == target:
            capturing = True
            if ":" in line:
                after = line.split(":", 1)[1].strip()
                if after:
                    captured.append(after)
            continue
        if capturing:
            if _is_section_header(line):
                break
            captured.append(line)
    return "\n".join(captured).strip()


def _fallback_str(case_data: dict, start: float, *, reason: str | None = None) -> dict:
    from datetime import date

    today = date.today().strftime("%d %b %Y")
    case_id = case_data.get("case_id", "UNKNOWN")
    typology = case_data.get("typology_name", "Suspicious Pattern")
    amount = case_data.get("total_amount", 0)
    score = round(float(case_data.get("gnn_score", 0)) * 100, 1)
    accounts = case_data.get("accounts_count", 0)
    duration_h = case_data.get("duration_hours", 0)

    reason_hint = _fallback_reason_hint(reason)
    narrative = (
        f"FundLens flagged case {case_id} for {typology} involving {accounts} accounts "
        f"and ₹{amount:,.0f} moved over {duration_h:.1f} hours (GNN confidence {score}%). "
        f"[MANUAL REVIEW REQUIRED — Gemini API unavailable]"
    )

    full_text = f"""FIU-IND FORM STR-01 (DRAFT)
Report Date: {today}
Filing Entity: Union Bank of India

CASE REF: {case_id}
TYPOLOGY: {typology}
RISK SCORE: {score}% (GNN confidence)
ACCOUNTS INVOLVED: {accounts}
TOTAL AMOUNT: ₹{amount:,.0f}
PERIOD: {duration_h:.1f} hours

NARRATIVE:
{narrative}

RECOMMENDED ACTION:
Review and freeze implicated accounts pending investigation. Escalate per bank AML policy.

REGULATORY BASIS:
PMLA 2002, Section 12 and Section 16 | {case_data.get("typology_fatf_reference", "FATF Typology")}"""

    return _report_dict(
        case_data,
        english_narrative=narrative,
        hindi_narrative="[मैन्युअल समीक्षा आवश्यक]",
        recommended_action="Review and freeze implicated accounts pending investigation.",
        regulatory_basis=f"PMLA 2002 | {case_data.get('typology_fatf_reference', 'FATF Typology')}",
        full_report_text=full_text,
        model_used="fallback-template",
        elapsed=time.time() - start,
        fallback_reason=reason_hint,
    )


def _fallback_reason_hint(reason: str | None) -> str:
    if not reason:
        return "Gemini API unavailable"
    lower = reason.lower()
    if "429" in lower or "resource_exhausted" in lower or "quota" in lower:
        if "limit: 0" in lower and "flash-lite" in lower:
            return (
                "gemini-2.0-flash-lite has no free-tier quota on your API key (limit: 0). "
                "Set GEMINI_STR_MODEL=gemini-2.0-flash in .env (same family as test.py), restart "
                "uvicorn, wait ~1 minute, then Regenerate once."
            )
        return (
            "Gemini API quota exceeded (429). Wait for the retry delay shown in logs (~60s), "
            "then Regenerate once. Avoid opening STR repeatedly — each visit triggers a request."
        )
    if "gemini_api_key" in lower or "not set" in lower:
        return "GEMINI_API_KEY is not set in .env"
    if "no module named 'google'" in lower or "google-genai" in lower:
        return "google-genai package not installed (run: pip install -r requirements.txt)"
    if "api key not valid" in lower or "api_key_invalid" in lower:
        return "GEMINI_API_KEY is invalid — create a new key at https://aistudio.google.com/apikey"
    return reason[:240]


async def nl_to_cypher(query: str) -> str:
    from backend.llm.prompts import DEFAULT_GRAPH_SCHEMA, build_cypher_prompt

    system_prompt, user_prompt = build_cypher_prompt(query, DEFAULT_GRAPH_SCHEMA)
    response = await _generate_content(_model_chain()[0], system_prompt, user_prompt, max_tokens=300)
    cypher = (response.text or "").strip().strip("`")
    if cypher.startswith("cypher"):
        cypher = cypher.split("\n", 1)[-1].strip()
    for op in ("CREATE", "MERGE", "SET ", "DELETE", "REMOVE", "DROP"):
        if op in cypher.upper():
            raise ValueError(f"Unsafe Cypher operation: {op}")
    return cypher


def _parse_nl_answer_sections(text: str) -> tuple[str, str | None]:
    summary = _extract_section(text, "SUMMARY:") or text.strip()[:500]
    narrative = _extract_section(text, "NARRATIVE:")
    if narrative and narrative.strip().upper() in ("N/A", "NA", "NONE", "-"):
        narrative = None
    return summary.strip(), (narrative.strip() if narrative else None)


async def answer_nl_query(query: str, context: dict) -> dict:
    """
    Gemini investigative answer using the same client/model chain as STR generation.
    """
    from backend.llm.prompts import build_nl_query_answer_prompt

    system_prompt, user_prompt = build_nl_query_answer_prompt(query, context)
    last_error: Exception | None = None

    for model_used in _model_chain():
        try:
            response = await _generate_content(model_used, system_prompt, user_prompt, max_tokens=1536)
            text = (response.text or "").strip()
            if not text:
                raise RuntimeError("Empty response from Gemini")
            summary, narrative = _parse_nl_answer_sections(text)
            return {
                "summary": summary,
                "narrative": narrative,
                "model_used": model_used,
            }
        except Exception as e:
            last_error = e
            kind = _error_kind(e)
            logger.warning("Gemini NL query failed on %s (%s): %s", model_used, kind, e)
            if kind == "quota":
                continue
            if kind == "retryable":
                await asyncio.sleep(2)
                try:
                    response = await _generate_content(model_used, system_prompt, user_prompt, max_tokens=1536)
                    text = (response.text or "").strip()
                    summary, narrative = _parse_nl_answer_sections(text)
                    return {
                        "summary": summary,
                        "narrative": narrative,
                        "model_used": model_used,
                    }
                except Exception as e2:
                    last_error = e2
                    continue
            break

    reason = _fallback_reason_hint(str(last_error) if last_error else None)
    sql_summary = context.get("sql_summary") or ""
    return {
        "summary": sql_summary or "Could not generate an AI answer for this question.",
        "narrative": None,
        "model_used": "fallback-template",
        "fallback_reason": reason,
    }
