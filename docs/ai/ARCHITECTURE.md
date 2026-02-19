# Architecture Map

## Application surfaces

## Web app
- Entry: `app.py`
- Purpose: UI, auth/user flows, device management pages
- Upstream binding in Docker: `0.0.0.0:8000` (inside `app` service)

## API app
- Entry: `api.py`
- Purpose: device/link/update endpoints and API-related flows
- Upstream binding in Docker: `0.0.0.0:8001` (inside `app` service)

## Data layer

- SQLite database file stored in volume at `/app/data/database.db`
- Database bootstrapped from `database.opensource.db` via `docker/entrypoint.sh`
- Redis used for runtime cache/frequency checks and transient state
- Redis runs inside the `app` container for low-resource single-node deployments

## Edge layer (Nginx)

Source: `ext_conf/docker/nginx.conf.template`

Key responsibilities:
- Redirect HTTP (`80`) to HTTPS (`443`)
- Terminate TLS using env-driven cert/key paths
- Route by host:
  - `WLP_SERVER_NAME` -> `WLP_WEB_UPSTREAM`
  - `WLP_API_SERVER_NAME` -> `WLP_API_UPSTREAM`
- Propagate forwarding headers
- Support Cloudflare real client IP via `CF-Connecting-IP`

## Background processing

## Cron service
- Entrypoint: `docker/cron-entrypoint.sh`
- Schedule source: `ext_conf/crontab.ini`
- Main jobs:
  - `email_alerts_cron.py`
  - `sms_alerts_cron.py`
  - daily/full report generation from Nginx logs
  - report retention cleanup

## GoAccess service
- Runner: `ext_conf/docker/goaccess-runner.sh`
- Reads Nginx logs from shared volume
- Writes reports to shared reports volume (`/reports`)

## Volumes (compose source of truth)

- `wlp_data` -> app/cron DB persistence
- `wlp_reports` -> generated HTML reports used by app
- `wlp_nginx_logs` -> logs consumed by goaccess/cron report jobs

## Design constraints

- Keep API as subdomain of same base domain for minimal deployment model.
- Keep ingress centralized in Nginx (`80/443` only).
- Keep SQLite-first architecture unless explicitly migrated.
