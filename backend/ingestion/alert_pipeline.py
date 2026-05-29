import json
import logging
import signal
import time
from datetime import datetime

import requests
from kafka import KafkaConsumer

from backend.blockchain.evidence_chain import write_alert_created
from backend.core.config import settings
from backend.core.logging import configure_logging
from backend.db import neo4j as neo4j_db
from backend.db import postgres as postgres_db
from backend.graph.typology_queries import detect_patterns
from backend.realtime.alerts import publish_alert


logger = logging.getLogger(__name__)

stop_requested = False


def _handle_signal(_sig, _frame):
    global stop_requested
    stop_requested = True


signal.signal(signal.SIGINT, _handle_signal)


def main() -> None:
    configure_logging()
    neo4j_db.connect()
    postgres_db.connect()

    consumer = KafkaConsumer(
        "transactions.enriched",
        bootstrap_servers=settings.kafka_bootstrap,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="fundlens-alerts",
    )

    processed = 0
    matched = 0
    created = 0
    window_start = time.time()

    logger.info("Alert pipeline started")

    while not stop_requested:
        message = consumer.poll(timeout_ms=1000)
        if not message:
            window_start = _log_stats(window_start, processed, matched, created)
            continue

        for _, records in message.items():
            for record in records:
                transaction = record.value
                processed += 1
                try:
                    with neo4j_db.get_session() as session:
                        patterns = detect_patterns(session, transaction)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Typology detection failed: %s", exc)
                    patterns = []

                if not patterns:
                    continue

                matched += len(patterns)
                gnn_score = _fetch_gnn_score(transaction)
                if gnn_score <= 0.70:
                    continue

                alert_payload = _create_alert(transaction, patterns[0], gnn_score)
                created += 1

                write_alert_created(alert_payload["case_id"], alert_payload)
                _publish_ws(alert_payload)

        window_start = _log_stats(window_start, processed, matched, created)

    logger.info("Alert pipeline stopping")
    consumer.close()
    neo4j_db.close()
    postgres_db.close()


def _fetch_gnn_score(transaction: dict) -> float:
    try:
        response = requests.post(settings.gnn_score_url, json=transaction, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data.get("score", data.get("gnn_score", 0.0)))
    except Exception as exc:  # noqa: BLE001
        logger.warning("GNN score failed: %s", exc)
        return 0.0


def _create_alert(transaction: dict, typology: str, gnn_score: float) -> dict:
    payload = {
        "case_id": transaction.get("case_id", "UNKNOWN"),
        "typology": typology,
        "gnn_score": gnn_score,
        "transaction_id": transaction.get("transaction_id"),
        "created_at": datetime.utcnow().isoformat(),
        "transaction": transaction,
    }

    with postgres_db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alerts (case_id, typology, gnn_score, payload)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    payload["case_id"],
                    payload["typology"],
                    payload["gnn_score"],
                    json.dumps(payload),
                ),
            )
        conn.commit()

    return payload


def _publish_ws(alert_payload: dict) -> None:
    try:
        import asyncio

        asyncio.run(publish_alert(json.dumps(alert_payload)))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to publish alert: %s", exc)


def _log_stats(window_start: float, processed: int, matched: int, created: int) -> float:
    elapsed = time.time() - window_start
    if elapsed >= 60:
        rate = processed / elapsed if elapsed > 0 else 0
        logger.info(
            "Processed/min: %.1f | Patterns: %s | Alerts: %s",
            rate * 60,
            matched,
            created,
        )
        return time.time()
    return window_start


if __name__ == "__main__":
    main()
