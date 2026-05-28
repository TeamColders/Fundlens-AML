# FundLens — Blockchain Evidence Chain

Cryptographically linked, append-only evidence ledger for the FundLens AML platform.
Behaves identically to Hyperledger Fabric from the frontend's perspective.
Runs on SQLite with zero infrastructure for the hackathon demo.

---

## Quickstart

```python
from evidence_chain import (
    init_db, write_block, get_chain, verify_chain,
    ALERT_CREATED, CASE_OPENED, STR_SUBMITTED,
)

init_db()   # once at startup — creates fundlens_evidence.db

# Write 2 blocks for a case
b1 = write_block("CASE-2847", ALERT_CREATED,
                 {"gnn_score": 0.94, "typology": "Round-trip Layering"},
                 actor_id="system")

b2 = write_block("CASE-2847", CASE_OPENED,
                 {"investigator": "RK"},
                 actor_id="RK-001")

print(b1.block_hash)   # SHA-256 hex
print(b2.prev_hash)    # equals b1.block_hash — the chain link

# Verify the full chain
result = verify_chain("CASE-2847")
print(result.valid)     # True
print(result.to_dict()) # JSON-safe — return directly from FastAPI route
```

---

## Two modes

| Mode | Storage | When to use |
|---|---|---|
| `demo` | SQLite (local file) | Hackathon, laptop demo, development |
| `production` | Hyperledger Fabric | Real bank deployment (stubs provided) |

```bash
export FUNDLENS_BLOCKCHAIN_MODE=demo        # default
export FUNDLENS_BLOCKCHAIN_MODE=production  # requires Fabric network
export FUNDLENS_EVIDENCE_DB=custom_path.db  # override DB location
```

---

## Files

```
evidence_chain.py       Main module — import this
test_evidence_chain.py  Full test suite (77 tests)
requirements.txt        No external deps in demo mode
README.md               This file
```

---

## Event types

```python
ALERT_CREATED           # Block 1 — alert fires, evidence sealed
CASE_OPENED             # Block 2 — investigator opens case
SUBGRAPH_EXPORTED       # Block 3 — subgraph extracted for STR
LLM_NARRATIVE_GENERATED # Block 4 — Claude drafts the narrative
SUPERVISOR_APPROVED     # Block 5 — supervisor approves
STR_SUBMITTED           # Block 6 — filed with FIU-IND
```

---

## Run tests

```bash
python test_evidence_chain.py
# 77 passed, 0 failed
```

Tests cover: initialisation, compute_hash determinism, 6-block chain
write, hash linkage, tamper detection, multi-case isolation,
concurrent writes, helper functions, and all to_dict() serialisation.

---

## Integration with FastAPI

```python
# In your lifespan startup:
from evidence_chain import init_db
init_db()

# In your STR generation route:
from evidence_chain import write_block, LLM_NARRATIVE_GENERATED
block = write_block(
    case_id=case_id,
    event_type=LLM_NARRATIVE_GENERATED,
    payload={"model": "claude-opus-4-5", "word_count": 847},
    actor_id="system",
)

# In your blockchain audit trail route:
from evidence_chain import get_chain, verify_chain
chain = verify_chain(case_id)
return chain.to_dict()   # directly JSON-serialisable
```
