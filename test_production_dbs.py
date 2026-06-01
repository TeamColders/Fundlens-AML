"""
Test production database connections before deployment.
Run: python test_production_dbs.py
"""
import os
from dotenv import load_dotenv

# Load production environment variables
load_dotenv('.env.production')

print("=" * 60)
print("🔍 Testing Production Database Connections")
print("=" * 60)

# Test Neo4j
print("\n1️⃣  Testing Neo4j Aura...")
try:
    from neo4j import GraphDatabase
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER')
    password = os.getenv('NEO4J_PASSWORD')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        record = result.single()
        if record and record['test'] == 1:
            print("   ✅ Neo4j connection successful!")
            print(f"   URI: {uri}")
        else:
            print("   ❌ Neo4j query failed")
    driver.close()
except Exception as e:
    print(f"   ❌ Neo4j connection failed: {e}")

# Test PostgreSQL
print("\n2️⃣  Testing Neon PostgreSQL...")
try:
    import psycopg2
    dsn = os.getenv('POSTGRES_DSN')
    
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("SELECT 1 as test")
    result = cur.fetchone()
    if result and result[0] == 1:
        print("   ✅ PostgreSQL connection successful!")
        print(f"   Host: {dsn.split('@')[1].split('/')[0]}")
    else:
        print("   ❌ PostgreSQL query failed")
    cur.close()
    conn.close()
except Exception as e:
    print(f"   ❌ PostgreSQL connection failed: {e}")

# Test Redis
print("\n3️⃣  Testing Upstash Redis...")
try:
    from redis import asyncio as redis
    import asyncio
    
    async def test_redis():
        url = os.getenv('REDIS_URL')
        client = redis.from_url(url, decode_responses=True)
        await client.ping()
        print("   ✅ Redis connection successful!")
        print(f"   Host: {url.split('@')[1].split(':')[0]}")
        await client.close()
    
    asyncio.run(test_redis())
except Exception as e:
    print(f"   ❌ Redis connection failed: {e}")

print("\n" + "=" * 60)
print("✅ All database connections tested!")
print("=" * 60)
print("\nNext steps:")
print("1. Run: python seed_production.py")
print("2. Push to GitHub: git push origin main")
print("3. Deploy to Vercel: https://vercel.com/new")
print("=" * 60)
