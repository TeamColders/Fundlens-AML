"""
demo_seed.py
============
FundLens — Demo data seeder.

Creates all accounts, entities, and transactions shown in the UI screenshots:
  • CASE-2847 — Round-trip Layering  (7 accounts, ₹47.2L)
  • CASE-2848 — Smurfing / Structuring (14 accounts, ₹23.1L)
  • CASE-2849 — Shell Company Flow    (5 accounts, ₹156.4L)

Works in three modes (auto-detected):
  1. FULL   — writes to Neo4j + PostgreSQL (requires Docker stack running)
  2. NEO4J  — writes to Neo4j only
  3. LOCAL  — writes to SQLite + JSON files (no infrastructure needed)

Run:
    python demo_seed.py               # auto-detects mode
    python demo_seed.py --mode local  # force local mode (laptop demo)
    python demo_seed.py --mode neo4j  # Neo4j only
    python demo_seed.py --mode full   # Neo4j + PostgreSQL

After running, the backend API will return real data for all three cases.
"""

import argparse
import json
import os
import sqlite3
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Optional

# ── Colour helpers for terminal output ───────────────────────────
def green(s):  return f"\033[92m{s}\033[0m"
def red(s):    return f"\033[91m{s}\033[0m"
def cyan(s):   return f"\033[96m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def bold(s):   return f"\033[1m{s}\033[0m"

def log(msg):    print(f"  {msg}")
def ok(msg):     print(f"  {green('✓')} {msg}")
def warn(msg):   print(f"  {yellow('⚠')} {msg}")
def fail(msg):   print(f"  {red('✗')} {msg}")
def section(msg): print(f"\n{bold(cyan('──'))} {bold(msg)}")


# ════════════════════════════════════════════════════════════════
# DATA MODELS
# ════════════════════════════════════════════════════════════════

@dataclass
class Account:
    account_id:       str
    account_type:     str          # savings | current | nri
    status:           str          # active | dormant | flagged
    kyc_tier:         int          # 1 | 2 | 3
    created_date:     str          # ISO date string
    last_active_date: str
    declared_income:  float        # annual, INR
    home_branch:      str
    is_dormant:       bool
    is_pep_adjacent:  bool
    owner_name:       str
    owner_type:       str          # individual | entity
    risk_level:       str          # low | medium | high | critical
    notes:            str = ""

@dataclass
class Transaction:
    transaction_id:   str
    sender:           str          # account_id or "EXTERNAL"
    receiver:         str
    amount:           float        # INR
    currency:         str = "INR"
    timestamp:        str = ""     # HH:MM:SS on the demo date
    channel:          str = "NEFT" # NEFT | UPI | IMPS | RTGS | SWIFT
    branch_code:      str = "MUM001"
    reference_number: str = ""
    is_fraud:         bool = False
    typology:         str = ""     # round_trip_layering | structuring | shell_flow
    case_id:          str = ""
    demo_date:        str = "2026-03-22"

    def full_timestamp(self) -> str:
        return f"{self.demo_date}T{self.timestamp}"


# ════════════════════════════════════════════════════════════════
# CASE DEFINITIONS
# ════════════════════════════════════════════════════════════════

def build_case_2847() -> tuple[list[Account], list[Transaction]]:
    """
    CASE-2847 — Round-trip Layering
    ₹47,23,000 cycled through 7 accounts over 6h 14m.
    Matches FATF Typology 12. GNN score 0.94.
    """
    accounts = [
        Account(
            account_id="ACC-0041",
            account_type="savings",
            status="flagged",
            kyc_tier=2,
            created_date="2019-03-15",
            last_active_date="2024-01-22",   # 26 months dormant before today
            declared_income=480000,
            home_branch="SB-Branch Mumbai Central",
            is_dormant=True,
            is_pep_adjacent=True,
            owner_name="Rajesh Kumar",
            owner_type="individual",
            risk_level="high",
            notes="Dormant 26 months. PEP adjacent — linked to Priya Kumar (same address). KYC review pending Feb 2026.",
        ),
        Account(
            account_id="ACC-0089",
            account_type="current",
            status="flagged",
            kyc_tier=1,
            created_date="2021-07-11",
            last_active_date="2026-03-22",
            declared_income=0,
            home_branch="CB-Branch Andheri East",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Nexus Trade Solutions Pvt Ltd",
            owner_type="entity",
            risk_level="critical",
            notes="Shell entity. Registered 2021. No declared business income. High-volume hub — ₹3.4Cr passed through in 90 days.",
        ),
        Account(
            account_id="ACC-0112",
            account_type="savings",
            status="flagged",
            kyc_tier=2,
            created_date="2020-11-03",
            last_active_date="2026-03-22",
            declared_income=360000,
            home_branch="SB-Branch Borivali West",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Amit Desai",
            owner_type="individual",
            risk_level="medium",
            notes="Intermediary. Received and immediately forwarded ₹7.8L.",
        ),
        Account(
            account_id="ACC-0203",
            account_type="savings",
            status="flagged",
            kyc_tier=2,
            created_date="2021-04-20",
            last_active_date="2026-03-22",
            declared_income=420000,
            home_branch="SB-Branch Malad West",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Sunita Patil",
            owner_type="individual",
            risk_level="medium",
            notes="Intermediary. Received and immediately forwarded ₹9.1L.",
        ),
        Account(
            account_id="ACC-0317",
            account_type="savings",
            status="flagged",
            kyc_tier=2,
            created_date="2022-02-14",
            last_active_date="2026-03-22",
            declared_income=300000,
            home_branch="SB-Branch Kandivali East",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Vikram Nair",
            owner_type="individual",
            risk_level="medium",
            notes="Intermediary — second layer.",
        ),
        Account(
            account_id="ACC-0455",
            account_type="savings",
            status="flagged",
            kyc_tier=2,
            created_date="2022-05-30",
            last_active_date="2026-03-22",
            declared_income=340000,
            home_branch="SB-Branch Dahisar East",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Meena Shah",
            owner_type="individual",
            risk_level="medium",
            notes="Intermediary — second layer.",
        ),
        Account(
            account_id="ACC-0043",
            account_type="current",
            status="flagged",
            kyc_tier=1,
            created_date="2021-09-01",
            last_active_date="2026-03-22",
            declared_income=0,
            home_branch="CB-Branch Goregaon West",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Primex Ventures LLP",
            owner_type="entity",
            risk_level="high",
            notes="Return destination. Linked to Nexus Trade Solutions via common director.",
        ),
    ]

    txns = [
        Transaction(
            transaction_id="TXN-2847-001",
            sender="EXTERNAL",
            receiver="ACC-0041",
            amount=4723000,
            timestamp="09:14:03",
            channel="NEFT",
            reference_number="NEFT20260322001",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
        Transaction(
            transaction_id="TXN-2847-002",
            sender="ACC-0041",
            receiver="ACC-0112",
            amount=780000,
            timestamp="09:16:22",
            channel="NEFT",
            reference_number="NEFT20260322002",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
        Transaction(
            transaction_id="TXN-2847-003",
            sender="ACC-0041",
            receiver="ACC-0203",
            amount=910000,
            timestamp="09:16:22",
            channel="UPI",
            reference_number="UPI20260322003",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
        Transaction(
            transaction_id="TXN-2847-004",
            sender="ACC-0112",
            receiver="ACC-0089",
            amount=780000,
            timestamp="10:02:11",
            channel="NEFT",
            reference_number="NEFT20260322004",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
        Transaction(
            transaction_id="TXN-2847-005",
            sender="ACC-0203",
            receiver="ACC-0089",
            amount=910000,
            timestamp="10:02:11",
            channel="IMPS",
            reference_number="IMPS20260322005",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
        Transaction(
            transaction_id="TXN-2847-006",
            sender="ACC-0089",
            receiver="ACC-0317",
            amount=840000,
            timestamp="11:44:55",
            channel="NEFT",
            reference_number="NEFT20260322006",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
        Transaction(
            transaction_id="TXN-2847-007",
            sender="ACC-0089",
            receiver="ACC-0455",
            amount=890000,
            timestamp="11:44:55",
            channel="UPI",
            reference_number="UPI20260322007",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
        Transaction(
            transaction_id="TXN-2847-008",
            sender="ACC-0317",
            receiver="ACC-0043",
            amount=840000,
            timestamp="15:28:07",
            channel="UPI",
            reference_number="UPI20260322008",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
        Transaction(
            transaction_id="TXN-2847-009",
            sender="ACC-0455",
            receiver="ACC-0043",
            amount=890000,
            timestamp="15:28:07",
            channel="IMPS",
            reference_number="IMPS20260322009",
            is_fraud=True,
            typology="round_trip_layering",
            case_id="CASE-2847",
        ),
    ]

    return accounts, txns


def build_case_2848() -> tuple[list[Account], list[Transaction]]:
    """
    CASE-2848 — Smurfing / Structuring
    14 source accounts each send sub-₹2L transfers to a single destination.
    Aggregate: ₹23.1L. Channel: UPI + IMPS. Duration: 3 days.
    """
    destination = Account(
        account_id="ACC-0601",
        account_type="current",
        status="flagged",
        kyc_tier=1,
        created_date="2022-06-10",
        last_active_date="2026-03-22",
        declared_income=0,
        home_branch="CB-Branch Bandra West",
        is_dormant=False,
        is_pep_adjacent=False,
        owner_name="Skyline Imports Pvt Ltd",
        owner_type="entity",
        risk_level="critical",
        notes="Smurfing destination. Received 14 sub-threshold UPI/IMPS transfers over 3 days.",
    )

    mule_accounts = []
    for i in range(14):
        acc_id = f"ACC-{700 + i:04d}"
        mule_accounts.append(Account(
            account_id=acc_id,
            account_type="savings",
            status="flagged",
            kyc_tier=2,
            created_date=f"202{2 + (i % 2)}-0{1 + (i % 9)}-{10 + i}",
            last_active_date="2026-03-22",
            declared_income=240000 + i * 10000,
            home_branch=f"SB-Branch Mumbai Zone {i + 1}",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name=f"Mule Account Holder {i + 1:02d}",
            owner_type="individual",
            risk_level="medium",
            notes=f"Smurfing mule #{i + 1}. Sent one sub-threshold transfer.",
        ))

    accounts = [destination] + mule_accounts

    # 14 transfers — each between ₹1.5L and ₹1.9L (below ₹2L CTR threshold)
    amounts = [
        1650000, 1720000, 1580000, 1890000, 1640000, 1750000, 1600000,
        1810000, 1570000, 1680000, 1700000, 1590000, 1760000, 1920000,
    ]
    channels = ["UPI", "IMPS", "UPI", "UPI", "IMPS", "UPI", "IMPS",
                "UPI", "IMPS", "UPI", "UPI", "IMPS", "UPI", "IMPS"]
    timestamps = [
        "09:12:05", "10:34:22", "14:05:44", "16:22:11", "18:01:33",
        "09:45:00", "11:18:29", "13:55:10", "15:40:02", "17:22:45",
        "08:55:17", "12:30:08", "14:44:59", "16:10:33",
    ]
    dates = ["2026-03-20", "2026-03-20", "2026-03-20", "2026-03-20", "2026-03-20",
             "2026-03-21", "2026-03-21", "2026-03-21", "2026-03-21", "2026-03-21",
             "2026-03-22", "2026-03-22", "2026-03-22", "2026-03-22"]

    txns = []
    for i, (acc, amount, ch, ts, dt) in enumerate(
        zip(mule_accounts, amounts, channels, timestamps, dates)
    ):
        txns.append(Transaction(
            transaction_id=f"TXN-2848-{i + 1:03d}",
            sender=acc.account_id,
            receiver="ACC-0601",
            amount=amount,
            timestamp=ts,
            channel=ch,
            reference_number=f"{ch}{dt.replace('-', '')}{i + 1:03d}",
            is_fraud=True,
            typology="structuring",
            case_id="CASE-2848",
            demo_date=dt,
        ))

    return accounts, txns


def build_case_2849() -> tuple[list[Account], list[Transaction]]:
    """
    CASE-2849 — Shell Company Flow
    5 accounts. ₹156.4L moved through 3 shell entities.
    Cross-border SWIFT component. Duration: 2 hours.
    """
    accounts = [
        Account(
            account_id="ACC-0901",
            account_type="current",
            status="flagged",
            kyc_tier=1,
            created_date="2020-04-05",
            last_active_date="2026-03-22",
            declared_income=0,
            home_branch="CB-Branch Fort Mumbai",
            is_dormant=False,
            is_pep_adjacent=True,
            owner_name="Arcturus Holdings Pvt Ltd",
            owner_type="entity",
            risk_level="critical",
            notes="Origin shell entity. Registered in Gujarat with Mumbai branch. PEP adjacent — director linked to Tier-1 political donor.",
        ),
        Account(
            account_id="ACC-0902",
            account_type="current",
            status="flagged",
            kyc_tier=1,
            created_date="2021-01-15",
            last_active_date="2026-03-22",
            declared_income=0,
            home_branch="CB-Branch Nariman Point",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Meridian Exports LLP",
            owner_type="entity",
            risk_level="critical",
            notes="Transit shell. Received ₹156.4L, forwarded within 45 mins. No legitimate trade activity on record.",
        ),
        Account(
            account_id="ACC-0903",
            account_type="current",
            status="flagged",
            kyc_tier=1,
            created_date="2021-08-22",
            last_active_date="2026-03-22",
            declared_income=0,
            home_branch="CB-Branch Colaba",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Zenith Capital Advisory Pvt Ltd",
            owner_type="entity",
            risk_level="critical",
            notes="Second transit shell. Same registered address as ACC-0902 owner.",
        ),
        Account(
            account_id="ACC-0904",
            account_type="current",
            status="flagged",
            kyc_tier=1,
            created_date="2023-03-10",
            last_active_date="2026-03-22",
            declared_income=0,
            home_branch="CB-Branch Churchgate",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Vega Consultants Pvt Ltd",
            owner_type="entity",
            risk_level="high",
            notes="Penultimate account before SWIFT outward transfer.",
        ),
        Account(
            account_id="ACC-0905",
            account_type="current",
            status="flagged",
            kyc_tier=3,
            created_date="2023-11-01",
            last_active_date="2026-03-22",
            declared_income=0,
            home_branch="CB-Branch SWIFT Desk",
            is_dormant=False,
            is_pep_adjacent=False,
            owner_name="Cross-Border Beneficiary (Dubai)",
            owner_type="entity",
            risk_level="critical",
            notes="SWIFT outward beneficiary. UAE-registered entity. No correspondent bank relationship established before transfer.",
        ),
    ]

    txns = [
        Transaction(
            transaction_id="TXN-2849-001",
            sender="ACC-0901",
            receiver="ACC-0902",
            amount=15640000,
            timestamp="08:10:00",
            channel="RTGS",
            reference_number="RTGS20260322001",
            is_fraud=True,
            typology="shell_company_flow",
            case_id="CASE-2849",
        ),
        Transaction(
            transaction_id="TXN-2849-002",
            sender="ACC-0902",
            receiver="ACC-0903",
            amount=15620000,
            timestamp="08:41:15",
            channel="RTGS",
            reference_number="RTGS20260322002",
            is_fraud=True,
            typology="shell_company_flow",
            case_id="CASE-2849",
        ),
        Transaction(
            transaction_id="TXN-2849-003",
            sender="ACC-0903",
            receiver="ACC-0904",
            amount=15600000,
            timestamp="09:05:44",
            channel="NEFT",
            reference_number="NEFT20260322010",
            is_fraud=True,
            typology="shell_company_flow",
            case_id="CASE-2849",
        ),
        Transaction(
            transaction_id="TXN-2849-004",
            sender="ACC-0904",
            receiver="ACC-0905",
            amount=15580000,
            timestamp="09:58:30",
            channel="SWIFT",
            reference_number="SWIFT20260322001",
            is_fraud=True,
            typology="shell_company_flow",
            case_id="CASE-2849",
        ),
        Transaction(
            transaction_id="TXN-2849-005",
            sender="ACC-0901",
            receiver="ACC-0903",
            amount=800000,
            timestamp="08:15:00",
            channel="IMPS",
            reference_number="IMPS20260322020",
            is_fraud=True,
            typology="shell_company_flow",
            case_id="CASE-2849",
        ),
    ]

    return accounts, txns


# ════════════════════════════════════════════════════════════════
# CASE METADATA (for alert dashboard)
# ════════════════════════════════════════════════════════════════

CASE_META = {
    "CASE-2847": {
        "case_id":             "CASE-2847",
        "typology":            "Round-trip Layering",
        "typology_code":       "round_trip_layering",
        "fatf_reference":      "FATF Typology 12",
        "pmla_section":        "Section 16",
        "risk_score":          0.94,
        "confidence":          "94%",
        "risk_level":          "critical",
        "total_amount":        4723000,
        "accounts_count":      7,
        "hops":                3,
        "duration_minutes":    374,
        "duration_display":    "6h 14m",
        "channel":             "NEFT + UPI",
        "status":              "active",
        "created_at":          "2026-03-22T09:14:03",
        "gnn_score":           0.94,
        "investigator_id":     None,
        "notes":               "",
    },
    "CASE-2848": {
        "case_id":             "CASE-2848",
        "typology":            "Smurfing Pattern",
        "typology_code":       "structuring",
        "fatf_reference":      "FATF Typology 4",
        "pmla_section":        "Section 12",
        "risk_score":          0.87,
        "confidence":          "87%",
        "risk_level":          "critical",
        "total_amount":        2310000,
        "accounts_count":      14,
        "hops":                1,
        "duration_minutes":    4320,
        "duration_display":    "3 days",
        "channel":             "UPI + IMPS",
        "status":              "active",
        "created_at":          "2026-03-22T08:00:00",
        "gnn_score":           0.87,
        "investigator_id":     None,
        "notes":               "",
    },
    "CASE-2849": {
        "case_id":             "CASE-2849",
        "typology":            "Shell Company Flow",
        "typology_code":       "shell_company_flow",
        "fatf_reference":      "FATF Typology 20",
        "pmla_section":        "Section 12",
        "risk_score":          0.91,
        "confidence":          "91%",
        "risk_level":          "critical",
        "total_amount":        15640000,
        "accounts_count":      5,
        "hops":                4,
        "duration_minutes":    108,
        "duration_display":    "1h 48m",
        "channel":             "RTGS + SWIFT",
        "status":              "active",
        "created_at":          "2026-03-22T08:10:00",
        "gnn_score":           0.91,
        "investigator_id":     None,
        "notes":               "",
    },
}


# ════════════════════════════════════════════════════════════════
# NETWORKX GRAPH ANALYSIS
# ════════════════════════════════════════════════════════════════

def run_networkx_analysis(accounts: list[Account], txns: list[Transaction]) -> dict:
    """
    Build a NetworkX graph and run fraud detection algorithms.
    Returns analysis results that the backend API serves.
    """
    try:
        import networkx as nx
    except ImportError:
        warn("NetworkX not installed — skipping graph analysis. Install: pip install networkx")
        return {}

    G = nx.DiGraph()

    # Add nodes
    for acc in accounts:
        if acc.account_id != "EXTERNAL":
            G.add_node(acc.account_id,
                account_type=acc.account_type,
                is_dormant=acc.is_dormant,
                risk_level=acc.risk_level,
                owner=acc.owner_name,
            )

    # Add edges
    for txn in txns:
        if txn.sender == "EXTERNAL":
            G.add_node("EXTERNAL", account_type="external", is_dormant=False, risk_level="unknown", owner="Unknown")
        G.add_edge(txn.sender, txn.receiver,
            amount=txn.amount,
            timestamp=txn.timestamp,
            channel=txn.channel,
            transaction_id=txn.transaction_id,
            case_id=txn.case_id,
        )

    # ── Betweenness centrality — identify hubs ──────────────────
    if G.number_of_nodes() > 1:
        centrality = nx.betweenness_centrality(G, weight=None)
    else:
        centrality = {}

    # ── Cycle detection — circular transactions ─────────────────
    try:
        cycles = list(nx.simple_cycles(G))
    except Exception:
        cycles = []

    # ── Flag suspicious nodes ───────────────────────────────────
    suspicious = []
    for node, score in centrality.items():
        if score > 0.1:
            suspicious.append({
                "account_id":        node,
                "centrality_score":  round(score, 4),
                "flag":              "HIGH_CENTRALITY_HUB",
                "interpretation":    "This account acts as a central relay in the fund flow network.",
            })

    results = {
        "node_count":           G.number_of_nodes(),
        "edge_count":           G.number_of_edges(),
        "centrality_scores":    {k: round(v, 4) for k, v in centrality.items()},
        "suspicious_nodes":     suspicious,
        "circular_patterns":    [
            {"accounts": c, "length": len(c), "flag": "CIRCULAR_TRANSACTION"}
            for c in cycles if len(c) >= 2
        ],
        "density":              round(nx.density(G), 4),
        "is_weakly_connected":  nx.is_weakly_connected(G) if G.number_of_nodes() > 0 else False,
    }

    return results


# ════════════════════════════════════════════════════════════════
# STORAGE BACKENDS
# ════════════════════════════════════════════════════════════════

# ── 1. LOCAL — SQLite + JSON ─────────────────────────────────────

def seed_local(
    all_accounts: list[Account],
    all_txns: list[Transaction],
    nx_results: dict,
) -> None:
    """Write all seed data to SQLite + JSON files. No infrastructure needed."""
    from backend.paths import demo_db_path, project_root

    DB_PATH = demo_db_path()
    DATA_DIR = project_root() / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── SQLite ───────────────────────────────────────────────────
    con = sqlite3.connect(DB_PATH)

    con.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id       TEXT PRIMARY KEY,
            account_type     TEXT,
            status           TEXT,
            kyc_tier         INTEGER,
            created_date     TEXT,
            last_active_date TEXT,
            declared_income  REAL,
            home_branch      TEXT,
            is_dormant       INTEGER,
            is_pep_adjacent  INTEGER,
            owner_name       TEXT,
            owner_type       TEXT,
            risk_level       TEXT,
            notes            TEXT
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id   TEXT PRIMARY KEY,
            sender           TEXT,
            receiver         TEXT,
            amount           REAL,
            currency         TEXT,
            timestamp        TEXT,
            channel          TEXT,
            branch_code      TEXT,
            reference_number TEXT,
            is_fraud         INTEGER,
            typology         TEXT,
            case_id          TEXT,
            demo_date        TEXT
        );

        CREATE TABLE IF NOT EXISTS cases (
            case_id          TEXT PRIMARY KEY,
            typology         TEXT,
            typology_code    TEXT,
            fatf_reference   TEXT,
            pmla_section     TEXT,
            risk_score       REAL,
            confidence       TEXT,
            risk_level       TEXT,
            total_amount     REAL,
            accounts_count   INTEGER,
            hops             INTEGER,
            duration_minutes INTEGER,
            duration_display TEXT,
            channel          TEXT,
            status           TEXT,
            created_at       TEXT,
            gnn_score        REAL,
            investigator_id  TEXT,
            notes            TEXT
        );
    """)

    # Clear existing demo data
    con.execute("DELETE FROM accounts")
    con.execute("DELETE FROM transactions")
    con.execute("DELETE FROM cases")

    # Insert accounts
    for acc in all_accounts:
        con.execute("""
            INSERT OR REPLACE INTO accounts VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            acc.account_id, acc.account_type, acc.status, acc.kyc_tier,
            acc.created_date, acc.last_active_date, acc.declared_income,
            acc.home_branch, int(acc.is_dormant), int(acc.is_pep_adjacent),
            acc.owner_name, acc.owner_type, acc.risk_level, acc.notes,
        ))

    # Insert transactions
    for txn in all_txns:
        con.execute("""
            INSERT OR REPLACE INTO transactions VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            txn.transaction_id, txn.sender, txn.receiver, txn.amount,
            txn.currency, txn.full_timestamp(), txn.channel, txn.branch_code,
            txn.reference_number, int(txn.is_fraud), txn.typology,
            txn.case_id, txn.demo_date,
        ))

    # Insert case metadata
    for case_id, meta in CASE_META.items():
        con.execute("""
            INSERT OR REPLACE INTO cases VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            meta["case_id"], meta["typology"], meta["typology_code"],
            meta["fatf_reference"], meta["pmla_section"], meta["risk_score"],
            meta["confidence"], meta["risk_level"], meta["total_amount"],
            meta["accounts_count"], meta["hops"], meta["duration_minutes"],
            meta["duration_display"], meta["channel"], meta["status"],
            meta["created_at"], meta["gnn_score"],
            meta["investigator_id"], meta["notes"],
        ))

    con.commit()
    con.close()
    ok(f"SQLite DB: {DB_PATH} ({len(all_accounts)} accounts, {len(all_txns)} transactions)")

    # ── JSON exports (for API fallback + frontend) ───────────────
    json_data = {
        "accounts":   [asdict(a) for a in all_accounts],
        "transactions": [
            {**asdict(t), "full_timestamp": t.full_timestamp()}
            for t in all_txns
        ],
        "cases":      CASE_META,
        "networkx_analysis": nx_results,
        "generated_at": datetime.now().isoformat(),
        "seed_version": "1.0.0",
    }

    json_path = DATA_DIR / "demo_seed.json"
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2, default=str)
    ok(f"JSON export: {json_path} ({json_path.stat().st_size // 1024} KB)")

    # Case-specific JSON for the graph API
    for case_id, meta in CASE_META.items():
        case_txns = [
            {**asdict(t), "full_timestamp": t.full_timestamp()}
            for t in all_txns if t.case_id == case_id
        ]
        case_accs = list({t.sender for t in all_txns if t.case_id == case_id} |
                         {t.receiver for t in all_txns if t.case_id == case_id})
        case_accs = [asdict(a) for a in all_accounts if a.account_id in case_accs]

        case_path = DATA_DIR / f"{case_id.lower()}.json"
        with open(case_path, "w") as f:
            json.dump({
                "case": meta,
                "accounts":     case_accs,
                "transactions": case_txns,
            }, f, indent=2, default=str)
        ok(f"  Case file: {case_path}")


# ── 2. NEO4J ─────────────────────────────────────────────────────

def seed_neo4j(all_accounts: list[Account], all_txns: list[Transaction]) -> bool:
    """Write all data to Neo4j using the official Python driver."""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        fail("neo4j driver not installed. Run: pip install neo4j")
        return False

    uri  = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER",     "neo4j")
    pwd  = os.getenv("NEO4J_PASSWORD", "fundlens123")

    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        driver.verify_connectivity()
    except Exception as e:
        fail(f"Cannot connect to Neo4j at {uri}: {e}")
        return False

    with driver.session() as session:
        # Clear existing demo nodes
        session.run("MATCH (n) WHERE n.is_demo = true DETACH DELETE n")

        # Create indexes
        for label, prop in [("Account", "account_id"), ("Entity", "entity_id"),
                             ("Case", "case_id")]:
            session.run(
                f"CREATE INDEX {label.lower()}_{prop}_idx IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.{prop})"
            )

        # Create accounts
        for acc in all_accounts:
            session.run("""
                MERGE (a:Account {account_id: $account_id})
                SET a += $props, a.is_demo = true
            """, account_id=acc.account_id, props={
                "account_type":     acc.account_type,
                "status":           acc.status,
                "kyc_tier":         acc.kyc_tier,
                "created_date":     acc.created_date,
                "last_active_date": acc.last_active_date,
                "declared_income":  acc.declared_income,
                "home_branch":      acc.home_branch,
                "is_dormant":       acc.is_dormant,
                "is_pep_adjacent":  acc.is_pep_adjacent,
                "owner_name":       acc.owner_name,
                "owner_type":       acc.owner_type,
                "risk_level":       acc.risk_level,
                "notes":            acc.notes,
            })

        # Create EXTERNAL node
        session.run("""
            MERGE (e:Account {account_id: 'EXTERNAL'})
            SET e.account_type = 'external', e.is_demo = true
        """)

        # Create transactions as edges
        for txn in all_txns:
            session.run("""
                MATCH (s:Account {account_id: $sender})
                MATCH (r:Account {account_id: $receiver})
                MERGE (s)-[t:TRANSFERRED_TO {transaction_id: $txn_id}]->(r)
                SET t += $props, t.is_demo = true
            """, sender=txn.sender, receiver=txn.receiver,
                 txn_id=txn.transaction_id, props={
                "amount":           txn.amount,
                "currency":         txn.currency,
                "timestamp":        txn.full_timestamp(),
                "channel":          txn.channel,
                "branch_code":      txn.branch_code,
                "reference_number": txn.reference_number,
                "is_fraud":         txn.is_fraud,
                "typology":         txn.typology,
                "case_id":          txn.case_id,
            })

        # Create case nodes
        for case_id, meta in CASE_META.items():
            session.run("""
                MERGE (c:Case {case_id: $case_id})
                SET c += $props, c.is_demo = true
            """, case_id=case_id, props={k: v for k, v in meta.items() if k != "case_id"})

    driver.close()
    ok(f"Neo4j: {len(all_accounts)} account nodes + {len(all_txns)} TRANSFERRED_TO edges")
    return True


# ── 3. POSTGRESQL ────────────────────────────────────────────────

def seed_postgres(all_accounts: list[Account], all_txns: list[Transaction]) -> bool:
    """Write all data to PostgreSQL."""
    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError:
        fail("psycopg2 not installed. Run: pip install psycopg2-binary")
        return False

    db_url = os.getenv("POSTGRES_URL", "postgresql://postgres:fundlens123@localhost:5432/fundlens")

    try:
        con = psycopg2.connect(db_url)
        cur = con.cursor()
    except Exception as e:
        fail(f"Cannot connect to PostgreSQL: {e}")
        return False

    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id       TEXT PRIMARY KEY,
            account_type     TEXT,
            status           TEXT,
            kyc_tier         INTEGER,
            created_date     DATE,
            last_active_date DATE,
            declared_income  NUMERIC,
            home_branch      TEXT,
            is_dormant       BOOLEAN,
            is_pep_adjacent  BOOLEAN,
            owner_name       TEXT,
            owner_type       TEXT,
            risk_level       TEXT,
            notes            TEXT
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id   TEXT PRIMARY KEY,
            sender           TEXT,
            receiver         TEXT,
            amount           NUMERIC,
            currency         TEXT DEFAULT 'INR',
            timestamp        TIMESTAMPTZ,
            channel          TEXT,
            branch_code      TEXT,
            reference_number TEXT,
            is_fraud         BOOLEAN,
            typology         TEXT,
            case_id          TEXT,
            demo_date        DATE
        );

        CREATE TABLE IF NOT EXISTS cases (
            case_id          TEXT PRIMARY KEY,
            typology         TEXT,
            typology_code    TEXT,
            fatf_reference   TEXT,
            pmla_section     TEXT,
            risk_score       NUMERIC,
            confidence       TEXT,
            risk_level       TEXT,
            total_amount     NUMERIC,
            accounts_count   INTEGER,
            hops             INTEGER,
            duration_minutes INTEGER,
            duration_display TEXT,
            channel          TEXT,
            status           TEXT,
            created_at       TIMESTAMPTZ,
            gnn_score        NUMERIC,
            investigator_id  TEXT,
            notes            TEXT
        );
    """)

    # Upsert accounts
    execute_values(cur, """
        INSERT INTO accounts VALUES %s
        ON CONFLICT (account_id) DO UPDATE SET
            status = EXCLUDED.status,
            last_active_date = EXCLUDED.last_active_date,
            risk_level = EXCLUDED.risk_level,
            notes = EXCLUDED.notes
    """, [(
        a.account_id, a.account_type, a.status, a.kyc_tier,
        a.created_date, a.last_active_date, a.declared_income,
        a.home_branch, a.is_dormant, a.is_pep_adjacent,
        a.owner_name, a.owner_type, a.risk_level, a.notes,
    ) for a in all_accounts])

    # Upsert transactions
    execute_values(cur, """
        INSERT INTO transactions VALUES %s
        ON CONFLICT (transaction_id) DO NOTHING
    """, [(
        t.transaction_id, t.sender, t.receiver, t.amount,
        t.currency, t.full_timestamp(), t.channel, t.branch_code,
        t.reference_number, t.is_fraud, t.typology,
        t.case_id, t.demo_date,
    ) for t in all_txns])

    # Upsert case metadata
    execute_values(cur, """
        INSERT INTO cases VALUES %s
        ON CONFLICT (case_id) DO UPDATE SET
            status = EXCLUDED.status,
            gnn_score = EXCLUDED.gnn_score,
            investigator_id = EXCLUDED.investigator_id
    """, [(
        m["case_id"], m["typology"], m["typology_code"], m["fatf_reference"],
        m["pmla_section"], m["risk_score"], m["confidence"], m["risk_level"],
        m["total_amount"], m["accounts_count"], m["hops"], m["duration_minutes"],
        m["duration_display"], m["channel"], m["status"], m["created_at"],
        m["gnn_score"], m["investigator_id"], m["notes"],
    ) for m in CASE_META.values()])

    con.commit()
    cur.close()
    con.close()
    ok(f"PostgreSQL: {len(all_accounts)} accounts, {len(all_txns)} transactions, {len(CASE_META)} cases")
    return True


# ════════════════════════════════════════════════════════════════
# CONNECTIVITY CHECK
# ════════════════════════════════════════════════════════════════

def check_neo4j() -> bool:
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"),
                  os.getenv("NEO4J_PASSWORD", "fundlens123")),
        )
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


def check_postgres() -> bool:
    try:
        import psycopg2
        con = psycopg2.connect(
            os.getenv("POSTGRES_URL",
                      "postgresql://postgres:fundlens123@localhost:5432/fundlens"),
            connect_timeout=3,
        )
        con.close()
        return True
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════
# PRINT SUMMARY
# ════════════════════════════════════════════════════════════════

def print_summary(all_accounts, all_txns, nx_results):
    print()
    print(bold("═" * 60))
    print(bold(cyan("  FundLens Demo Seed — Summary")))
    print(bold("═" * 60))

    for case_id, meta in CASE_META.items():
        case_txns = [t for t in all_txns if t.case_id == case_id]
        case_total = sum(t.amount for t in case_txns if t.sender != "EXTERNAL")
        print()
        print(f"  {bold(case_id)}  {meta['typology']}")
        print(f"    Risk score    : {yellow(meta['confidence'])} ({meta['risk_level'].upper()})")
        print(f"    Total amount  : ₹{meta['total_amount']:,.0f}")
        print(f"    Accounts      : {meta['accounts_count']}")
        print(f"    Hops          : {meta['hops']}")
        print(f"    Duration      : {meta['duration_display']}")
        print(f"    Channel       : {meta['channel']}")
        print(f"    Transactions  : {len(case_txns)}")
        print(f"    FATF Ref      : {meta['fatf_reference']}")

    if nx_results:
        print()
        print(f"  {bold('NetworkX Analysis — CASE-2847')}")
        nx = nx_results
        print(f"    Nodes         : {nx.get('node_count', '-')}")
        print(f"    Edges         : {nx.get('edge_count', '-')}")
        print(f"    Density       : {nx.get('density', '-')}")
        print(f"    Circular patterns: {len(nx.get('circular_patterns', []))}")
        for sp in nx.get("suspicious_nodes", []):
            print(f"    {red('⚠')} {sp['account_id']} — centrality {sp['centrality_score']} — {sp['flag']}")

    print()
    print(bold("═" * 60))
    print()
    print(f"  {bold('Total accounts seeded  :')} {len(all_accounts)}")
    print(f"  {bold('Total transactions     :')} {len(all_txns)}")
    print(f"  {bold('Cases created         :')} {len(CASE_META)}")
    print()
    print(f"  {green('Start the API server:')}")
    print(f"    uvicorn backend.api.main:app --reload --port 8000")
    print()
    print(f"  {green('Start the frontend:')}")
    print(f"    cd frontend && npm run dev")
    print()
    print(f"  {green('Test the API:')}")
    print(f"    curl http://localhost:8000/api/health")
    print(f"    curl http://localhost:8000/api/alerts")
    print()
    print(bold("═" * 60))


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def ensure_local_demo_data() -> bool:
    """
    Seed SQLite demo cases if fundlens_demo.db is missing.
    Used on cloud cold start (FUNDLENS_AUTO_SEED=1).
    Returns True if seeding ran.
    """
    from backend.paths import demo_db_path

    if demo_db_path().exists():
        return False

    accs_2847, txns_2847 = build_case_2847()
    accs_2848, txns_2848 = build_case_2848()
    accs_2849, txns_2849 = build_case_2849()
    acc_map: dict[str, Account] = {}
    for acc in accs_2847 + accs_2848 + accs_2849:
        acc_map[acc.account_id] = acc
    all_accounts = list(acc_map.values())
    all_txns = txns_2847 + txns_2848 + txns_2849
    nx_results = run_networkx_analysis(accs_2847, txns_2847) or {}
    seed_local(all_accounts, all_txns, nx_results)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="FundLens — Demo data seeder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  auto   Auto-detect available infrastructure (default)
  local  SQLite + JSON only — works on any laptop, no Docker needed
  neo4j  Neo4j only
  full   Neo4j + PostgreSQL

Examples:
  python demo_seed.py
  python demo_seed.py --mode local
  python demo_seed.py --mode full
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "local", "neo4j", "full"],
        default="auto",
        help="Storage backend (default: auto)",
    )
    args = parser.parse_args()

    print()
    print(bold(cyan("  FundLens — Demo Data Seeder")))
    print(f"  Mode: {args.mode}")
    print()

    # ── Build all data ──────────────────────────────────────────
    section("Building case data")

    accs_2847, txns_2847 = build_case_2847()
    ok(f"CASE-2847: {len(accs_2847)} accounts, {len(txns_2847)} transactions")

    accs_2848, txns_2848 = build_case_2848()
    ok(f"CASE-2848: {len(accs_2848)} accounts, {len(txns_2848)} transactions")

    accs_2849, txns_2849 = build_case_2849()
    ok(f"CASE-2849: {len(accs_2849)} accounts, {len(txns_2849)} transactions")

    # Deduplicate accounts (some may appear in multiple cases)
    acc_map: dict[str, Account] = {}
    for acc in accs_2847 + accs_2848 + accs_2849:
        acc_map[acc.account_id] = acc
    all_accounts = list(acc_map.values())
    all_txns = txns_2847 + txns_2848 + txns_2849

    ok(f"Total unique accounts: {len(all_accounts)}")
    ok(f"Total transactions   : {len(all_txns)}")

    # ── NetworkX analysis ───────────────────────────────────────
    section("Running NetworkX graph analysis (CASE-2847)")
    nx_results = run_networkx_analysis(accs_2847, txns_2847)
    if nx_results:
        ok(f"Graph: {nx_results['node_count']} nodes, {nx_results['edge_count']} edges")
        ok(f"Circular patterns detected: {len(nx_results.get('circular_patterns', []))}")
        for sp in nx_results.get("suspicious_nodes", []):
            log(f"  {red('→')} Hub detected: {sp['account_id']} (centrality {sp['centrality_score']})")

    # ── Determine mode ──────────────────────────────────────────
    mode = args.mode
    if mode == "auto":
        has_neo4j    = check_neo4j()
        has_postgres = check_postgres()
        if has_neo4j and has_postgres:
            mode = "full"
        elif has_neo4j:
            mode = "neo4j"
        else:
            mode = "local"
        log(f"Auto-detected mode: {bold(mode)}"
            f"  (Neo4j: {'✓' if has_neo4j else '✗'}, "
            f"PostgreSQL: {'✓' if has_postgres else '✗'})")

    # ── Write data ──────────────────────────────────────────────
    section(f"Writing data — mode: {mode}")

    # Always write local (serves as fallback + JSON cache)
    seed_local(all_accounts, all_txns, nx_results)

    if mode in ("neo4j", "full"):
        neo4j_ok = seed_neo4j(all_accounts, all_txns)
        if not neo4j_ok:
            warn("Neo4j seeding failed — falling back to local SQLite only")

    if mode == "full":
        pg_ok = seed_postgres(all_accounts, all_txns)
        if not pg_ok:
            warn("PostgreSQL seeding failed — falling back to local SQLite only")

    # ── Summary ─────────────────────────────────────────────────
    print_summary(all_accounts, all_txns, nx_results)


if __name__ == "__main__":
    main()
