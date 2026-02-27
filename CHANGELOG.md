# Changelog

All notable changes to this project are documented in this file.


## v1.0.4 - 2026-02-27

### Added
- New Water Volume card on the device page showing liters and a vertical fill bar.
- New API endpoint `/sensor_stats` that returns 24 hourly aggregated buckets (average fill percent and reported voltage) for a sensor, based on Redis history points.
- Two hourly charts on the device page: hourly fill percent (bar) and hourly voltage with computed battery charge (line + columns).

### Changed
- Removed the inline "Current Volume" numeric display from the device header; numeric liters now presented only in the Water Volume card.
- `templates/sensor_device_info.html`: moved hourly stats into two dedicated cards, restored English UI text for titles/labels, removed `:00` suffix from hour labels, improved tooltip wording and offline display handling.
- Chart rendering polish: per-bar offline coloring, distributed bars for offline markers, and shared tooltips for mixed-series voltage/charge chart.
- `api.py`: persisting per-update history points to Redis sorted set `tin-history/{pubkey}` as `"percent|voltage"` with epoch score; retention trimmed to recent days.

### Fixed
- Database compatibility: migrated legacy `litros_por_cm` -> `liters_per_cm` in demo seed DB and added safe migration SQL (`scripts/migrate_remove_litros_por_cm_from_sensor_settings.sql`).
- `db.py`: return value for `load_device_settings` now supports attribute access and `.get()` (helps avoid runtime 500s).
- `app.py`: `device_admin` now accepts and validates `LITERS_PER_CM` from sensor settings and persists it via `DevicesDB.update_sensor_settings`.

### Notes
- Redis history key retention is short-lived (~3 days) by default; for persistent history across restarts enable Redis persistence in Docker Compose.
- Included `.gitlab-ci.yml` in the commit so CI config aligns with recent test/stack changes.
- UI and templates updated: `templates/sensor_device_info.html` + related CSS and JS changes to support the Water Volume card.
- Recommended: run integration tests and apply the same DB migration to the runtime DB (`/app/data/database.db`) if present.


## v1.0.3 - 2026-02-25

### Added
- Copilot feature-request guide for non-developers: `docs/COPILOT_FEATURE_REQUESTS.md`.

### Changed
- README: add GitHub Copilot “AI capable” badge and link the feature-request guide.

### Fixed
- Docker entrypoint now always compiles Flask-Babel translations at container startup, fixing missing .mo files and restoring Spanish UI translations after rebuilds.

## v1.0.2 - 2026-02-22

### Added
- Deployment agent input template: add optional reCAPTCHA env keys (`APP_RECAPTCHA_SECRET_KEY`, `RECAPTCHA_PUBLIC_KEY`).
- CI docker smoke tests: allow optional reCAPTCHA keys via GitHub Secrets; smoke script persists provided env overrides into `.env`.
- Deployment agent input template: document that `verification_targets` is optional and provide a localhost override example.

### Fixed
- Relay UI: restore the rocker-style ON/OFF switch styling so it no longer renders as a plain checkbox.

### Changed
- Device embed mode (`smallversion=1`): hide the global open-source attribution footer in the embedded iframe view.
- Docker Compose: remove default `DEMO_*` env overrides from the `cron` service so runtime keys come from `.env`.
- Deployment docs: explicitly note that `TXT` record values should be in quotation marks (Cloudflare may auto-add quotes; behavior is unchanged).

## v1.0.1 - 2026-02-21

### Added
- Cron env bootstrap script `docker/cron-env.sh` and updated `ext_conf/crontab.ini` so jobs reliably inherit the container env.
- Nginx internal network aliases for `${WLP_SERVER_NAME}` and `${WLP_API_SERVER_NAME}` so cron simulator traffic uses correct TLS SNI + host routing.

### Fixed
- Cron demo simulators routing: jobs now post to `https://${WLP_API_SERVER_NAME}` (not `https://nginx` / HTTP redirect), preventing HTML/502 responses caused by SNI/redirect mismatches.
- Compose rebuild behavior: `cron` now supports `build:` so repo changes (cron scripts/schedule) can be applied with `docker compose ... up --build`.

### Changed
- Docker helper scripts now use `docker compose --env-file .env ...` so Compose interpolation always uses the intended env values (no `docker/.env` workaround).
- Deployment docs updated with Cloudflare/TLS guardrails and a brief “AI-agent deploy” summary, including tested profile (AlmaLinux 10, 1 vCPU / 1 GB RAM, `firewalld`, Cloudflare proxied + Full (strict), direct-send SMTP mode).

## 2026-02-20

### Added
- AI deploy input template for low-input agents in `docs/ai/DEPLOY_AGENT_INPUT_TEMPLATE.yaml`.
- Local Docker resync helper script `docker/resync.sh` for rebuilding/recreating runtime services without removing volumes.
- Environment-driven tracking controls (`WLP_ENABLE_TRACKING`, `WLP_GA_MEASUREMENT_ID`, `WLP_TWITTER_PIXEL_ID`, `WLP_ENABLE_ADSENSE`, `WLP_ADSENSE_CLIENT_ID`).
- Secure SMTP configuration knobs (`SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_STARTTLS`, `SMTP_USE_SSL`, `SMTP_TIMEOUT_SECONDS`).
- Split test architecture under `tests/unit` and `tests/integration` with dedicated suites for Flask web/API behavior, cron paths, and dockerized runtime validation.
- Dedicated GitHub Actions workflows for unit tests and integration tests in `.github/workflows/unit-tests.yml` and `.github/workflows/integration-tests.yml`.
- Unit-test coverage artifacts in GitHub Actions (XML + HTML) and Codecov upload wiring for coverage reporting.
- New unit suites for `db.py`, `email_tools.py`, and `twilio_sms.py`, plus integration coverage for active cron execution.

### Changed
- `base2.html` now injects analytics/ads scripts only when explicitly enabled via environment.
- `base2-tracking.js` now initializes providers dynamically from runtime config instead of hardcoded IDs.
- `email_tools.py` now supports secure SMTP delivery with STARTTLS/SSL, optional authentication, and connection timeout.
- Docs index and runtime docs updated to include deploy agent metadata and local resync workflow.
- `.env.example` and `README.md` env references expanded for tracking and secure SMTP settings.
- CI pipelines now separate unit and integration validation jobs in both GitHub Actions and GitLab CI.
- Unit coverage scope and test depth were increased for core modules; `db.py` unit coverage now exceeds baseline target.
- README badges and testing docs now distinguish unit status, integration status, and coverage reporting.

### Security
- Tracking defaults remain opt-in for open-source deployments.
- Firewall baseline documented for deploy agents (public: 22/80/443; internal services kept private).
