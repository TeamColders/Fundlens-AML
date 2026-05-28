"""
FundLens — /api/analytics endpoints.
"""
from fastapi import APIRouter
from backend.database.demo_data import get_analytics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("")
async def analytics():
    """Return analytics dashboard data."""
    return get_analytics()
