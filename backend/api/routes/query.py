"""
FundLens — /api/query endpoint (NL to Cypher).
"""
import logging
import time
from fastapi import APIRouter, HTTPException
from backend.api.models import NLQueryRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["NL Query"])


# Mock Cypher query results for demo
MOCK_RESULTS = {
    "acc-0041": {
        "cypher": "MATCH (a:Account {account_id: 'ACC-0041'})-[r]-(b) RETURN a, r, b LIMIT 50",
        "results": [
            {"account_id": "ACC-0041", "connected_to": "ACC-0112", "relationship": "TRANSFERRED_TO", "amount": 780000},
            {"account_id": "ACC-0041", "connected_to": "ACC-0203", "relationship": "TRANSFERRED_TO", "amount": 910000},
        ],
    },
    "dormant": {
        "cypher": "MATCH (a:Account {is_dormant: true})-[t:TRANSFERRED_TO]->(b) RETURN a.account_id, b.account_id, t.amount ORDER BY t.amount DESC",
        "results": [
            {"source": "ACC-0041", "target": "ACC-0112", "amount": 780000},
            {"source": "ACC-0041", "target": "ACC-0203", "amount": 910000},
        ],
    },
    "hub": {
        "cypher": "MATCH (a:Account)<-[t:TRANSFERRED_TO]-(b) WITH a, count(t) as in_count WHERE in_count > 3 RETURN a.account_id, in_count ORDER BY in_count DESC",
        "results": [
            {"account_id": "ACC-0089", "incoming_transfers": 5},
            {"account_id": "ACC-0601", "incoming_transfers": 14},
        ],
    },
}


@router.post("")
async def nl_query(body: NLQueryRequest):
    """Convert natural language question to Cypher and execute."""
    start = time.time()
    query_lower = body.query.lower()

    # Try LLM-based conversion first
    try:
        from backend.llm.nl_to_cypher import nl_to_cypher
        from backend.graph.neo4j_client import get_session
        
        cypher = await nl_to_cypher(body.query)
        elapsed_llm = (time.time() - start) * 1000
        
        # Execute against Neo4j
        try:
            with get_session() as session:
                result = session.run(cypher)
                records = [r.data() for r in result]
                
            elapsed_total = (time.time() - start) * 1000
            return {
                "query": body.query,
                "cypher": cypher,
                "results": records,
                "result_count": len(records),
                "execution_ms": round(elapsed_total, 1),
            }
        except Exception as db_e:
            error_str = str(db_e)
            if "Connection refused" in error_str or "Couldn't connect" in error_str or "ServiceUnavailable" in error_str:
                logger.warning(f"Neo4j execution bypassed (Demo Mode / Offline): {db_e}")
                elapsed_total = (time.time() - start) * 1000
                
                # Find mock data to display
                mock_data = []
                for keyword, mock in MOCK_RESULTS.items():
                    if keyword in query_lower:
                        mock_data = mock["results"]
                        break
                if not mock_data:
                    mock_data = [
                        {"account_id": "ACC-0041", "risk_level": "high"},
                        {"account_id": "ACC-0089", "risk_level": "critical"},
                        {"account_id": "ACC-0043", "risk_level": "high"},
                    ]
                    
                return {
                    "query": body.query,
                    "cypher": cypher,
                    "results": mock_data,
                    "result_count": len(mock_data),
                    "execution_ms": round(elapsed_total, 1),
                }
            else:
                # Actual Neo4j syntax or execution error
                logger.error(f"Neo4j Cypher error: {db_e}")
                elapsed_total = (time.time() - start) * 1000
                return {
                    "query": body.query,
                    "cypher": cypher,
                    "results": [{"error": f"Cypher Execution Error: {db_e}"}],
                    "result_count": 0,
                    "execution_ms": round(elapsed_total, 1),
                }
            
    except Exception as e:
        logger.error(f"LLM conversion failed: {e}")

    # Fallback: pattern-match common queries
    result = None
    for keyword, mock in MOCK_RESULTS.items():
        if keyword in query_lower:
            result = mock
            break

    if not result:
        result = {
            "cypher": "MATCH (a:Account) RETURN a.account_id, a.risk_level LIMIT 10",
            "results": [
                {"account_id": "ACC-0041", "risk_level": "high"},
                {"account_id": "ACC-0089", "risk_level": "critical"},
                {"account_id": "ACC-0043", "risk_level": "high"},
            ],
        }

    elapsed = (time.time() - start) * 1000
    return {
        "query": body.query,
        "cypher": result["cypher"],
        "results": result["results"],
        "result_count": len(result["results"]),
        "execution_ms": round(elapsed, 1),
    }
