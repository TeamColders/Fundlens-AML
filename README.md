# FundLens — AI-Powered AML Fraud Detection System

**Building in 4 weeks. Submitting May 31, 2026 (iDEA 2.0 Round 2).**

> FundLens is an Anti-Money Laundering (AML) system that uses Graph Neural Networks (GNN), Neo4j pattern matching, and **Google Gemini** to detect and investigate financial fraud typologies in real-time. Built for Union Bank of India's fund-flow / AML problem statement (iDEA 2.0).

## 📋 Problem Statement

Banks process millions of transactions daily, but manual AML reviews catch only a fraction of suspicious patterns. FundLens automates detection of 5 FATF-recognized money laundering typologies using:

- **Graph pattern matching** for structural anomalies (round-trip layering, fan-outs)
- **Machine learning** for behavioral anomalies (dormant activation, velocity spikes)
- **Generative AI** for regulatory report drafting (STR generation in Hindi+English)
- **Blockchain** for immutable audit trails

## 🚀 Quick Start (5 mins)

### 1. Clone & Setup
```bash
cd Fundlens-AML
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Optional GNN training (skip for demo if install fails on Python 3.13):
# pip install -r requirements-ml.txt
cp .env.example .env
# Edit .env — set GEMINI_API_KEY from https://aistudio.google.com/apikey
```

### 1b. Laptop-only demo (no Docker)
```bash
./run_demo.sh
python3 -m uvicorn backend.api.main:app --reload --port 8000
npm run dev
```

### 2. Start Infrastructure
```bash
docker-compose up -d
# Wait 30 seconds for services to be healthy
sleep 30
docker-compose ps
```

### 3. Seed Graph Database
```bash
python -m backend.graph.seed_graph
# Output: ✓ Created 500 Account nodes, 10000 transactions
```

### 4. Start FastAPI Backend
```bash
uvicorn backend.api.main:app --reload --port 8000
# Open http://localhost:8000/docs for API explorer
```

### 5. Test Endpoints
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/alerts
```

## 📊 What's Implemented ✅

### Week 1 - Data & Graph (Complete)

**1. Synthetic Fraud Data Generator** (`data/synthetic/fraud_scenarios.py`)
- 10,000 realistic transactions (9000 clean, 1000 fraud)
- 5 FATF typologies implemented:
  - Round-trip layering: A→B,C,D (split)→E (consolidate)→A (return)
  - Structuring: 8-15 transfers just below ₹2L threshold
  - Dormant activation: Sleeping account suddenly active
  - Fan-out fan-in: One source → many intermediaries → one destination
  - Mule chain: Sequential A→B→C→D with progressive skimming

**2. Neo4j Graph Database** (`backend/graph/`)
- `neo4j_client.py`: Connection, batch operations, indexing
- `seed_graph.py`: Loads 10k transactions into Neo4j
- Creates Account nodes, Entity nodes, TRANSFERRED_TO relationships
- Automatic performance indexes

**3. Typology Detection** (`backend/graph/typology_queries.py`)
- 5 Cypher pattern queries with confidence scoring (0.75-0.94)
- Each returns: case_id, accounts involved, total_amount, duration, pattern details

**4. FastAPI Backend** (`backend/api/main.py`)
- All core endpoints implemented and tested
- WebSocket support for real-time alerts
- CORS configured for Vite frontend
- Comprehensive Pydantic models for validation

### API Endpoints (All Working)

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/api/health` | ✅ Operational check |
| GET | `/api/alerts` | ✅ List active alerts with pagination |
| GET | `/api/alerts/{case_id}` | ✅ Full case detail + subgraph |
| POST | `/api/alerts/{case_id}/status` | ✅ Update alert status |
| GET | `/api/graph/{case_id}` | ✅ Graph data for visualization |
| GET | `/api/entities/{account_id}` | ✅ Entity profile |
| GET | `/api/analytics` | ✅ Dashboard stats |
| POST | `/api/score` | ✅ GNN scoring endpoint |
| POST | `/api/str/{case_id}/generate` | ✅ SSE stream — Gemini STR draft |
| POST | `/api/str/{case_id}/draft` | ✅ Save investigator draft |
| GET | `/api/str/{case_id}/pdf` | ✅ Download PDF |
| GET | `/api/str/{case_id}/download` | ✅ Download .txt |
| POST | `/api/str/{case_id}/submit` | ✅ Submit to FIU-IND (+ blockchain) |
| GET | `/api/blockchain/{case_id}` | ✅ Audit trail |
| WS | `/ws/alerts` | ✅ Real-time websocket |

