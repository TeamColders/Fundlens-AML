"""
FundLens — /api/blockchain endpoints.
"""
from fastapi import APIRouter, HTTPException
from backend.blockchain.evidence_chain import get_chain, verify_chain, get_all_cases

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain"])


@router.get("")
async def list_blockchain_cases():
    """Return all cases with blockchain evidence."""
    cases = get_all_cases()
    return {"cases": cases, "total": len(cases)}


@router.get("/{case_id}")
async def blockchain_chain(case_id: str):
    """Return the full evidence chain for a case."""
    chain = get_chain(case_id)
    return {
        "case_id": case_id,
        "block_count": len(chain),
        "blocks": [b.to_dict() for b in chain],
    }


@router.get("/{case_id}/verify")
async def blockchain_verify(case_id: str):
    """Cryptographically verify the evidence chain."""
    result = verify_chain(case_id)
    return result.to_dict()
