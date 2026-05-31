"""
FundLens — FastAPI application entry point.
Run with: uvicorn backend.api.main:app --reload --port 8000
"""
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: list = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        import json

        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FundLens API starting up...")
    from backend.blockchain.evidence_chain import init_db
    from backend.database.config_store import init_config_tables
    from backend.database.str_store import init_str_tables

    init_db()
    init_str_tables()
    init_config_tables()

    try:
        from backend.graph.neo4j_client import get_client

        if get_client().verify_connection():
            logger.info("Neo4j connection verified")
        else:
            logger.warning("Neo4j unavailable — using Postgres/SQLite demo data")
    except Exception as exc:
        logger.warning("Neo4j check skipped: %s", exc)

    try:
        from backend.database.postgres_client import init_db as init_pg

        init_pg()
        logger.info("PostgreSQL schema ready")
    except Exception as exc:
        logger.warning("PostgreSQL init skipped: %s", exc)

    logger.info("FundLens API ready")
    yield
    logger.info("FundLens API shutting down")


app = FastAPI(
    title="FundLens AML API",
    description="Intelligent Fund Flow Intelligence Platform — Union Bank of India",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.routes.alerts import router as alerts_router
from backend.api.routes.analytics import router as analytics_router
from backend.api.routes.blockchain import router as blockchain_router
from backend.api.routes.cases import router as cases_router
from backend.api.routes.entities import router as entities_router
from backend.api.routes.graph import router as graph_router
from backend.api.routes.config import router as config_router
from backend.api.routes.mobile import router as mobile_router
from backend.api.routes.query import router as query_router
from backend.api.routes.str_report import router as str_router

app.include_router(alerts_router)
app.include_router(cases_router)
app.include_router(graph_router)
app.include_router(entities_router)
app.include_router(str_router)
app.include_router(analytics_router)
app.include_router(blockchain_router)
app.include_router(query_router)
app.include_router(config_router)
app.include_router(mobile_router)


@app.get("/api/health")
async def health():
    postgres_ok = False
    sqlite_ok = False
    try:
        from backend.database.demo_data import DEMO_DB_PATH, _load_all_cases

        postgres_ok = len(_load_all_cases()) > 0
    except Exception:
        pass
    sqlite_ok = DEMO_DB_PATH.exists()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    llm_status = "no_key"
    if api_key:
        try:
            from google import genai  # noqa: F401
            llm_status = "configured"
        except ImportError:
            llm_status = "missing_package"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "ok",
            "blockchain": "ok",
            "postgres": "ok" if postgres_ok else "fallback",
            "sqlite_demo": "ok" if sqlite_ok else "missing",
            "llm": llm_status,
        },
        "endpoints": [
            "/api/alerts",
            "/api/cases",
            "/api/graph/{case_id}",
            "/api/entities/{account_id}",
            "/api/str/{case_id}/generate",
            "/api/analytics",
            "/api/blockchain/{case_id}",
            "/api/query",
            "/api/config",
            "/api/mobile/dashboard",
        ],
    }


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def broadcast_alert(alert: dict):
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast({"type": "new_alert", "data": alert}))
    except RuntimeError:
        pass


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=port, reload=True)
