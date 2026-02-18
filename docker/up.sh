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

docker compose \
  -f "$ROOT_DIR/docker/docker-compose.yml" \
  up --build "$@"
