#!/bin/sh
set -eu

mkdir -p /var/log/cron /app/reports

if [ ! -f /app/ext_conf/crontab.ini ]; then
  echo "Missing /app/ext_conf/crontab.ini"
  exit 1
fi

crontab /app/ext_conf/crontab.ini

exec cron -f
