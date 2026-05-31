#!/bin/bash

# FundLens Quick Start Script
# Automates the 5-step setup process

set -e

PROJECT_DIR="/home/nathanpimenta/Projects/Fundlens-AML"
cd "$PROJECT_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        FundLens AML Fraud Detection System                 ║"
echo "║              Quick Start Setup (5 steps)                   ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Step 1: Check Python
echo ""
echo "📌 Step 1/5: Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi
python3 --version

# Step 2: Create virtual environment
echo ""
echo "📌 Step 2/5: Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Step 3: Install dependencies
echo ""
echo "📌 Step 3/5: Installing dependencies (this may take 2-3 min)..."
source venv/bin/activate
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Step 4: Start Docker services
echo ""
echo "📌 Step 4/5: Starting Docker services..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Desktop"
    exit 1
fi

docker-compose down -v 2>/dev/null || true
docker-compose up -d

echo "⏳ Waiting for services to be healthy (30 seconds)..."
sleep 30

# Check health
HEALTH=$(docker-compose ps 2>/dev/null | grep -c "healthy" || echo "0")
if [ "$HEALTH" -gt "0" ]; then
    echo "✅ Docker services are running"
    docker-compose ps
else
    echo "⚠️  Some services may still be starting. Check with: docker-compose ps"
fi

# Step 5: Seed graph
echo ""
echo "📌 Step 5/5: Seeding Neo4j graph with synthetic data..."
echo "   (This will generate 10,000 transactions in Neo4j)"
python -m backend.graph.seed_graph

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ SETUP COMPLETE!                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Next: Start the backend in a new terminal with:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   uvicorn backend.api.main:app --reload --port 8000"
echo ""
echo "📊 Then access:"
echo "   - API Docs:  http://localhost:8000/docs"
echo "   - Alerts:    http://localhost:8000/api/alerts"
echo "   - Neo4j:     http://localhost:7474 (neo4j/fundlens123)"
echo ""
echo "📚 Full README: cat README.md"
echo ""
