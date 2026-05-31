#!/usr/bin/env bash
# Build and optionally smoke-test the FundLens production image.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${FUNDLENS_IMAGE:-fundlens:latest}"
SMOKE="${SMOKE_TEST:-1}"

cd "$ROOT"

if command -v docker >/dev/null 2>&1; then
  BUILDER=docker
elif command -v podman >/dev/null 2>&1; then
  BUILDER=podman
else
  echo "Error: install docker or podman" >&2
  exit 1
fi

echo "==> Building ${IMAGE} with ${BUILDER}..."
"${BUILDER}" build -t "${IMAGE}" .

if [ "${SMOKE}" = "1" ]; then
  echo "==> Smoke test (health + alerts)..."
  CID="$("${BUILDER}" run -d -p 127.0.0.1:18000:8000 "${IMAGE}")"
  cleanup() { "${BUILDER}" rm -f "${CID}" >/dev/null 2>&1 || true; }
  trap cleanup EXIT

  for i in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:18000/api/health" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  curl -sf "http://127.0.0.1:18000/api/health" | head -c 200
  echo ""
  ALERTS="$(curl -sf "http://127.0.0.1:18000/api/alerts" | head -c 120)"
  echo "alerts: ${ALERTS}..."
  echo "==> Smoke test passed"
fi

echo "==> Done. Run: ${BUILDER} run --rm -p 8000:8000 -e GEMINI_API_KEY=... ${IMAGE}"
