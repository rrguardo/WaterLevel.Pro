# Copilot Instructions for WLP

## Fast context first
- Read in this order before major changes: `docs/ai/QUICK_CONTEXT.md`, `docs/ai/ARCHITECTURE.md`, `docs/ai/OPERATIONS_PLAYBOOK.md`, `docs/ai/CHANGE_CHECKLIST.md`.
- Treat `docker/docker-compose.yml` as runtime source of truth.

## Architecture and boundaries
- This repo has two Flask entrypoints: web UI in `app.py` and device/API in `api.py`.
- In Docker, both run inside one `app` container via two Gunicorn binds (`0.0.0.0:8000` and `0.0.0.0:8001`).
- Public ingress is only Nginx (`80/443`) and routing is host-based in `ext_conf/docker/nginx.conf.template`:
  - `${WLP_SERVER_NAME}` -> `${WLP_WEB_UPSTREAM}`
  - `${WLP_API_SERVER_NAME}` -> `${WLP_API_UPSTREAM}`
- Keep API as a subdomain of the same base domain (SQLite-oriented single-node model).

## Data and runtime behavior
- Persistence is SQLite on shared volume (`/app/data/database.db`), configured through `DATABASE_URL` (see `settings.py`).
- On first container boot, `docker/entrypoint.sh` seeds `/app/data/database.db` from `database.opensource.db`.
- Redis is used for transient state/cache; web and API use separate DB indexes (`WEB_REDIS_DB`, `API_REDIS_DB`).
- Background jobs run in `cron` container from `ext_conf/crontab.ini` (alerts + GoAccess report generation/retention).

## Developer workflows that matter
- Local Docker start: `docker compose -f docker/docker-compose.yml up --build` (or `./docker/up.sh`).
- Primary validation contract: `./scripts/docker_smoke_test.sh`.
- Smoke test asserts host-based routing and known endpoints:
  - Web: `GET /ping` should contain `PONG` (host `${WLP_SERVER_NAME}`)
  - API: `GET /link` should contain `FAIL` without params (host `${WLP_API_SERVER_NAME}`)
- After cron schedule edits, rebuild cron service: `docker compose -f docker/docker-compose.yml up -d --build cron`.

## Change guardrails
- Do not expose internal app ports publicly; keep ingress centralized in Nginx.
- If you add/rename env vars, update all three: `.env.example`, `settings.py`, and compose env wiring.
- If runtime behavior changes, update docs in `README.md`, `docker/README.md`, and `docs/ai/*`.
- Keep `scripts/docker_smoke_test.sh` aligned with real routing/health behavior.
- Do not reintroduce legacy uWSGI topology; current contract is Gunicorn + Nginx host split.

## Codebase patterns to follow
- `app.py` handles localized UI routes (`/<lang>/...`) and Flask-Babel locale flow.
- `api.py` is device-facing and CORS is restricted to `settings.APP_DOMAIN` (`CORS(app, origins=[WEB_APP_DOMAIN])`).
- Prefer env-driven behavior over hardcoded hostnames; check `settings.py` first for config knobs.