"""
FundLens — /api/cases endpoints.
"""
from fastapi import APIRouter, HTTPException
from backend.database.demo_data import list_cases, get_case_data

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("")
async def get_cases():
    """Return list of all cases."""
    return {"cases": list_cases(), "total": len(list_cases())}


@router.get("/{case_id}")
async def get_case(case_id: str):
    """Return full case data."""
    case = get_case_data(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case
