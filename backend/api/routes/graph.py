"""
FundLens — /api/graph endpoints.
"""
from fastapi import APIRouter, HTTPException
from backend.database.demo_data import get_subgraph

router = APIRouter(prefix="/api/graph", tags=["Graph"])


@router.get("/{case_id}")
async def get_graph(case_id: str):
    """Return enriched subgraph for fund-flow visualization."""
    subgraph = get_subgraph(case_id)
    if not subgraph:
        raise HTTPException(status_code=404, detail=f"No graph data for case {case_id}")

    return subgraph
