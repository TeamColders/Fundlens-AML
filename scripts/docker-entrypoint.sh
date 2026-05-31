#!/bin/sh
set -e

export PYTHONPATH="${PYTHONPATH:-/app}"
DATA_DIR="${FUNDLENS_DATA_DIR:-/data}"
mkdir -p "${DATA_DIR}"

# Copy baked-in seed DB on first boot (avoids ~30s seed on cold start)
if [ ! -f "${DATA_DIR}/fundlens_demo.db" ] && [ -f /app/seed-data/fundlens_demo.db ]; then
  echo "==> Initializing data volume from image seed..."
  cp -a /app/seed-data/. "${DATA_DIR}/"
fi

if [ "${FUNDLENS_AUTO_SEED:-1}" = "1" ]; then
  if [ ! -f "${DATA_DIR}/fundlens_demo.db" ]; then
    echo "==> Seeding demo data (first boot, no baked seed)..."
    FUNDLENS_DATA_DIR="${DATA_DIR}" python backend/database/demo_seed.py --mode local
  fi
fi

PORT="${PORT:-8000}"
echo "==> FundLens ready — API + UI on 0.0.0.0:${PORT} (data: ${DATA_DIR})"
exec python -m uvicorn backend.api.main:app --host 0.0.0.0 --port "${PORT}"
