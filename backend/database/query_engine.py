"""
Execute natural-language AML questions against Postgres/SQLite when Neo4j is unavailable.
"""
from __future__ import annotations

import re
import time
from typing import Any, Optional

from backend.database.demo_data import (
    DEMO_DB_PATH,
    _load_all_cases,
    get_alert_detail,
    get_case_data,
    get_dict_db,
    get_entity,
)

_RISK_SCORE = {"critical": 94, "high": 78, "medium": 58, "low": 42}


def _extract_account_id(text: str) -> Optional[str]:
    match = re.search(r"ACC-[\w-]+", text, re.IGNORECASE)
    return match.group(0).upper() if match else None


def _risk_score(level: Optional[str]) -> int:
    return _RISK_SCORE.get((level or "medium").lower(), 55)


def _run_sql(sql: str, params: tuple = ()) -> list[dict]:
    rows: list[dict] = []
    if get_dict_db is not None:
        try:
            with get_dict_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    rows = [dict(r) for r in cur.fetchall()]
            return rows
        except Exception:
            pass

    if DEMO_DB_PATH.exists():
        import sqlite3

        con = sqlite3.connect(DEMO_DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.execute(sql.replace("%s", "?"), params)
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
    return rows


def _connected_accounts(account_id: str) -> tuple[list[dict], str]:
    sql = """
        SELECT
            CASE WHEN sender = %s THEN receiver ELSE sender END AS account_id,
            SUM(amount) AS total_amount,
            COUNT(*) AS transfer_count,
            MAX(channel) AS channel
        FROM transactions
        WHERE sender = %s OR receiver = %s
        GROUP BY account_id
        ORDER BY total_amount DESC
        LIMIT 50
    """
    rows = _run_sql(sql, (account_id, account_id, account_id))
    enriched = []
    for row in rows:
        cp = row.get("account_id")
        if not cp or cp == account_id:
            continue
        acc = _run_sql("SELECT risk_level, is_dormant, owner_name FROM accounts WHERE account_id = %s", (cp,))
        meta = acc[0] if acc else {}
        enriched.append({
            "account_id": cp,
            "total_amount": float(row.get("total_amount") or 0),
            "transfer_count": int(row.get("transfer_count") or 0),
            "channel": row.get("channel") or "—",
            "risk_level": meta.get("risk_level") or "medium",
            "risk_score": _risk_score(meta.get("risk_level")),
            "is_dormant": bool(meta.get("is_dormant")),
            "owner_name": meta.get("owner_name") or "—",
        })
    cypher = (
        f"MATCH (a:Account {{account_id: '{account_id}'}})-[t:TRANSFERRED_TO]-(b:Account)\n"
        "RETURN b.account_id, sum(t.amount) AS total_amount\n"
        "ORDER BY total_amount DESC LIMIT 50"
    )
    return enriched, cypher


def _is_dormant_flag(value: Any) -> bool:
    return value in (1, True, "1", "true", "True")


def _dormant_activation() -> tuple[list[dict], str]:
    dormant_accounts = _run_sql("SELECT account_id, last_active_date, is_dormant FROM accounts")
    dormant_ids = {
        r["account_id"]: r.get("last_active_date")
        for r in dormant_accounts
        if _is_dormant_flag(r.get("is_dormant"))
    }
    if not dormant_ids:
        return [], (
            "MATCH (source:Account {is_dormant: true})-[t:TRANSFERRED_TO]->(target:Account)\n"
            "RETURN target.account_id, sum(t.amount) AS amount_received LIMIT 50"
        )

    placeholders = ",".join(["%s"] * len(dormant_ids))
    sql = f"""
        SELECT receiver AS account_id, sender AS dormant_source, SUM(amount) AS amount_received
        FROM transactions
        WHERE sender IN ({placeholders})
        GROUP BY receiver, sender
        ORDER BY amount_received DESC
        LIMIT 50
    """
    rows = _run_sql(sql, tuple(dormant_ids.keys()))
    results = []
    for row in rows:
        receiver = row.get("account_id")
        acc = _run_sql("SELECT risk_level FROM accounts WHERE account_id = %s", (receiver,))
        level = acc[0].get("risk_level") if acc else "medium"
        src = row.get("dormant_source")
        results.append({
            "account_id": receiver,
            "amount_received": float(row.get("amount_received") or 0),
            "dormant_source": src,
            "source_last_active": dormant_ids.get(src),
            "risk_score": _risk_score(level),
        })
    cypher = (
        "MATCH (source:Account {is_dormant: true})-[t:TRANSFERRED_TO]->(target:Account)\n"
        "RETURN target.account_id, sum(t.amount) AS amount_received, source.account_id\n"
        "ORDER BY amount_received DESC LIMIT 50"
    )
    return results, cypher


def _structuring_patterns(min_amount: float = 100_000) -> tuple[list[dict], str]:
    sql = """
        SELECT sender, receiver, amount, channel, timestamp, case_id
        FROM transactions
        WHERE amount >= %s
        ORDER BY amount DESC
        LIMIT 50
    """
    rows = _run_sql(sql, (min_amount,))
    results = [
        {
            "sender": r.get("sender"),
            "receiver": r.get("receiver"),
            "amount": float(r.get("amount") or 0),
            "channel": r.get("channel"),
            "timestamp": str(r.get("timestamp") or "")[:19],
            "case_id": r.get("case_id"),
        }
        for r in rows
    ]
    cypher = (
        f"MATCH ()-[t:TRANSFERRED_TO]->() WHERE t.amount >= {min_amount}\n"
        "RETURN t.sender, t.receiver, t.amount, t.channel\n"
        "ORDER BY t.amount DESC LIMIT 50"
    )
    return results, cypher


def _hub_accounts() -> tuple[list[dict], str]:
    sql = """
        SELECT receiver AS account_id, COUNT(*) AS incoming_count, SUM(amount) AS total_in
        FROM transactions
        GROUP BY receiver
        HAVING COUNT(*) >= 3
        ORDER BY incoming_count DESC
        LIMIT 20
    """
    rows = _run_sql(sql)
    results = []
    for row in rows:
        aid = row.get("account_id")
        acc = _run_sql("SELECT risk_level FROM accounts WHERE account_id = %s", (aid,))
        level = acc[0].get("risk_level") if acc else "medium"
        results.append({
            "account_id": aid,
            "incoming_transfers": int(row.get("incoming_count") or 0),
            "total_inbound": float(row.get("total_in") or 0),
            "risk_level": level,
            "risk_score": _risk_score(level),
        })
    cypher = (
        "MATCH (a:Account)<-[t:TRANSFERRED_TO]-(b)\n"
        "WITH a, count(t) AS incoming\n"
        "WHERE incoming >= 3\n"
        "RETURN a.account_id, incoming ORDER BY incoming DESC LIMIT 20"
    )
    return results, cypher


def _entity_risk(name_fragment: str) -> tuple[list[dict], str, Optional[dict]]:
    sql = """
        SELECT account_id, owner_name, risk_level, home_branch, is_dormant, declared_income
        FROM accounts
        WHERE LOWER(owner_name) LIKE %s
        LIMIT 10
    """
    pattern = f"%{name_fragment.lower()}%"
    rows = _run_sql(sql, (pattern,))
    if not rows and name_fragment:
        rows = _run_sql(
            "SELECT account_id, owner_name, risk_level, home_branch, is_dormant, declared_income "
            "FROM accounts WHERE account_id = %s LIMIT 1",
            (name_fragment.upper(),),
        )
    results = []
    for r in rows:
        results.append({
            "account_id": r.get("account_id"),
            "owner_name": r.get("owner_name"),
            "risk_level": r.get("risk_level"),
            "risk_score": _risk_score(r.get("risk_level")),
            "home_branch": r.get("home_branch"),
            "is_dormant": bool(r.get("is_dormant")),
        })
    entity_card = None
    if results:
        first_id = results[0]["account_id"]
        entity_card = get_entity(first_id)
    cypher = (
        "MATCH (a:Account) WHERE toLower(a.owner_name) CONTAINS toLower($name)\n"
        "RETURN a.account_id, a.owner_name, a.risk_level LIMIT 10"
    )
    return results, cypher, entity_card


def _case_accounts(case_id: str) -> tuple[list[dict], str]:
    sql = """
        SELECT DISTINCT a.account_id, a.owner_name, a.risk_level, a.is_dormant
        FROM accounts a
        JOIN transactions t ON t.sender = a.account_id OR t.receiver = a.account_id
        WHERE t.case_id = %s
        LIMIT 50
    """
    rows = _run_sql(sql, (case_id,))
    results = [
        {
            "account_id": r.get("account_id"),
            "owner_name": r.get("owner_name"),
            "risk_level": r.get("risk_level"),
            "risk_score": _risk_score(r.get("risk_level")),
            "is_dormant": bool(r.get("is_dormant")),
        }
        for r in rows
    ]
    cypher = (
        f"MATCH (a:Account)-[t:TRANSFERRED_TO]-(b:Account)\n"
        f"WHERE t.case_id = '{case_id}'\n"
        "RETURN DISTINCT a.account_id, a.risk_level LIMIT 50"
    )
    return results, cypher


def _top_risk_accounts() -> tuple[list[dict], str]:
    cases = _load_all_cases()
    results = [
        {
            "case_id": c.get("case_id"),
            "typology": c.get("typology"),
            "risk_level": c.get("risk_level"),
            "risk_score": _risk_score(c.get("risk_level")),
            "total_amount": float(c.get("total_amount") or 0),
        }
        for c in cases[:20]
    ]
    cypher = "MATCH (a:Account) RETURN a.account_id, a.risk_level ORDER BY a.risk_level LIMIT 20"
    return results, cypher


_ANALYTICAL_HINTS = (
    "explain",
    "why ",
    "why?",
    "how ",
    "what should",
    "recommend",
    "summarize",
    "summary of",
    "compare",
    "describe",
    "tell me about",
    "meaning of",
    "suspicious because",
    "next step",
    "investigate",
    "overview",
    "analysis",
    "pattern suggest",
    "typology mean",
    "red flag",
)


def is_analytical_question(query: str) -> bool:
    q = query.lower()
    return any(hint in q for hint in _ANALYTICAL_HINTS)


def should_use_gemini_answer(query: str, handler: str) -> bool:
    return handler == "fallback" or is_analytical_question(query)


def _extract_case_id(text: str) -> Optional[str]:
    match = re.search(r"CASE-[\w-]+", text, re.IGNORECASE)
    return match.group(0).upper() if match else None


def _compact_entity(entity: dict) -> dict:
    metrics = entity.get("metrics") or {}
    return {
        "account_id": entity.get("account_id"),
        "owner_name": entity.get("owner_name"),
        "risk_level": entity.get("risk_level"),
        "risk_score": entity.get("risk_score"),
        "home_branch": entity.get("home_branch"),
        "is_dormant": entity.get("is_dormant"),
        "counterparties_30d": metrics.get("counterparties_30d"),
        "current_month_volume": metrics.get("current_month_volume"),
        "watch_flags": entity.get("watch_flags"),
    }


def _compact_case(case_data: dict) -> dict:
    nodes = (case_data.get("subgraph") or {}).get("nodes") or []
    return {
        "case_id": case_data.get("case_id"),
        "typology": case_data.get("typology_name") or case_data.get("typology"),
        "fatf_reference": case_data.get("typology_fatf_reference"),
        "total_amount": case_data.get("total_amount"),
        "accounts_count": case_data.get("accounts_count"),
        "gnn_score": case_data.get("gnn_score"),
        "channel": case_data.get("channel"),
        "accounts": [
            {
                "id": n.get("id"),
                "role": "hub"
                if n.get("is_hub")
                else "origin"
                if n.get("is_origin")
                else "dormant"
                if n.get("is_dormant")
                else "intermediary",
                "risk_level": n.get("risk_level"),
            }
            for n in nodes[:12]
        ],
        "timeline_sample": (case_data.get("timeline") or [])[:8],
    }


def build_query_context(
    query: str,
    *,
    case_id: Optional[str] = None,
    sql_payload: Optional[dict] = None,
    neo4j_records: Optional[list] = None,
) -> dict:
    """Gather investigation facts for Gemini Q&A (same data family as STR prompts)."""
    account_id = _extract_account_id(query)
    resolved_case = case_id or _extract_case_id(query)

    active_case = None
    if resolved_case:
        active_case = get_case_data(resolved_case) or get_alert_detail(resolved_case)
    if not active_case:
        cases = _load_all_cases()
        if cases:
            active_case = get_case_data(cases[0]["case_id"]) or get_alert_detail(cases[0]["case_id"])

    entity = None
    if account_id:
        try:
            entity = get_entity(account_id)
        except Exception:
            entity = None

    recent_cases = [
        {
            "case_id": c.get("case_id"),
            "typology": c.get("typology"),
            "risk_level": c.get("risk_level"),
            "total_amount": c.get("total_amount"),
        }
        for c in _load_all_cases()[:8]
    ]

    sql_results = (sql_payload or {}).get("results") or []
    ctx = {
        "active_case": _compact_case(active_case) if active_case else None,
        "entity": _compact_entity(entity) if entity else None,
        "recent_cases": recent_cases,
        "sql_handler": (sql_payload or {}).get("handler"),
        "sql_row_count": len(sql_results),
        "sql_results_preview": sql_results[:15],
        "sql_summary": (sql_payload or {}).get("summary"),
        "neo4j_results_preview": (neo4j_records or [])[:15],
    }
    return ctx


def execute_nl_query_local(query: str, case_id: Optional[str] = None) -> dict:
    """Pattern-based NL query over SQL demo store."""
    start = time.time()
    q = query.lower().strip()
    account_id = _extract_account_id(query)
    results: list[dict] = []
    cypher = ""
    summary = ""
    entity_card: Optional[dict] = None
    display_type = "table"
    handler = "fallback"

    if account_id and ("connected" in q or "link" in q or "neighbor" in q):
        results, cypher = _connected_accounts(account_id)
        summary = f"Found {len(results)} accounts connected to {account_id} in the transaction ledger."
        handler = "connected"
    elif "dormant" in q:
        results, cypher = _dormant_activation()
        summary = f"Found {len(results)} receive paths from dormant accounts."
        handler = "dormant"
    elif "hub" in q or "central" in q:
        results, cypher = _hub_accounts()
        summary = f"Identified {len(results)} hub-style accounts (3+ inbound transfers)."
        handler = "hub"
    elif "structur" in q or "10l" in q or "10 l" in q or "100000" in q:
        results, cypher = _structuring_patterns()
        summary = f"Found {len(results)} transfers at or above ₹1L."
        handler = "structuring"
    elif "risk profile" in q or "entity" in q or "owner" in q:
        name = re.sub(r"(?i)(what is|the|risk profile of|entity|account|owner)", "", query).strip()
        name = name.replace("?", "").strip() or account_id or ""
        results, cypher, entity_card = _entity_risk(name)
        display_type = "entity" if entity_card else "table"
        summary = f"Found {len(results)} matching account(s) for “{name or account_id}”."
        handler = "entity"
    elif re.search(r"case[-\s]?db[-\s]?\d+", q, re.I) or re.search(r"case-\d+", q, re.I):
        case_match = re.search(r"CASE-[\w-]+", query, re.I)
        cid = case_match.group(0).upper() if case_match else None
        if cid:
            results, cypher = _case_accounts(cid)
            summary = f"Listed {len(results)} accounts in case {cid}."
            handler = "case"
    elif "active investigation" in q or "active case" in q or (
        case_id and ("case" in q or "investigation" in q)
    ):
        cid = case_id or _extract_case_id(query)
        if not cid:
            cases = _load_all_cases()
            cid = cases[0]["case_id"] if cases else None
        if cid:
            results, cypher = _case_accounts(cid)
            summary = f"Accounts involved in case {cid}."
            handler = "case"
    elif case_id and ("account" in q or "list" in q):
        results, cypher = _case_accounts(case_id)
        summary = f"Listed {len(results)} accounts in case {case_id}."
        handler = "case"
    else:
        results, cypher = _top_risk_accounts()
        summary = f"Showing {len(results)} recent investigation cases from the alert queue."
        handler = "fallback"

    elapsed = round((time.time() - start) * 1000, 1)
    return {
        "query": query,
        "cypher": cypher,
        "results": results,
        "result_count": len(results),
        "execution_ms": elapsed,
        "summary": summary,
        "source": "sql",
        "display_type": display_type,
        "entity": entity_card,
        "handler": handler,
    }
