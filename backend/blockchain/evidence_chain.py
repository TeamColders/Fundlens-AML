"""
FundLens — Blockchain Evidence Chain.

Append-only, cryptographically linked evidence ledger.
DEMO MODE: SQLite-backed local chain (works on any laptop).
PRODUCTION MODE: Hyperledger Fabric stubs (implement when Fabric network is live).

Usage:
    from backend.blockchain.evidence_chain import (
        init_db, write_block, get_chain, verify_chain,
        ALERT_CREATED, CASE_OPENED, SUBGRAPH_EXPORTED,
        LLM_NARRATIVE_GENERATED, SUPERVISOR_APPROVED, STR_SUBMITTED,
    )
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Mode detection ────────────────────────────────────────────────
_MODE = os.getenv("FUNDLENS_BLOCKCHAIN_MODE", "demo").lower()
DEMO_MODE       = _MODE == "demo"
PRODUCTION_MODE = _MODE == "production"

# ── DB path ───────────────────────────────────────────────────────
DB_PATH = Path(os.getenv("FUNDLENS_EVIDENCE_DB", "fundlens_evidence.db"))

# ── Event type constants ──────────────────────────────────────────
ALERT_CREATED           = "ALERT_CREATED"
CASE_OPENED             = "CASE_OPENED"
SUBGRAPH_EXPORTED       = "SUBGRAPH_EXPORTED"
LLM_NARRATIVE_GENERATED = "LLM_NARRATIVE_GENERATED"
SUPERVISOR_APPROVED     = "SUPERVISOR_APPROVED"
STR_SUBMITTED           = "STR_SUBMITTED"

ALL_EVENT_TYPES = (
    ALERT_CREATED, CASE_OPENED, SUBGRAPH_EXPORTED,
    LLM_NARRATIVE_GENERATED, SUPERVISOR_APPROVED, STR_SUBMITTED,
)

EVENT_LABELS = {
    ALERT_CREATED:           "Initial alert created",
    CASE_OPENED:             "Investigator opened case",
    SUBGRAPH_EXPORTED:       "Subgraph exported",
    LLM_NARRATIVE_GENERATED: "LLM narrative generated",
    SUPERVISOR_APPROVED:     "STR draft reviewed",
    STR_SUBMITTED:           "STR submitted to FIU-IND",
}


# ════════════════════════════════════════════════════════════════
# DATA CLASSES
# ════════════════════════════════════════════════════════════════

class BlockRecord:
    """A single immutable block in the evidence chain."""
    def __init__(self, block_id, block_hash, prev_hash, case_id,
                 event_type, payload_hash, timestamp, actor_id, metadata):
        self.block_id     = block_id
        self.block_hash   = block_hash
        self.prev_hash    = prev_hash
        self.case_id      = case_id
        self.event_type   = event_type
        self.payload_hash = payload_hash
        self.timestamp    = timestamp
        self.actor_id     = actor_id
        self.metadata     = metadata

    @property
    def event_label(self) -> str:
        return EVENT_LABELS.get(self.event_type, self.event_type)

    @property
    def short_hash(self) -> str:
        return f"0x{self.block_hash[:4]}...{self.block_hash[-4:]}"

    @property
    def short_prev(self) -> str:
        if self.prev_hash == "GENESIS":
            return "GENESIS"
        return f"0x{self.prev_hash[:4]}...{self.prev_hash[-4:]}"

    def to_dict(self) -> dict:
        return {
            "block_id":     self.block_id,
            "block_hash":   self.block_hash,
            "short_hash":   self.short_hash,
            "prev_hash":    self.prev_hash,
            "short_prev":   self.short_prev,
            "case_id":      self.case_id,
            "event_type":   self.event_type,
            "event_label":  self.event_label,
            "payload_hash": self.payload_hash,
            "timestamp":    self.timestamp,
            "actor_id":     self.actor_id,
            "metadata":     self.metadata,
            "verified":     True,
        }


class ChainVerification:
    """Result of verify_chain()."""
    def __init__(self, valid, block_count, blocks, broken_at_block=None):
        self.valid           = valid
        self.block_count     = block_count
        self.blocks          = blocks
        self.broken_at_block = broken_at_block
        self.verified_at     = datetime.now(timezone.utc).isoformat()
        self.network         = "UBI-Fabric-Private"
        self.mode            = "DEMO" if DEMO_MODE else "PRODUCTION"

    def to_dict(self) -> dict:
        blocks_list = []
        for b in self.blocks:
            d = b.to_dict()
            if not self.valid and b.block_id == self.broken_at_block:
                d["verified"] = False
            blocks_list.append(d)

        return {
            "valid":           self.valid,
            "block_count":     self.block_count,
            "blocks":          blocks_list,
            "broken_at_block": self.broken_at_block,
            "verified_at":     self.verified_at,
            "network":         self.network,
            "mode":            self.mode,
            "integrity_label": "VERIFIED" if self.valid else "COMPROMISED",
        }


# ════════════════════════════════════════════════════════════════
# CORE CRYPTO
# ════════════════════════════════════════════════════════════════

def compute_hash(payload: dict) -> str:
    """SHA-256 of a deterministically serialised dict."""
    serialised = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def _compute_block_hash(block_id, prev_hash, payload_hash, timestamp) -> str:
    content = f"{block_id}|{prev_hash}|{payload_hash}|{timestamp}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ════════════════════════════════════════════════════════════════
# DEMO MODE — SQLite
# ════════════════════════════════════════════════════════════════

def init_db(db_path: Path = DB_PATH) -> None:
    """Create the blocks table (idempotent)."""
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            block_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            block_hash    TEXT    NOT NULL,
            prev_hash     TEXT    NOT NULL,
            case_id       TEXT    NOT NULL,
            event_type    TEXT    NOT NULL,
            payload_hash  TEXT    NOT NULL,
            timestamp     TEXT    NOT NULL,
            actor_id      TEXT,
            metadata      TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_case_id ON blocks (case_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON blocks (event_type)")
    con.commit()
    con.close()
    logger.info(f"Evidence chain DB ready: {db_path} (mode={_MODE.upper()})")


def _get_prev_hash(case_id: str, db_path: Path = DB_PATH) -> str:
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT block_hash FROM blocks WHERE case_id = ? ORDER BY block_id DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    con.close()
    return row[0] if row else "GENESIS"


def _demo_write_block(case_id, event_type, payload, actor_id=None,
                       metadata=None, db_path=DB_PATH) -> BlockRecord:
    ts           = datetime.now(timezone.utc).isoformat()
    payload_hash = compute_hash(payload)
    prev_hash    = _get_prev_hash(case_id, db_path)
    meta_json    = json.dumps(metadata) if metadata else None

    con = sqlite3.connect(db_path)
    cur = con.execute(
        """INSERT INTO blocks
               (block_hash, prev_hash, case_id, event_type,
                payload_hash, timestamp, actor_id, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("PENDING", prev_hash, case_id, event_type,
         payload_hash, ts, actor_id, meta_json),
    )
    block_id = cur.lastrowid
    block_hash = _compute_block_hash(block_id, prev_hash, payload_hash, ts)
    con.execute("UPDATE blocks SET block_hash = ? WHERE block_id = ?",
                (block_hash, block_id))
    con.commit()
    con.close()

    logger.info(f"Block #{block_id} written | case={case_id} | event={event_type} | hash={block_hash[:12]}...")

    return BlockRecord(
        block_id=block_id, block_hash=block_hash, prev_hash=prev_hash,
        case_id=case_id, event_type=event_type, payload_hash=payload_hash,
        timestamp=ts, actor_id=actor_id, metadata=metadata,
    )


