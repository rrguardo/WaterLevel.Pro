# Docker guide

This folder contains Docker-related configuration and runtime scripts.

Fast setup from zero (test/real domain):
- [`docs/SETUP_DOCKER_FAST.md`](../docs/SETUP_DOCKER_FAST.md)
- AI-agent deploy handoff (real VPS + Cloudflare options): [`docs/DEPLOY_VPS_AI_AGENT_README.md`](../docs/DEPLOY_VPS_AI_AGENT_README.md)

## Quick start

1. Copy `.env.example` to `.env` at repository root.
2. Start all services:
	- `docker compose -f docker/docker-compose.yml up --build`
   - or: `./docker/up.sh`
	  - `up.sh` auto-creates `.env` from `.env.example` if missing
3. Open services:
	- Web (via Nginx): `https://localhost`
	- API (via Nginx host rule): `https://api.localhost`

Stop services:
- `./docker/down.sh`

View logs:
- `./docker/logs.sh`

Build app image directly:
- `docker build -f docker/Dockerfile -t rguardo/waterlevel-pro:latest .`

Publish image to Docker Hub:
- `docker login`
- `docker push rguardo/waterlevel-pro:latest`

## Runtime notes

- Redis runs inside the `app` container (port `6379` internal).
- Web and API run in the same `app` container (ports `8000` and `8001`).
- A dedicated `cron` container runs scheduled jobs from `ext_conf/crontab.ini`.
- SQLite persists in a Docker volume (`wlp_data`).
- On first run, `/app/data/database.db` is auto-created from `database.opensource.db`.
- Relay daily consumption stats are persisted in SQLite table `relay_daily_stats`
	(auto-created at runtime on first relay update handling, no manual migration required).
- Nginx writes access logs to a shared volume used by GoAccess.
- GoAccess generates live reports in `/app/reports` (mounted in `web` service).

Cron jobs in Docker include:

- alert workers (`email_alerts_cron.py`, `sms_alerts_cron.py`)
- demo S1 device simulator every 30 seconds (`scripts/s1_demo_device_service.py`, env keys `DEMO_S1_PUB_KEY`/`DEMO_S1_PRV_KEY`)
- demo relay R1 simulator every 30 seconds (`scripts/r1_demo_relay_service.py`, env keys `DEMO_RELAY_PUB_KEY`/`DEMO_RELAY_PRV_KEY`)
- daily/fulls reports from Nginx logs into `/app/reports`
- old report cleanup (retention)

Runtime Redis note:

- Redis DB indexes are fixed internally for minimal setup:
	- runtime keys: DB `0`
	- web cache: DB `1`
	- api cache: DB `2`

## Networking and hostnames

Nginx hostnames/upstreams are configurable through `.env`:

- `WLP_BASE_DOMAIN` (default: `localhost`)
- `WLP_API_SUBDOMAIN` (default: `api`)
- `WLP_WEB_UPSTREAM` (default: `app:8000`)
- `WLP_API_UPSTREAM` (default: `app:8001`)
- `WLP_SSL_CERT_PATH` (default: `/etc/nginx/certs/localhost.crt`)
- `WLP_SSL_KEY_PATH` (default: `/etc/nginx/certs/localhost.key`)
- `WLP_APP_IMAGE` (default: `rguardo/waterlevel-pro:latest`)

Timezone in Docker:

- `WLP_TZ` (default: `America/Santo_Domingo`, UTC-4 no DST)

Optional tracking and ads (disabled by default, app service only):

- `WLP_ENABLE_TRACKING` (default: `false`)
- `WLP_GA_MEASUREMENT_ID` (default: empty)
- `WLP_TWITTER_PIXEL_ID` (default: empty)
- `WLP_ENABLE_ADSENSE` (default: `false`)
- `WLP_ADSENSE_CLIENT_ID` (default: empty)

Minimal DNS layout (recommended for this SQLite-oriented setup):

- Web app on root domain: `example.com`
- API on subdomain of the same domain: `api.example.com`

This keeps routing, CORS, and deployment simple while the project is focused on
a single-node SQLite architecture (without external SQL server topology).

Nginx behavior in Docker:

- HTTP (`80`) always redirects to HTTPS (`443`).
- HTTPS routing is domain-based at Nginx level:
	- `${WLP_SERVER_NAME}` -> web upstream
	- `${WLP_API_SERVER_NAME}` -> api upstream
