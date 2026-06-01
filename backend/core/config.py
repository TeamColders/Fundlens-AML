import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env explicitly so it works regardless of working directory
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)


@dataclass(frozen=True)
class Settings:
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    dependency_timeout_seconds: int = int(os.getenv("DEPENDENCY_TIMEOUT_SECONDS", "120"))
    dependency_retry_interval_seconds: int = int(os.getenv("DEPENDENCY_RETRY_INTERVAL_SECONDS", "2"))

    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")

    postgres_dsn: str = os.getenv(
        "POSTGRES_DSN",
        "postgresql://postgres:postgres@postgres:5432/fundlens",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    kafka_bootstrap: str = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")

    gnn_score_url: str = os.getenv("GNN_SCORE_URL", "http://gnn:8001/score")

    alerts_channel: str = os.getenv("ALERTS_CHANNEL", "alerts")


settings = Settings()