def _demo_get_chain(case_id: str, db_path: Path = DB_PATH) -> list[BlockRecord]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM blocks WHERE case_id = ? ORDER BY block_id ASC",
        (case_id,),
    ).fetchall()
    con.close()
    return [_row_to_block(r) for r in rows]


def _demo_verify_chain(case_id: str, db_path: Path = DB_PATH) -> ChainVerification:
    blocks = _demo_get_chain(case_id, db_path)
    if not blocks:
        return ChainVerification(valid=False, block_count=0, blocks=[], broken_at_block=None)

    broken_at = None
    for i, block in enumerate(blocks):
        expected = _compute_block_hash(
            block.block_id, block.prev_hash, block.payload_hash, block.timestamp)
        if expected != block.block_hash:
            broken_at = block.block_id
            break
        if i == 0:
            if block.prev_hash != "GENESIS":
                broken_at = block.block_id
                break
        else:
            if block.prev_hash != blocks[i - 1].block_hash:
                broken_at = block.block_id
                break

    return ChainVerification(
        valid=broken_at is None, block_count=len(blocks),
        blocks=blocks, broken_at_block=broken_at,
    )


def _row_to_block(row) -> BlockRecord:
    metadata = None
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except (json.JSONDecodeError, TypeError):
            pass
    return BlockRecord(
        block_id=row["block_id"], block_hash=row["block_hash"],
        prev_hash=row["prev_hash"], case_id=row["case_id"],
        event_type=row["event_type"], payload_hash=row["payload_hash"],
        timestamp=row["timestamp"], actor_id=row["actor_id"],
        metadata=metadata,
    )


