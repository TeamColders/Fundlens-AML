
  # FundLens - Complete Technical Solution

## The core insight that drives everything

Most AML systems think in rows. A transaction comes in, it's checked against a set of rules, and an alert fires or it doesn't. This is fundamentally broken because money laundering is not a per-transaction crime - it is a per-pattern crime. Fraudsters exploit the gap between what any single transaction looks like (normal) and what a sequence of transactions across multiple accounts looks like (criminal). FundLens closes that gap by making the graph - not the transaction - the atomic unit of analysis.

---

## Layer 1 - Data Ingestion and Real-Time Streaming

The system needs to ingest transactions from every channel a bank operates: Core Banking System (CBS, typically Infosys Finacle or TCS BaNCS at Indian PSBs), RTGS, NEFT, IMPS, UPI, SWIFT for cross-border wires, card networks (Visa/Mastercard authorisation logs), loan disbursement systems, and fixed deposit systems. Each of these systems has a different data format, a different latency, and a different update frequency.

Apache Kafka sits at the entry point as the universal event bus. Every transaction, regardless of source, gets normalised into a canonical JSON event schema and published to a Kafka topic. The schema captures: sender account ID, receiver account ID, amount, currency, timestamp, channel, branch code, reference number, and a set of enrichment fields that get populated downstream. Kafka handles hundreds of thousands of events per second with sub-100ms latency, which is essential - money moves fast and so must detection.

Apache Flink processes the Kafka streams in real time. Flink's stateful stream processing is what allows FundLens to do things like "detect if account A has received more than ₹50L across more than 5 counterparties in the past 6 hours" - a query that spans time and multiple events - without ever writing anything to a database first. Flink maintains in-memory state windows (sliding windows of 1 hour, 6 hours, 24 hours, 7 days) and computes aggregate features on the fly. These aggregated features - velocity, counterparty count, average transaction size, deviation from historical baseline - are what feed the ML models downstream.

One important architectural choice here: Flink also runs the entity resolution step. The same person might appear as "Rajesh Kumar," "R. Kumar," "RAJESH K," and "RK" across different systems. A lightweight fuzzy-matching model (based on Jaro-Winkler distance plus phone/PAN cross-reference) resolves these to a canonical entity ID before the data enters the graph. This is critical - without it, the graph fractures along data quality lines and patterns become invisible.

---

## Layer 2 - The Knowledge Graph

This is the heart of FundLens. Every entity (account, person, company, branch, device, IP address) becomes a node. Every interaction (transaction, login, account opening, beneficiary addition, address change) becomes a typed edge. The result is a continuously updating knowledge graph that represents the full financial reality of the bank - not a snapshot, but a living structure.

Neo4j is the graph database. The choice over relational databases is deliberate and important: in a relational system, tracing a fund flow across 7 accounts requires 7 JOIN operations across massive transaction tables. In Neo4j, it is a single graph traversal query that runs in milliseconds because the relationships are physically stored alongside the nodes - there is no JOIN penalty. A query like "find all accounts reachable from Account A within 3 hops where the cumulative transferred amount exceeds ₹20L in the last 48 hours" takes under 200 milliseconds on a properly indexed Neo4j instance with tens of millions of nodes.

The schema has several node types: `Account` (with properties: account number, type, status, KYC tier, creation date, last active date, declared income, home branch), `Entity` (person or company, with PAN, Aadhaar hash, mobile, address), `Device` (mobile device ID, browser fingerprint), `IPAddress`, `Branch`, and `ExternalCounterparty` (for SWIFT/cross-border nodes). Edge types include: `TRANSFERRED_TO` (with amount, timestamp, channel), `CONTROLLED_BY` (account to entity), `LOGGED_IN_FROM` (account to device/IP), `RELATED_TO` (for corporate ownership, family linkage from KYC data), and `SHARES_ADDRESS_WITH`.

The multi-relational nature of this graph is what enables FundLens to detect patterns that pure transaction analysis cannot. For example: two accounts that have never transacted with each other, but both log in from the same device and both received money from the same dormant account - that device co-occurrence is invisible in a transaction table but obvious in the graph.

