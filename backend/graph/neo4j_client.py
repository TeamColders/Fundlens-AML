"""
Neo4j database client for FundLens graph operations.
Handles connection, queries, and batch operations.
"""

import os
from contextlib import contextmanager
from neo4j import GraphDatabase, Session
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "fundlens123")


class Neo4jClient:
    def __init__(self):
        self._driver = None

    def connect(self):
        if not self._driver:
            self._driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            logger.info(f"✓ Connected to Neo4j at {NEO4J_URI}")

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

    def verify_connection(self) -> bool:
        """Verify connection to Neo4j."""
        try:
            with self.session() as session:
                session.run("RETURN 1")
            logger.info("✓ Neo4j connection verified")
            return True
        except Exception as e:
            logger.error(f"✗ Neo4j connection failed: {e}")
            return False

    def create_indexes(self):
        """Create necessary indexes for performance."""
        with self.session() as session:
            indexes = [
                "CREATE INDEX account_id IF NOT EXISTS FOR (a:Account) ON (a.account_id)",
                "CREATE INDEX entity_id IF NOT EXISTS FOR (e:Entity) ON (e.entity_id)",
                "CREATE INDEX txn_timestamp IF NOT EXISTS FOR ()-[r:TRANSFERRED_TO]-() ON (r.timestamp)",
                "CREATE INDEX txn_is_fraud IF NOT EXISTS FOR ()-[r:TRANSFERRED_TO]-() ON (r.is_fraud)",
            ]
            for index_query in indexes:
                try:
                    session.run(index_query)
                    logger.info(f"✓ Index created: {index_query.split('FOR')[0].strip()}")
                except Exception as e:
                    logger.warning(f"Index creation note: {e}")

    def batch_merge_nodes(
        self, nodes: List[Dict], label: str, batch_size: int = 500
    ) -> int:
        """
        Merge nodes in batches using UNWIND for performance.
        """
        total_merged = 0
        with self.session() as session:
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i : i + batch_size]

                if label == "Account":
                    query = """
                    UNWIND $nodes AS node
                    MERGE (a:Account {account_id: node.account_id})
                    SET a.account_type = node.account_type,
                        a.kyc_tier = node.kyc_tier,
                        a.status = node.status,
                        a.is_dormant = node.is_dormant,
                        a.created_date = node.created_date,
                        a.declared_income = node.declared_income,
                        a.home_branch = node.home_branch
                    RETURN count(a) as count
                    """
                elif label == "Entity":
                    query = """
                    UNWIND $nodes AS node
                    MERGE (e:Entity {entity_id: node.entity_id})
                    SET e.kyc_tier = node.kyc_tier
                    RETURN count(e) as count
                    """
                else:
                    continue

                result = session.run(query, nodes=batch)
                count = result.single()["count"]
                total_merged += count
                logger.info(
                    f"  Merged {count} {label} nodes (batch {i//batch_size + 1})"
                )

        return total_merged

    def batch_merge_relationships(
        self, relationships: List[Dict], rel_type: str, batch_size: int = 500
    ) -> int:
        """Merge relationships in batches."""
        total_merged = 0

        with self.session() as session:
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i : i + batch_size]

                if rel_type == "CONTROLLED_BY":
                    query = """
                    UNWIND $rels AS rel
                    MATCH (a:Account {account_id: rel.account_id})
                    MATCH (e:Entity {entity_id: rel.entity_id})
                    MERGE (a)-[:CONTROLLED_BY]->(e)
                    RETURN count(*) as count
                    """
                elif rel_type == "TRANSFERRED_TO":
                    query = """
                    UNWIND $rels AS rel
                    MATCH (a:Account {account_id: rel.sender_account})
                    MATCH (b:Account {account_id: rel.receiver_account})
                    MERGE (a)-[t:TRANSFERRED_TO]->(b)
                    SET t.transaction_id = rel.transaction_id,
                        t.amount = rel.amount,
                        t.currency = rel.currency,
                        t.timestamp = rel.timestamp,
                        t.channel = rel.channel,
                        t.is_fraud = rel.is_fraud,
                        t.typology = rel.typology,
                        t.case_id = rel.case_id
                    RETURN count(*) as count
                    """
                else:
                    continue

                result = session.run(query, rels=batch)
                count = result.single()["count"]
                total_merged += count
                logger.info(
                    f"  Merged {count} {rel_type} relationships (batch {i//batch_size + 1})"
                )

        return total_merged

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        with self.session() as session:
            queries = {
                "accounts": "MATCH (a:Account) RETURN count(a) as count",
                "entities": "MATCH (e:Entity) RETURN count(e) as count",
                "all_transfers": "MATCH ()-[t:TRANSFERRED_TO]->() RETURN count(t) as count",
                "fraud_transfers": "MATCH ()-[t:TRANSFERRED_TO {is_fraud: true}]->() RETURN count(t) as count",
            }

            stats = {}
            for key, query in queries.items():
                result = session.run(query)
                record = result.single()
                if record:
                    stats[key] = record["count"]

            return stats

    def run_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Run a Cypher query and return results."""
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]


# Singleton instance
client = Neo4jClient()


def get_session():
    """Context manager for obtaining a neo4j session."""
    return client.session()


def get_client() -> Neo4jClient:
    """Get the Neo4j client instance."""
    return client


def close_driver():
    """Close the database connection."""
    client.close()
