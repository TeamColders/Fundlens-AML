#!/usr/bin/env bash
# FundLens — one-command local demo for iDEA Round 2 (PS3: Fund Flow Tracking)
set -e
cd "$(dirname "$0")"

if [ ! -f .env ] && [ -f .env.example ]; then
  echo "==> Copy .env.example to .env and set GEMINI_API_KEY for live STR generation"
  cp -n .env.example .env 2>/dev/null || true
fi

echo "==> Seeding demo data (SQLite — no Docker required)"
python3 backend/database/demo_seed.py --mode local

echo ""
echo "==> Install Python deps: pip install -r requirements.txt"
echo "    (Python 3.11–3.13; uses wheels — no g++ required for demo)"
echo ""
echo "==> Start backend (terminal 1):"
echo "    python3 -m uvicorn backend.api.main:app --reload --port 8000"
echo ""
echo "==> Start frontend (terminal 2):"
echo "    npm install && npm run dev"
echo ""
echo "==> Open http://localhost:5173"
echo "    • Select a case → Generate STR Report (uses Gemini if GEMINI_API_KEY is set)"
echo "    • Save draft / Download PDF / Download .txt on STR screen"
echo ""
echo "==> API: curl http://localhost:8000/api/health"
