# AI Agent Entry Guide (WLP)

This file is the fast entrypoint for AI agents working in this repository.

## Read order (fast context)

1. `docs/ai/QUICK_CONTEXT.md`
2. `docs/ai/ARCHITECTURE.md`
3. `docs/ai/OPERATIONS_PLAYBOOK.md`
4. `docs/ai/CHANGE_CHECKLIST.md`
5. `docs/ai/system-index.yaml`

## Project intent

WLP is a water-level platform with:
- Web app (Flask in `app.py`)
- Device/API app (Flask in `api.py`)
- Redis cache + SQLite persistence
- Nginx TLS edge with host-based routing
- Cron workers for alerts/report tasks
- Docker-first runtime for local and CI smoke validation

## Current runtime model (important)

- Single `app` container runs both Flask apps via two Gunicorn processes:
  - web upstream on `app:8000`
  - api upstream on `app:8001`
- Nginx is the only public ingress (`80` and `443`).
- Web/API split is by host header:
  - `WLP_SERVER_NAME` -> web upstream
  - `WLP_API_SERVER_NAME` -> api upstream
- `cron` service executes `ext_conf/crontab.ini` against shared volumes.

## High-signal files

- `docker/docker-compose.yml` (source of truth for runtime topology)
- `ext_conf/docker/nginx.conf.template` (edge routing, TLS, Cloudflare IP handling)
- `scripts/docker_smoke_test.sh` (CI/local health contract)
- `settings.py` (env-driven settings for app/api)
- `ext_conf/crontab.ini` (cron contract)
- `scripts/firewall/sync_cloudflare_firewalld.sh` (Cloudflare IP allowlist for host firewalld)
- `scripts/firewall/install_cloudflare_firewalld_timer.sh` (weekly Cloudflare IP sync automation)
- `scripts/firewall/install_fail2ban_ssh_firewalld.sh` (SSH brute-force protection with fail2ban)

## Guardrails for changes

- Preserve host-based split between web and api at Nginx level.
- Keep SQLite single-node assumptions unless explicitly requested otherwise.
- Do not expose internal app upstream ports publicly unless required.
- Apply firewall changes at VPS host level (`firewalld`), not inside containers.
- Prefer updating docs + smoke test whenever runtime behavior changes.
