#!/usr/bin/env bash
set -euo pipefail

# Docker smoke test for local/CI execution.
#
# What this script validates:
# 1) Docker services build and start correctly.
# 2) Nginx redirects HTTP to HTTPS.
# 3) Web and API are reachable through Nginx host-based routing.
# 4) GoAccess live reports are generated in the shared reports volume.
# 5) Redis is reachable inside the app container.
#
# Notes:
# - This script is intentionally strict and exits on first failure.
# - It copies .env.example to .env for deterministic local/CI behavior.
# - It always tears down the stack (including volumes) on exit.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker/docker-compose.yml"

START_RETRIES=30
HTTP_RETRIES=30
REPORT_RETRIES=40
RETRY_SLEEP_SECONDS=3

cd "$ROOT_DIR"

# Use a known env baseline for smoke checks.
cp .env.example .env

read_env_value() {
  key="$1"
  grep -E "^${key}=" .env | tail -n 1 | cut -d= -f2- || true
}

# Load host headers from env file to match nginx domain routing.
BASE_DOMAIN="$(read_env_value WLP_BASE_DOMAIN)"
API_SUBDOMAIN="$(read_env_value WLP_API_SUBDOMAIN)"
BASE_DOMAIN="${BASE_DOMAIN:-localhost}"
API_SUBDOMAIN="${API_SUBDOMAIN:-api}"

WEB_HOST_HEADER="$(read_env_value WLP_SERVER_NAME)"
API_HOST_HEADER="$(read_env_value WLP_API_SERVER_NAME)"

if [ -z "${WEB_HOST_HEADER}" ]; then
  WEB_HOST_HEADER="${BASE_DOMAIN}"
fi

if [ -z "${API_HOST_HEADER}" ]; then
  if [ "${API_SUBDOMAIN}" = "@" ] || [ -z "${API_SUBDOMAIN}" ]; then
    API_HOST_HEADER="${BASE_DOMAIN}"
  else
    API_HOST_HEADER="${API_SUBDOMAIN}.${BASE_DOMAIN}"
  fi
fi

cleanup() {
  exit_status=$?
  if [ "${SMOKE_KEEP_STACK_ON_FAIL:-0}" = "1" ] && [ "$exit_status" -ne 0 ]; then
    echo "[info] preserving stack for post-failure diagnostics"
    return
  fi

  # Always clean resources to keep CI/local runs reproducible.
  docker compose -f "$COMPOSE_FILE" down -v >/dev/null 2>&1 || true
}
trap cleanup EXIT

fail() {
  message="$1"
  echo "[fail] $message"
  echo "[debug] docker compose ps"
  docker compose -f "$COMPOSE_FILE" ps || true
  echo "[debug] docker compose logs (tail=200)"
  docker compose -f "$COMPOSE_FILE" logs --no-color --tail=200 || true
  exit 1
}

# Build application image and start runtime services.
docker compose -f "$COMPOSE_FILE" build app
GOACCESS_REFRESH_SECONDS=5 docker compose -f "$COMPOSE_FILE" up -d app nginx cron goaccess

# Wait until all expected services are in running state.
for i in $(seq 1 "$START_RETRIES"); do
  running_count=$(docker compose -f "$COMPOSE_FILE" ps --status running --services | wc -l)
  if [ "$running_count" -ge 4 ]; then
    echo "[ok] services running"
    break
  fi

  if [ "$i" -eq "$START_RETRIES" ]; then
    fail "services did not reach running state"
  fi

  sleep "$RETRY_SLEEP_SECONDS"
done

# Validate Redis process inside app container.
for i in $(seq 1 "$HTTP_RETRIES"); do
  if docker compose -f "$COMPOSE_FILE" exec -T app sh -lc 'redis-cli -h 127.0.0.1 -p 6379 ping | grep -q PONG'; then
    echo "[ok] redis in app"
    break
  fi

  if [ "$i" -eq "$HTTP_RETRIES" ]; then
    fail "redis in app"
  fi

  sleep "$RETRY_SLEEP_SECONDS"
done

# Ensure nginx TLS socket is responsive before route checks.
for i in $(seq 1 "$HTTP_RETRIES"); do
  if curl -kIsS --connect-timeout 2 https://localhost >/dev/null 2>&1; then
    echo "[ok] https listener ready"
    break
  fi

  if [ "$i" -eq "$HTTP_RETRIES" ]; then
    fail "https listener not ready"
  fi

  sleep "$RETRY_SLEEP_SECONDS"
done

# Validate redirect policy: HTTP must redirect to HTTPS.
for i in $(seq 1 "$HTTP_RETRIES"); do
  if curl -sSI --connect-timeout 2 -H "Host: $WEB_HOST_HEADER" http://localhost/ping | grep -qE '^HTTP/.* 301'; then
    echo "[ok] http->https redirect"
    break
  fi

  if [ "$i" -eq "$HTTP_RETRIES" ]; then
    fail "http->https redirect"
  fi

  sleep "$RETRY_SLEEP_SECONDS"
done

# Validate web route through nginx virtual host.
for i in $(seq 1 "$HTTP_RETRIES"); do
  if curl -kfsS --connect-timeout 2 -H "Host: $WEB_HOST_HEADER" "https://localhost/ping" | grep -q "PONG"; then
    echo "[ok] web smoke"
    break
  fi

  if [ "$i" -eq "$HTTP_RETRIES" ]; then
    fail "web smoke"
  fi

  sleep "$RETRY_SLEEP_SECONDS"
done

# Validate api route through nginx virtual host.
for i in $(seq 1 "$HTTP_RETRIES"); do
  if curl -kfsS --connect-timeout 2 -H "Host: $API_HOST_HEADER" "https://localhost/link" | grep -q "FAIL"; then
    echo "[ok] api smoke"
    break
  fi

  if [ "$i" -eq "$HTTP_RETRIES" ]; then
    fail "api smoke"
  fi

  sleep "$RETRY_SLEEP_SECONDS"
done

# Generate traffic so GoAccess has recent entries to process.
curl -kfsS -H "Host: $WEB_HOST_HEADER" "https://localhost/ping" >/dev/null
curl -kfsS -H "Host: $API_HOST_HEADER" "https://localhost/link" >/dev/null || true

# Wait for GoAccess live reports in shared reports volume.
for i in $(seq 1 "$REPORT_RETRIES"); do
  if docker compose -f "$COMPOSE_FILE" exec -T app sh -lc 'test -f /app/reports/WEB_LIVE.html && test -f /app/reports/API_LIVE.html'; then
    echo "[ok] goaccess smoke"
    break
  fi

  if [ "$i" -eq "$REPORT_RETRIES" ]; then
    fail "goaccess smoke"
  fi

  sleep "$RETRY_SLEEP_SECONDS"
done

echo "ALL_SMOKE_TESTS_PASSED"
