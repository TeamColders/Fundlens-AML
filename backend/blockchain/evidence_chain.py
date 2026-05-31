"""
backend/blockchain/evidence_chain.py
=====================================
FundLens — Blockchain Evidence Chain

Implements an append-only, cryptographically linked evidence chain
that behaves identically to Hyperledger Fabric from the frontend's
perspective.

TWO MODES
─────────
DEMO       SQLite-backed local ledger. Works on any laptop.
           No infrastructure. Fully cryptographic (SHA-256).
           This is what you run for the hackathon demo.

PRODUCTION Hyperledger Fabric via fabric-sdk-py.
           Stubbed here — replace the _fabric_* helpers with
           real chaincode calls when you have a Fabric network.

AUTO-DETECTION
──────────────
Set the environment variable:
    FUNDLENS_BLOCKCHAIN_MODE=demo        # force demo mode
    FUNDLENS_BLOCKCHAIN_MODE=production  # force production mode
If not set, DEMO mode is used (safe default).

USAGE
─────
    from backend.blockchain.evidence_chain import (
        init_db, write_block, get_chain, verify_chain,
        ALERT_CREATED, CASE_OPENED, SUBGRAPH_EXPORTED,
        LLM_NARRATIVE_GENERATED, SUPERVISOR_APPROVED, STR_SUBMITTED,
    )

    init_db()   # call once at app startup

    block = write_block(
        case_id="CASE-2847",
        event_type=ALERT_CREATED,
        payload={"gnn_score": 0.94, "typology": "Round-trip Layering"},
        actor_id="system",
    )
    print(block.block_id, block.block_hash)

    chain = get_chain("CASE-2847")
    result = verify_chain("CASE-2847")
    print(result.valid, result.block_count)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Mode detection ────────────────────────────────────────────────
_MODE = os.getenv("FUNDLENS_BLOCKCHAIN_MODE", "demo").lower()
DEMO_MODE       = _MODE == "demo"
PRODUCTION_MODE = _MODE == "production"

# ── DB path (overridable via env) ─────────────────────────────────
DB_PATH = Path(os.getenv("FUNDLENS_EVIDENCE_DB", "fundlens_evidence.db"))

# ── Event type constants ──────────────────────────────────────────
ALERT_CREATED           = "ALERT_CREATED"
CASE_OPENED             = "CASE_OPENED"
SUBGRAPH_EXPORTED       = "SUBGRAPH_EXPORTED"
LLM_NARRATIVE_GENERATED = "LLM_NARRATIVE_GENERATED"
SUPERVISOR_APPROVED     = "SUPERVISOR_APPROVED"
STR_SUBMITTED           = "STR_SUBMITTED"
INVESTIGATOR_ACTION     = "INVESTIGATOR_ACTION"

ALL_EVENT_TYPES = (
    ALERT_CREATED,
    CASE_OPENED,
    SUBGRAPH_EXPORTED,
    LLM_NARRATIVE_GENERATED,
    SUPERVISOR_APPROVED,
    STR_SUBMITTED,
    INVESTIGATOR_ACTION,
)

# Human-readable labels for the frontend audit trail
EVENT_LABELS = {
    ALERT_CREATED:           "Initial alert created",
    CASE_OPENED:             "Investigator opened case",
    SUBGRAPH_EXPORTED:       "Subgraph exported",
    LLM_NARRATIVE_GENERATED: "LLM narrative generated",
    SUPERVISOR_APPROVED:     "STR draft reviewed",
    STR_SUBMITTED:           "STR submitted to FIU-IND",
    INVESTIGATOR_ACTION:     "Investigator action recorded",
}


# ════════════════════════════════════════════════════════════════
# DATA CLASSES
# ════════════════════════════════════════════════════════════════

@dataclass
class BlockRecord:
    """A single immutable block in the evidence chain."""
    block_id:     int
    block_hash:   str
    prev_hash:    str
    case_id:      str
    event_type:   str
    payload_hash: str
    timestamp:    str
    actor_id:     Optional[str]
    metadata:     Optional[dict]

    @property
    def event_label(self) -> str:
        return EVENT_LABELS.get(self.event_type, self.event_type)

    @property
    def short_hash(self) -> str:
        """Truncated hash for UI display: 0x3a8f...2c19"""
        return f"0x{self.block_hash[:4]}...{self.block_hash[-4:]}"

    @property
    def short_prev(self) -> str:
        if self.prev_hash == "GENESIS":
            return "GENESIS"
        return f"0x{self.prev_hash[:4]}...{self.prev_hash[-4:]}"

    @property
    def details(self) -> str:
        return format_block_details(self)

    @property
    def display_timestamp(self) -> str:
        """HH:MM:SS for UI timeline."""
        ts = self.timestamp or ""
        if "T" in ts:
            part = ts.split("T", 1)[1]
            return part[:8] if len(part) >= 8 else part
        return ts[:8] if len(ts) >= 8 else ts

    def to_dict(self) -> dict:
        preview = None
        if self.metadata and isinstance(self.metadata, dict):
            preview = self.metadata.get("payload_preview")
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
            "display_timestamp": self.display_timestamp,
            "actor_id":     self.actor_id,
            "metadata":     self.metadata,
            "payload_preview": preview,
            "details":      self.details,
            "verified":     True,  # set to False by verify_chain if broken
        }


@dataclass
class ChainVerification:
    """Result of verify_chain()."""
    valid:           bool
    block_count:     int
    blocks:          list[BlockRecord]
    broken_at_block: Optional[int]
    verified_at:     str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    network:         str = "UBI-Fabric-Private"
    mode:            str = "DEMO" if DEMO_MODE else "PRODUCTION"

    @property
    def empty(self) -> bool:
        return self.block_count == 0

    def to_dict(self) -> dict:
        blocks_list = []
        for b in self.blocks:
            d = b.to_dict()
            # Mark the broken block if chain is invalid
            if not self.valid and b.block_id == self.broken_at_block:
                d["verified"] = False
            blocks_list.append(d)

        if self.empty:
            integrity = "NO_BLOCKS"
        elif self.valid:
            integrity = "VERIFIED"
        else:
            integrity = "COMPROMISED"

        return {
            "valid":           self.valid,
            "empty":           self.empty,
            "block_count":     self.block_count,
            "blocks":          blocks_list,
            "broken_at_block": self.broken_at_block,
            "verified_at":     self.verified_at,
            "network":         self.network,
            "mode":            self.mode,
            "integrity_label": integrity,
        }


# ════════════════════════════════════════════════════════════════
# CORE CRYPTO FUNCTIONS
# ════════════════════════════════════════════════════════════════

def compute_hash(payload: dict) -> str:
    """
    Compute SHA-256 of a deterministically serialised dict.

    Sorted keys ensure the same dict always produces the same hash
    regardless of insertion order — critical for blockchain integrity.

    Args:
        payload: Any JSON-serialisable dict.

    Returns:
        64-character lowercase hex digest.
    """
    serialised = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def format_block_details(block: BlockRecord) -> str:
    """Human-readable audit line for UI and exports."""
    meta = block.metadata if isinstance(block.metadata, dict) else {}
    if meta.get("details"):
        return str(meta["details"])

    preview = meta.get("payload_preview") if isinstance(meta.get("payload_preview"), dict) else {}

    if block.event_type == ALERT_CREATED:
        gnn = preview.get("gnn_score", "")
        pct = f"{float(gnn) * 100:.0f}%" if isinstance(gnn, (int, float)) and gnn <= 1 else str(gnn)
        return (
            f"Alert {block.case_id} generated · Typology: {preview.get('typology', '—')} · "
            f"GNN score: {pct} · ₹{float(preview.get('total_amount', 0) or 0):,.0f}"
        )
    if block.event_type == CASE_OPENED:
        inv = block.actor_id or preview.get("investigator") or "investigator"
        status = preview.get("new_status") or preview.get("status") or "investigating"
        return f"Case opened by {inv} · Status: {status}"
    if block.event_type == SUBGRAPH_EXPORTED:
        nodes = preview.get("node_count", "—")
        return f"Subgraph exported for STR · {nodes} accounts · hash sealed on chain"
    if block.event_type == LLM_NARRATIVE_GENERATED:
        model = preview.get("model_used", "Gemini")
        words = preview.get("word_count", "—")
        return f"LLM narrative generated · Model: {model} · {words} words · I/O hash recorded"
    if block.event_type == SUPERVISOR_APPROVED:
        return f"STR draft reviewed · Investigator: {block.actor_id or '—'}"
    if block.event_type == STR_SUBMITTED:
        fiu = preview.get("fiu_reference", "FIU-IND")
        sub = preview.get("submission_id", "")
        return f"STR submitted · Ref {fiu}" + (f" · Submission {sub}" if sub else "")

    if block.event_type == INVESTIGATOR_ACTION:
        action = preview.get("action", "Action")
        account = preview.get("account_id", "")
        return f"{action}" + (f" · Account {account}" if account else "")

    notes = meta.get("notes")
    if notes:
        return str(notes)
    return f"Payload hash: {block.payload_hash[:16]}…"


def _merge_write_metadata(
    event_type: str,
    payload: dict,
    metadata: Optional[dict],
) -> dict:
    meta = dict(metadata or {})
    meta.setdefault("payload_preview", payload)
    meta.setdefault("details", format_block_details(
        BlockRecord(
            block_id=0,
            block_hash="",
            prev_hash="GENESIS",
            case_id=payload.get("case_id", ""),
            event_type=event_type,
            payload_hash=compute_hash(payload),
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor_id=meta.get("actor_id"),
            metadata=meta,
        )
    ))
    return meta


def _compute_block_hash(
    block_id:     int,
    prev_hash:    str,
    payload_hash: str,
    timestamp:    str,
) -> str:
    """
    Compute the block's own hash by combining its identity fields.

    block_hash = SHA-256( block_id | prev_hash | payload_hash | timestamp )

    This links every block to:
      - Its position in the chain (block_id)
      - The previous block (prev_hash)
      - The evidence it seals (payload_hash)
      - The exact moment it was created (timestamp)
    """
    content = f"{block_id}|{prev_hash}|{payload_hash}|{timestamp}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ════════════════════════════════════════════════════════════════
# DEMO MODE — SQLite implementation
# ════════════════════════════════════════════════════════════════

def init_db(db_path: Path = DB_PATH) -> None:
    """
    Create the blocks table if it does not exist.
    Safe to call multiple times (idempotent).
    Called once at FastAPI app startup via lifespan.
    """
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
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_case_id ON blocks (case_id)"
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_event_type ON blocks (event_type)"
    )
    con.commit()
    con.close()
    logger.info(f"Evidence chain DB ready: {db_path} (mode={_MODE.upper()})")


def _get_prev_hash(case_id: str, db_path: Path = DB_PATH) -> str:
    """
    Return the hash of the most recent block for case_id.
    Returns "GENESIS" if this is the first block for this case.
    """
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT block_hash FROM blocks WHERE case_id = ? "
        "ORDER BY block_id DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    con.close()
    return row[0] if row else "GENESIS"


def _demo_write_block(
    case_id:    str,
    event_type: str,
    payload:    dict,
    actor_id:   Optional[str] = None,
    metadata:   Optional[dict] = None,
    db_path:    Path = DB_PATH,
) -> BlockRecord:
    """
    DEMO MODE: write an immutable block to SQLite.

    Steps:
      1. Compute payload_hash from the payload dict.
      2. Get prev_hash from the last block for this case (or GENESIS).
      3. Get the next block_id by inserting a placeholder then updating.
         (SQLite's AUTOINCREMENT gives us the ID after insert.)
      4. Compute block_hash = SHA-256(block_id|prev_hash|payload_hash|ts).
      5. Update the row with the computed hash.
      6. Return the full BlockRecord.
    """
    ts           = datetime.now(timezone.utc).isoformat()
    payload_hash = compute_hash(payload)
    prev_hash    = _get_prev_hash(case_id, db_path)
    metadata     = _merge_write_metadata(event_type, payload, metadata)
    meta_json    = json.dumps(metadata) if metadata else None

    con = sqlite3.connect(db_path)

    # Insert placeholder — we need block_id before computing block_hash
    cur = con.execute(
        """
        INSERT INTO blocks
               (block_hash, prev_hash, case_id, event_type,
                payload_hash, timestamp, actor_id, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "PENDING",      # will be updated immediately below
            prev_hash,
            case_id,
            event_type,
            payload_hash,
            ts,
            actor_id,
            meta_json,
        ),
    )
    block_id = cur.lastrowid

    # Now we know block_id — compute the real hash
    block_hash = _compute_block_hash(block_id, prev_hash, payload_hash, ts)

    # Update the placeholder
    con.execute(
        "UPDATE blocks SET block_hash = ? WHERE block_id = ?",
        (block_hash, block_id),
    )
    con.commit()
    con.close()

    logger.info(
        f"Block #{block_id} written | "
        f"case={case_id} | event={event_type} | "
        f"hash={block_hash[:12]}..."
    )

    return BlockRecord(
        block_id=block_id,
        block_hash=block_hash,
        prev_hash=prev_hash,
        case_id=case_id,
        event_type=event_type,
        payload_hash=payload_hash,
        timestamp=ts,
        actor_id=actor_id,
        metadata=metadata,
    )


