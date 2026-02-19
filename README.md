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
- `rrguardo/waterlevel-pro:latest`

Docker setup and operational notes are documented in:
- [`docker/README.md`](docker/README.md)
- Fast setup for test/real domain:
   - [`docs/SETUP_DOCKER_FAST.md`](docs/SETUP_DOCKER_FAST.md)

Basic run:
1. Copy `.env.example` to `.env`
2. Pull public image (optional but recommended for fast deploy): `docker pull rrguardo/waterlevel-pro:latest`
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
