from fastapi import APIRouter


router = APIRouter()


@router.get("")
def analytics_overview():
    return {
        "total_cases": 0,
        "total_alerts": 0,
        "risk_breakdown": {"low": 0, "medium": 0, "high": 0},
    }