def _demo_get_chain(case_id: str, db_path: Path = DB_PATH) -> list[BlockRecord]:
    """
    DEMO MODE: return all blocks for case_id in chronological order.
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM blocks WHERE case_id = ? ORDER BY block_id ASC",
        (case_id,),
    ).fetchall()
    con.close()
    return [_row_to_block(r) for r in rows]


def _demo_verify_chain(case_id: str, db_path: Path = DB_PATH) -> ChainVerification:
    """
    DEMO MODE: cryptographically verify the entire chain for case_id.

    Checks:
      1. Each block's block_hash matches the recomputed hash.
      2. Each block's prev_hash equals the previous block's block_hash.
      3. The first block's prev_hash is "GENESIS".

    Returns ChainVerification with valid=True only if all checks pass.
    """
    blocks = _demo_get_chain(case_id, db_path)

    if not blocks:
        return ChainVerification(
            valid=True,
            block_count=0,
            blocks=[],
            broken_at_block=None,
        )

    broken_at = None

    for i, block in enumerate(blocks):
        # Recompute the expected block hash
        expected = _compute_block_hash(
            block.block_id,
            block.prev_hash,
            block.payload_hash,
            block.timestamp,
        )

        # Check 1: block hash integrity
        if expected != block.block_hash:
            broken_at = block.block_id
            logger.error(
                f"Chain broken at block #{block.block_id} — "
                f"hash mismatch for case {case_id}"
            )
            break

        # Check 2: prev_hash linkage
        if i == 0:
            if block.prev_hash != "GENESIS":
                broken_at = block.block_id
                logger.error(f"Block #1 prev_hash is not GENESIS for case {case_id}")
                break
        else:
            if block.prev_hash != blocks[i - 1].block_hash:
                broken_at = block.block_id
                logger.error(
                    f"Chain broken at block #{block.block_id} — "
                    f"prev_hash mismatch for case {case_id}"
                )
                break

    return ChainVerification(
        valid=broken_at is None,
        block_count=len(blocks),
        blocks=blocks,
        broken_at_block=broken_at,
    )


def _row_to_block(row: sqlite3.Row) -> BlockRecord:
    """Convert a SQLite row to a BlockRecord dataclass."""
    metadata = None
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except (json.JSONDecodeError, TypeError):
            pass
    return BlockRecord(
        block_id=row["block_id"],
        block_hash=row["block_hash"],
        prev_hash=row["prev_hash"],
        case_id=row["case_id"],
        event_type=row["event_type"],
        payload_hash=row["payload_hash"],
        timestamp=row["timestamp"],
        actor_id=row["actor_id"],
        metadata=metadata,
    )


# ════════════════════════════════════════════════════════════════
# PRODUCTION MODE — Hyperledger Fabric stubs
# ════════════════════════════════════════════════════════════════
#
# Replace these stubs with real fabric-sdk-py calls when you have
# a Hyperledger Fabric network running.
#
# Chaincode interface expected:
#   invoke WriteBlock(case_id, event_type, payload_hash, prev_hash,
#                     block_hash, timestamp, actor_id, metadata_json)
#   query  GetChain(case_id) -> []Block
#   query  VerifyChain(case_id) -> VerificationResult

def _fabric_write_block(
    case_id:    str,
    event_type: str,
    payload:    dict,
    actor_id:   Optional[str] = None,
    metadata:   Optional[dict] = None,
) -> BlockRecord:
    """
    PRODUCTION MODE stub.
    Replace with fabric-sdk-py Gateway.submit_transaction() call.
    """
    raise NotImplementedError(
        "Hyperledger Fabric integration not yet configured. "
        "Set FUNDLENS_BLOCKCHAIN_MODE=demo to use the SQLite ledger."
    )


def _fabric_get_chain(case_id: str) -> list[BlockRecord]:
    """PRODUCTION MODE stub."""
    raise NotImplementedError(
        "Hyperledger Fabric integration not yet configured."
    )


def _fabric_verify_chain(case_id: str) -> ChainVerification:
    """PRODUCTION MODE stub."""
    raise NotImplementedError(
        "Hyperledger Fabric integration not yet configured."
    )


# ════════════════════════════════════════════════════════════════
# PUBLIC API — mode-dispatched
# ════════════════════════════════════════════════════════════════

def write_block(
    case_id:    str,
    event_type: str,
    payload:    dict,
    actor_id:   Optional[str] = None,
    metadata:   Optional[dict] = None,
    db_path:    Path = DB_PATH,
) -> BlockRecord:
    """
    Append an immutable block to the evidence chain for case_id.

    Args:
        case_id:    The case this block belongs to (e.g. "CASE-2847").
        event_type: One of the EVENT_TYPE constants (e.g. ALERT_CREATED).
        payload:    Dict of evidence data. Its SHA-256 hash is stored.
        actor_id:   Who triggered this event (e.g. "system", "RK-001").
        metadata:   Optional extra fields stored alongside the block.
        db_path:    Override the SQLite DB path (useful for tests).

    Returns:
        A BlockRecord with all fields populated, including the computed
        block_hash and the block_id assigned by the chain.

    Raises:
        ValueError: if event_type is not a recognised constant.
    """
    if event_type not in ALL_EVENT_TYPES:
        raise ValueError(
            f"Unknown event_type '{event_type}'. "
            f"Must be one of: {', '.join(ALL_EVENT_TYPES)}"
        )

    if PRODUCTION_MODE:
        return _fabric_write_block(case_id, event_type, payload, actor_id, metadata)
    return _demo_write_block(case_id, event_type, payload, actor_id, metadata, db_path)


def get_chain(case_id: str, db_path: Path = DB_PATH) -> list[BlockRecord]:
    """
    Return all blocks for case_id in chronological order.

    Returns an empty list if no blocks exist for this case.
    Each BlockRecord includes a .to_dict() method for JSON serialisation.
    """
    if PRODUCTION_MODE:
        return _fabric_get_chain(case_id)
    return _demo_get_chain(case_id, db_path)


def verify_chain(case_id: str, db_path: Path = DB_PATH) -> ChainVerification:
    """
    Cryptographically verify the entire evidence chain for case_id.

    Recomputes every block hash and checks prev_hash linkage.
    Returns ChainVerification with .valid=True only if all checks pass.

    The returned object's .to_dict() method is safe to return directly
    from a FastAPI route as JSON.
    """
    if PRODUCTION_MODE:
        return _fabric_verify_chain(case_id)
    return _demo_verify_chain(case_id, db_path)


def get_all_cases(db_path: Path = DB_PATH) -> list[str]:
    """Return a list of all case_ids that have at least one block."""
    if PRODUCTION_MODE:
        return []
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT DISTINCT case_id FROM blocks ORDER BY case_id"
    ).fetchall()
    con.close()
    return [r[0] for r in rows]


def has_event(case_id: str, event_type: str, db_path: Path = DB_PATH) -> bool:
    """Return True if case_id already has a block of this event_type."""
    if PRODUCTION_MODE:
        return False
    con = sqlite3.connect(db_path)
    row = con.execute(
        "SELECT 1 FROM blocks WHERE case_id = ? AND event_type = ? LIMIT 1",
        (case_id, event_type),
    ).fetchone()
    con.close()
    return row is not None


def get_block_count(case_id: str, db_path: Path = DB_PATH) -> int:
    """Return the number of blocks for a case."""
    if PRODUCTION_MODE:
        return 0
    con = sqlite3.connect(db_path)
    count = con.execute(
        "SELECT COUNT(*) FROM blocks WHERE case_id = ?",
        (case_id,),
    ).fetchone()[0]
    con.close()
    return count


def seal_case(
    case_id:         str,
    gnn_score:       float,
    typology:        str,
    total_amount:    float,
    accounts_count:  int,
    actor_id:        str = "system",
    db_path:         Path = DB_PATH,
) -> BlockRecord:
    """
    Convenience function: write Block 1 (ALERT_CREATED) for a new case.
    Called by the alert pipeline when a new fraud case is opened.
    """
    return write_block(
        case_id=case_id,
        event_type=ALERT_CREATED,
        payload={
            "case_id":        case_id,
            "gnn_score":      gnn_score,
            "typology":       typology,
            "total_amount":   total_amount,
            "accounts_count": accounts_count,
        },
        actor_id=actor_id,
        metadata={"source": "FundLens GNN Pipeline"},
        db_path=db_path,
    )
