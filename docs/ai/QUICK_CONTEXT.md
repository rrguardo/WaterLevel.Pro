# Quick Context for AI Agents

## One-minute summary

WLP is a Flask-based system with two app surfaces:
- web UI (`app.py`)
- device/API (`api.py`)

Both run inside one Docker service (`app`) and are fronted by Nginx over HTTPS.
The API should remain on a subdomain of the same base domain for minimal setup.

## Current container graph

- `app`: runs Redis (`:6379` internal) + Gunicorn web (`:8000`) + Gunicorn api (`:8001`)
- `nginx`: TLS edge, HTTP->HTTPS redirect, host-based split web/api
- `cron`: executes scheduled tasks from `ext_conf/crontab.ini`
- `goaccess`: generates report HTML files from Nginx logs

## Public entrypoints

- Web: `https://<WLP_SERVER_NAME>`
- API: `https://<WLP_API_SERVER_NAME>`

## Device update contracts (critical)

### Sensor S1 update
- Endpoint: `GET /update`
- Query params: `key` (private key), `distance` (cm), `voltage` (centivolts)
- Request headers: `FW-Version`, `RSSI`
- Response body: `OK` (or error)
- Response headers used by firmware: `fw-version`, `wpl` (next poll time)

### Relay R1 update
- Endpoint: `GET /relay-update`
- Query params: `key` (private key), `status` (`0|1`)
- Request headers: `FW-Version`, `RSSI`, `EVENTS` (5 comma-separated event codes)
- Response body: `OK` (or error)
- Response headers used by firmware: `fw-version`, `pool-time`, `ACTION`, `percent`, `event-time`, `current-time`, `distance`, plus smart config headers (`ALGO`, `SAFE_MODE`, `START_LEVEL`, `END_LEVEL`, `AUTO_OFF`, `AUTO_ON`, `MIN_FLOW_MM_X_MIN`, `BLIND_DISTANCE`, `HOURS_OFF`)

## Internal routing

- `WLP_WEB_UPSTREAM` default: `app:8000`
- `WLP_API_UPSTREAM` default: `app:8001`

## Where to start for most tasks

- Runtime/infra: `docker/docker-compose.yml`
- Nginx behavior: `ext_conf/docker/nginx.conf.template`
- Env contract: `.env.example`, `settings.py`
- Health contract: `scripts/docker_smoke_test.sh`
- Scheduled jobs: `ext_conf/crontab.ini`, `docker/cron-entrypoint.sh`
