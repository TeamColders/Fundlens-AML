"""
Enrich case subgraphs for fund-flow visualization.
Marks origin/hub nodes and ensures all transaction edges are included.
"""
from __future__ import annotations

from typing import Any, Optional


def _volume_in(edges: list[dict], account_id: str) -> float:
    return sum(float(e.get("amount") or 0) for e in edges if e.get("target") == account_id)


def enrich_subgraph(
    subgraph: dict,
    accounts: Optional[list[dict]] = None,
) -> dict:
    """
    Add is_origin, is_hub, is_dormant, risk_level on nodes.
    Include EXTERNAL when present in edges.
    """
    accounts = accounts or []
    account_by_id = {a["account_id"]: a for a in accounts}

    edges = list(subgraph.get("edges") or [])
    nodes_map: dict[str, dict] = {}

    for raw in subgraph.get("nodes") or []:
        nid = raw.get("id") or raw.get("account_id")
        if not nid:
            continue
        nodes_map[nid] = {
            **raw,
            "id": nid,
            "label": raw.get("label") or nid,
            "is_hub": bool(raw.get("is_hub")),
            "is_origin": bool(raw.get("is_origin")),
            "is_dormant": bool(raw.get("is_dormant")),
        }

    for edge in edges:
        for key in ("source", "target"):
            aid = edge.get(key)
            if not aid or aid in nodes_map:
                continue
            acc = account_by_id.get(aid)
            nodes_map[aid] = {
                "id": aid,
                "label": aid,
                "risk_level": acc.get("risk_level", "medium") if acc else "medium",
                "amount": float(acc.get("declared_income") or 0) if acc else 0,
                "account_type": acc.get("account_type", "savings") if acc else "savings",
                "is_hub": False,
                "is_origin": False,
                "is_dormant": bool(int(acc.get("is_dormant") or 0)) if acc else False,
            }

    if any(e.get("source") == "EXTERNAL" or e.get("target") == "EXTERNAL" for e in edges):
        nodes_map["EXTERNAL"] = {
            "id": "EXTERNAL",
            "label": "External",
            "risk_level": "medium",
            "amount": 0,
            "account_type": "external",
            "is_hub": False,
            "is_origin": False,
            "is_dormant": False,
            "is_external": True,
        }

    in_count: dict[str, int] = {}
    out_count: dict[str, int] = {}
    for edge in edges:
        src, tgt = edge.get("source"), edge.get("target")
        if tgt:
            in_count[tgt] = in_count.get(tgt, 0) + 1
        if src:
            out_count[src] = out_count.get(src, 0) + 1

    internal_ids = [aid for aid in nodes_map if aid != "EXTERNAL"]
    hub_id: Optional[str] = None
    if internal_ids:
        # Hub = high inbound AND outbound (consolidation point), not just terminal sink
        hub_id = max(
            internal_ids,
            key=lambda aid: (
                in_count.get(aid, 0),
                out_count.get(aid, 0),
                _volume_in(edges, aid),
            ),
        )

    external_in = [e["target"] for e in edges if e.get("source") == "EXTERNAL"]
    zero_in = [aid for aid in internal_ids if in_count.get(aid, 0) == 0]
    if external_in:
        origin_id = external_in[0]
    elif zero_in:
        origin_id = zero_in[0]
    else:
        origin_id = min(internal_ids, key=lambda aid: in_count.get(aid, 999))

    for aid, node in nodes_map.items():
        acc = account_by_id.get(aid)
        if acc:
            node["risk_level"] = acc.get("risk_level") or node.get("risk_level", "medium")
            node["account_type"] = acc.get("account_type") or node.get("account_type", "savings")
            node["is_dormant"] = bool(acc.get("is_dormant"))
        node["is_hub"] = aid == hub_id
        node["is_origin"] = aid == origin_id

    sorted_edges = sorted(edges, key=lambda e: e.get("timestamp") or "")

    return {
        "nodes": list(nodes_map.values()),
        "edges": sorted_edges,
        "hub_id": hub_id,
        "origin_id": origin_id,
    }


def build_subgraph_from_transactions(
    transactions: list[dict],
    accounts: list[dict],
) -> dict:
    """Build a subgraph dict from DB transaction + account rows."""
    edges = []
    for t in transactions:
        edges.append({
            "source": t["sender"],
            "target": t["receiver"],
            "amount": float(t["amount"]),
            "timestamp": (
                t["timestamp"].isoformat()
                if hasattr(t["timestamp"], "isoformat")
                else str(t.get("timestamp") or "")
            ),
            "channel": t.get("channel", "NEFT"),
            "transaction_id": t.get("transaction_id", ""),
        })

    node_ids = set()
    for e in edges:
        node_ids.add(e["source"])
        node_ids.add(e["target"])

    nodes = []
    account_by_id = {a["account_id"]: a for a in accounts}
    for aid in node_ids:
        if aid == "EXTERNAL":
            continue
        acc = account_by_id.get(aid)
        nodes.append({
            "id": aid,
            "label": aid,
            "risk_level": acc.get("risk_level", "medium") if acc else "medium",
            "amount": float(acc.get("declared_income") or 0) if acc else 0,
            "account_type": acc.get("account_type", "savings") if acc else "savings",
            "is_hub": False,
            "is_origin": False,
            "is_dormant": bool(int(acc.get("is_dormant") or 0)) if acc else False,
        })

    return enrich_subgraph({"nodes": nodes, "edges": edges}, accounts)
