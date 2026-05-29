from contextlib import contextmanager

import psycopg2
from psycopg2.pool import SimpleConnectionPool

from backend.core.config import settings

_pool = None


def connect() -> None:
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(minconn=1, maxconn=5, dsn=settings.postgres_dsn)
        _ensure_schema()


def close() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_conn():
    if _pool is None:
        connect()
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)


def _ensure_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
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
            cur.execute(
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
            cur.execute(
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
