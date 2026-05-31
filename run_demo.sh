#!/usr/bin/env bash
# FundLens — one-command local demo for iDEA Round 2 (PS3: Fund Flow Tracking)
set -e
cd "$(dirname "$0")"

echo "==> Seeding demo data (SQLite — no Docker required)"
python3 backend/database/demo_seed.py --mode local

echo ""
echo "==> Start backend (terminal 1):"
echo "    python3 -m uvicorn backend.api.main:app --reload --port 8000"
echo ""
echo "==> Start frontend (terminal 2):"
echo "    npm run dev"
echo ""
echo "==> Open http://localhost:5173 — dashboard graph + /graph for full view"
echo "==> API health: curl http://localhost:8000/api/health"
