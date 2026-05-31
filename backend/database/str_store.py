"""Persist STR reports and investigator drafts (SQLite)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.paths import demo_db_path

DB_PATH = demo_db_path()


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_str_tables() -> None:
    with _conn() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS str_reports (
                case_id TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                model_used TEXT
            );
            CREATE TABLE IF NOT EXISTS str_drafts (
                case_id TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                investigator_id TEXT,
                is_draft INTEGER DEFAULT 1
            );
            """
        )
        con.commit()


def save_generated_report(case_id: str, report: dict[str, Any]) -> None:
    init_str_tables()
    payload = json.dumps(report, default=str)
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        con.execute(
            """
            INSERT INTO str_reports (case_id, report_json, generated_at, model_used)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                report_json=excluded.report_json,
                generated_at=excluded.generated_at,
                model_used=excluded.model_used
            """,
            (case_id, payload, now, report.get("model_used", "")),
        )
        con.commit()


def save_draft(case_id: str, report: dict[str, Any], investigator_id: str = "investigator") -> None:
    init_str_tables()
    payload = json.dumps(report, default=str)
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        con.execute(
            """
            INSERT INTO str_drafts (case_id, report_json, updated_at, investigator_id, is_draft)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(case_id) DO UPDATE SET
                report_json=excluded.report_json,
                updated_at=excluded.updated_at,
                investigator_id=excluded.investigator_id
            """,
            (case_id, payload, now, investigator_id),
        )
        con.commit()


def count_str_reports() -> int:
    if not DB_PATH.exists():
        return 0
    init_str_tables()
    with _conn() as con:
        row = con.execute("SELECT COUNT(*) AS cnt FROM str_reports").fetchone()
        return int(row["cnt"]) if row else 0


def load_report(case_id: str) -> Optional[dict[str, Any]]:
    init_str_tables()
    with _conn() as con:
        row = con.execute(
            "SELECT report_json FROM str_drafts WHERE case_id = ?", (case_id,)
        ).fetchone()
        if row:
            return json.loads(row["report_json"])
        row = con.execute(
            "SELECT report_json FROM str_reports WHERE case_id = ?", (case_id,)
        ).fetchone()
        if row:
            return json.loads(row["report_json"])
    return None
