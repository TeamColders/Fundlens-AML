"""Shared filesystem paths for local and deployed runtimes."""
from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    """Writable directory for SQLite DBs (use FUNDLENS_DATA_DIR on cloud)."""
    raw = os.getenv("FUNDLENS_DATA_DIR", "").strip()
    if raw:
        path = Path(raw).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    return project_root()


def demo_db_path() -> Path:
    return data_dir() / "fundlens_demo.db"


def evidence_db_path() -> Path:
    raw = os.getenv("FUNDLENS_EVIDENCE_DB", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return data_dir() / "fundlens_evidence.db"


def config_db_path() -> Path:
    raw = os.getenv("FUNDLENS_CONFIG_DB", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return data_dir() / "fundlens_config.db"
