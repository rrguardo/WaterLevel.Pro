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

## Device API flows (firmware contracts)

### Sensor S1 firmware flow
- Update endpoint: `GET /update`
- Auth model: device private key (`key`) mapped to public key via DB
- Required query params: `key`, `distance`, `voltage`
- Important request headers: `FW-Version`, `RSSI`
- Cache write: `tin-keys/<public_key> = "distance|epoch|voltage|rssi"`
- Response body/header contract: body `OK`, headers `fw-version`, `wpl`

### Relay R1 firmware flow
- Update endpoint: `GET /relay-update`
- Auth model: device private key (`key`) mapped to public key via DB
- Required query params: `key`, `status`
- Important request headers: `FW-Version`, `RSSI`, `EVENTS`
- Cache write: `relay-keys/<public_key> = "status|epoch|rssi"`
- Optional event write (developer mode): `relay-events/<public_key>` and DB `relay_events`
- Runtime stats write: compares current/previous relay state and persists ON runtime
  plus estimated liters added into DB `relay_daily_stats`
- Estimation source: linked S1 (`relay_settings.SENSOR_KEY`) + sensor settings
  (`EMPTY_LEVEL`, `TOP_MARGIN`, `liters_per_cm`) + latest `tin-keys/<sensor_public_key>`
- Response body/header contract: body `OK`, headers include control values (`ACTION`, `ALGO`, `SAFE_MODE`, levels, pool times, etc.) plus linked sensor-derived values (`percent`, `distance`, times)

### Relay consumption web stats flow
- Web endpoint: `GET /relay_consumption_stats?public_key=<relay_public_key>`
- Returns last 15 days (zero-filled) with `{ day, on_minutes, liters }`
- UI consumer: `templates/relay_device_info.html` daily liters bar chart
- Liters rule (brief): for ON intervals, accumulate only positive tank-liter deltas from linked S1 (`max(0, current_liters - previous_liters)`).

## Data layer

- SQLite database file stored in volume at `/app/data/database.db`
- Database bootstrapped from `database.opensource.db` via `docker/entrypoint.sh`
- Relay daily stats table: `relay_daily_stats` (`relay_id`, `day_date`, `on_seconds`, `liters_added`, `updated_at`)
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
