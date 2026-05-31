"""
Persisted platform configuration, audit log, and connection registry.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from backend.paths import config_db_path

CONFIG_DB_PATH = config_db_path()

DEFAULT_THRESHOLDS = {
    "structuring_threshold_inr": 200_000,
    "velocity_threshold_lakh": 15,
    "dormancy_months": 6,
    "gnn_confidence_pct": 70,
}

DEFAULT_FIU = {
    "endpoint": "https://fiuindia.gov.in/api/v2/str",
    "enabled": True,
    "auto_submit": False,
    "last_test_status": "not_tested",
}

DEFAULT_USERS = [
    {"id": "RK-001", "name": "Rajesh Kumar", "role": "Senior Investigator", "branch": "Mumbai HQ", "active": True},
    {"id": "PS-002", "name": "Priya Sharma", "role": "AML Analyst", "branch": "Delhi", "active": True},
    {"id": "AM-003", "name": "Amit Mehta", "role": "Supervisor", "branch": "Mumbai HQ", "active": True},
    {"id": "SK-004", "name": "Sneha Kapoor", "role": "FIU Liaison", "branch": "Central Ops", "active": True},
]


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(CONFIG_DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_config_tables() -> None:
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS config_kv (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS config_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            action TEXT NOT NULL,
            section TEXT NOT NULL,
            details TEXT,
            payload_json TEXT
        )
    """)
    con.commit()
    con.close()


def _get_json(key: str, default: Any) -> Any:
    con = _conn()
    row = con.execute("SELECT value_json FROM config_kv WHERE key = ?", (key,)).fetchone()
    con.close()
    if not row:
        return default
    try:
        return json.loads(row["value_json"])
    except json.JSONDecodeError:
        return default


def _set_json(key: str, value: Any) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    con = _conn()
    con.execute(
        """
        INSERT INTO config_kv (key, value_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, updated_at = excluded.updated_at
        """,
        (key, json.dumps(value, default=str), ts),
    )
    con.commit()
    con.close()


def append_audit_log(
    *,
    actor_id: str,
    action: str,
    section: str,
    details: str = "",
    payload: Optional[dict] = None,
) -> dict:
    ts = datetime.now(timezone.utc).isoformat()
    con = _conn()
    cur = con.execute(
        """
        INSERT INTO config_audit_log (timestamp, actor_id, action, section, details, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ts, actor_id, action, section, details, json.dumps(payload or {}, default=str)),
    )
    log_id = cur.lastrowid
    con.commit()
    con.close()
    return {
        "id": log_id,
        "timestamp": ts,
        "actor_id": actor_id,
        "action": action,
        "section": section,
        "details": details,
        "payload": payload or {},
    }


def get_audit_log(limit: int = 50) -> list[dict]:
    con = _conn()
    rows = con.execute(
        "SELECT * FROM config_audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    con.close()
    out = []
    for row in rows:
        payload = {}
        if row["payload_json"]:
            try:
                payload = json.loads(row["payload_json"])
            except json.JSONDecodeError:
                pass
        out.append({
            "id": row["id"],
            "timestamp": row["timestamp"],
            "actor_id": row["actor_id"],
            "action": row["action"],
            "section": row["section"],
            "details": row["details"],
            "payload": payload,
        })
    return out


def get_thresholds() -> dict:
    stored = _get_json("thresholds", {})
    return {**DEFAULT_THRESHOLDS, **stored}


def update_thresholds(updates: dict, actor_id: str = "admin") -> dict:
    current = get_thresholds()
    merged = {**current, **updates}
    _set_json("thresholds", merged)
    append_audit_log(
        actor_id=actor_id,
        action="thresholds_updated",
        section="thresholds",
        details="Detection thresholds saved",
        payload=updates,
    )
    return merged


def get_fiu_settings() -> dict:
    stored = _get_json("fiu", {})
    return {**DEFAULT_FIU, **stored}


def update_fiu_settings(updates: dict, actor_id: str = "admin") -> dict:
    current = get_fiu_settings()
    merged = {**current, **updates}
    _set_json("fiu", merged)
    append_audit_log(
        actor_id=actor_id,
        action="fiu_settings_updated",
        section="fiu",
        details="FIU integration settings updated",
        payload={k: v for k, v in updates.items() if k != "api_key"},
    )
    return merged


def get_users() -> list[dict]:
    return _get_json("users", DEFAULT_USERS)


def update_users(users: list[dict], actor_id: str = "admin") -> list[dict]:
    _set_json("users", users)
    append_audit_log(
        actor_id=actor_id,
        action="users_updated",
        section="users",
        details=f"User roster updated ({len(users)} users)",
    )
    return users


def get_data_source_overrides() -> dict:
    return _get_json("data_sources", {})


def update_data_source(source_id: str, patch: dict, actor_id: str = "admin") -> dict:
    overrides = get_data_source_overrides()
    current = overrides.get(source_id, {})
    overrides[source_id] = {**current, **patch}
    _set_json("data_sources", overrides)
    append_audit_log(
        actor_id=actor_id,
        action="data_source_updated",
        section="data",
        details=f"Data source {source_id} updated",
        payload=patch,
    )
    return overrides[source_id]
