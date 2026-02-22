# WaterLevel.Pro (Open Source)

[![Unit Tests](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/unit-tests.yml) [![Docker Integration Tests](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/integration-tests.yml) [![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/rrguardo/WaterLevel.Pro/gh-pages/badges/coverage.json)](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/unit-tests.yml) [![Docker Smoke Tests](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/docker-smoke.yml/badge.svg)](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/docker-smoke.yml) [![Docker Publish](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/rrguardo/WaterLevel.Pro/actions/workflows/docker-publish.yml) [![Docker Hub Version](https://img.shields.io/docker/v/rguardo/waterlevel-pro?label=Docker%20Hub&sort=semver)](https://hub.docker.com/r/rguardo/waterlevel-pro) [![Docker Hub Pulls](https://img.shields.io/docker/pulls/rguardo/waterlevel-pro?label=Pulls)](https://hub.docker.com/r/rguardo/waterlevel-pro) [![GitHub Copilot: AI capable](https://img.shields.io/badge/GitHub%20Copilot-AI%20capable-6e40c9?logo=githubcopilot&logoColor=white)](https://github.com/features/copilot)

Open-source server-side platform for:
- [WiFi-Water-Level-S1](https://github.com/rrguardo/WiFi-Water-Level-S1) (smart tank/cistern water level monitoring)
- [WiFi-Smart-Water-Pump-Controller-S1](https://github.com/rrguardo/WiFi-Smart-Water-Pump-Controller-S1) (smart water pump relay control)

This repository is the backend + web dashboard that devices connect to in production and self-hosted deployments. It provides a Flask-based web UI, device API endpoints, alert automation, and Docker runtime orchestration for low-cost VPS hosting.

Free online demo: [https://waterlevel.pro/](https://waterlevel.pro/)

<p align="center">
   <img src="https://waterlevel.pro/static/prod_img/tab.png" alt="WaterLevel.Pro tablet dashboard preview" width="340" />
   <img src="https://waterlevel.pro/static/prod_img/cel.png" alt="WaterLevel.Pro mobile dashboard preview" width="180" />
</p>

SEO keywords: IoT water level monitoring, smart water pump controller, Flask backend API, ESP8266/ESP32 telemetry ingestion, self-hosted water tank dashboard, SMS/email water alerts.

## Table of contents

- [What this server-side includes today](#what-this-server-side-includes-today)
   - [Web UI features (`app.py`)](#web-ui-features-apppy)
   - [Device/API service features (`api.py`)](#deviceapi-service-features-apipy)
   - [Platform/runtime features](#platformruntime-features)
- [Project structure](#project-structure)
- [Quick start (local Python)](#quick-start-local-python)
- [Quick start (Docker)](#quick-start-docker)
- [Minimal server requirements (low-cost VPS)](#minimal-server-requirements-low-cost-vps)
- [What unit tests represent (and what CI runs here)](#what-unit-tests-represent-and-what-ci-runs-here)
- [S1 demo device simulator (Python service)](#s1-demo-device-simulator-python-service)
- [R1 demo relay simulator (Python service)](#r1-demo-relay-simulator-python-service)
- [Open-source safe configuration](#open-source-safe-configuration)
- [Environment variables reference (`settings.py`)](#environment-variables-reference-settingspy)
- [Demo database](#demo-database)
- [i18n workflow (Flask-Babel)](#i18n-workflow-flask-babel)
- [Contributing](#contributing)
- [Security](#security)

## What this server-side includes today

### Web UI features (`app.py`)

- User account flows (register/login/verification/recovery patterns)
- Device management pages for sensor + relay devices
- Dashboard views for level, relay state, and account settings
- Admin/dashboard templates and localized routes (`/<lang>/...`)
- Flask-Babel translation support (`translations/`)
- Optional tracking integrations controlled by environment variables

### Device/API service features (`api.py`)

- Sensor ingestion endpoint: `GET /update` (`key`, `distance`, `voltage`)
- Relay ingestion/control endpoint: `GET /relay-update` (`key`, `status`, events)
- Firmware response headers for runtime control (`wpl`, `pool-time`, `ACTION`, safety/config fields)
- Device/link and validation flows used by hardware onboarding
- Redis-backed transient runtime state + SQLite persistence

### Platform/runtime features

- Dockerized deployment with Nginx host-based routing (web + API subdomain split)
- Gunicorn runtime for both Flask surfaces in one `app` container
- Cron automation for email alerts, SMS alerts, and GoAccess report generation
- Smoke-test contract for deployment validation ([`scripts/docker_smoke_test.sh`](scripts/docker_smoke_test.sh))
- Copilot-friendly workflow for requesting new features in VS Code (even for non-developers): [`docs/COPILOT_FEATURE_REQUESTS.md`](docs/COPILOT_FEATURE_REQUESTS.md)

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
- AI-agent-ready VPS deployment handoff (including Cloudflare option):
   - [`docs/DEPLOY_VPS_AI_AGENT_README.md`](docs/DEPLOY_VPS_AI_AGENT_README.md)

What the AI-agent deploy does (brief):
- Uses `docs/ai/DEPLOY_AGENT_INPUT.private.yaml` as the single source of truth for a real VPS deploy.
- Installs/validates Docker + Compose, writes `.env`, and starts the stack from `docker/docker-compose.yml`.
- Keeps Nginx as the only public ingress (`80/443`) and applies a firewall baseline.
- Optionally automates Cloudflare DNS (and Cloudflare Origin CA TLS for `Full (strict)`).
- Optionally applies SMTP DNS records (SPF/DKIM/DMARC) and supports direct-send SMTP mode (`SMTP_SERVER=127.0.0.1`, port `25`).
- Runs post-deploy checks (smoke test + `/ping` + `/link`).

Tested deployment profile (real VPS):
- AlmaLinux 10, 1 vCPU / 1 GB RAM, `firewalld`, Cloudflare proxied + `Full (strict)`, and direct-send SMTP mode.

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

DNS setup for Docker is env-driven and can be configured with one main input:
`WLP_BASE_DOMAIN` (plus `WLP_API_SUBDOMAIN`, default `api`).
Keep API under a
subdomain of the same base domain (for example `api.example.com`) to preserve a minimal
single-node setup aligned with SQLite usage.

Nginx receives both web/api on the same public ports (`80` and `443`) and
separates traffic by hostname.

Smoke test local (Docker + services):
- `./scripts/docker_smoke_test.sh`

## What unit tests represent (and what CI runs here)

- **Unit tests** validate one small unit of logic in isolation (for example a single function), usually with dependencies mocked/stubbed.
- **Integration tests** validate that multiple real components work together (for example Nginx + Flask + Redis + SQLite via real HTTP).

In this repository, CI runs both layers in separate jobs:

- **Unit Tests** (fast, isolated):
   - `tests/unit/test_app_unit.py`
   - `tests/unit/test_api_unit.py`
- **Docker Integration Tests** (real stack, no mocks):
   - `tests/integration/test_app_integration.py`
   - `tests/integration/test_api_integration.py`
   - `tests/integration/docker_integration.py`

This keeps quick feedback from unit tests and realistic runtime validation from integration tests. [`scripts/docker_smoke_test.sh`](scripts/docker_smoke_test.sh) remains the fast deployment contract check.

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

- Redis DB indexes are fixed internally for minimal setup:
   - runtime keys: DB `0`
   - web cache: DB `1`
   - api cache: DB `2`

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

See [`.env.example`](.env.example) for full list.

## Environment variables reference (`settings.py`)

| Group | Variable | What it does | Default | Production example |
|---|---|---|---|---|
| Core app | `DEV_MODE` | Enables development-oriented behavior when `true`. | `true` | `false` |
| Core app | `APP_SEC_KEY` | Flask secret key used for sessions/signing. | `CHANGE_ME_IN_PRODUCTION` | `use-a-64-char-random-secret` |
| Core app | `APP_RECAPTCHA_SECRET_KEY` | Server-side key used to verify reCAPTCHA tokens. | empty | `your-google-recaptcha-secret` |
| Core app | `RECAPTCHA_PUBLIC_KEY` | Client-side reCAPTCHA site key rendered in forms. | empty | `your-google-recaptcha-site-key` |
| Core app | `WLP_BASE_DOMAIN` | Single base domain used to derive hostnames/URLs. | `localhost` | `example.com` |
| Core app | `WLP_API_SUBDOMAIN` | API subdomain prefix used with `WLP_BASE_DOMAIN`. | `api` | `api` |
| Tracking | `WLP_ENABLE_TRACKING` | Enables optional analytics/pixel bootstrapping in templates. | `false` | `true` |
| Tracking | `WLP_GA_MEASUREMENT_ID` | Google Analytics 4 measurement ID used when tracking is enabled. | empty | `G-XXXXXXXXXX` |
| Tracking | `WLP_TWITTER_PIXEL_ID` | X/Twitter pixel ID used when tracking is enabled. | empty | `p00pf` |
| Tracking | `WLP_ENABLE_ADSENSE` | Enables optional AdSense script injection. | `false` | `true` |
| Tracking | `WLP_ADSENSE_CLIENT_ID` | AdSense publisher client ID used when AdSense is enabled. | empty | `ca-pub-1234567890123456` |
| SMTP | `SMTP_TEST` | Enables test mode for outbound email behavior. | follows `DEV_MODE` | `false` |
| SMTP | `EMAIL_SENDER` | Default sender header for system emails. | `"Water Level .Pro" <no-reply@example.com>` | `"WaterLevel Pro" <no-reply@example.com>` |
| SMTP | `SMTP_SERVER` | SMTP host used by mail helpers. | `127.0.0.1` | `smtp.mailprovider.com` |
| SMTP | `SMTP_PORT` | SMTP TCP port. | `25` | `587` |
| SMTP | `SMTP_USERNAME` | SMTP account username for authenticated relays/providers. | empty | `smtp-user@example.com` |
| SMTP | `SMTP_PASSWORD` | SMTP account password/token (store as secret). | empty | `app-password-or-token` |
| SMTP | `SMTP_USE_STARTTLS` | Enables STARTTLS upgrade for plaintext SMTP connections. | `true` | `true` |
| SMTP | `SMTP_USE_SSL` | Enables implicit TLS (`SMTP_SSL`, usually port `465`). | `false` | `false` |
| SMTP | `SMTP_TIMEOUT_SECONDS` | Network timeout for SMTP connect/send operations. | `20` | `20` |
| Redis runtime | `REDIS_HOST` | Redis host used by web/API runtime clients. | `127.0.0.1` | `redis` |
| Redis runtime | `REDIS_PORT` | Redis port used by web/API runtime clients. | `6379` | `6379` |
| Redis cache | `API_CACHE_REDIS_HOST` | Redis host used by API Flask-Caching backend. | `127.0.0.1` | `redis` |
| Redis cache | `API_CACHE_DEFAULT_TIMEOUT` | Default TTL (seconds) for API cache entries. | `30` | `30` |
| Redis cache | `WEB_CACHE_REDIS_HOST` | Redis host used by web Flask-Caching backend. | `127.0.0.1` | `redis` |
| Redis cache | `WEB_CACHE_DEFAULT_TIMEOUT` | Default TTL (seconds) for web cache entries. | `30` | `30` |
| Persistence | `DATABASE_URL` | SQLAlchemy database URL (SQLite WAL2 by default). | `sqlite:///database.db?journal_mode=WAL2` | `sqlite:////app/data/database.db?journal_mode=WAL2` |
| Twilio | `TWILIO_ACCOUNT_SID` | Twilio account identifier. | empty | `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Twilio | `TWILIO_AUTH_TOKEN` | Twilio authentication token. | empty | `set-in-secret-store` |
| Twilio | `TWILIO_NUMBER` | Twilio sender number for SMS. | empty | `+15551234567` |
| Demo keys | `DEMO_S1_PUB_KEY` | Public key used by the S1 demo sensor flow. | empty | `1pubDEMO_SENSOR_S1` |
| Demo keys | `DEMO_S1_PRV_KEY` | Private key used by the S1 demo sensor flow. | empty | `1prvDEMO_SENSOR_S1` |
| Demo keys | `DEMO_RELAY_PUB_KEY` | Public key used by the relay demo flow. | empty | `3pubDEMO_RELAY_R1` |
| Demo keys | `DEMO_RELAY_PRV_KEY` | Private key used by the relay demo flow. | empty | `3prvDEMO_RELAY_R1` |

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

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

New to development and want Copilot to implement a feature for you?
Start here: [`docs/COPILOT_FEATURE_REQUESTS.md`](docs/COPILOT_FEATURE_REQUESTS.md).

## Security

See [`SECURITY.md`](SECURITY.md).
