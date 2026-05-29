import logging

from fastapi import APIRouter

from backend.blockchain.evidence_chain import list_evidence_blocks


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/case/{case_id}")
def get_case_evidence(case_id: str):
    return {"case_id": case_id, "blocks": list_evidence_blocks(case_id)}
