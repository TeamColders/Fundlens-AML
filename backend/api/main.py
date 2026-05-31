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

# Load .env before anything else
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── WebSocket connection manager ─────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WS client connected — total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.info(f"WS client disconnected — total: {len(self.active)}")

    async def broadcast(self, message: dict):
        import json
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.active:
                self.active.remove(ws)


manager = ConnectionManager()


# ── Lifespan: startup + shutdown ─────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FundLens API starting up...")

    # Initialise blockchain SQLite DB
    from backend.blockchain.evidence_chain import init_db
    init_db()
    logger.info("Evidence chain DB ready")

    logger.info("FundLens API ready — listening on port 8000")
    yield
    logger.info("FundLens API shutting down")


# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="FundLens AML API",
    description="Intelligent Fund Flow Intelligence Platform — Union Bank of India",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server and common origins
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


# ── Mount all routers ────────────────────────────────────────────
from backend.api.routes.alerts import router as alerts_router
from backend.api.routes.cases import router as cases_router
from backend.api.routes.graph import router as graph_router
from backend.api.routes.entities import router as entities_router
from backend.api.routes.str_report import router as str_router
from backend.api.routes.analytics import router as analytics_router
from backend.api.routes.blockchain import router as blockchain_router
from backend.api.routes.query import router as query_router

app.include_router(alerts_router)
app.include_router(cases_router)
app.include_router(graph_router)
app.include_router(entities_router)
app.include_router(str_router)
app.include_router(analytics_router)
app.include_router(blockchain_router)
app.include_router(query_router)


# ── Health check ─────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "api":        "ok",
            "blockchain": "ok",
            "llm":        "ok" if os.getenv("GEMINI_API_KEY") else "no_key",
            "neo4j":      "demo_mode",
            "postgres":   "demo_mode",
        },
        "endpoints": [
            "/api/alerts", "/api/cases", "/api/graph/{case_id}",
            "/api/entities/{account_id}", "/api/str/{case_id}/generate",
            "/api/analytics", "/api/blockchain/{case_id}",
            "/api/query",
        ],
    }


# ── WebSocket — real-time alert feed ─────────────────────────────
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Expose broadcast so other modules can push alerts ────────────
def broadcast_alert(alert: dict):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast({"type": "new_alert", "data": alert}))
    except RuntimeError:
        pass
