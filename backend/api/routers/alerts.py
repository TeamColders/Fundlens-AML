import json
import logging

from fastapi import APIRouter

from backend.db import postgres as postgres_db


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
def list_alerts():
    try:
        with postgres_db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, case_id, typology, gnn_score, created_at, payload "
                    "FROM alerts ORDER BY created_at DESC LIMIT 200"
                )
                rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load alerts: %s", exc)
        return {"alerts": []}

    alerts = [
        {
            "id": row[0],
            "case_id": row[1],
            "typology": row[2],
            "gnn_score": float(row[3]),
            "created_at": row[4].isoformat() if row[4] else None,
            "payload": row[5] if isinstance(row[5], dict) else _safe_json(row[5]),
        }
        for row in rows
    ]
    return {"alerts": alerts}


def _safe_json(value):
    if value is None:
        return None
    try:
        return json.loads(value)
    except Exception:  # noqa: BLE001
        return {"raw": str(value)}
