import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")

    postgres_dsn: str = os.getenv(
        "POSTGRES_DSN",
        "postgresql://postgres:postgres@localhost:5432/fundlens",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    kafka_bootstrap: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

    gnn_score_url: str = os.getenv("GNN_SCORE_URL", "http://localhost:8001/score")

    alerts_channel: str = os.getenv("ALERTS_CHANNEL", "alerts")


settings = Settings()
