# Implementation Guide

## The 5 AI prompts that write the hardest parts for you

These are the prompts where the implementation is genuinely complex. Paste these directly into Claude or ChatGPT to get working code.

**Prompt 1 - Complete FastAPI app with all routes wired:**
```text
Write a complete FastAPI application (backend/api/main.py) that:
- Mounts all routers: /api/alerts, /api/cases, /api/graph, /api/entities, /api/str, /api/analytics, /api/blockchain, /api/query, /api/score
- Configures CORS for localhost:5173 (the Vite dev server)
- Uses lifespan context manager to connect to Neo4j, PostgreSQL, and Redis on startup
- Includes a GET /api/health endpoint returning status of all connections
- Includes WebSocket endpoint /ws/alerts that pushes new alert notifications to the frontend in real time
- Uses python-dotenv to load .env file
- Runs on port 8000

The app should start with: uvicorn backend.api.main:app --reload --port 8000
```

**Prompt 2 - Graph data API endpoint:**
```text
Write a FastAPI endpoint GET /api/graph/{case_id} that:
1. Connects to Neo4j using the neo4j Python driver
2. Runs this Cypher query to extract the full subgraph for a case:
   MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account)
   WHERE t.case_id = $case_id
   RETURN a, t, b
3. Also fetches node metadata: account type, kyc_tier, is_dormant, total_volume
4. Formats the result as:
   {nodes: [{id, label, risk_level, amount, account_type, is_hub, is_dormant}],
    edges: [{source, target, amount, timestamp, channel, transaction_id}]}
5. Sorts edges by timestamp ascending
6. Identifies the hub node (highest incoming edge count) and marks it
7. Returns proper 404 if case not found
Include the full Cypher query as a constant at the top of the file.
```

**Prompt 3 - Real-time alert pipeline:**
```text
Write a Python script (backend/ingestion/alert_pipeline.py) that:

1. Continuously reads from a Kafka topic 'transactions.enriched'
2. For each transaction, queries Neo4j to check if it completes any of the 5 typology patterns (import from typology_queries.py)
3. If a pattern is detected:
   a. Calls the GNN scoring service at POST http://localhost:8001/score
   b. If GNN score > 0.70: creates an alert record in PostgreSQL
   c. Writes Block 1 (ALERT_CREATED) to the evidence chain
   d. Sends a WebSocket message to all connected frontend clients
4. Runs as a continuous loop with error handling and logging
5. Can be stopped gracefully with CTRL+C

The script should log: transactions processed/min, patterns detected, alerts created.
Run with: python -m backend.ingestion.alert_pipeline
```

**Prompt 4 - SSE streaming for STR generation:**
```text
Write a FastAPI endpoint POST /api/str/{case_id}/generate that uses Server-Sent Events to stream the STR generation progress to the frontend.

Stream these events in order:
1. {"stage": "analysing_pattern", "message": "Extracting subgraph from Neo4j...", "progress": 20}
2. {"stage": "compiling_evidence", "message": "Assembling case evidence...", "progress": 50}
3. {"stage": "drafting_narrative", "message": "LLM drafting STR narrative...", "progress": 75}
4. (call the actual LLM here - use asyncio to not block)
5. {"stage": "complete", "message": "STR ready for review", "progress": 100, "report": {full STR dict}}

Use FastAPI's StreamingResponse with media_type="text/event-stream".
Each SSE event: "data: {json}\n\n"
Include a keep-alive comment every 15 seconds: ": keep-alive\n\n"

The frontend hook should use EventSource API to consume this stream and update the three-step progress indicator (Analysing pattern -> Compiling evidence -> Drafting narrative).
```

**Prompt 5 - Connecting Sigma.js to real graph data:**
```text
Write a React component GraphVisualization that:

1. Accepts props: {caseId: string, onNodeClick: (nodeId: string) => void}
2. Uses the useGraphData(caseId) hook to fetch and format graph data
3. Renders using @react-sigma/core (Sigma.js React wrapper)
4. Applies these visual settings:
   - Dark background: #060C1E
   - Node renderer: circle with colored ring (ring color = risk level color)
   - Edge renderer: curved arrow with amount label
   - Camera: auto-fit to graph on load
5. Implements animateFlow() on mount:
   - Edges appear one by one with a 400ms delay in timestamp order
   - Currently highlighted edge glows teal
   - Completed edges stay at 40% opacity
6. On node hover: shows a tooltip with {account_id, risk_score, total_amount, is_dormant}
7. On node click: calls onNodeClick with the account_id (triggers entity profile panel)
8. Shows a loading spinner while data is fetching

Use @react-sigma/core, graphology, and graphology-layout-forceatlas2 for the layout.
Install: npm install @react-sigma/core graphology graphology-layout-forceatlas2
```

