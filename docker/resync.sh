#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker/docker-compose.yml"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  if [[ -f "$ROOT_DIR/.env.example" ]]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    echo "[wlp] .env not found. Created from .env.example"
  else
    echo "[wlp] Missing .env and .env.example in $ROOT_DIR"
    exit 1
  fi
fi

BUILD_FLAG="--build"
FORCE_RECREATE_FLAG="--force-recreate"
INCLUDE_GOACCESS="0"

for arg in "$@"; do
  case "$arg" in
    --no-build)
      BUILD_FLAG=""
      ;;
    --no-recreate)
      FORCE_RECREATE_FLAG=""
      ;;
    --full)
      INCLUDE_GOACCESS="1"
      ;;
    --help|-h)
      cat <<'EOF'
Usage: ./docker/resync.sh [options]

Rebuild/recreate runtime services so local code and .env changes are applied.
This keeps named volumes intact (database/reports/logs are not removed).

Options:
  --no-build      Skip image build step and only recreate containers
  --no-recreate   Reuse containers when possible (no forced recreation)
  --full          Also include goaccess service in the resync
  -h, --help      Show this help
EOF
      exit 0
      ;;
    *)
      echo "[wlp] Unknown option: $arg"
      echo "[wlp] Use --help to see supported options."
      exit 1
      ;;
  esac
done

SERVICES=(app nginx cron)
if [[ "$INCLUDE_GOACCESS" == "1" ]]; then
  SERVICES+=(goaccess)
fi

echo "[wlp] Resync services: ${SERVICES[*]}"

docker compose \
  -f "$COMPOSE_FILE" \
  up -d $BUILD_FLAG $FORCE_RECREATE_FLAG "${SERVICES[@]}"

echo "[wlp] Resync complete."
echo "[wlp] Optional quick check: ./scripts/docker_smoke_test.sh"
