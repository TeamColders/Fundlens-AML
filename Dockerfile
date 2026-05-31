# FundLens — production image (API + built React UI on one port)
#
# Build:  docker build -t fundlens:latest .
# Run:    docker run --rm -p 8000:8000 -e GEMINI_API_KEY=... fundlens:latest
# Or:     docker compose -f docker-compose.prod.yml up --build

# ── Frontend build ───────────────────────────────────────────────
FROM node:20-alpine AS frontend
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.ts ./
COPY src ./src

# Same-origin API when UI is served by FastAPI
ENV VITE_API_URL=
RUN npm run build

# ── Python API ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FUNDLENS_DATA_DIR=/data \
    FUNDLENS_AUTO_SEED=1 \
    SERVE_FRONTEND=1 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY data ./data
COPY scripts/docker-entrypoint.sh /entrypoint.sh
COPY --from=frontend /app/dist ./dist

# Pre-bake demo SQLite so first container start is fast (copied to /data on boot)
RUN mkdir -p /app/seed-data \
    && FUNDLENS_DATA_DIR=/app/seed-data python backend/database/demo_seed.py --mode local

RUN chmod +x /entrypoint.sh \
    && mkdir -p /data

VOLUME ["/data"]
EXPOSE 8000

LABEL org.opencontainers.image.title="FundLens AML" \
      org.opencontainers.image.description="AML investigation demo — FastAPI + React" \
      org.opencontainers.image.source="https://github.com/fundlens/fundlens-aml"

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import os, urllib.request; p=os.environ.get('PORT','8000'); urllib.request.urlopen(f'http://127.0.0.1:{p}/api/health')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
