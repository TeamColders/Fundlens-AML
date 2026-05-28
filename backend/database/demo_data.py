"""
FundLens — Demo data service.

Provides all data for the API when running in local/demo mode.
Loads from SQLite (fundlens_demo.db) if available, otherwise uses
hardcoded data matching the UI screenshots.

All API routes import from here — never directly from SQLite.
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Paths for demo data files (created by demo_seed.py)
DEMO_DB_PATH   = Path("fundlens_demo.db")
DEMO_JSON_DIR  = Path("data")

# ════════════════════════════════════════════════════════════════
# HARDCODED DEMO DATA (fallback when no demo_seed.py has been run)
# ════════════════════════════════════════════════════════════════

CASES = {
    "CASE-2847": {
        "case_id":           "CASE-2847",
        "typology":          "Round-trip Layering",
        "typology_code":     "round_trip_layering",
        "fatf_reference":    "FATF Typology 12",
        "pmla_section":      "Section 16",
        "risk_score":        0.94,
        "confidence":        "94%",
        "risk_level":        "critical",
        "total_amount":      4723000,
        "accounts_count":    7,
        "hops":              3,
        "duration_minutes":  374,
        "duration_display":  "6h 14m",
        "channel":           "NEFT + UPI",
        "status":            "active",
        "created_at":        "2026-03-22T09:14:03",
        "gnn_score":         0.94,
    },
    "CASE-2848": {
        "case_id":           "CASE-2848",
        "typology":          "Smurfing Pattern",
        "typology_code":     "structuring",
        "fatf_reference":    "FATF Typology 4",
        "pmla_section":      "Section 12",
        "risk_score":        0.87,
        "confidence":        "87%",
        "risk_level":        "critical",
        "total_amount":      2310000,
        "accounts_count":    14,
        "hops":              1,
        "duration_minutes":  4320,
        "duration_display":  "3 days",
        "channel":           "UPI + IMPS",
        "status":            "active",
        "created_at":        "2026-03-22T08:00:00",
        "gnn_score":         0.87,
    },
    "CASE-2849": {
        "case_id":           "CASE-2849",
        "typology":          "Shell Company Flow",
        "typology_code":     "shell_company_flow",
        "fatf_reference":    "FATF Typology 20",
        "pmla_section":      "Section 12",
        "risk_score":        0.91,
        "confidence":        "91%",
        "risk_level":        "critical",
        "total_amount":      15640000,
        "accounts_count":    5,
        "hops":              4,
        "duration_minutes":  108,
        "duration_display":  "1h 48m",
        "channel":           "RTGS + SWIFT",
        "status":            "active",
        "created_at":        "2026-03-22T08:10:00",
        "gnn_score":         0.91,
    },
}

ACCOUNTS = {
    "ACC-0041": {
        "account_id": "ACC-0041", "account_type": "savings", "status": "flagged",
        "kyc_tier": 2, "created_date": "2019-03-15", "last_active_date": "2024-01-22",
        "declared_income": 480000, "home_branch": "SB-Branch Mumbai Central",
        "is_dormant": True, "is_pep_adjacent": True,
        "owner_name": "Rajesh Kumar", "owner_type": "individual",
        "risk_level": "high", "risk_score": 87,
        "notes": "Dormant 26 months. PEP adjacent. KYC review pending Feb 2026.",
    },
    "ACC-0089": {
        "account_id": "ACC-0089", "account_type": "current", "status": "flagged",
        "kyc_tier": 1, "created_date": "2021-07-11", "last_active_date": "2026-03-22",
        "declared_income": 0, "home_branch": "CB-Branch Andheri East",
        "is_dormant": False, "is_pep_adjacent": False,
        "owner_name": "Nexus Trade Solutions Pvt Ltd", "owner_type": "entity",
        "risk_level": "critical", "risk_score": 96,
        "notes": "Shell entity. High-volume hub — ₹3.4Cr passed through in 90 days.",
    },
    "ACC-0112": {
        "account_id": "ACC-0112", "account_type": "savings", "status": "flagged",
        "kyc_tier": 2, "created_date": "2020-11-03", "last_active_date": "2026-03-22",
        "declared_income": 360000, "home_branch": "SB-Branch Borivali West",
        "is_dormant": False, "is_pep_adjacent": False,
        "owner_name": "Amit Desai", "owner_type": "individual",
        "risk_level": "medium", "risk_score": 62,
        "notes": "Intermediary. Received and immediately forwarded ₹7.8L.",
    },
    "ACC-0203": {
        "account_id": "ACC-0203", "account_type": "savings", "status": "flagged",
        "kyc_tier": 2, "created_date": "2021-04-20", "last_active_date": "2026-03-22",
        "declared_income": 420000, "home_branch": "SB-Branch Malad West",
        "is_dormant": False, "is_pep_adjacent": False,
        "owner_name": "Sunita Patil", "owner_type": "individual",
        "risk_level": "medium", "risk_score": 58,
        "notes": "Intermediary. Received and immediately forwarded ₹9.1L.",
    },
    "ACC-0317": {
        "account_id": "ACC-0317", "account_type": "savings", "status": "flagged",
        "kyc_tier": 2, "created_date": "2022-02-14", "last_active_date": "2026-03-22",
        "declared_income": 300000, "home_branch": "SB-Branch Kandivali East",
        "is_dormant": False, "is_pep_adjacent": False,
        "owner_name": "Vikram Nair", "owner_type": "individual",
        "risk_level": "medium", "risk_score": 55,
        "notes": "Intermediary — second layer.",
    },
    "ACC-0455": {
        "account_id": "ACC-0455", "account_type": "savings", "status": "flagged",
        "kyc_tier": 2, "created_date": "2022-05-30", "last_active_date": "2026-03-22",
        "declared_income": 340000, "home_branch": "SB-Branch Dahisar East",
        "is_dormant": False, "is_pep_adjacent": False,
        "owner_name": "Meena Shah", "owner_type": "individual",
        "risk_level": "medium", "risk_score": 54,
        "notes": "Intermediary — second layer.",
    },
    "ACC-0043": {
        "account_id": "ACC-0043", "account_type": "current", "status": "flagged",
        "kyc_tier": 1, "created_date": "2021-09-01", "last_active_date": "2026-03-22",
        "declared_income": 0, "home_branch": "CB-Branch Goregaon West",
        "is_dormant": False, "is_pep_adjacent": False,
        "owner_name": "Primex Ventures LLP", "owner_type": "entity",
        "risk_level": "high", "risk_score": 82,
        "notes": "Return destination. Linked to Nexus Trade Solutions via common director.",
    },
}

# ── CASE-2847 subgraph ───────────────────────────────────────────
SUBGRAPHS = {
    "CASE-2847": {
        "nodes": [
            {"id": "ACC-0041", "label": "ACC-0041", "risk_level": "high",
             "amount": 4723000, "account_type": "savings",
             "is_hub": False, "is_dormant": True, "is_origin": True},
            {"id": "ACC-0089", "label": "ACC-0089", "risk_level": "critical",
             "amount": 3420000, "account_type": "current",
             "is_hub": True, "is_dormant": False, "is_origin": False},
            {"id": "ACC-0112", "label": "ACC-0112", "risk_level": "medium",
             "amount": 780000, "account_type": "savings",
             "is_hub": False, "is_dormant": False, "is_origin": False},
            {"id": "ACC-0203", "label": "ACC-0203", "risk_level": "medium",
             "amount": 910000, "account_type": "savings",
             "is_hub": False, "is_dormant": False, "is_origin": False},
            {"id": "ACC-0317", "label": "ACC-0317", "risk_level": "medium",
             "amount": 840000, "account_type": "savings",
             "is_hub": False, "is_dormant": False, "is_origin": False},
            {"id": "ACC-0455", "label": "ACC-0455", "risk_level": "medium",
             "amount": 890000, "account_type": "savings",
             "is_hub": False, "is_dormant": False, "is_origin": False},
            {"id": "ACC-0043", "label": "ACC-0043", "risk_level": "high",
             "amount": 1730000, "account_type": "current",
             "is_hub": False, "is_dormant": False, "is_origin": False},
        ],
        "edges": [
            {"source": "EXTERNAL", "target": "ACC-0041", "amount": 4723000,
             "timestamp": "2026-03-22T09:14:03", "channel": "NEFT", "transaction_id": "TXN-2847-001"},
            {"source": "ACC-0041", "target": "ACC-0112", "amount": 780000,
             "timestamp": "2026-03-22T09:16:22", "channel": "NEFT", "transaction_id": "TXN-2847-002"},
            {"source": "ACC-0041", "target": "ACC-0203", "amount": 910000,
             "timestamp": "2026-03-22T09:16:22", "channel": "UPI", "transaction_id": "TXN-2847-003"},
            {"source": "ACC-0112", "target": "ACC-0089", "amount": 780000,
             "timestamp": "2026-03-22T10:02:11", "channel": "NEFT", "transaction_id": "TXN-2847-004"},
            {"source": "ACC-0203", "target": "ACC-0089", "amount": 910000,
             "timestamp": "2026-03-22T10:02:11", "channel": "IMPS", "transaction_id": "TXN-2847-005"},
            {"source": "ACC-0089", "target": "ACC-0317", "amount": 840000,
             "timestamp": "2026-03-22T11:44:55", "channel": "NEFT", "transaction_id": "TXN-2847-006"},
            {"source": "ACC-0089", "target": "ACC-0455", "amount": 890000,
             "timestamp": "2026-03-22T11:44:55", "channel": "UPI", "transaction_id": "TXN-2847-007"},
            {"source": "ACC-0317", "target": "ACC-0043", "amount": 840000,
             "timestamp": "2026-03-22T15:28:07", "channel": "UPI", "transaction_id": "TXN-2847-008"},
            {"source": "ACC-0455", "target": "ACC-0043", "amount": 890000,
             "timestamp": "2026-03-22T15:28:07", "channel": "IMPS", "transaction_id": "TXN-2847-009"},
        ],
    },
    "CASE-2848": {
        "nodes": [
            {"id": "ACC-0601", "label": "ACC-0601", "risk_level": "critical",
             "amount": 2310000, "account_type": "current",
             "is_hub": True, "is_dormant": False, "is_origin": False},
        ] + [
            {"id": f"ACC-{700+i:04d}", "label": f"ACC-{700+i:04d}", "risk_level": "medium",
             "amount": amt, "account_type": "savings",
             "is_hub": False, "is_dormant": False, "is_origin": True}
            for i, amt in enumerate([165000, 172000, 158000, 189000, 164000,
                                      175000, 160000, 181000, 157000, 168000,
                                      170000, 159000, 176000, 192000])
        ],
        "edges": [
            {"source": f"ACC-{700+i:04d}", "target": "ACC-0601", "amount": amt,
             "timestamp": f"2026-03-{20 + i//5}T{9 + i%5*2:02d}:00:00",
             "channel": "UPI" if i % 2 == 0 else "IMPS",
             "transaction_id": f"TXN-2848-{i+1:03d}"}
            for i, amt in enumerate([1650000, 1720000, 1580000, 1890000, 1640000,
                                      1750000, 1600000, 1810000, 1570000, 1680000,
                                      1700000, 1590000, 1760000, 1920000])
        ],
    },
    "CASE-2849": {
        "nodes": [
            {"id": "ACC-0901", "label": "ACC-0901", "risk_level": "critical",
             "amount": 15640000, "account_type": "current",
             "is_hub": False, "is_dormant": False, "is_origin": True},
            {"id": "ACC-0902", "label": "ACC-0902", "risk_level": "critical",
             "amount": 15620000, "account_type": "current",
             "is_hub": False, "is_dormant": False, "is_origin": False},
            {"id": "ACC-0903", "label": "ACC-0903", "risk_level": "critical",
             "amount": 15600000, "account_type": "current",
             "is_hub": False, "is_dormant": False, "is_origin": False},
            {"id": "ACC-0904", "label": "ACC-0904", "risk_level": "high",
             "amount": 15580000, "account_type": "current",
             "is_hub": False, "is_dormant": False, "is_origin": False},
            {"id": "ACC-0905", "label": "ACC-0905", "risk_level": "critical",
             "amount": 15580000, "account_type": "current",
             "is_hub": False, "is_dormant": False, "is_origin": False},
        ],
        "edges": [
            {"source": "ACC-0901", "target": "ACC-0902", "amount": 15640000,
             "timestamp": "2026-03-22T08:10:00", "channel": "RTGS", "transaction_id": "TXN-2849-001"},
            {"source": "ACC-0902", "target": "ACC-0903", "amount": 15620000,
             "timestamp": "2026-03-22T08:41:15", "channel": "RTGS", "transaction_id": "TXN-2849-002"},
            {"source": "ACC-0903", "target": "ACC-0904", "amount": 15600000,
             "timestamp": "2026-03-22T09:05:44", "channel": "NEFT", "transaction_id": "TXN-2849-003"},
            {"source": "ACC-0904", "target": "ACC-0905", "amount": 15580000,
             "timestamp": "2026-03-22T09:58:30", "channel": "SWIFT", "transaction_id": "TXN-2849-004"},
            {"source": "ACC-0901", "target": "ACC-0903", "amount": 800000,
             "timestamp": "2026-03-22T08:15:00", "channel": "IMPS", "transaction_id": "TXN-2849-005"},
        ],
    },
}

TIMELINES = {
    "CASE-2847": [
        {"timestamp": "09:14:03", "sender": "EXTERNAL", "receiver": "ACC-0041", "amount": 4723000, "channel": "NEFT"},
        {"timestamp": "09:16:22", "sender": "ACC-0041", "receiver": "ACC-0112", "amount": 780000, "channel": "NEFT"},
        {"timestamp": "09:16:22", "sender": "ACC-0041", "receiver": "ACC-0203", "amount": 910000, "channel": "UPI"},
        {"timestamp": "10:02:11", "sender": "ACC-0112", "receiver": "ACC-0089", "amount": 780000, "channel": "NEFT"},
        {"timestamp": "10:02:11", "sender": "ACC-0203", "receiver": "ACC-0089", "amount": 910000, "channel": "IMPS"},
        {"timestamp": "11:44:55", "sender": "ACC-0089", "receiver": "ACC-0317", "amount": 840000, "channel": "NEFT"},
        {"timestamp": "11:44:55", "sender": "ACC-0089", "receiver": "ACC-0455", "amount": 890000, "channel": "UPI"},
        {"timestamp": "15:28:07", "sender": "ACC-0317", "receiver": "ACC-0043", "amount": 840000, "channel": "UPI"},
        {"timestamp": "15:28:07", "sender": "ACC-0455", "receiver": "ACC-0043", "amount": 890000, "channel": "IMPS"},
    ],
    "CASE-2848": [],
    "CASE-2849": [
        {"timestamp": "08:10:00", "sender": "ACC-0901", "receiver": "ACC-0902", "amount": 15640000, "channel": "RTGS"},
        {"timestamp": "08:15:00", "sender": "ACC-0901", "receiver": "ACC-0903", "amount": 800000, "channel": "IMPS"},
        {"timestamp": "08:41:15", "sender": "ACC-0902", "receiver": "ACC-0903", "amount": 15620000, "channel": "RTGS"},
        {"timestamp": "09:05:44", "sender": "ACC-0903", "receiver": "ACC-0904", "amount": 15600000, "channel": "NEFT"},
        {"timestamp": "09:58:30", "sender": "ACC-0904", "receiver": "ACC-0905", "amount": 15580000, "channel": "SWIFT"},
    ],
}

# Transactions for entity profile pages
ENTITY_TRANSACTIONS = {
    "ACC-0041": [
        {"date": "2026-03-22", "time": "09:14", "counterparty": "EXTERNAL", "amount": 4723000, "channel": "NEFT", "flagged": True, "direction": "in"},
        {"date": "2026-03-22", "time": "09:16", "counterparty": "ACC-0112", "amount": 780000, "channel": "NEFT", "flagged": True, "direction": "out"},
        {"date": "2026-03-22", "time": "09:16", "counterparty": "ACC-0203", "amount": 910000, "channel": "UPI", "flagged": True, "direction": "out"},
        {"date": "2023-12-15", "time": "10:45", "counterparty": "Utility Bill", "amount": 1240, "channel": "Bill Pay", "flagged": False, "direction": "out"},
        {"date": "2023-12-08", "time": "14:20", "counterparty": "Salary Credit", "amount": 45000, "channel": "NEFT", "flagged": False, "direction": "in"},
        {"date": "2023-11-28", "time": "09:15", "counterparty": "Grocery Store", "amount": 3200, "channel": "UPI", "flagged": False, "direction": "out"},
        {"date": "2023-11-20", "time": "16:30", "counterparty": "Utility Bill", "amount": 1180, "channel": "Bill Pay", "flagged": False, "direction": "out"},
    ],
}

ENTITY_METRICS = {
    "ACC-0041": {
        "avg_monthly_volume": 12400,
        "current_month_volume": 4723000,
        "baseline_deviation": "3,800%",
        "counterparties_30d": 8,
        "inbound_ratio": 0.97,
        "outbound_ratio": 0.03,
    },
}

ENTITY_NETWORK = {
    "ACC-0041": [
        {"id": "ACC-0112", "risk_level": "medium"},
        {"id": "ACC-0203", "risk_level": "medium"},
        {"id": "ACC-0089", "risk_level": "critical"},
        {"id": "ACC-0317", "risk_level": "medium"},
        {"id": "ACC-0455", "risk_level": "medium"},
    ],
}

ENTITY_RELATED = {
    "ACC-0041": [
        {"name": "Priya Kumar", "relation": "Same address", "risk_score": 42},
        {"name": "Amit Sharma", "relation": "Same mobile", "risk_score": 68},
        {"name": "ACC-0892", "relation": "Shared device login", "risk_score": 81},
    ],
}

ANALYTICS = {
    "alerts_today":         47,
    "alerts_this_week":     312,
    "total_cases":          3,
    "critical_count":       3,
    "high_count":           12,
    "medium_count":         32,
    "total_amount_flagged": 22673000,
    "false_positive_rate":  0.028,
    "avg_resolution_time":  "4h 22m",
    "top_typologies": [
        {"name": "Structuring / Smurfing", "count": 18, "percentage": 38.3},
        {"name": "Round-trip Layering", "count": 12, "percentage": 25.5},
        {"name": "Shell Company Flow", "count": 8, "percentage": 17.0},
        {"name": "Dormant Account Activation", "count": 5, "percentage": 10.6},
        {"name": "Fan-out / Fan-in", "count": 4, "percentage": 8.5},
    ],
    "channel_breakdown": [
        {"channel": "NEFT", "count": 156, "percentage": 33.2},
        {"channel": "UPI", "count": 141, "percentage": 30.0},
        {"channel": "IMPS", "count": 94, "percentage": 20.0},
        {"channel": "RTGS", "count": 47, "percentage": 10.0},
        {"channel": "SWIFT", "count": 22, "percentage": 4.7},
        {"channel": "Cards", "count": 10, "percentage": 2.1},
    ],
    "daily_trend": [
        {"date": "2026-03-16", "alerts": 38},
        {"date": "2026-03-17", "alerts": 42},
        {"date": "2026-03-18", "alerts": 35},
        {"date": "2026-03-19", "alerts": 51},
        {"date": "2026-03-20", "alerts": 44},
        {"date": "2026-03-21", "alerts": 39},
        {"date": "2026-03-22", "alerts": 47},
    ],
    "risk_distribution": [
        {"level": "Critical", "count": 3, "color": "#EF4444"},
        {"level": "High", "count": 12, "color": "#F59E0B"},
        {"level": "Medium", "count": 32, "color": "#3B82F6"},
    ],
}


# ════════════════════════════════════════════════════════════════
# PUBLIC API — functions used by API routes
# ════════════════════════════════════════════════════════════════

def get_alerts(status: Optional[str] = None, limit: int = 20, offset: int = 0) -> dict:
    """Return paginated alert list."""
    alerts = []
    for case_id, meta in CASES.items():
        if status and meta.get("status") != status:
            continue
        alerts.append({
            "case_id":        meta["case_id"],
            "typology":       meta["typology"],
            "risk_score":     meta["risk_score"],
            "total_amount":   meta["total_amount"],
            "accounts_count": meta["accounts_count"],
            "hops":           meta["hops"],
            "duration":       meta["duration_display"],
            "channel":        meta["channel"],
            "created_at":     meta["created_at"],
            "status":         meta["status"],
            "confidence":     meta["confidence"],
            "risk_level":     meta["risk_level"],
        })

    # Sort by risk_score descending
    alerts.sort(key=lambda a: a["risk_score"], reverse=True)
    total = len(alerts)
    alerts = alerts[offset:offset + limit]

    return {"alerts": alerts, "total": total, "page": (offset // limit) + 1}


def get_alert_detail(case_id: str) -> Optional[dict]:
    """Return full alert detail including subgraph and timeline."""
    meta = CASES.get(case_id)
    if not meta:
        return None

    subgraph = SUBGRAPHS.get(case_id, {"nodes": [], "edges": []})
    timeline = TIMELINES.get(case_id, [])

    return {
        **meta,
        "subgraph": subgraph,
        "timeline": timeline,
    }


def get_case_data(case_id: str) -> Optional[dict]:
    """Return case data formatted for LLM prompts."""
    meta = CASES.get(case_id)
    if not meta:
        return None

    subgraph = SUBGRAPHS.get(case_id, {"nodes": [], "edges": []})
    timeline = TIMELINES.get(case_id, [])

    return {
        "case_id":                 meta["case_id"],
        "typology_name":           meta["typology"],
        "typology_fatf_reference": meta["fatf_reference"],
        "total_amount":            meta["total_amount"],
        "accounts_count":          meta["accounts_count"],
        "hop_count":               meta["hops"],
        "duration_hours":          meta["duration_minutes"] / 60,
        "gnn_score":               meta["gnn_score"],
        "channel":                 meta["channel"],
        "subgraph":                subgraph,
        "timeline":                timeline,
    }


def get_subgraph(case_id: str) -> Optional[dict]:
    """Return subgraph nodes and edges for a case."""
    return SUBGRAPHS.get(case_id)


def get_entity(account_id: str) -> Optional[dict]:
    """Return full entity profile."""
    account = ACCOUNTS.get(account_id)
    if not account:
        return None

    return {
        **account,
        "transactions":    ENTITY_TRANSACTIONS.get(account_id, []),
        "metrics":         ENTITY_METRICS.get(account_id, {}),
        "network":         ENTITY_NETWORK.get(account_id, []),
        "related_entities": ENTITY_RELATED.get(account_id, []),
    }


def get_analytics() -> dict:
    """Return analytics dashboard data."""
    return ANALYTICS


def list_cases() -> list[dict]:
    """Return summary list of all cases."""
    return list(CASES.values())


def update_alert_status(case_id: str, status: str, investigator_id: str, notes: str = "") -> bool:
    """Update case status (in-memory for demo)."""
    if case_id not in CASES:
        return False
    CASES[case_id]["status"] = status
    return True
