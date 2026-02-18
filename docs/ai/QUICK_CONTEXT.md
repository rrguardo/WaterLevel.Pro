# Quick Context for AI Agents

## One-minute summary

WLP is a Flask-based system with two app surfaces:
- web UI (`app.py`)
- device/API (`api.py`)

Both run inside one Docker service (`app`) and are fronted by Nginx over HTTPS.
The API should remain on a subdomain of the same base domain for minimal setup.

## Current container graph

- `redis`: shared cache/state backend
- `app`: runs Gunicorn for web (`:8000`) and api (`:8001`)
- `nginx`: TLS edge, HTTP->HTTPS redirect, host-based split web/api
- `cron`: executes scheduled tasks from `ext_conf/crontab.ini`
- `goaccess`: generates report HTML files from Nginx logs

## Public entrypoints

- Web: `https://<WLP_SERVER_NAME>`
- API: `https://<WLP_API_SERVER_NAME>`

## Internal routing

- `WLP_WEB_UPSTREAM` default: `app:8000`
- `WLP_API_UPSTREAM` default: `app:8001`

## Where to start for most tasks

- Runtime/infra: `docker/docker-compose.yml`
- Nginx behavior: `ext_conf/docker/nginx.conf.template`
- Env contract: `.env.example`, `settings.py`
- Health contract: `scripts/docker_smoke_test.sh`
- Scheduled jobs: `ext_conf/crontab.ini`, `docker/cron-entrypoint.sh`
