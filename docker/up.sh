#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  if [[ -f "$ROOT_DIR/.env.example" ]]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    echo "[wlp] .env not found. Created from .env.example"
  else
    echo "[wlp] Missing .env and .env.example in $ROOT_DIR"
    exit 1
  fi
fi

# Compose variable interpolation does NOT use env_file; it uses the process environment.
# Load .env so values like WLP_SERVER_NAME/WLP_API_SERVER_NAME are available for interpolation.
set -a
# shellcheck disable=SC1090
. "$ROOT_DIR/.env"
set +a

docker compose \
  -f "$ROOT_DIR/docker/docker-compose.yml" \
  up --build "$@"
