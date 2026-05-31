import os
from contextlib import contextmanager
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "fundlens123")

class Neo4jClient:
    def __init__(self):
        self._driver = None

    def connect(self):
        if not self._driver:
            self._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    @contextmanager
    def session(self):
        self.connect()
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

# Singleton instance
client = Neo4jClient()

def get_session():
    """Context manager for obtaining a neo4j session."""
    return client.session()

def close_driver():
    client.close()
