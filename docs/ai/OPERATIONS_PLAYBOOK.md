# Operations Playbook

## Local bootstrap (Docker)

1. Copy `.env.example` to `.env`
2. Start stack:
   - `docker compose -f docker/docker-compose.yml up --build`
3. Open:
   - Web: `https://localhost`
   - API (host-based): `https://api.localhost`

## Health verification

Primary smoke test:
- `./scripts/docker_smoke_test.sh`

What smoke test checks:
- Services running (`app`, `nginx`, `cron`, `goaccess`)
- Redis reachable inside `app` container
- HTTP redirect to HTTPS
- Web/API host routing through Nginx
- GoAccess live report generation

## CI local

- `gitlab-ci-local --force-shell-executor docker_smoke_test`

## Useful operational commands

- Status:
  - `docker compose -f docker/docker-compose.yml ps`
- Logs:
  - `docker compose -f docker/docker-compose.yml logs --no-color`
- Rebuild only cron after schedule changes:
  - `docker compose -f docker/docker-compose.yml up -d --build cron`
- Full reset:
  - `docker compose -f docker/docker-compose.yml down -v`

## Device update API checks

Sensor S1 update contract (`/update`):
- Required: `key`, `distance`, `voltage`
- Typical headers: `FW-Version`, `RSSI`
- Expected success: HTTP `200`, body `OK`, response headers `fw-version` and `wpl`

Relay R1 update contract (`/relay-update`):
- Required: `key`, `status`
- Typical headers: `FW-Version`, `RSSI`, `EVENTS`
- Expected success: HTTP `200`, body `OK`, response headers include `ACTION` and `pool-time`

Demo simulators (cron-managed):
- `scripts/s1_demo_device_service.py`
- `scripts/r1_demo_relay_service.py`
- In Docker cron, both target `https://nginx` with host header `${WLP_API_SERVER_NAME}` and run every 30 seconds.

## Domain/TLS config knobs

- `WLP_SERVER_NAME`
- `WLP_API_SERVER_NAME`
- `WLP_WEB_UPSTREAM`
- `WLP_API_UPSTREAM`
- `WLP_SSL_CERT_PATH`
- `WLP_SSL_KEY_PATH`

## Common failure signatures

- `No module named ...` in app logs:
  - Missing dependency in `requirements.txt`
- Nginx startup TLS errors:
  - Missing/incorrect cert path in env or missing mounted cert files
- API route returning web content:
  - Wrong host header or misconfigured `WLP_API_SERVER_NAME`
- Missing reports:
  - Check `goaccess` and `cron` logs + shared volumes