- Cloudflare real client IP is enabled through `CF-Connecting-IP` + trusted Cloudflare CIDRs.
- If configured cert/key files are missing, `nginx-entrypoint.sh` auto-generates a temporary self-signed cert in `/tmp/wlp-certs` (useful for CI and fresh local clones).

Example `.env` for production:

- `WLP_BASE_DOMAIN=example.com`
- `WLP_API_SUBDOMAIN=api`

After changing DNS values, recreate the stack:

- `docker compose -f docker/docker-compose.yml up -d --build`

To apply cron schedule changes from `ext_conf/crontab.ini`, recreate the `cron` service:

- `docker compose -f docker/docker-compose.yml up -d --build cron`

## Production on a VPS with system nginx (this deployment)

The VPS runs a system nginx that owns `:80`/`:443`, so the container must not
bind those ports. Use the override file:

- `docker compose -f docker/docker-compose.yml -f docker/docker-compose.vps-proxy.yml up -d`
  (`ports: !override` in that file replaces the base 80/443 bindings; Compose
  appends lists otherwise — requires Compose >= 2.24.4)

That publishes `127.0.0.1:8080 -> 80` and `127.0.0.1:8443 -> 443`. Never merge
those ports into `docker-compose.yml`: the default file must keep `80:80`/`443:443`
for standalone/local use. Traffic path: Cloudflare → host nginx `:80`/stream
`:443` → `127.0.0.1:8080`/`:8443` → this stack.

Rules that avoid self-inflicted outages:

- **nginx image is pinned in `docker-compose.yml`.** It is `nginx:1.30-alpine`
  since 2026-11 (fixes the Nov-2026 CVE batch incl. CVE-2026-118899). The
  `1.27-alpine` tag is EOL/frozen since Apr 2025 — never downgrade to it. To
  bump: change the tag, `docker compose pull nginx`, then
  `docker compose up -d --no-deps nginx` (a few seconds of downtime, no DB impact).
- **The crontab is baked into the image.** `docker/cron-entrypoint.sh` runs
  `crontab /app/ext_conf/crontab.ini`; that path is not mounted, so editing the
  host copy does nothing until the image is rebuilt/recreated. Recreate with
  `docker compose up -d --force-recreate cron` after a rebuild.
- **Daily report jobs need rotated logs.** The crontab lines guard on
  `wlp_web_access.log.1` / `wlp_api_access.log.1`; without rotation they never
  run. Install `docker/logrotate-wlp-nginx.conf` (see below).
- **TLS at the origin is a Cloudflare Origin CA cert** (15-year, in
  `ext_conf/docker/certs/`). Let's Encrypt/certbot is not needed and must not be
  re-enabled for `waterlevel.pro`.
- **systemd unit**: `waterlevel-pro.service` on the VPS points at
  `/usr/local/bin/docker-compose` and is intentionally **disabled** — every
  container is `restart: unless-stopped`, so dockerd restores them at boot.

### Log rotation and Docker log caps

- nginx access/error logs live in the `wlp_nginx_logs` volume. Install on the host:
  - `cp docker/logrotate-wlp-nginx.conf /etc/logrotate.d/wlp-nginx-logs`
  - `logrotate -d /etc/logrotate.d/wlp-nginx-logs` (dry-run)
  - `copytruncate` is used, so no container restart/signal is required.
- Docker `json-file` logs are unlimited when there is no `/etc/docker/daemon.json`.
  Cap them per service with the logging override (requires recreating containers):
  - `docker compose -f docker/docker-compose.yml -f docker/docker-compose.logging.yml up -d`
  - or add a `logging:` block to `docker-compose.yml` / `daemon.json` permanently.

## Local resync helper

For local development changes (code or `.env`) without destroying volumes, use:

- `./docker/resync.sh`

This rebuilds/recreates `app`, `nginx`, and `cron` so runtime state matches local sources.

Useful options:

- `./docker/resync.sh --no-build` (faster container refresh)
- `./docker/resync.sh --full` (also refreshes `goaccess`)

## Reports used by web app

The app reads report HTML files from `reports/`. In Docker this path is backed by
the shared `wlp_reports` volume, generated by GoAccess from Nginx logs.

Examples generated periodically:
- `WEB_LIVE.html`
- `API_LIVE.html`

## Entrypoint behavior

The container entrypoint initializes `/app/data/database.db` from
`database.opensource.db` when the database file does not exist.

This enables first-run startup with a ready demo dataset and persistent storage via volume.
