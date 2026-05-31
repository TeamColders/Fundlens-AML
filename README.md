# FundLens — AI-Powered AML Fraud Detection System

**iDEA 2.0 Round 2 · Union Bank of India · Fund flow / AML**

FundLens is an Anti-Money Laundering (AML) platform that combines graph analytics, GNN scoring, **Google Gemini**, and a cryptographic evidence chain to detect and investigate fraud typologies in real time.

## Problem statement

Banks process millions of transactions daily, but manual AML reviews catch only a fraction of suspicious patterns. FundLens automates detection of FATF-recognized typologies using:

- **Graph pattern matching** — round-trip layering, fan-out/fan-in, mule chains
- **Machine learning** — dormant activation, velocity spikes, hub accounts
- **Generative AI** — bilingual STR drafting (English + Hindi)
- **Evidence audit trail** — append-only SHA-256 chain per case

---

## Run the project

### First-time setup

```bash
cd Fundlens-AML

# Python environment (pick one)
python3 -m venv venv && source venv/bin/activate
# OR: conda activate fundlens

pip install -r requirements.txt
# Optional GNN / training stack (large; skip for demo):
# pip install -r requirements-ml.txt

cp .env.example .env
# Edit .env — set GEMINI_API_KEY from https://aistudio.google.com/apikey

# Seed demo cases into SQLite (no Docker required)
python3 backend/database/demo_seed.py --mode local

# Frontend dependencies
npm install
```

Shortcut (seeds data and prints next steps):

```bash
chmod +x run_demo.sh
./run_demo.sh
```

### Run every time (two terminals)

**Terminal 1 — API**

```bash
cd Fundlens-AML
source venv/bin/activate   # or: conda activate fundlens
python3 -m uvicorn backend.api.main:app --reload --port 8000
```

**Terminal 2 — UI**

```bash
cd Fundlens-AML
npm run dev
```

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | React app (Vite proxies `/api` → port 8000) |
| http://localhost:8000/docs | Swagger API explorer |
| http://localhost:8000/api/health | Health check |

Quick checks:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/alerts
curl http://localhost:8000/api/analytics
```

### Using the UI

1. Open **http://localhost:5173**
2. Select a case on the **Investigation Dashboard** (case is stored in URL as `?case=`)
3. Use the bottom nav: Graph, STR, Entity, Analytics, AI Query, Audit Trail, Configuration, Mobile

---

## Optional: full stack (Neo4j + Postgres + Kafka)

For graph DB, Postgres batch ingest, and Kafka pipeline:

```bash
docker compose up -d
sleep 30
docker compose ps

python3 -m backend.graph.seed_graph
python3 backend/database/demo_seed.py --mode local

