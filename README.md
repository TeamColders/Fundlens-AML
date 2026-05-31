# FundLens - Agentic AI AML Platform

FundLens is an advanced Anti-Money Laundering (AML) and financial crime detection platform. It leverages Graph Neural Networks (GNNs), a Neo4j graph database, real-time Kafka streaming, and Gemini AI to detect, visualize, and report suspicious financial behavior.

## Key Features

- **Agentic AI Graph Queries (NL-to-Cypher):** Ask questions in natural language and have Gemini automatically translate them into Neo4j Cypher queries to interrogate the live graph database.
- **Real-Time Data Streaming:** Simulate Core Banking System (CBS) transaction streams using Kafka and Zookeeper.
- **Automated STR Generation:** Instantly generate bilingual (English & Hindi) Suspicious Transaction Reports (STRs) using generative AI.
- **Graph Neural Network (GNN):** Advanced anomaly detection capabilities to flag highly complex money laundering typologies (like layering, smurfing, and circular flows).

## Architecture Stack

- **Backend:** FastAPI (Python)
- **AI/LLM:** Google Gemini 2.5 Flash
- **Database:** Neo4j (Graph), PostgreSQL (Evidence Chain), Redis (Caching)
- **Streaming:** Confluent Kafka, Zookeeper
- **Frontend:** React, Vite, TailwindCSS

---

## Setup & Installation

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js & npm

### 2. Environment Variables
Ensure you have a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fundlens123
KAFKA_BROKER=localhost:9092
```

### 3. Spin Up Infrastructure
Run the following command to start Neo4j, Kafka, PostgreSQL, and Redis:
```bash
docker-compose up -d
```

### 4. Seed the Graph Database
Once the Neo4j container is healthy (accessible on port 7474), populate it with the synthetic transaction dataset:
```bash
conda activate fundlens  # Or use your virtual environment
python -m backend.graph.seed_graph
```
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
