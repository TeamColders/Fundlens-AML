# FundLens — Backend Only API Image
#
# Build:  docker build -f Dockerfile.api -t fundlens-api:latest .
# Run:    docker run --rm -p 8000:8000 -e GEMINI_API_KEY=... fundlens-api:latest

FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FUNDLENS_DATA_DIR=/data \
    FUNDLENS_AUTO_SEED=1 \
    SERVE_FRONTEND=0 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY data ./data
COPY scripts/docker-entrypoint.sh /entrypoint.sh

# Pre-bake demo SQLite so first container start is fast
RUN mkdir -p /app/seed-data \
    && FUNDLENS_DATA_DIR=/app/seed-data python backend/database/demo_seed.py --mode local

RUN chmod +x /entrypoint.sh \
    && mkdir -p /data

VOLUME ["/data"]
EXPOSE 8000

LABEL org.opencontainers.image.title="FundLens AML API" \
      org.opencontainers.image.description="AML investigation demo Backend API"

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import os, urllib.request; p=os.environ.get('PORT','8000'); urllib.request.urlopen(f'http://127.0.0.1:{p}/api/health')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