# Then start API + frontend as above
```

Neo4j Browser: http://localhost:7474 (`neo4j` / `fundlens123`)

---

## Laptop-only demo (no Docker)

If Neo4j or Postgres are unavailable, the API **automatically falls back** to:

| Store | File | Purpose |
|-------|------|---------|
| Cases / transactions | `fundlens_demo.db` | Alert queue, subgraphs, entity profiles |
| Evidence chain | `fundlens_evidence.db` | Audit trail blocks |
| Admin config | `fundlens_config.db` | Thresholds, FIU settings, users |

- NL Query uses **SQL + Gemini** when Neo4j is down
- STR generation uses a **template fallback** if `GEMINI_API_KEY` is missing

Delete `fundlens_evidence.db` to reset a corrupted audit chain; it rebuilds on next visit.

---

## STR generation (Gemini)

1. Set `GEMINI_API_KEY` and `GEMINI_STR_MODEL=gemini-2.0-flash` in `.env` (avoid `flash-lite` on free tier — often quota 0).
2. Select a case → **Generate STR Report**
3. **Save draft**, **Download PDF**, **Download .txt**, **Submit** (writes evidence block)

Restart uvicorn after changing `.env`.

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health |
| GET | `/api/alerts` | Alert list |
| GET | `/api/alerts/{case_id}` | Case detail + subgraph |
| POST | `/api/alerts/{case_id}/status` | Update status |
| GET | `/api/graph/{case_id}` | Graph for visualization |
| GET | `/api/entities/{account_id}` | Entity profile |
| POST | `/api/entities/{account_id}/watchlist` | Watchlist action |
| GET | `/api/analytics` | Dashboard KPIs |
| POST | `/api/query` | Natural-language query |
| POST | `/api/str/{case_id}/generate` | SSE — Gemini STR |
| POST | `/api/str/{case_id}/draft` | Save STR draft |
| GET | `/api/str/{case_id}/pdf` | Download PDF |
| POST | `/api/str/{case_id}/submit` | Submit STR + blockchain |
| GET | `/api/blockchain/{case_id}` | Evidence chain |
| GET | `/api/blockchain/{case_id}/verify` | Verify chain |
| GET | `/api/blockchain/{case_id}/export` | Export JSON |
| GET | `/api/config` | Platform configuration |
| PATCH | `/api/config/thresholds` | Save detection thresholds |
| GET | `/api/config/audit-log` | Config audit log |
| GET | `/api/mobile/dashboard` | Mobile alert feed |
| POST | `/api/mobile/alerts/{case_id}/acknowledge` | Mobile investigate |
| WS | `/ws/alerts` | Real-time alerts |

---

## Architecture

```
Browser (http://localhost:5173)
    ↓  /api proxy
FastAPI (http://localhost:8000)
    ├→ Neo4j          (optional — bolt://localhost:7687)
    ├→ PostgreSQL     (optional — falls back to SQLite)
    ├→ SQLite demo    fundlens_demo.db / fundlens_evidence.db / fundlens_config.db
    ├→ Google Gemini  STR + NL query + NL-to-Cypher
    └→ Kafka          (optional — ingestion pipeline)
```

---

## Project structure

```
Fundlens-AML/
├── backend/
│   ├── api/main.py              FastAPI app + lifespan
│   ├── api/routes/              alerts, graph, str, blockchain, config, mobile, query, …
│   ├── blockchain/              evidence_chain.py, bootstrap.py
│   ├── database/                demo_data.py, demo_seed.py, config_store.py, query_engine.py
│   ├── graph/                   neo4j_client.py, seed_graph.py, typology_queries.py
│   ├── llm/                     str_generator.py, prompts.py, str_pdf.py
│   └── ml/                      gnn_model.py (optional — requirements-ml.txt)
├── src/                         React + Vite UI
│   ├── api/client.ts
│   └── app/pages/               Dashboard, Graph, STR, Analytics, NL Query, Audit, Admin, Mobile
├── data/                        demo_seed.json, case JSON, synthetic generators
├── requirements.txt             Core API (Python 3.11–3.14)
├── requirements-ml.txt          Optional PyTorch / GNN
├── run_demo.sh                  Seed SQLite + print run commands
├── docker-compose.yml           Neo4j, Postgres, Kafka, Redis
└── .env.example
```

---

## Environment variables

Copy `.env.example` to `.env`:

```env
# Neo4j (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fundlens123

# PostgreSQL (optional)
POSTGRES_URL=postgresql://postgres:fundlens123@localhost:5432/fundlens

# Gemini — STR + NL query
GEMINI_API_KEY=your_key_here
GEMINI_STR_MODEL=gemini-2.0-flash

# Kafka / Redis (optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379

# Evidence chain (optional overrides)
# FUNDLENS_BLOCKCHAIN_MODE=demo
# FUNDLENS_EVIDENCE_DB=fundlens_evidence.db
# FUNDLENS_CONFIG_DB=fundlens_config.db
```

---

## Troubleshooting

**Port 8000 in use**

```bash
lsof -i :8000
kill -9 <PID>
```

**No alerts in UI**

```bash
python3 backend/database/demo_seed.py --mode local
curl http://localhost:8000/api/alerts
```

**Gemini STR shows template fallback**

- Confirm `GEMINI_API_KEY` in `.env`
- Use `GEMINI_STR_MODEL=gemini-2.0-flash` (not `flash-lite`)
- Restart uvicorn; wait ~60s after 429 quota errors before retrying

**Neo4j connection failed**

```bash
docker compose ps
docker compose restart neo4j
```

API continues in SQLite demo mode without Neo4j.

---

## Deployment (D2 live URL)

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for Render, Docker, and Vercel instructions.

Quick Docker test:

```bash
docker build -t fundlens .
docker run --rm -p 8000:8000 -e GEMINI_API_KEY=your_key fundlens
# → http://localhost:8000 (UI + API)
```

---

## Optional: Kafka ingestion

```bash
python3 -m backend.ingestion.kafka_producer   # simulate live transactions
python3 -m backend.ingestion.alert_pipeline   # GNN scoring (requires requirements-ml.txt)
```

---

## Tech stack

Python · FastAPI · Neo4j · SQLite · Google Gemini · React · Vite · Tailwind CSS · PyTorch Geometric (optional)

**Submission deadline:** May 31, 2026, 11:59 PM IST
