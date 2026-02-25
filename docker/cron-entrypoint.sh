#!/bin/sh
set -eu

if [ -n "${TZ:-}" ]; then
  ZONEINFO="/usr/share/zoneinfo/${TZ}"
  if [ -f "${ZONEINFO}" ]; then
    ln -snf "${ZONEINFO}" /etc/localtime
    echo "${TZ}" > /etc/timezone || true
  fi
fi

mkdir -p /var/log/cron /app/reports

if [ ! -f /app/ext_conf/crontab.ini ]; then
  echo "Missing /app/ext_conf/crontab.ini"
  exit 1
fi

crontab /app/ext_conf/crontab.ini

exec cron -f
