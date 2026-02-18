#!/bin/sh
set -eu

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
