from contextlib import asynccontextmanager
import asyncio
import json
import logging
import os
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers import (
    graph,
)
from backend.api.routers import alerts
from backend.api.routers import cases
from backend.api.routers import entities
from backend.api.routers import analytics
from backend.api.routers import blockchain
from backend.api.routers import query
from backend.api.routers import str_reports
from backend.api.routers import score
from backend.core.config import settings
from backend.core.logging import configure_logging
from backend.db import neo4j as neo4j_db
from backend.db import postgres as postgres_db
from backend.db import redis_client
from backend.realtime.alerts import subscribe_alerts


logger = logging.getLogger(__name__)


async def _wait_for_dependencies() -> None:
    deadline = time.monotonic() + settings.dependency_timeout_seconds

    async def wait_for_check(name: str, check) -> None:
        while True:
            try:
                await check()
                logger.info("%s is ready", name)
                return
            except Exception as exc:  # noqa: BLE001
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"Timed out waiting for {name}") from exc
                logger.info("Waiting for %s: %s", name, exc)
                await asyncio.sleep(settings.dependency_retry_interval_seconds)

    async def check_neo4j() -> None:
        def run_check() -> None:
            with neo4j_db.get_session() as session:
                session.run("RETURN 1").single()

        await asyncio.to_thread(run_check)

    async def check_postgres() -> None:
        def run_check() -> None:
            with postgres_db.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()

        await asyncio.to_thread(run_check)

    async def check_redis() -> None:
        client = redis_client.get_client()
        await client.ping()

    await wait_for_check("Neo4j", check_neo4j)
    await wait_for_check("PostgreSQL", check_postgres)
    await wait_for_check("Redis", check_redis)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting backend services")

    await _wait_for_dependencies()

    neo4j_db.connect()
    postgres_db.connect()
    redis_client.connect()

    yield

    logger.info("Shutting down backend services")
    await redis_client.close()
    postgres_db.close()
    neo4j_db.close()


app = FastAPI(lifespan=lifespan, title="FundLens Backend")

# CORS configuration - allow frontend origins
allowed_origins = settings.cors_origins.split(",") if hasattr(settings, 'cors_origins') else os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(entities.router, prefix="/api/entities", tags=["entities"])
app.include_router(str_reports.router, prefix="/api/str", tags=["str"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["blockchain"])
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(score.router, prefix="/api/score", tags=["score"])


@app.get("/api/debug")
async def debug_info():
    """Temporary endpoint to diagnose serverless environment issues."""
    import os
    return {
        "env_vars_present": {
            "NEO4J_URI": bool(os.getenv("NEO4J_URI")),
            "NEO4J_USER": bool(os.getenv("NEO4J_USER")),
            "NEO4J_PASSWORD": bool(os.getenv("NEO4J_PASSWORD")),
            "POSTGRES_DSN": bool(os.getenv("POSTGRES_DSN")),
            "REDIS_URL": bool(os.getenv("REDIS_URL")),
        },
        "python_version": __import__("sys").version,
    }


@app.get("/api/health")
async def health_check():
    status = {"neo4j": False, "postgres": False, "redis": False}

    try:
        with neo4j_db.get_session() as session:
            session.run("RETURN 1").single()
        status["neo4j"] = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j health check failed: %s", exc)

    try:
        with postgres_db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        status["postgres"] = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Postgres health check failed: %s", exc)

    try:
        client = redis_client.get_client()
        await client.ping()
        status["redis"] = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis health check failed: %s", exc)

    return {"status": status}


@app.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        async for message in subscribe_alerts():
            if isinstance(message, str):
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    payload = {"message": message}
            else:
                payload = message
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        logger.info("Alerts websocket disconnected")
