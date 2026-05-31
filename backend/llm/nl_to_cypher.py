import os
from google import genai

async def nl_to_cypher(query: str) -> str:
    """
    Converts a natural language query into a Neo4j Cypher query using Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client()

    system_prompt = """
    You are a Neo4j Cypher expert for AML (Anti-Money Laundering) investigations.
    The database schema is as follows:
    - Nodes: 
      - Account: properties include account_id, account_type, status, kyc_tier, created_date, last_active_date, declared_income, home_branch, is_dormant
      - Entity: properties include entity_id, name_hash, pan_hash, mobile_hash, kyc_tier
    - Relationships: 
      - (Account)-[:TRANSFERRED_TO {transaction_id, amount, currency, timestamp, channel, branch_code, reference_number, is_fraud, typology}]->(Account)
      - (Account)-[:CONTROLLED_BY]->(Entity)
    
    CRITICAL INSTRUCTIONS:
    1. Return ONLY the raw Cypher query string. NO EXPLANATIONS. NO MARKDOWN (e.g. ```cypher). 
    2. Your response must begin with MATCH, WITH, or CALL.
    3. Always append 'LIMIT 50' to the query unless the user specifically asks for a different limit.
    4. Provide valid Neo4j Cypher only. Do NOT use 'OR' between two separate relationship patterns like '(a)-[]->(b) OR (b)-[]->(a)'. Instead, use undirected relationships like '(a)-[]-(b)' or a UNION clause.
    """

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=query,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.0
        )
    )

    print("=== RAW GEMINI RESPONSE ===")
    print(repr(response.text))
    print("===========================")

    cypher_query = response.text.strip()
    
    # Extract cypher from markdown if present
    import re
    match = re.search(r'```(?:cypher)?(.*?)```', cypher_query, re.DOTALL)
    if match:
        cypher_query = match.group(1).strip()
    else:
        # If no markdown blocks, maybe it's just raw cypher, but if it starts with chat, try to extract from MATCH
        if "MATCH" in cypher_query.upper():
            cypher_query = "MATCH" + cypher_query.upper().split("MATCH", 1)[1]
            # preserve original casing where possible
            idx = response.text.upper().find("MATCH")
            if idx != -1:
                cypher_query = response.text[idx:].strip()

    # Safety check to prevent destructive queries
    write_ops = ["CREATE", "MERGE", "SET ", "DELETE", "REMOVE", "DROP"]
    cypher_upper = cypher_query.upper()
    for op in write_ops:
        if op in cypher_upper:
            raise ValueError(f"Generated Cypher contains unsafe operation '{op}'. Query rejected: {cypher_query}")

    return cypher_query
