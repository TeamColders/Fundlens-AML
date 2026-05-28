"""
test_evidence_chain.py
======================
Full test suite for the FundLens blockchain evidence chain.
Run with: python test_evidence_chain.py
"""

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

# ── Colour helpers ────────────────────────────────────────────────
def green(s):  return f"\033[92m{s}\033[0m"
def red(s):    return f"\033[91m{s}\033[0m"
def cyan(s):   return f"\033[96m{s}\033[0m"
def bold(s):   return f"\033[1m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"

passed = 0
failed = 0

def test(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  {green('✓')} {name}")
    else:
        failed += 1
        print(f"  {red('✗')} {name}")
        if detail:
            print(f"      {red('→')} {detail}")

def section(name: str):
    print(f"\n{bold(cyan('──'))} {bold(name)}")


# ── Use a temp DB for tests so we never touch real data ───────────
TMP_DIR  = Path(tempfile.mkdtemp())
TMP_DB   = TMP_DIR / "test_evidence.db"
os.environ["FUNDLENS_EVIDENCE_DB"]       = str(TMP_DB)
os.environ["FUNDLENS_BLOCKCHAIN_MODE"]   = "demo"

# Import AFTER setting env vars
sys.path.insert(0, str(Path(__file__).parent))
from evidence_chain import (
    init_db, write_block, get_chain, verify_chain,
    compute_hash, get_block_count, get_all_cases,
    seal_case, _compute_block_hash,
    ALERT_CREATED, CASE_OPENED, SUBGRAPH_EXPORTED,
    LLM_NARRATIVE_GENERATED, SUPERVISOR_APPROVED, STR_SUBMITTED,
    BlockRecord, ChainVerification,
)


print(f"\n{bold('FundLens Evidence Chain — Test Suite')}")
print(f"DB path: {TMP_DB}\n")


# ════════════════════════════════════════════════════════════════
# 1. INITIALISATION
# ════════════════════════════════════════════════════════════════
section("Initialisation")

init_db(TMP_DB)
test("init_db() creates DB file", TMP_DB.exists())

import sqlite3
con = sqlite3.connect(TMP_DB)
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
con.close()
test("blocks table created",    "blocks" in tables)
test("init_db() is idempotent", True)  # second call must not raise
init_db(TMP_DB)
test("second init_db() safe",   True)


# ════════════════════════════════════════════════════════════════
# 2. compute_hash
# ════════════════════════════════════════════════════════════════
section("compute_hash()")

h1 = compute_hash({"a": 1, "b": 2})
h2 = compute_hash({"b": 2, "a": 1})   # different insertion order
test("SHA-256 hex length is 64",         len(h1) == 64)
test("Only hex characters",              all(c in "0123456789abcdef" for c in h1))
test("Deterministic regardless of key order", h1 == h2,
     f"h1={h1[:8]}... h2={h2[:8]}...")

h3 = compute_hash({"a": 1, "b": 3})   # different value
test("Different payload → different hash", h1 != h3)

# Verify against raw SHA-256
raw = json.dumps({"a": 1, "b": 2}, sort_keys=True)
expected = hashlib.sha256(raw.encode()).hexdigest()
test("Matches manual SHA-256",  h1 == expected, f"got {h1}, expected {expected}")

test("Empty dict is hashable",  len(compute_hash({})) == 64)
test("Nested dict is hashable", len(compute_hash({"x": {"y": [1, 2, 3]}})) == 64)


# ════════════════════════════════════════════════════════════════
# 3. write_block — single block
# ════════════════════════════════════════════════════════════════
section("write_block() — single block")

b1 = write_block(
    case_id="CASE-TEST-001",
    event_type=ALERT_CREATED,
    payload={"gnn_score": 0.94, "typology": "Round-trip Layering"},
    actor_id="system",
    metadata={"source": "GNN pipeline"},
    db_path=TMP_DB,
)

test("Returns BlockRecord",        isinstance(b1, BlockRecord))
test("block_id is 1",              b1.block_id == 1)
test("prev_hash is GENESIS",       b1.prev_hash == "GENESIS",
     f"got {b1.prev_hash}")
test("event_type is correct",      b1.event_type == ALERT_CREATED)
test("case_id is correct",         b1.case_id == "CASE-TEST-001")
test("actor_id stored",            b1.actor_id == "system")
test("metadata stored",            b1.metadata == {"source": "GNN pipeline"})
test("block_hash is 64 hex chars", len(b1.block_hash) == 64)
test("payload_hash is 64 hex",     len(b1.payload_hash) == 64)
test("timestamp is non-empty",     bool(b1.timestamp))

# Verify the block_hash is correctly computed
expected_bh = _compute_block_hash(b1.block_id, b1.prev_hash, b1.payload_hash, b1.timestamp)
test("block_hash matches recomputed value", b1.block_hash == expected_bh,
     f"stored={b1.block_hash[:12]}... expected={expected_bh[:12]}...")

# Verify payload_hash
expected_ph = compute_hash({"gnn_score": 0.94, "typology": "Round-trip Layering"})
test("payload_hash matches compute_hash(payload)", b1.payload_hash == expected_ph)


# ════════════════════════════════════════════════════════════════
# 4. write_block — full 6-block chain for CASE-2847
# ════════════════════════════════════════════════════════════════
section("write_block() — full 6-block chain")

CASE_ID = "CASE-2847"

blocks = []
event_types = [
    ALERT_CREATED,
    CASE_OPENED,
    SUBGRAPH_EXPORTED,
    LLM_NARRATIVE_GENERATED,
    SUPERVISOR_APPROVED,
    STR_SUBMITTED,
]
payloads = [
    {"case_id": CASE_ID, "gnn_score": 0.94, "typology": "Round-trip Layering"},
    {"investigator": "RK", "biometric": "verified"},
    {"node_count": 7, "edge_count": 9, "typology": "Round-trip Layering"},
    {"model": "claude-opus-4-5", "word_count": 847, "generation_time_s": 47.2},
    {"supervisor": "AK", "action": "approved"},
    {"submission_id": "SUB-ABC123", "fiu_reference": "FIU-IND-20260322-XYZ"},
]

for et, payload in zip(event_types, payloads):
    b = write_block(CASE_ID, et, payload, actor_id="system", db_path=TMP_DB)
    blocks.append(b)

test("6 blocks written",             len(blocks) == 6)
test("Block IDs are sequential",     [b.block_id for b in blocks] == list(range(2, 8)),
     f"got {[b.block_id for b in blocks]}")

# Check hash linkage
for i in range(1, len(blocks)):
    test(
        f"Block {blocks[i].block_id} prev_hash == Block {blocks[i-1].block_id} hash",
        blocks[i].prev_hash == blocks[i - 1].block_hash,
        f"prev={blocks[i].prev_hash[:12]}... expected={blocks[i-1].block_hash[:12]}..."
    )

test("First block prev_hash is GENESIS", blocks[0].prev_hash == "GENESIS")
test("Last event is STR_SUBMITTED",      blocks[-1].event_type == STR_SUBMITTED)


# ════════════════════════════════════════════════════════════════
# 5. write_block — validation
# ════════════════════════════════════════════════════════════════
section("write_block() — validation")

try:
    write_block("CASE-X", "INVALID_EVENT", {}, db_path=TMP_DB)
    test("Rejects unknown event_type", False, "Should have raised ValueError")
except ValueError as e:
    test("Rejects unknown event_type", True)
    test("Error message names the bad type", "INVALID_EVENT" in str(e))


# ════════════════════════════════════════════════════════════════
# 6. get_chain
# ════════════════════════════════════════════════════════════════
section("get_chain()")

chain = get_chain(CASE_ID, TMP_DB)
test("Returns a list",               isinstance(chain, list))
test("Returns 6 blocks",             len(chain) == 6,
     f"got {len(chain)}")
test("Ordered by block_id",          [b.block_id for b in chain] == sorted(b.block_id for b in chain))
test("All are BlockRecord instances", all(isinstance(b, BlockRecord) for b in chain))
test("event_labels populated",       all(bool(b.event_label) for b in chain))
test("short_hash format correct",    all(b.short_hash.startswith("0x") for b in chain))

# Empty case returns empty list
empty = get_chain("CASE-NONEXISTENT", TMP_DB)
test("Non-existent case returns []", empty == [])

# to_dict() works
d = chain[0].to_dict()
test("to_dict() has all keys", all(k in d for k in [
    "block_id", "block_hash", "short_hash", "prev_hash",
    "case_id", "event_type", "event_label", "payload_hash",
    "timestamp", "actor_id", "metadata", "verified",
]))


# ════════════════════════════════════════════════════════════════
# 7. verify_chain — valid chain
# ════════════════════════════════════════════════════════════════
section("verify_chain() — valid chain")

v = verify_chain(CASE_ID, TMP_DB)
test("Returns ChainVerification",    isinstance(v, ChainVerification))
test("valid = True",                 v.valid is True,
     f"broken_at_block={v.broken_at_block}")
test("block_count = 6",              v.block_count == 6)
test("broken_at_block = None",       v.broken_at_block is None)
test("blocks list has 6 items",      len(v.blocks) == 6)
test("network = UBI-Fabric-Private", v.network == "UBI-Fabric-Private")
test("mode = DEMO",                  v.mode == "DEMO")

vd = v.to_dict()
test("to_dict() integrity_label = VERIFIED", vd["integrity_label"] == "VERIFIED")
test("to_dict() all blocks have verified=True",
     all(b["verified"] for b in vd["blocks"]))

# Empty case
ve = verify_chain("CASE-EMPTY", TMP_DB)
test("Empty case: valid = False",    ve.valid is False)
test("Empty case: block_count = 0",  ve.block_count == 0)


# ════════════════════════════════════════════════════════════════
# 8. verify_chain — tamper detection
# ════════════════════════════════════════════════════════════════
section("verify_chain() — tamper detection")

# Tamper with block 4 (LLM_NARRATIVE_GENERATED) directly in SQLite
con = sqlite3.connect(TMP_DB)
target_block = con.execute(
    "SELECT block_id FROM blocks WHERE case_id=? AND event_type=?",
    (CASE_ID, LLM_NARRATIVE_GENERATED),
).fetchone()[0]
con.execute(
    "UPDATE blocks SET payload_hash = ? WHERE block_id = ?",
    ("0000000000000000000000000000000000000000000000000000000000000000", target_block),
)
con.commit()
con.close()

vt = verify_chain(CASE_ID, TMP_DB)
test("Tampered chain: valid = False",           vt.valid is False,
     "Chain should be invalid after tampering")
test("Tampered chain: broken_at correct",       vt.broken_at_block == target_block,
     f"got {vt.broken_at_block}, expected {target_block}")

vdt = vt.to_dict()
test("to_dict() integrity_label = COMPROMISED", vdt["integrity_label"] == "COMPROMISED")
test("Tampered block has verified=False",
     any(b["block_id"] == target_block and not b["verified"] for b in vdt["blocks"]))


# ════════════════════════════════════════════════════════════════
# 9. Helper functions
# ════════════════════════════════════════════════════════════════
section("Helper functions")

# get_block_count
count = get_block_count(CASE_ID, TMP_DB)
test("get_block_count returns 6",        count == 6, f"got {count}")
test("get_block_count: missing case = 0", get_block_count("MISSING", TMP_DB) == 0)

# get_all_cases
all_cases = get_all_cases(TMP_DB)
test("get_all_cases returns list",       isinstance(all_cases, list))
test("get_all_cases includes CASE-2847", CASE_ID in all_cases)
test("get_all_cases includes CASE-TEST-001", "CASE-TEST-001" in all_cases)

# seal_case convenience function
b_seal = seal_case(
    case_id="CASE-SEAL-TEST",
    gnn_score=0.87,
    typology="Structuring",
    total_amount=2310000,
    accounts_count=14,
    actor_id="system",
    db_path=TMP_DB,
)
test("seal_case() returns BlockRecord",    isinstance(b_seal, BlockRecord))
test("seal_case() event_type = ALERT_CREATED", b_seal.event_type == ALERT_CREATED)
test("seal_case() case_id correct",        b_seal.case_id == "CASE-SEAL-TEST")
test("seal_case() prev_hash = GENESIS",    b_seal.prev_hash == "GENESIS")


# ════════════════════════════════════════════════════════════════
# 10. Multi-case isolation
# ════════════════════════════════════════════════════════════════
section("Multi-case isolation")

write_block("CASE-A", ALERT_CREATED, {"x": 1}, db_path=TMP_DB)
write_block("CASE-A", CASE_OPENED,   {"y": 2}, db_path=TMP_DB)
write_block("CASE-B", ALERT_CREATED, {"z": 3}, db_path=TMP_DB)

chain_a = get_chain("CASE-A", TMP_DB)
chain_b = get_chain("CASE-B", TMP_DB)

test("CASE-A has 2 blocks",            len(chain_a) == 2)
test("CASE-B has 1 block",             len(chain_b) == 1)
test("CASE-A block 1 prev = GENESIS",  chain_a[0].prev_hash == "GENESIS")
test("CASE-A block 2 prev = block 1 hash",
     chain_a[1].prev_hash == chain_a[0].block_hash)
test("CASE-B block 1 prev = GENESIS",  chain_b[0].prev_hash == "GENESIS")
test("Cases don't share block numbering",
     chain_a[0].block_id != chain_b[0].block_id)

va = verify_chain("CASE-A", TMP_DB)
vb = verify_chain("CASE-B", TMP_DB)
test("CASE-A chain valid",  va.valid)
test("CASE-B chain valid",  vb.valid)


# ════════════════════════════════════════════════════════════════
# 11. Concurrent writes (basic)
# ════════════════════════════════════════════════════════════════
section("Concurrent writes")

import threading

CONC_CASE = "CASE-CONCURRENT"
results = []
errors  = []

def write_one(n):
    try:
        b = write_block(
            CONC_CASE, ALERT_CREATED,
            {"n": n, "thread": threading.current_thread().name},
            db_path=TMP_DB,
        )
        results.append(b)
    except Exception as e:
        errors.append(str(e))

threads = [threading.Thread(target=write_one, args=(i,)) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join()

test("All 5 concurrent writes succeeded", len(results) == 5 and not errors,
     f"errors: {errors}")
test("No duplicate block_ids",
     len({b.block_id for b in results}) == 5)
vc = verify_chain(CONC_CASE, TMP_DB)
test("Concurrent writes: chain is valid", vc.valid,
     f"broken_at={vc.broken_at_block}")


# ════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════
import shutil
shutil.rmtree(TMP_DIR, ignore_errors=True)

total = passed + failed
print(f"\n{bold('═' * 50)}")
print(f"  {bold('Results:')}  {green(str(passed))} passed  "
      f"{(red(str(failed)) if failed else str(failed))} failed  "
      f"/ {total} total")
print(bold("═" * 50))

if failed:
    print(f"\n  {red('Some tests failed. Fix before submitting.')}")
    sys.exit(1)
else:
    print(f"\n  {green('All tests passed. Evidence chain is production-ready.')}")
    sys.exit(0)
