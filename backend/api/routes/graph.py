"""
FundLens — /api/graph endpoints.
"""
from fastapi import APIRouter, HTTPException
from backend.database.demo_data import get_subgraph

router = APIRouter(prefix="/api/graph", tags=["Graph"])


@router.get("/{case_id}")
async def get_graph(case_id: str):
    """
    Return the full subgraph for a case.
    Format: {nodes: [...], edges: [...]}
    Edges sorted by timestamp ascending.
    Hub node identified by highest incoming edge count.
    """
    subgraph = get_subgraph(case_id)
    if not subgraph:
        raise HTTPException(status_code=404, detail=f"No graph data for case {case_id}")

    # Sort edges by timestamp
    edges = sorted(subgraph["edges"], key=lambda e: e.get("timestamp", ""))

    # Identify hub node (highest incoming edge count)
    in_count: dict[str, int] = {}
    for edge in edges:
        target = edge["target"]
        in_count[target] = in_count.get(target, 0) + 1

    hub_id = max(in_count, key=in_count.get) if in_count else None

    # Mark hub node
    nodes = []
    for node in subgraph["nodes"]:
        n = {**node}
        if n["id"] == hub_id:
            n["is_hub"] = True
        nodes.append(n)

    return {"nodes": nodes, "edges": edges, "hub_id": hub_id}
