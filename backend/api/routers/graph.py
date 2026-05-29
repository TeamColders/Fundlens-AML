from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException

from backend.db import neo4j as neo4j_db


logger = logging.getLogger(__name__)
router = APIRouter()

CYPHER_QUERY = """
MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account)
WHERE t.case_id = $case_id
RETURN a, t, b
"""


@router.get("/{case_id}")
def get_graph(case_id: str):
    with neo4j_db.get_session() as session:
        records = list(session.run(CYPHER_QUERY, case_id=case_id))

    if not records:
        raise HTTPException(status_code=404, detail="Case not found")

    nodes = {}
    incoming_counts = {}
    edges = []

    for record in records:
        a = record["a"]
        b = record["b"]
        t = record["t"]

        a_id = _node_id(a)
        b_id = _node_id(b)

        nodes.setdefault(a_id, _node_payload(a, a_id))
        nodes.setdefault(b_id, _node_payload(b, b_id))

        incoming_counts[b_id] = incoming_counts.get(b_id, 0) + 1

        edge = {
            "source": a_id,
            "target": b_id,
            "amount": t.get("amount") or t.get("value"),
            "timestamp": t.get("timestamp") or t.get("created_at"),
            "channel": t.get("channel"),
            "transaction_id": t.get("transaction_id") or t.element_id,
        }
        edges.append(edge)

    hub_id = max(incoming_counts, key=incoming_counts.get)
    for node_id, payload in nodes.items():
        payload["is_hub"] = node_id == hub_id

    edges.sort(key=_edge_sort_key)

    return {"nodes": list(nodes.values()), "edges": edges}


def _node_id(node):
    return node.get("account_id") or node.get("id") or node.element_id


def _node_payload(node, node_id: str):
    total_volume = node.get("total_volume") or node.get("amount")
    risk_level = node.get("risk_level") or _risk_from_volume(total_volume)
    return {
        "id": node_id,
        "label": node.get("label") or node_id,
        "risk_level": risk_level,
        "amount": total_volume,
        "account_type": node.get("account_type"),
        "is_hub": False,
        "is_dormant": bool(node.get("is_dormant")),
    }


def _risk_from_volume(total_volume):
    try:
        amount = float(total_volume)
    except (TypeError, ValueError):
        return "medium"
    if amount >= 10000000:
        return "high"
    if amount >= 1000000:
        return "medium"
    return "low"


def _edge_sort_key(edge):
    value = edge.get("timestamp")
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            return 0
    return 0
