import logging

from fastapi import APIRouter, HTTPException

from backend.db import postgres as postgres_db


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
def list_cases():
    try:
        with postgres_db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT case_id, typology, total_amount, status, created_at "
                    "FROM cases ORDER BY created_at DESC LIMIT 200"
                )
                rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load cases: %s", exc)
        return {"cases": []}

    cases = [
        {
            "case_id": row[0],
            "typology": row[1],
            "total_amount": float(row[2]) if row[2] is not None else None,
            "status": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
        }
        for row in rows
    ]
    return {"cases": cases}


@router.get("/{case_id}")
def get_case(case_id: str):
    try:
        with postgres_db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT case_id, typology, total_amount, status, created_at "
                    "FROM cases WHERE case_id = %s",
                    (case_id,),
                )
                row = cur.fetchone()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load case %s: %s", case_id, exc)
        raise HTTPException(status_code=500, detail="Case lookup failed") from exc

    if row is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "case_id": row[0],
        "typology": row[1],
        "total_amount": float(row[2]) if row[2] is not None else None,
        "status": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
    }
