from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool

from backend.core.config import settings

_pool: ConnectionPool | None = None


def connect() -> None:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(conninfo=settings.postgres_dsn, min_size=1, max_size=5, open=True)
        _ensure_schema()


def close() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_conn():
    if _pool is None:
        connect()
    with _pool.connection() as conn:
        yield conn


def _ensure_schema() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                case_id TEXT NOT NULL,
                typology TEXT NOT NULL,
                gnn_score NUMERIC NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                payload JSONB
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                typology TEXT,
                total_amount NUMERIC,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_blocks (
                id SERIAL PRIMARY KEY,
                case_id TEXT NOT NULL,
                block_type TEXT NOT NULL,
                payload JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        conn.commit()
