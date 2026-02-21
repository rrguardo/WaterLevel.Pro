#!/usr/bin/env bash
set -euo pipefail

# Cron implementations often run jobs with a minimal environment.
# In containers, the full environment is typically present on PID 1.
# This helper re-imports that environment so cron jobs can reliably access needed variables.
#
# IMPORTANT: Do not use `export $(...)` here. Values like EMAIL_SENDER can include spaces/quotes
# and would get split incorrectly.

if [[ ! -r /proc/1/environ ]]; then
  exit 0
fi

while IFS= read -r -d '' kv; do
  case "$kv" in
    WLP_*=*|APP_DOMAIN=*|API_DOMAIN=*|DEV_MODE=*|DEMO_*=*|REDIS_*=*|DATABASE_URL=*|SMTP_*=*|EMAIL_SENDER=*|APP_SEC_KEY=*|APP_RECAPTCHA_SECRET_KEY=*|RECAPTCHA_PUBLIC_KEY=*|TWILIO_*=*|API_CACHE_*=*|WEB_CACHE_*=*|GOACCESS_REFRESH_SECONDS=*)
      export "$kv"
      ;;
  esac
done < /proc/1/environ
