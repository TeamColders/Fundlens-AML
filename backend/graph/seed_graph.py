"""
Neo4j graph seeding script for FundLens.
Loads synthetic transaction data into the graph database.
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from backend.graph.neo4j_client import get_client
from data.synthetic.fraud_scenarios import generate_transactions
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_account_nodes(df: pd.DataFrame, client) -> int:
    """Create Account nodes from transaction data."""
    logger.info("Creating Account nodes...")

    # Get unique accounts
    senders = set(df["sender_account"].unique())
    receivers = set(df["receiver_account"].unique())
    all_accounts = senders | receivers

    # Create account metadata
    account_nodes = []
    for account_id in all_accounts:
        account_nodes.append(
            {
                "account_id": account_id,
                "account_type": "savings",
                "kyc_tier": 2,
                "status": "active",
                "is_dormant": False,
                "created_date": datetime(2023, 1, 1).isoformat(),
                "home_branch": "BR001",
            }
        )

    # Merge in batches
    total = client.batch_merge_nodes(account_nodes, "Account", batch_size=500)
    logger.info(f"✓ Created {total} Account nodes")
    return total


def create_entity_nodes(df: pd.DataFrame, client) -> int:
    """Create Entity nodes (one per account for simplicity)."""
    logger.info("Creating Entity nodes...")

    senders = set(df["sender_account"].unique())
    receivers = set(df["receiver_account"].unique())
    all_accounts = senders | receivers

    entity_nodes = []
    for i, account_id in enumerate(all_accounts):
        entity_nodes.append(
            {
                "entity_id": f"ENT-{i:05d}",
                "name_hash": f"name_{i}",
                "pan_hash": f"pan_{i}",
                "mobile_hash": f"mobile_{i}",
                "kyc_tier": 2,
            }
        )

    # Merge in batches
    total = client.batch_merge_nodes(entity_nodes, "Entity", batch_size=500)
    logger.info(f"✓ Created {total} Entity nodes")
    return total


def create_controlled_by_relationships(df: pd.DataFrame, client) -> int:
    """Create CONTROLLED_BY relationships between accounts and entities."""
    logger.info("Creating CONTROLLED_BY relationships...")

    senders = set(df["sender_account"].unique())
    receivers = set(df["receiver_account"].unique())
    all_accounts = senders | receivers

    relationships = []
    for i, account_id in enumerate(all_accounts):
        relationships.append(
            {"account_id": account_id, "entity_id": f"ENT-{i:05d}"}
        )

    # Merge in batches
    total = client.batch_merge_relationships(
        relationships, "CONTROLLED_BY", batch_size=500
    )
    logger.info(f"✓ Created {total} CONTROLLED_BY relationships")
    return total


def create_transferred_to_relationships(df: pd.DataFrame, client) -> int:
    """Create TRANSFERRED_TO relationships between accounts."""
    logger.info("Creating TRANSFERRED_TO relationships...")

    # Prepare relationship data
    relationships = []
    for _, row in df.iterrows():
        rel = {
            "sender_account": row["sender_account"],
            "receiver_account": row["receiver_account"],
            "transaction_id": row["transaction_id"],
            "amount": float(row["amount"]),
            "currency": row["currency"],
            "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], 'isoformat') else str(row["timestamp"]),
            "channel": row["channel"],
            "is_fraud": bool(row["is_fraud"]),
            "typology": row["typology"],
            "case_id": row["case_id"],
        }
        relationships.append(rel)

    # Merge in batches
    total = client.batch_merge_relationships(
        relationships, "TRANSFERRED_TO", batch_size=500
    )
    logger.info(f"✓ Created {total} TRANSFERRED_TO relationships")
    return total


def seed_graph(transactions_file: str = None) -> None:
    """
    Main function to seed the graph database.
    """
    logger.info("=" * 60)
    logger.info("FundLens Graph Seeding")
    logger.info("=" * 60)

    client = get_client()

    # Verify connection
    if not client.verify_connection():
        logger.error("Cannot connect to Neo4j. Exiting.")
        return

    # Generate or load transactions
    if transactions_file and Path(transactions_file).exists():
        logger.info(f"Loading transactions from {transactions_file}...")
        df = pd.read_csv(transactions_file)
    else:
        logger.info("Generating synthetic transactions...")
        df = generate_transactions(10000)
        # Save for future use
        df.to_csv(
            "/home/nathanpimenta/Projects/Fundlens-AML/data/synthetic/transactions.csv",
            index=False,
        )

    # Convert timestamp column to datetime if it's a string
    if df["timestamp"].dtype == "object":
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    logger.info(f"Loaded {len(df)} transactions")
    logger.info(f"  Clean: {len(df[df['is_fraud'] == False])}")
    logger.info(f"  Fraud: {len(df[df['is_fraud'] == True])}")

    # Create indexes
    logger.info("Creating indexes...")
    client.create_indexes()

    # Clear existing data (optional - comment out for incremental loads)
    # logger.info("Clearing existing data...")
    # with client.session() as session:
    #     session.run("MATCH (n) DETACH DELETE n")

    # Create nodes
    create_account_nodes(df, client)
    create_entity_nodes(df, client)

    # Create relationships
    create_controlled_by_relationships(df, client)
    create_transferred_to_relationships(df, client)

    # Print stats
    logger.info("\n" + "=" * 60)
    logger.info("Graph Statistics:")
    logger.info("=" * 60)
    stats = client.get_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    logger.info("=" * 60)
    logger.info("✓ Graph seeding complete!")
    logger.info("=" * 60)

    client.close()
        
        print(f"Loading {len(records)} transactions into Neo4j...")
        
        # Cypher query using UNWIND to batch merge Accounts and relationships
        query = """
        CALL apoc.periodic.iterate(
            "UNWIND $records AS record RETURN record",
            "
            // Merge Sender
            MERGE (s:Account {account_id: record.sender_account})
            ON CREATE SET 
                s.account_type = 'savings', 
                s.status = 'active', 
                s.kyc_tier = 1,
                s.created_date = '2023-01-01',
                s.last_active_date = record.timestamp,
                s.declared_income = 500000.0,
                s.home_branch = record.branch_code,
                s.is_dormant = false

            // Merge Receiver
            MERGE (r:Account {account_id: record.receiver_account})
            ON CREATE SET 
                r.account_type = 'savings', 
                r.status = 'active', 
                r.kyc_tier = 1,
                r.created_date = '2023-01-01',
                r.last_active_date = record.timestamp,
                r.declared_income = 500000.0,
                r.home_branch = record.branch_code,
                r.is_dormant = false

            // Merge Sender Entity
            MERGE (es:Entity {entity_id: 'ENT-' + record.sender_account})
            ON CREATE SET es.name_hash = 'hash1', es.pan_hash = 'pan1', es.mobile_hash = 'mob1', es.kyc_tier = 1
            MERGE (s)-[:CONTROLLED_BY]->(es)

            // Merge Receiver Entity
            MERGE (er:Entity {entity_id: 'ENT-' + record.receiver_account})
            ON CREATE SET er.name_hash = 'hash2', er.pan_hash = 'pan2', er.mobile_hash = 'mob2', er.kyc_tier = 1
            MERGE (r)-[:CONTROLLED_BY]->(er)

            // Create Transaction Edge
            CREATE (s)-[t:TRANSFERRED_TO {
                transaction_id: record.transaction_id,
                amount: toFloat(record.amount),
                currency: record.currency,
                timestamp: record.timestamp,
                channel: record.channel,
                branch_code: record.branch_code,
                reference_number: record.reference_number,
                is_fraud: toBoolean(record.is_fraud),
                typology: record.typology
            }]->(r)
            ",
            {batchSize: 500, parallel: true, params: {records: $records}}
        )
        """
        
        result = session.run(query, records=records)
        stats = result.single()
        print("Batch processing complete:", stats)

        # Print final counts
        nodes = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
        edges = session.run("MATCH ()-[r]->() RETURN count(r) as c").single()["c"]
        fraud = session.run("MATCH ()-[r:TRANSFERRED_TO {is_fraud: true}]->() RETURN count(r) as c").single()["c"]

        print(f"Total Nodes: {nodes}")
        print(f"Total Relationships: {edges}")
        print(f"Fraud Edges: {fraud}")

if __name__ == "__main__":
    import os
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "synthetic", "transactions.json")
    if os.path.exists(json_path):
        load_data(json_path)
    else:
        print(f"File not found: {json_path}. Please ensure transactions.json exists.")
