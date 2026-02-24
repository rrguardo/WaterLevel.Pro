#!/bin/sh
set -eu

if [ -n "${TZ:-}" ]; then
  ZONEINFO="/usr/share/zoneinfo/${TZ}"
  if [ -f "${ZONEINFO}" ]; then
    ln -snf "${ZONEINFO}" /etc/localtime
    echo "${TZ}" > /etc/timezone || true
  fi
fi

DB_TARGET="/app/data/database.db"

if [ ! -f "$DB_TARGET" ] && [ -f database.opensource.db ]; then
  echo "[entrypoint] /app/data/database.db not found. Building demo DB from database.opensource.db"
  python3.14 scripts/reset_demo_db.py --target "$DB_TARGET" --source database.opensource.db
fi

exec "$@"