---

## Testing - run these after each week

```bash
# Week 1: verify graph is loaded correctly
python -c "
from backend.graph.neo4j_client import get_session
with get_session() as s:
    result = s.run('MATCH (a:Account) RETURN count(a) as count')
    print('Accounts:', result.single()['count'])
    result = s.run('MATCH ()-[t:TRANSFERRED_TO]->() WHERE t.is_fraud=true RETURN count(t) as count')
    print('Fraud edges:', result.single()['count'])
"

# Week 1: verify typology detection
python -c "
from backend.graph.typology_queries import detect_round_trip_layering
from backend.graph.neo4j_client import get_session
with get_session() as s:
    results = detect_round_trip_layering(s)
    print(f'Round-trip patterns found: {len(results)}')
    if results: print('First result:', results[0])
"

# Week 2: verify GNN scoring
curl -X POST http://localhost:8001/score \
  -H "Content-Type: application/json" \
  -d '{"case_id": "TEST-001", "subgraph": {"nodes": [], "edges": []}}'

# Week 3: verify STR generation
python -c "
import asyncio
from backend.llm.str_generator import generate_str
case = {'case_id': 'CASE-2847', 'typology_name': 'Round-trip Layering', 
        'total_amount': 4723000, 'accounts_count': 7, 'hop_count': 3,
        'duration_hours': 6.2, 'gnn_score': 0.94, 'typology_fatf_reference': 'Typology 12'}
result = asyncio.run(generate_str(case))
print('STR generated in:', result['generation_time_seconds'], 'seconds')
print(result['english_narrative'][:200])
"

# Week 4: verify full API
curl http://localhost:8000/api/health
curl http://localhost:8000/api/alerts
```

---

## Demo data script - run this to seed realistic demo data

```python
# Prompt:

"""
Write a Python script demo_seed.py that creates exactly the data shown in the FundLens screenshots:

Create these specific accounts and transactions so the demo matches the UI:

Account setup:
- ACC-0041: savings account, dormant 26 months, KYC Tier 2, PEP adjacent, owner: Rajesh Kumar
- ACC-0089: current account, high volume, identified as hub, owner: Shell entity
- ACC-0112, ACC-0203, ACC-0317, ACC-0455, ACC-0043: intermediary accounts

Transaction sequence (case CASE-2847 - Round-trip layering):
1. 09:14:03  External -> ACC-0041: INR 47,23,000 (activates dormant account)
2. 09:16:22  ACC-0041 -> ACC-0112: INR 7,80,000 NEFT
3. 09:16:22  ACC-0041 -> ACC-0203: INR 9,10,000 UPI  
4. 10:02:11  ACC-0112 -> ACC-0089: INR 7,80,000 NEFT
5. 10:02:11  ACC-0203 -> ACC-0089: INR 9,10,000 IMPS
6. 11:44:55  ACC-0089 -> ACC-0317: INR 8,40,000 NEFT
7. 11:44:55  ACC-0089 -> ACC-0455: INR 8,90,000 UPI
8. 15:28:07  ACC-0317 -> ACC-0043: INR 8,40,000 UPI  
9. 15:28:07  ACC-0455 -> ACC-0043: INR 8,90,000 IMPS

Mark all these transactions with case_id=CASE-2847, is_fraud=True, typology=round_trip_layering.

Also create CASE-2848 (Smurfing, 14 accounts, INR 23.1L) and 
CASE-2849 (Shell Company Flow, 5 accounts, INR 156.4L).

Load everything into Neo4j and PostgreSQL.
Print confirmation of what was created.
"""
```

---

## The order that matters

Run `docker-compose up -d` first and wait for all services to be healthy. Then run `demo_seed.py` to put the exact demo data in. Then start the FastAPI backend on port 8000 and the GNN inference service on port 8001. Then start your existing Vite frontend on port 5173. Point the axios client at `localhost:8000`.

The whole stack is Python + Neo4j + Kafka + React. You already have the frontend. The backend is four weeks of focused work. The prompts above will write 80 percent of the code. Your job is to wire the pieces together, fix the edge cases, and make the demo data match exactly what your Figma screens show.
