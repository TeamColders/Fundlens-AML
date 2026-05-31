"""
Seed script to populate databases with sample AML data for testing.
Run: python -m backend.seed_data
"""
import asyncio
from datetime import datetime, timedelta

from backend.db import neo4j as neo4j_db
from backend.db import postgres as postgres_db
from backend.db import redis_client


def seed_postgres():
    """Seed PostgreSQL with cases and alerts."""
    print("🔄 Seeding PostgreSQL...")
    
    with postgres_db.get_conn() as conn:
        with conn.cursor() as cur:
            # Insert cases
            cases = [
                ('CASE-2847', 'Round-trip Layering', 4723000, 'open'),
                ('CASE-2848', 'Smurfing Pattern', 2310000, 'open'),
                ('CASE-2849', 'Shell Company Flow', 15640000, 'under_review'),
                ('CASE-2850', 'Trade-Based Laundering', 8970000, 'open'),
            ]
            
            for case_id, typology, amount, status in cases:
                cur.execute(
                    """
                    INSERT INTO cases (case_id, typology, total_amount, status, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (case_id) DO NOTHING
                    """,
                    (case_id, typology, amount, status, datetime.now() - timedelta(hours=2))
                )
            
            # Insert alerts
            alerts = [
                ('CASE-2847', 'Round-trip Layering', 0.94, {'accounts': 7, 'total_amount': 4723000}),
                ('CASE-2848', 'Smurfing Pattern', 0.87, {'accounts': 14, 'total_amount': 2310000}),
                ('CASE-2849', 'Shell Company Flow', 0.91, {'accounts': 5, 'total_amount': 15640000}),
                ('CASE-2850', 'Trade-Based Laundering', 0.78, {'accounts': 9, 'total_amount': 8970000}),
            ]
            
            for case_id, typology, score, payload in alerts:
                cur.execute(
                    """
                    INSERT INTO alerts (case_id, typology, gnn_score, created_at, payload)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (case_id, typology, score, datetime.now() - timedelta(minutes=30), str(payload).replace("'", '"'))
                )
            
            # Insert evidence blocks
            evidence = [
                ('CASE-2847', 'alert_created', {'hash': '0x3a8f...2c19', 'event': 'Initial alert'}),
                ('CASE-2847', 'case_opened', {'hash': '0x7b2e...8d4a', 'event': 'Investigator opened'}),
                ('CASE-2847', 'subgraph_exported', {'hash': '0x9c1d...3f7b', 'event': 'Subgraph exported'}),
            ]
            
            for case_id, block_type, payload in evidence:
                cur.execute(
                    """
                    INSERT INTO evidence_blocks (case_id, block_type, payload, created_at)
                    VALUES (%s, %s, %s::jsonb, %s)
                    """,
                    (case_id, block_type, str(payload).replace("'", '"'), datetime.now() - timedelta(minutes=20))
                )
        
        conn.commit()
    
    print("✅ PostgreSQL seeded")


def seed_neo4j():
    """Seed Neo4j with account graph data."""
    print("🔄 Seeding Neo4j...")
    
    with neo4j_db.get_session() as session:
        # Create accounts
        accounts = [
            ('ACC-0041', 'Savings', 'Tier-2', True, 4723000, 'high', 'Rajesh Kumar'),
            ('ACC-0112', 'Current', 'Tier-3', False, 780000, 'medium', 'Priya Sharma'),
            ('ACC-0203', 'Savings', 'Tier-2', False, 910000, 'medium', 'Amit Patel'),
            ('ACC-0089', 'Current', 'Tier-1', False, 4680000, 'high', 'Suresh Industries'),
            ('ACC-0317', 'Savings', 'Tier-2', False, 840000, 'medium', 'Neha Gupta'),
            ('ACC-0455', 'Current', 'Tier-3', False, 890000, 'medium', 'Vikram Mehta'),
        ]
        
        for acc_id, acc_type, kyc, dormant, volume, risk, owner in accounts:
            session.run(
                """
                MERGE (a:Account {account_id: $account_id})
                SET a.account_type = $account_type,
                    a.kyc_tier = $kyc_tier,
                    a.is_dormant = $is_dormant,
                    a.total_volume = $total_volume,
                    a.risk_level = $risk_level,
                    a.owner = $owner
                """,
                account_id=acc_id,
                account_type=acc_type,
                kyc_tier=kyc,
                is_dormant=dormant,
                total_volume=volume,
                risk_level=risk,
                owner=owner
            )
        
        # Create transfers for CASE-2847
        transfers = [
            ('ACC-0041', 'ACC-0112', 780000, 'NEFT', 'CASE-2847'),
            ('ACC-0041', 'ACC-0203', 910000, 'UPI', 'CASE-2847'),
            ('ACC-0112', 'ACC-0089', 780000, 'NEFT', 'CASE-2847'),
            ('ACC-0203', 'ACC-0089', 910000, 'UPI', 'CASE-2847'),
            ('ACC-0089', 'ACC-0317', 840000, 'IMPS', 'CASE-2847'),
            ('ACC-0089', 'ACC-0455', 890000, 'NEFT', 'CASE-2847'),
            ('ACC-0317', 'ACC-0041', 840000, 'NEFT', 'CASE-2847'),
            ('ACC-0455', 'ACC-0041', 890000, 'UPI', 'CASE-2847'),
        ]
        
        for src, tgt, amount, channel, case_id in transfers:
            session.run(
                """
                MATCH (a:Account {account_id: $src})
                MATCH (b:Account {account_id: $tgt})
                MERGE (a)-[t:TRANSFERRED_TO]->(b)
                SET t.amount = $amount,
                    t.channel = $channel,
                    t.case_id = $case_id,
                    t.timestamp = datetime()
                """,
                src=src,
                tgt=tgt,
                amount=amount,
                channel=channel,
                case_id=case_id
            )
    
    print("✅ Neo4j seeded")


async def seed_redis():
    """Seed Redis with sample alert channel data."""
    print("🔄 Seeding Redis...")
    client = redis_client.get_client()
    
    # Publish a test alert
    await client.publish(
        'alerts',
        '{"case_id": "CASE-2847", "typology": "Round-trip Layering", "score": 0.94}'
    )
    
    print("✅ Redis seeded (published test alert)")


def main():
    print("=" * 60)
    print("🌱 FundLens Database Seeding")
    print("=" * 60)
    
    # Connect to databases
    print("\n📡 Connecting to databases...")
    neo4j_db.connect()
    postgres_db.connect()
    redis_client.connect()
    print("✅ Connected\n")
    
    # Seed each database
    try:
        seed_postgres()
        seed_neo4j()
        asyncio.run(seed_redis())
        
        print("\n" + "=" * 60)
        print("✅ Seeding complete!")
        print("=" * 60)
        print("\nYou can now:")
        print("  • View alerts:     http://localhost:8000/api/alerts")
        print("  • View cases:      http://localhost:8000/api/cases")
        print("  • View graph:      http://localhost:8000/api/graph/CASE-2847")
        print("  • View entity:     http://localhost:8000/api/entities/ACC-0041")
        print("  • View blockchain: http://localhost:8000/api/blockchain/case/CASE-2847")
        print("\nFrontend: http://localhost:5173")
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        raise
    finally:
        # Cleanup
        postgres_db.close()
        neo4j_db.close()
        # Skip Redis close to avoid event loop error
        # asyncio.run(redis_client.close())


if __name__ == "__main__":
    main()
