"""
FundLens — /api/entities endpoints.
"""
from fastapi import APIRouter, HTTPException
from backend.database.demo_data import get_entity

router = APIRouter(prefix="/api/entities", tags=["Entities"])


@router.get("/{account_id}")
async def entity_profile(account_id: str):
    """
    Return full entity profile including:
    - Account details, KYC, risk
    - Transaction history
    - Peer metrics
    - Network connections
    - Related entities
    """
    entity = get_entity(account_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return entity
