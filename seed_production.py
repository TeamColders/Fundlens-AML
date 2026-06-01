"""
Seed production databases with sample data.
Run: python seed_production.py
"""
import os
from dotenv import load_dotenv

# Load production environment variables
load_dotenv('.env.production')

# Now run the seed script
from backend.seed_data import main

if __name__ == "__main__":
    print("🚀 Seeding PRODUCTION databases")
    print("=" * 60)
    print(f"Neo4j: {os.getenv('NEO4J_URI')}")
    print(f"Postgres: {os.getenv('POSTGRES_DSN')[:50]}...")
    print(f"Redis: {os.getenv('REDIS_URL')[:50]}...")
    print("=" * 60)
    
    confirm = input("\n⚠️  This will write to PRODUCTION databases. Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Aborted")
        exit(1)
    
    main()
