#!/bin/sh
set -eu

if [ -n "${TZ:-}" ]; then
  if [ ! -d /usr/share/zoneinfo ]; then
    if command -v apk >/dev/null 2>&1; then
      apk add --no-cache tzdata >/dev/null || true
    elif command -v apt-get >/dev/null 2>&1; then
      apt-get update >/dev/null 2>&1 || true
      apt-get install -y --no-install-recommends tzdata >/dev/null 2>&1 || true
      rm -rf /var/lib/apt/lists/* 2>/dev/null || true
    fi
  fi

  ZONEINFO="/usr/share/zoneinfo/${TZ}"
  if [ -f "${ZONEINFO}" ]; then
    ln -snf "${ZONEINFO}" /etc/localtime
    echo "${TZ}" > /etc/timezone || true
  fi
fi

mkdir -p /reports

while true; do
  if [ -f /var/log/nginx/wlp_web_access.log ]; then
    goaccess /var/log/nginx/wlp_web_access.log \
      -o /reports/WEB_LIVE.html \
      --log-format=COMBINED
  fi

  if [ -f /var/log/nginx/wlp_api_access.log ]; then
    goaccess /var/log/nginx/wlp_api_access.log \
      -o /reports/API_LIVE.html \
      --log-format=COMBINED
  fi

  find /reports -type f -mtime +14 -delete || true
  sleep "${GOACCESS_REFRESH_SECONDS:-600}"
done
