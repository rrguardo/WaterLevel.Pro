#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

docker compose \
  --env-file "$ROOT_DIR/.env" \
  -f "$ROOT_DIR/docker/docker-compose.yml" \
  logs -f --tail=200 "$@"
