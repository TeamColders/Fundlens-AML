import pandas as pd
from backend.graph.neo4j_client import get_session

def create_indexes(session):
    print("Creating indexes...")
    session.run("CREATE INDEX account_id IF NOT EXISTS FOR (a:Account) ON (a.account_id)")
    session.run("CREATE INDEX entity_id IF NOT EXISTS FOR (e:Entity) ON (e.entity_id)")
    session.run("CREATE INDEX txn_timestamp IF NOT EXISTS FOR ()-[r:TRANSFERRED_TO]-() ON (r.timestamp)")

import json

def load_data(json_path: str):
    """
    Load synthetic transaction JSON into Neo4j using APOC batching.
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    records = []
    for i, graph in enumerate(data):
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        
        fraud_nodes = {n['account_id']: n.get('is_fraud', 0) for n in nodes}
        
        for j, edge in enumerate(edges):
            source = edge.get('source')
            target = edge.get('target')
            is_fraud = bool(fraud_nodes.get(source, 0) or fraud_nodes.get(target, 0))
            
            features = edge.get('features', {})
            amount_log = features.get('amount_log_normalised', 0.5) * 5
            
            records.append({
                "transaction_id": f"TXN-{i}-{j}",
                "sender_account": source,
                "receiver_account": target,
                "amount": float(10 ** amount_log),
                "currency": "USD",
                "timestamp": "2023-10-01T12:00:00Z",
                "channel": "online",
                "branch_code": "BR-01",
                "reference_number": f"REF-{i}-{j}",
                "is_fraud": is_fraud,
                "typology": "unknown"
            })
            
    with get_session() as session:
        create_indexes(session)
        
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
