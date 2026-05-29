import asyncio
import time


def _build_report(case: dict) -> dict:
    return {
        "case_id": case.get("case_id"),
        "summary": "Automated STR draft based on detected typology.",
        "english_narrative": (
            "The transaction flow indicates a suspicious pattern consistent with "
            "layering behavior. Funds moved rapidly across multiple accounts "
            "with limited business rationale."
        ),
        "risk_rating": "High",
        "recommended_action": "Escalate for manual review.",
    }


async def generate_str(case: dict) -> dict:
    start = time.time()
    await asyncio.sleep(1.5)
    report = _build_report(case)
    report["generation_time_seconds"] = round(time.time() - start, 2)
    return report