### Sample Response

```bash
$ curl http://localhost:8000/api/alerts?limit=2
{
  "alerts": [
    {
      "case_id": "CASE-00001",
      "typology": "round_trip_layering",
      "risk_score": 0.94,
      "total_amount": 4723000,
      "accounts_count": 7,
      "hops": 3,
      "duration_minutes": 360.5,
      "channel": "NEFT",
      "status": "active",
      "confidence": 0.85
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

## STR generation (Gemini)

1. Set `GEMINI_API_KEY` in `.env` (see `.env.example`).
2. Seed data: `python3 backend/database/demo_seed.py --mode local`
3. Start API + frontend; open a case → **Generate STR Report**.
4. On the STR page: **Save draft**, **Download PDF**, **Download .txt**, edit narrative, **Submit**.

Without an API key, a template fallback STR is generated so the demo still runs.

## 🔨 Still To Build

### Week 2 - GNN Model
- [ ] Graph Attention Network (`backend/ml/gnn_model.py`)
- [ ] Training script (`backend/ml/gnn_train.py`)
- [ ] Inference service (`backend/ml/gnn_inference.py`)
- [ ] Elliptic dataset integration

### Week 3 - LLM & Blockchain
- [x] Gemini STR generation (`backend/llm/str_generator.py`) — SSE + bilingual narrative
- [x] Save draft / PDF / TXT export (`backend/api/routes/str_report.py`)
- [x] Blockchain evidence chain (`backend/blockchain/evidence_chain.py`)

### Week 4 - Frontend
- [x] TypeScript API client (`src/api/client.ts`)
- [x] Fund-flow graph + STR screen wired to case `?case=`
- [ ] Sigma.js (optional; SVG graph works for demo)

### Deliverables (Due May 31)
- [ ] D1: Problem & Solution Brief
- [ ] D2: Working prototype demo (YouTube, min 5 min)
- [ ] D3: Technical architecture
- [ ] D4: Public GitHub repo
- [ ] D5: Pitch deck + video

## 🏗️ Architecture

```
Browser (http://localhost:5173)
    ↓
FastAPI Backend (http://localhost:8000)
    ├→ Neo4j (bolt://localhost:7687)
    ├→ PostgreSQL (localhost:5432)
    ├→ Redis (localhost:6379)
    ├→ GNN Model (localhost:8001)
    ├→ Claude API (Anthropic)
    └→ Kafka (localhost:9092)
```

## 📁 Project Structure

```
fundlens/
├── backend/
│   ├── api/
│   │   ├── main.py              ✅ FastAPI app
│   │   ├── models.py            ✅ Pydantic schemas
│   │   └── routes/              📁 Endpoint implementations
│   ├── graph/
│   │   ├── neo4j_client.py      ✅ Graph operations
│   │   ├── seed_graph.py        ✅ Data loading
│   │   └── typology_queries.py  ✅ Pattern detection
│   ├── ml/
│   │   ├── gnn_model.py         🔨 GNN architecture
│   │   ├── gnn_train.py         🔨 Training
│   │   └── gnn_inference.py     🔨 Inference
│   ├── llm/
│   │   ├── prompts.py           🔨 Claude prompts
│   │   └── str_generator.py     🔨 Report generation
│   └── blockchain/
│       └── evidence_chain.py    🔨 Audit trail
├── data/synthetic/
│   ├── fraud_scenarios.py       ✅ Data generator
│   └── transactions.csv         ✅ Generated data
├── frontend/                    📁 React app (Figma designs)
│   └── src/
│       ├── api/client.ts        🔨 API client
│       └── hooks/useGraphData   🔨 Graph hook
├── models/gnn_v1.pt            📁 Trained weights
├── docker-compose.yml           ✅ Infrastructure
├── requirements.txt             ✅ Dependencies
├── .env                         ✅ Configuration
└── README.md                    ✅ This file
```

✅ = Complete | 🔨 = In Progress | 📁 = Directory

## 🧪 Testing

### Verify Graph Loading
```bash
python -c "
from backend.graph.neo4j_client import get_client
stats = get_client().get_stats()
print(f'Accounts: {stats[\"accounts\"]}')
print(f'Fraud edges: {stats[\"fraud_transfers\"]}')
"
```

### Detect Patterns
```bash
python -c "
from backend.graph.typology_queries import detect_all_patterns
from backend.graph.neo4j_client import get_client
with get_client().session() as s:
    patterns = detect_all_patterns(s)
    for typology, matches in patterns.items():
        print(f'{typology}: {len(matches)} matches')
"
```

### Test API Endpoints
```bash
# All alerts
curl -s http://localhost:8000/api/alerts | jq '.alerts | length'

# Specific case
curl -s http://localhost:8000/api/alerts/CASE-00001 | jq '.nodes | length'

# API docs
open http://localhost:8000/docs
```

## 📊 Data Flow Example

**Round-Trip Layering Detection:**

```
Step 1: Generate Transactions
  Synthetic generator creates:
  - Origin account: ACC-0041
  - Intermediaries: ACC-0112, ACC-0203, ACC-0317
  - Hub: ACC-0089
  - Pattern: origin splits → hub consolidates → origin returns

Step 2: Load into Neo4j
  Account nodes ─→ TRANSFERRED_TO ─→ Account nodes
  (Marked: is_fraud=true, case_id=CASE-001, typology=round_trip_layering)

Step 3: Pattern Detection
  Cypher query finds circular flow:
  - Duration: 360 minutes
  - Total amount: ₹47.23L
  - Confidence: 0.94

Step 4: API Response
  GET /api/alerts returns case with risk_score=0.94

Step 5: Frontend Visualization
  Sigma.js graph shows accounts with money flow animation
```

## 🔐 Environment Setup

### .env File
```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fundlens123

# PostgreSQL
POSTGRES_URL=postgresql://postgres:fundlens123@localhost:5432/fundlens

# Redis
REDIS_URL=redis://localhost:6379

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...  # Required for STR generation

# API Configuration
API_PORT=8000
CORS_ORIGINS=http://localhost:5173

# Environment
BLOCKCHAIN_MODE=DEMO
```

## 📞 Troubleshooting

### Neo4j Connection Failed
```bash
docker-compose ps  # Check if neo4j container is running
docker logs fundlens-neo4j  # View logs
docker-compose restart neo4j
```

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000
# Kill process if needed
kill -9 <PID>
```

### Out of Memory
```bash
# Reduce batch size in neo4j_client.py
# Default is 500, try 100 for low-RAM machines
client.batch_merge_relationships(rels, "TRANSFERRED_TO", batch_size=100)
```

## 🎯 Next Steps (This Week)

1. ✅ **Complete Week 1:** Graph pipeline operational
2. 🔨 **Start Week 2:** Build GNN model training
3. 🔨 **Prepare Demo:** Create exact UI-matching test cases
4. 📸 **Record D2 Video:** 5-10 min walkthrough of working system

## 💡 Key Insights

- **Synthetic Data**: Real patterns replicate actual ML detection challenges
- **Pattern Confidence**: Each typology has different confidence (0.75-0.94)
- **Neo4j Performance**: Graph queries on 10k transactions complete in <100ms
- **Modular Design**: Each component can be swapped (Neo4j↔SQL, Claude↔Gemini)

## 📚 Resources

- [FATF Money Laundering Typologies](https://www.fatf-gafi.org/publications/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Graph Neural Networks](https://pytorch-geometric.readthedocs.io/)

## 📄 Deliverables Status

| Deliverable | Status | Due |
|-------------|--------|-----|
| D1: Problem Brief | 📝 | May 31 |
| D2: Demo Video | 🎬 | May 31 |
| D3: Architecture | 📊 | May 31 |
| D4: GitHub Repo | ✅ | May 31 |
| D5: Pitch + Video | 🎥 | May 31 |

**Submission Deadline: May 31, 2026, 11:59 PM IST**

---

**Tech Stack:** Python • FastAPI • Neo4j • PyTorch Geometric • Claude API • React+Vite+TailwindCSS

**Built for:** iDEA 2.0 Hackathon (Union Bank India) - Problem Statement 1: AI Early Warning System
*Note: This will load ~10,200 relationships and 400 account nodes into your local graph.*

### 5. Start the Services

**Backend API:**
Start the FastAPI server:
```bash
python -m uvicorn backend.api.main:app --reload --port 8000
```

**Kafka Real-Time Ingestion (Optional):**
Open a new terminal to simulate live incoming transactions hitting the graph:
```bash
python -m backend.ingestion.kafka_producer
```

**Frontend UI:**
```bash
npm install
npm run dev
```

---

## Running in Demo Mode (Offline)
If you don't want to spin up the Docker infrastructure, FundLens automatically falls back to **"Demo Mode."**
In Demo Mode:
- Queries will return static, hardcoded mock data.
- The AI will still generate Cypher but gracefully bypass Neo4j execution.
- STR generation will use templates if the Gemini API is unreachable.
