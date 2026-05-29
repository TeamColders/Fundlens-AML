import json
from datetime import datetime

from backend.db import postgres as postgres_db


def write_alert_created(case_id: str, payload: dict) -> None:
    with postgres_db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO evidence_blocks (case_id, block_type, payload, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (case_id, "ALERT_CREATED", json.dumps(payload), datetime.utcnow()),
            )
        conn.commit()


def list_evidence_blocks(case_id: str):
    with postgres_db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT block_type, payload, created_at FROM evidence_blocks "
                "WHERE case_id = %s ORDER BY created_at ASC",
                (case_id,),
            )
            rows = cur.fetchall()

    return [
        {
            "block_type": row[0],
            "payload": row[1],
            "created_at": row[2].isoformat() if row[2] else None,
        }
        for row in rows
    ]
