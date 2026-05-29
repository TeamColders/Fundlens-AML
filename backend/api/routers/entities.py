import logging

from fastapi import APIRouter, HTTPException

from backend.db import neo4j as neo4j_db


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{account_id}")
def get_entity(account_id: str):
    query = (
        "MATCH (a:Account {account_id: $account_id}) "
        "RETURN a LIMIT 1"
    )
    with neo4j_db.get_session() as session:
        record = session.run(query, account_id=account_id).single()

    if record is None:
        raise HTTPException(status_code=404, detail="Account not found")

    node = record["a"]
    return {
        "account_id": node.get("account_id") or account_id,
        "account_type": node.get("account_type"),
        "kyc_tier": node.get("kyc_tier"),
        "is_dormant": bool(node.get("is_dormant")),
        "total_volume": node.get("total_volume"),
        "risk_level": node.get("risk_level"),
        "owner": node.get("owner"),
    }