# ════════════════════════════════════════════════════════════════
# PRODUCTION MODE — Hyperledger Fabric stubs
# ════════════════════════════════════════════════════════════════

def _fabric_write_block(case_id, event_type, payload, actor_id=None, metadata=None):
    raise NotImplementedError("Hyperledger Fabric not configured. Use FUNDLENS_BLOCKCHAIN_MODE=demo")

def _fabric_get_chain(case_id):
    raise NotImplementedError("Hyperledger Fabric not configured.")

def _fabric_verify_chain(case_id):
    raise NotImplementedError("Hyperledger Fabric not configured.")


# ════════════════════════════════════════════════════════════════
# PUBLIC API — mode-dispatched
# ════════════════════════════════════════════════════════════════

def write_block(case_id, event_type, payload, actor_id=None,
                metadata=None, db_path=DB_PATH) -> BlockRecord:
    """Append an immutable block to the evidence chain."""
    if event_type not in ALL_EVENT_TYPES:
        raise ValueError(f"Unknown event_type '{event_type}'. Must be one of: {', '.join(ALL_EVENT_TYPES)}")
    if PRODUCTION_MODE:
        return _fabric_write_block(case_id, event_type, payload, actor_id, metadata)
    return _demo_write_block(case_id, event_type, payload, actor_id, metadata, db_path)


def get_chain(case_id: str, db_path: Path = DB_PATH) -> list[BlockRecord]:
    """Return all blocks for case_id in chronological order."""
    if PRODUCTION_MODE:
        return _fabric_get_chain(case_id)
    return _demo_get_chain(case_id, db_path)


def verify_chain(case_id: str, db_path: Path = DB_PATH) -> ChainVerification:
    """Cryptographically verify the entire chain for case_id."""
    if PRODUCTION_MODE:
        return _fabric_verify_chain(case_id)
    return _demo_verify_chain(case_id, db_path)


def get_all_cases(db_path: Path = DB_PATH) -> list[str]:
    """Return all case_ids with at least one block."""
    if PRODUCTION_MODE:
        return []
    con = sqlite3.connect(db_path)
    rows = con.execute("SELECT DISTINCT case_id FROM blocks ORDER BY case_id").fetchall()
    con.close()
    return [r[0] for r in rows]


def seal_case(case_id, gnn_score, typology, total_amount, accounts_count,
              actor_id="system", db_path=DB_PATH) -> BlockRecord:
    """Write Block 1 (ALERT_CREATED) for a new case."""
    return write_block(
        case_id=case_id, event_type=ALERT_CREATED,
        payload={"case_id": case_id, "gnn_score": gnn_score, "typology": typology,
                 "total_amount": total_amount, "accounts_count": accounts_count},
        actor_id=actor_id, metadata={"source": "FundLens GNN Pipeline"}, db_path=db_path,
    )
