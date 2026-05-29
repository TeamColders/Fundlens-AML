from typing import List


PATTERNS = [
    {
        "name": "Round-trip Layering",
        "query": (
            "MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account) "
            "WHERE t.case_id = $case_id RETURN count(t) as cnt"
        ),
    },
    {
        "name": "Smurfing",
        "query": (
            "MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account) "
            "WHERE t.case_id = $case_id AND t.amount < 100000 RETURN count(t) as cnt"
        ),
    },
    {
        "name": "Shell Company Flow",
        "query": (
            "MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account) "
            "WHERE t.case_id = $case_id RETURN count(t) as cnt"
        ),
    },
    {
        "name": "Rapid Movement",
        "query": (
            "MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account) "
            "WHERE t.case_id = $case_id RETURN count(t) as cnt"
        ),
    },
    {
        "name": "Structuring",
        "query": (
            "MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account) "
            "WHERE t.case_id = $case_id RETURN count(t) as cnt"
        ),
    },
]


def detect_patterns(session, transaction: dict) -> List[str]:
    case_id = transaction.get("case_id")
    if not case_id:
        return []

    matched = []
    for pattern in PATTERNS:
        result = session.run(pattern["query"], case_id=case_id).single()
        if result and result.get("cnt", 0) > 0:
            matched.append(pattern["name"])
    return matched