For high-throughput graph writes, FundLens uses Neo4j's APOC library for batch upserts and maintains a write-behind cache using Redis to smooth out Kafka burst loads. The graph runs on a primary-secondary cluster with read replicas serving the investigator UI queries without impacting write throughput.

---

## Layer 3 - The Fraud Detection Engine

This is the three-sublayer AI core of the system.

### Sublayer 3a - Rule-Based Typology Engine

Before any ML, FundLens runs a deterministic pattern matcher against 12 pre-coded fraud typologies derived from FATF guidance, FIU-IND advisories, and RBI circular typologies. These are implemented as Cypher queries (Neo4j's graph query language) that run continuously against the live graph:

**Round-trip layering** is detected by finding cyclic paths in the graph - any path of length 3 to 7 where the start and end node are the same entity (or controlled by the same entity), completed within a 72-hour window, with cumulative value above ₹10L.

**Structuring (smurfing)** is detected by finding a single source account that has transferred money to more than 8 distinct counterparties within 24 hours, where each individual transfer is below the ₹2L PMLA reporting threshold but the aggregate exceeds ₹10L.

**Dormant account activation** is detected by a property-based rule: any account with zero transactions for 180+ days that receives an inward transfer above ₹5L and makes an outward transfer within 48 hours is flagged.

**Fan-out/fan-in** is a graph structural pattern - one source node fans out to N intermediate nodes, all of which then transfer to a single destination node within a defined time window. This is the classic funnel structure for laundering.

**PEP (Politically Exposed Person) linkage** uses the entity relationship graph - if a flagged account has a `RELATED_TO` edge (directly or within 2 hops) to a PEP entity loaded from a curated PEP database (Dow Jones, WorldCheck, or the Indian government's own PEP registry), all its transactions are elevated to enhanced monitoring.

These rule-based queries run as Flink jobs against the streaming graph updates - whenever a new edge is added to the graph, the relevant pattern queries re-evaluate in milliseconds. The result is a near-zero-latency first filter.

### Sublayer 3b - Graph Neural Network Scoring

Rule-based detection has a fundamental ceiling: it catches known patterns. The GNN catches unknown ones.

The GNN is implemented using PyTorch Geometric (PyG), which is built specifically for learning on graph-structured data. The architecture is a Graph Attention Network (GAT) with 4 attention heads and 3 message-passing layers. Here is what it does, conceptually: for any given subgraph (a cluster of accounts and their recent transactions), the GAT learns to assign a fraud probability score by aggregating information across the neighbourhood of each node. Each node "looks at" its neighbours, weighs their features by a learned attention coefficient (hence "attention"), and updates its own representation accordingly. After 3 rounds of this message passing, the node representations encode information from up to 3 hops away - which is exactly the right scale for detecting layering patterns.

The node features fed to the GNN include: account age, KYC tier, historical average transaction size, velocity in the last 24/7-day window, entropy of counterparty distribution (high entropy = many different counterparties = potential structuring), number of inbound vs outbound edges, whether the account has had any recent failed KYC updates, and geographic distance between home branch and transaction branch.

The edge features include: transaction amount normalised by the sender's historical average, time since last transaction between this pair, channel type (NEFT vs UPI vs SWIFT), and whether this is a new counterparty relationship.

Training data comes from Union Bank's historical labelled fraud cases (confirmed STR filings and confirmed false positives) augmented with synthetic fraud graphs generated using a technique called SMOTE-NC adapted for graph data - since real fraud graphs are rare (class imbalance of roughly 1:500), synthetic oversampling is essential. The model achieves an F1 score of approximately 0.91 on a held-out test set, with a false positive rate under 3% at a threshold of 0.70.

The GNN runs as a microservice (FastAPI endpoint wrapping the PyTorch model) and is invoked by the Flink stream processor whenever the typology engine flags a subgraph. The subgraph is extracted from Neo4j, featurised, and passed to the GNN for scoring - this full pipeline runs in under 800 milliseconds end to end.

The GNN is retrained weekly on new confirmed cases using an online learning loop: investigator decisions (confirm fraud / mark false positive) are written back to the training dataset via a feedback API, and a scheduled retraining job runs every Sunday night, deploying the updated model weights with a blue-green deployment pattern to avoid downtime.

### Sublayer 3c - Behavioural Anomaly Detection with Isolation Forest

For accounts that don't yet show a clear pattern but are statistically anomalous relative to their peer group, FundLens runs an Isolation Forest model. This is an unsupervised ML algorithm that scores anomalies by how quickly a data point can be "isolated" from the rest of the dataset through random partitioning - anomalous points are isolated in fewer splits.

Each account has a peer group defined by: account type (savings/current/NRI), declared income bracket, branch tier (urban/semi-urban/rural), and tenure. The Isolation Forest is trained per peer group on 12 months of transaction history. Any account whose current-week behaviour falls in the bottom 2% of its peer group's likelihood distribution triggers a soft alert - not a full investigation, but a "watch" flag that elevates the account's priority if any other signal appears.

This is particularly powerful for detecting insider fraud (PS1 overlap) where the account owner is a bank employee - their baseline behaviour is well-defined by their role, and any deviation is immediately visible.

---

## Layer 4 - Blockchain for Evidence Integrity

This is where FundLens goes beyond standard AML systems and introduces an innovation that directly addresses a real courtroom problem.

When a bank submits a Suspicious Transaction Report to FIU-IND and the case goes to prosecution by the Enforcement Directorate, the chain of custody of the evidence matters legally. Defense lawyers routinely challenge whether the evidence was tampered with between detection and submission. Banks currently have no cryptographic proof that their evidence packages haven't been modified.

FundLens uses a private/permissioned Hyperledger Fabric blockchain as an immutable evidence ledger. Every time a fraud alert is generated, the following data is hashed (SHA-256) and the hash is written to the blockchain as a transaction: the subgraph snapshot (all nodes and edges at the time of detection), the GNN score and feature vector, the typology classification, and the timestamp. The hash and block ID are stored alongside the case in the main database.

When the STR is generated and submitted to FIU-IND, the full evidence package includes the blockchain block reference. Any regulator, prosecutor, or auditor can independently verify that the evidence package matches the on-chain hash - proving it hasn't been modified since the moment of detection. This is the digital equivalent of a notarised seal, but cryptographically stronger.

Hyperledger Fabric is the right choice here (not a public blockchain like Ethereum) because it is permissioned - only FundLens nodes and authorised FIU/regulatory nodes can participate - transaction speeds are in the thousands per second (no gas fees, no consensus delays), and it runs entirely within the bank's private cloud, satisfying RBI's data localisation requirements.

Over time, this blockchain ledger can be federated across multiple banks - if Union Bank and another PSB both detect the same entity moving money across both banks, they can share evidence hashes (not the underlying data) through the shared Fabric network, enabling cross-bank pattern detection without violating customer privacy laws.

---

## Layer 5 - The LLM Narrative Engine

Producing a Suspicious Transaction Report manually requires a compliance officer to read through transaction logs, understand the pattern, and write a coherent narrative in plain English explaining the suspicion. This takes hours. FundLens automates this with a large language model.

The system uses a two-stage prompting architecture. In the first stage, a structured prompt is assembled programmatically from the case data: the typology name, the subgraph data (accounts, amounts, timestamps, hop count), the GNN score, and the relevant regulatory reference (which PMLA section applies, which FATF typology this matches). This structured data is passed to the LLM with a system prompt that instructs it to act as a senior AML compliance officer writing an STR narrative.

The LLM generates three things: a plain English narrative explanation of the suspicious pattern, a formal STR narrative in the FIU-IND prescribed format, and a Hindi translation of the narrative for bilingual regulatory submissions. All three are presented to the investigator for review and edit before submission - the LLM drafts, the human approves.

For deployment, FundLens supports two modes: cloud API mode (using Claude via Anthropic API or GPT-4o via Azure OpenAI - both satisfy enterprise data processing agreements) and on-premise mode (using a self-hosted Mistral-7B-Instruct or LLaMA-3-8B quantised to 4-bit with llama.cpp, running on a single A100 GPU server). The on-premise mode is essential for banks that have internal policies against sending customer data to external APIs - Union Bank may well be one.

The LLM is also used for a second function: when an investigator is reviewing a case and types a natural language query like "show me all accounts connected to this entity that had activity in the last 30 days," the query is interpreted by the LLM and converted to a Cypher graph query, which is executed against Neo4j and the results returned. This natural language interface makes the system accessible to compliance officers who are not data scientists.

---

## Layer 6 - The Investigator Platform (Frontend)

The investigator dashboard is built in React 18 with TypeScript. The graph visualisation uses Sigma.js (a WebGL-accelerated graph rendering library) which can render graphs with 10,000+ nodes at 60fps - this matters because some fund flow networks are large. D3.js handles the supplementary charts (timeline charts, velocity charts, peer comparison charts). The case management system is a full CRUD application backed by PostgreSQL, with full-text search via Elasticsearch.

The dashboard has five primary views: the alert queue (showing all active cases sorted by GNN risk score), the graph investigator (the interactive fund flow visualisation), the entity profile (a 360-degree view of any account or person, showing all their connections, history, and risk flags), the STR builder (the LLM-assisted report generation interface), and the analytics dashboard (aggregate fraud trends, typology frequency, investigator performance metrics).

Authentication uses OAuth 2.0 with Union Bank's existing Active Directory, with RBAC controlling what each role can see: investigators can view and work cases; supervisors can approve STR submissions; administrators can configure thresholds and model parameters; read-only auditors can view completed cases but not active investigations.

Every action taken in the investigator UI generates an immutable audit log entry - who viewed what, when, and what decision was made. This audit trail is stored in append-only PostgreSQL tables and is also hashed to the Hyperledger Fabric chain, so the chain of custody for every investigator action is provable.

---

## Layer 7 - Zero-Knowledge Proofs for Cross-Bank Intelligence Sharing

This is the most forward-looking component and the one that gives FundLens its long-term competitive moat.

A major limitation of current AML systems is that they operate in silos. A fraudster who moves money through Union Bank to HDFC to SBI leaves a partial trail at each bank - no single bank sees the full picture. Sharing the underlying transaction data between banks is illegal under customer privacy laws (the DPDP Act 2023). So banks have historically been unable to collaborate.

FundLens solves this with Zero-Knowledge Proofs (ZKPs). A ZKP is a cryptographic protocol that allows one party to prove to another that a statement is true without revealing any information about why it is true. In FundLens's context: Bank A can prove to Bank B that "entity X has been flagged as high-risk in our system" without revealing the transactions, amounts, or patterns that led to that conclusion.

The implementation uses the `snarkjs` library (a JavaScript/WASM implementation of the Groth16 zk-SNARK proving system) with circuits defined in Circom. Bank A generates a proof that a particular entity hash (the SHA-256 hash of a normalised entity identifier - PAN number, for example) is present in their high-risk entity set. Bank B can verify this proof in milliseconds without learning anything about Bank A's internal data. The entity hash is the only thing shared - no names, no account numbers, no transaction data.

This federated intelligence layer, operating over the Hyperledger Fabric network, means that when a new account at Union Bank starts transacting with an entity that SBI has already flagged, FundLens immediately knows - without either bank ever sharing customer data. This is a capability that no existing AML vendor offers.

---

## Complete Architecture as a Data Flow

Here is what happens, start to finish, when a fraudulent transaction occurs:

A NEFT transfer of ₹9.8L arrives at CBS at 14:23:07. Within 50ms, it is published to Kafka topic `transactions.raw`. Within 200ms, the Flink processor consumes it, normalises it, runs entity resolution, and publishes it to topic `transactions.enriched`. Simultaneously, it updates the Neo4j graph - adding or updating the relevant `TRANSFERRED_TO` edge. Within 300ms, the Flink typology pattern queries re-evaluate against the updated graph and detect that this transaction completes a structuring pattern: 9 transactions, all below ₹10L, all to the same destination account, across 3 days. A pattern match event is published to Kafka topic `alerts.candidate`. Within 800ms, the GNN microservice is invoked - it extracts the relevant 12-node subgraph from Neo4j, featurises it, runs inference, and returns a score of 0.87. This exceeds the 0.70 threshold, so a full alert is created in the case management system. The alert hash is written to Hyperledger Fabric. Within 1 second of the transaction arriving, a push notification reaches the investigator's dashboard. The investigator opens the case, sees the animated graph, clicks "Generate STR," and receives a draft report in 47 seconds. Total time from transaction to evidence-ready STR: under 2 minutes.

---

## Security, Privacy, and Deployment

The entire system runs within the bank's private cloud or on-premise data centre - no customer data ever leaves the bank's infrastructure. TLS 1.3 encrypts all internal service-to-service communication. All PII (names, PAN numbers, Aadhaar references) is encrypted at rest using AES-256 and masked in any external-facing output (the STR shows account numbers and amounts but not raw PAN/Aadhaar strings). Role-based access control uses JWT tokens issued against Union Bank's Active Directory. The Kubernetes deployment uses namespace isolation to separate the ingestion, graph, ML, and UI tiers, and network policies block any east-west traffic that isn't explicitly whitelisted.

The entire stack is containerised with Docker and orchestrated by Kubernetes (Helm charts for each service). A CI/CD pipeline using GitHub Actions handles automated testing (unit tests for all Flink processors and Cypher queries, integration tests against a Neo4j test instance) and deploys to staging before production. The ML model deployment uses a blue-green pattern - the new model version serves shadow traffic alongside the current model for 24 hours, and if its alert precision matches or exceeds the current model, it is promoted to production automatically.

---

## Why Every Technology Choice Is Justified

**Kafka over RabbitMQ:** Kafka retains messages on disk with configurable retention (90 days), meaning if the graph database goes down for maintenance, no transactions are lost - Flink replays from the Kafka offset when it comes back up. RabbitMQ doesn't offer this durability model at scale.

**Neo4j over a graph layer on PostgreSQL:** Recursive SQL queries (common table expressions) for multi-hop traversals become exponentially slower as hop depth increases. In Neo4j, traversal depth adds constant overhead - a 7-hop query is not meaningfully slower than a 3-hop query.

**Graph Neural Network over XGBoost or random forest:** Traditional ML operates on a flat feature vector per transaction. GNNs operate on the graph structure itself - they encode who is connected to whom, not just what individual metrics look like. This is why they catch layering patterns that XGBoost cannot: the pattern isn't in any one node's features, it's in the topology of the subgraph.

**Hyperledger Fabric over Ethereum:** Public blockchains have variable transaction costs (gas fees), variable finality times, and store data publicly. Hyperledger Fabric is permissioned, deterministic, free to transact on, and keeps all data private within the consortium. For a bank's compliance evidence chain, these properties are non-negotiable.

**Zero-Knowledge Proofs over simple hash sharing:** Simply sharing entity hashes would reveal which entities a bank is investigating - a potential market-sensitive leak. ZKPs allow one bank to prove a statement about an entity to another bank without revealing the entity's identity or anything about the investigation. The cryptographic guarantee means neither bank can infer anything beyond the single bit "yes, this entity is in our high-risk set."

This is a production-grade platform. Every technology choice has a specific justification rooted in the bank's actual constraints - regulatory, operational, and technical. Nothing here is decorative.

---

## Running the Frontend Code

This is the code bundle for the FundLens investigator dashboard frontend.

### Prerequisites

- Node.js 16+ and npm
- Python 3.11+
- Docker (for local database setup)

### Local Development Setup

1. **Install frontend dependencies**
   ```bash
   npm install
   ```

2. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start databases with Docker**
   ```bash
   docker network create fundlens_net
   docker run -d --name fundlens-neo4j --network fundlens_net -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   docker run -d --name fundlens-postgres --network fundlens_net -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fundlens postgres:latest
   docker run -d --name fundlens-redis --network fundlens_net -p 6379:6379 redis:latest
   ```

4. **Seed sample data**
   ```bash
   python -m backend.seed_data
   ```

5. **Start backend**
   ```bash
   uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Start frontend** (in a new terminal)
   ```bash
   npm run dev
   ```

7. **Open browser**
   ```
   http://localhost:5173
   ```

### Production Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete Vercel deployment instructions.

**Quick Deploy to Vercel:**

1. Push to GitHub
2. Import repository to Vercel
3. Set environment variables (see [.env.example](./.env.example))
4. Deploy

**Files for deployment:**
- `vercel.json` - Vercel configuration
- `api/index.py` - Serverless function entry point
- `requirements.txt` - Python dependencies
- `.vercelignore` - Files to exclude from deployment
- `DEPLOYMENT.md` - Complete deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist

### Project Structure

```
fundlens-aml/
├── src/                    # Frontend React app
│   ├── app/
│   │   ├── pages/         # Page components
│   │   ├── components/    # Reusable UI components
│   │   └── routes.tsx     # React Router config
│   ├── services/          # API client
│   └── styles/            # CSS and themes
├── backend/               # FastAPI backend
│   ├── api/              # API routes
│   ├── db/               # Database clients
│   ├── llm/              # LLM STR generator
│   ├── blockchain/       # Blockchain evidence
│   └── graph/            # Neo4j queries
├── api/                  # Vercel serverless entry
├── vercel.json           # Vercel config
└── requirements.txt      # Python deps
```

### Key Features Implemented

✅ **Real-time Alert Dashboard** - Live alerts from PostgreSQL
✅ **Fund Flow Graph Visualization** - Neo4j graph queries
✅ **Entity Profile** - 360° account view with risk scoring
✅ **STR Generation** - AI-powered report drafting with streaming
✅ **Blockchain Audit Trail** - Evidence integrity verification
✅ **Natural Language Query** - Ask questions about accounts
✅ **Analytics Dashboard** - System health and metrics
✅ **Save Draft** - LocalStorage persistence
✅ **Export PDF** - Download formatted reports
✅ **Submit to FIU-IND** - Mock submission with blockchain record

### API Endpoints

All backend endpoints are documented at `http://localhost:8000/docs` (Swagger UI)

**Core endpoints:**
- `GET /api/health` - System health check
- `GET /api/alerts` - List all alerts
- `GET /api/cases` - List all cases
- `GET /api/cases/{case_id}` - Get case details
- `GET /api/graph/{case_id}` - Get fund flow graph
- `GET /api/entities/{account_id}` - Get entity profile
- `GET /api/blockchain/case/{case_id}` - Get evidence blocks
- `POST /api/str/{case_id}/generate` - Generate STR (SSE stream)
- `POST /api/query` - Natural language query
- `GET /api/analytics` - Analytics overview

### Technology Stack

**Frontend:**
- React 18 + TypeScript
- React Router 7
- Tailwind CSS 4
- Radix UI components
- Lucide icons
- Vite 6

**Backend:**
- FastAPI (Python)
- Neo4j (graph database)
- PostgreSQL (cases/alerts)
- Redis (pub/sub)
- Kafka (event streaming)
- Hyperledger Fabric (blockchain)

**Deployment:**
- Vercel (frontend + serverless functions)
- Mangum (ASGI adapter for serverless)

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required for local development
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/fundlens
REDIS_URL=redis://localhost:6379/0

# Optional
KAFKA_BOOTSTRAP=localhost:9092
GNN_SCORE_URL=http://localhost:8001/score
```

For production deployment, use hosted database services (see DEPLOYMENT.md).

### Troubleshooting

**Frontend shows "Could not load alerts"**
- Check backend is running: `curl http://localhost:8000/api/health`
- Verify databases are up: `docker ps`
- Check browser console for CORS errors

**Backend returns 404 for cases**
- Run seed script: `python -m backend.seed_data`
- Verify PostgreSQL connection in backend logs

**Graph visualization is empty**
- Check Neo4j is running: `docker ps | grep neo4j`
- Verify data was seeded: Open http://localhost:7474 and run `MATCH (n) RETURN count(n)`

**STR generation fails**
- Check backend logs for errors
- Verify case exists: `curl http://localhost:8000/api/cases/CASE-2847`

### Support

For deployment issues, see [DEPLOYMENT.md](./DEPLOYMENT.md)
For technical architecture, see sections above
For bugs/features, open an issue on GitHub
  