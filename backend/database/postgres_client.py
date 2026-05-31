import os
import logging
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError as exc:
    psycopg2 = None  # type: ignore
    RealDictCursor = None  # type: ignore
    execute_values = None  # type: ignore
    _PSYCOPG2_ERROR = exc
else:
    _PSYCOPG2_ERROR = None

logger = logging.getLogger(__name__)

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:fundlens123@localhost:5432/fundlens")

def init_db():
    """Initialize the PostgreSQL schema."""
    _require_psycopg2()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id       TEXT PRIMARY KEY,
                    account_type     TEXT,
                    status           TEXT,
                    kyc_tier         INTEGER,
                    created_date     TEXT,
                    last_active_date TEXT,
                    declared_income  NUMERIC,
                    home_branch      TEXT,
                    is_dormant       BOOLEAN,
                    is_pep_adjacent  BOOLEAN,
                    owner_name       TEXT,
                    owner_type       TEXT,
                    risk_level       TEXT,
                    notes            TEXT
                );
                
                CREATE TABLE IF NOT EXISTS cases (
                    case_id          TEXT PRIMARY KEY,
                    typology         TEXT,
                    typology_code    TEXT,
                    fatf_reference   TEXT,
                    pmla_section     TEXT,
                    risk_score       NUMERIC,
                    confidence       TEXT,
                    risk_level       TEXT,
                    total_amount     NUMERIC,
                    accounts_count   INTEGER,
                    hops             INTEGER,
                    duration_minutes INTEGER,
                    duration_display TEXT,
                    channel          TEXT,
                    status           TEXT,
                    created_at       TIMESTAMPTZ,
                    gnn_score        NUMERIC,
                    investigator_id  TEXT,
                    notes            TEXT
                );
                
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id   TEXT PRIMARY KEY,
                    sender           TEXT,
                    receiver         TEXT,
                    amount           NUMERIC,
                    currency         TEXT DEFAULT 'INR',
                    timestamp        TIMESTAMPTZ,
                    channel          TEXT,
                    branch_code      TEXT,
                    reference_number TEXT,
                    is_fraud         BOOLEAN,
                    typology         TEXT,
                    case_id          TEXT,
                    demo_date        DATE
                );
            """)
        conn.commit()

def _require_psycopg2():
    if psycopg2 is None:
        raise ImportError("psycopg2 is not installed") from _PSYCOPG2_ERROR


@contextmanager
def get_db():
    _require_psycopg2()
    conn = psycopg2.connect(POSTGRES_URL)
    try:
        yield conn
    finally:
        conn.close()

def get_dict_db():
    _require_psycopg2()
    return psycopg2.connect(POSTGRES_URL, cursor_factory=RealDictCursor)

def get_case(case_id: str):
    with get_dict_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM cases WHERE case_id = %s", (case_id,))
            return cur.fetchone()

def get_case_transactions(case_id: str):
    with get_dict_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM transactions WHERE case_id = %s ORDER BY timestamp ASC", (case_id,))
            return cur.fetchall()

def get_case_accounts(case_id: str):
    with get_dict_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT a.* FROM accounts a 
                JOIN transactions t ON a.account_id = t.sender OR a.account_id = t.receiver
                WHERE t.case_id = %s
            """, (case_id,))
            return cur.fetchall()
