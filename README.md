# WaterLevel.Pro (Open Source)

[![Docker Smoke Tests](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/docker-smoke.yml/badge.svg)](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/docker-smoke.yml)

Water level monitoring platform with:
- Web app (`app.py`)
- Device/API service (`api.py`)
- Alert workers (email/SMS cron scripts)
- Redis caching + SQLite storage

## Project structure

- `app.py`: main web application
- `api.py`: device/API endpoints
- `db.py`: SQLAlchemy/SQLite data access
- `settings.py`: environment-based runtime settings
- `scripts/reset_demo_db.py`: rebuild open-source demo database
- `docker/docker-compose.yml`: local container stack (app, redis, nginx, goaccess, cron)
- `docker/Dockerfile`: app image for web/api runtime
- `templates/`, `static/`, `translations/`: frontend and i18n resources

## Quick start (local Python)

1. Create local environment variables:
   - Copy `.env.example` to `.env`
2. Install dependencies:
   - `python3.14 -m pip install -r requirements.txt`
3. Build demo DB:
   - `python3.14 scripts/reset_demo_db.py --sync-source`
4. Start Redis on port `6379`
5. Start services:
   - Web: `python3.14 app.py`
   - API: `python3.14 api.py`

Default local URLs:
- Web: `http://localhost` (app default port)
- API: `http://localhost:88`

## Quick start (Docker)

Public image (Docker Hub):
- `rguardo/waterlevel-pro:latest`

Docker setup and operational notes are documented in:
- [`docker/README.md`](docker/README.md)
- Fast setup for test/real domain:
   - [`docs/SETUP_DOCKER_FAST.md`](docs/SETUP_DOCKER_FAST.md)

Basic run:
1. Copy `.env.example` to `.env`
2. Pull public image (optional but recommended for fast deploy): `docker pull rguardo/waterlevel-pro:latest`
3. Start stack: `docker compose -f docker/docker-compose.yml up -d`
3. Open web: `https://localhost`

## Minimal server requirements (low-cost VPS)

This project is tuned for low-resource single-node deployment (SQLite + Redis embedded in `app` container).

- Minimum: `1 vCPU`, `1 GB RAM`, ~`8 GB` free disk (basic/light load).
- Recommended: `1 vCPU`, `2 GB RAM`, ~`12 GB` free disk (more stable with cron + logs + reports).
- For very small VPS (`3-5 USD` tier), keep background load low and monitor disk growth in Docker volumes/logs.

DNS setup for Docker is fully env-driven (`APP_DOMAIN`, `API_DOMAIN`,
`WLP_SERVER_NAME`, `WLP_API_SERVER_NAME`). Keep API under a subdomain of the
same base domain (for example `api.example.com`) to preserve a minimal
single-node setup aligned with SQLite usage.

Nginx receives both web/api on the same public ports (`80` and `443`) and
separates traffic by hostname.

Smoke test local (Docker + services):
- `./scripts/docker_smoke_test.sh`

## S1 demo device simulator (Python service)

This repo includes a Python service that simulates a real WiFi Water Level S1 device and sends updates to the API endpoint used by firmware:

- `/update?key=<private_key>&distance=<cm>&voltage=<centivolts>`
- Headers: `FW-Version`, `RSSI`

Script:

- `scripts/s1_demo_device_service.py`

Run one update (quick check):

- `python3 scripts/s1_demo_device_service.py --once`

Run continuously (default demo private key):

- `python3 scripts/s1_demo_device_service.py`

If your local DNS does not resolve `api.localhost`, use host routing explicitly:

- `python3 scripts/s1_demo_device_service.py --base-url https://localhost --host-header api.localhost`

Notes:

- Defaults are loaded from `.env`: `DEMO_S1_PUB_KEY`, `DEMO_S1_PRV_KEY`, `API_DOMAIN`.
- The service reads response header `wpl` and adapts posting interval automatically.
- Add `--verify-tls` only when using valid TLS certs.

Docker cron integration:

- `ext_conf/crontab.ini` runs this simulator every 30 seconds (2 runs per minute).
- In Docker cron, requests go to `https://nginx` with host header `${WLP_API_SERVER_NAME}`.
- Cron log file: `/var/log/cron/s1_demo_device_service.log`

## R1 demo relay simulator (Python service)

This repo includes a Python service that simulates the WiFi Smart Water Pump Controller S1 relay device and posts updates like firmware:

- `/relay-update?key=<private_key>&status=<0|1>`
- Headers: `FW-Version`, `RSSI`, `EVENTS`

Script:

- `scripts/r1_demo_relay_service.py`

Run one update (quick check):

- `python3 scripts/r1_demo_relay_service.py --once`

Run continuously:

- `python3 scripts/r1_demo_relay_service.py`

If your local DNS does not resolve `api.localhost`, use host routing explicitly:

- `python3 scripts/r1_demo_relay_service.py --base-url https://localhost --host-header api.localhost`

Notes:

- Defaults are loaded from `.env`: `DEMO_RELAY_PUB_KEY`, `DEMO_RELAY_PRV_KEY`, `API_DOMAIN`.
- It reads response header `pool-time` and adapts posting interval automatically.
- Add `--random-events` to inject occasional demo relay event codes.

Docker cron integration:

- `ext_conf/crontab.ini` runs this relay simulator every 30 seconds (2 runs per minute).
- Cron log file: `/var/log/cron/r1_demo_relay_service.log`

Redis runtime note:

- Keep `WEB_REDIS_DB` and `API_REDIS_DB` aligned (same DB index) so live device keys written by API are visible to web endpoints that read Redis state.

Run CI locally with gitlab-ci-local:
1. Install `gitlab-ci-local` (for example: `npm i -g gitlab-ci-local`)
2. Run: `gitlab-ci-local --force-shell-executor docker_smoke_test`

## Open-source safe configuration

Never commit production secrets. This project expects secrets through environment variables.

Important variables:
- `APP_SEC_KEY`
- `APP_RECAPTCHA_SECRET_KEY`
- `RECAPTCHA_PUBLIC_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_NUMBER`
- `SMTP_SERVER`
- `SMTP_PORT`
- `EMAIL_SENDER`
- `DATABASE_URL`
- `REDIS_HOST`
- `REDIS_PORT`

See `.env.example` for full list.

## Demo database

This repo includes a sanitized demo dataset for open-source usage:
- `database.db` (runtime DB, generated/updated locally)
- `database.opensource.db` (sanitized source copy)

Demo admin credentials:
- Email: `admin.demo@opensource.local`
- Password: `AdminDemo_2026_Open!`

Rebuild command:
- `python3.14 scripts/reset_demo_db.py --sync-source`

## i18n workflow (Flask-Babel)

Extract strings:
- `pybabel extract -F babel.cfg -o messages.pot .`

Create language catalog:
- `pybabel init -i messages.pot -d translations -l es`

Update catalogs:
- `pybabel update -i messages.pot -d translations`

Compile catalogs:
- `pybabel compile -d translations`

In templates:
- `{% trans %}Welcome to the site!{% endtrans %}`

In Python:
- `_("Hello, World!")`

## Contributing

See `CONTRIBUTING.md`.

## Security

See `SECURITY.md`.
