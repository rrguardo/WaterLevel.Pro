# Changelog

All notable changes to this project are documented in this file.

## v1.0.8 - 2026-03-14

### Added
- Relay R1 extended settings persisted in `relay_settings`: `WATER_COST_PER_M3`, `RELAY_POWER_WATTS`, `ENERGY_COST_PER_KWH`, and `CURRENCY_CODE`.
- Automatic relay settings schema guard/migration in `db.py` for backward-compatible column provisioning.
- Manual SQL helper script for relay cost/energy schema updates: `scripts/migrate_add_relay_cost_energy_fields.sql`.
- Relay consumption API period controls in `/relay_consumption_stats`:
	- month mode (`month=YYYY-MM`),
	- custom date range (`start_date`/`end_date`),
	- period metadata in JSON response.
- Relay chart UX controls on `templates/relay_device_info.html`:
	- previous/current/next month navigation,
	- quick ranges (`Last 7 days`, `Last 30 days`, `This month`, `Previous month`),
	- custom date range apply,
	- series visibility presets and per-series toggles.
- Currency support for relay costs with supported codes:
	`USD`, `DOP`, `EUR`, `MXN`, `COP`, `ARS`, `CLP`, `PEN`, `INR`, `CNY`.

### Changed
- Relay consumption chart converted to mixed-series visualization:
	- consumed liters as light-blue bars,
	- water/energy costs as lines,
	- energy usage (`Wh`) as line.
- Relay summary panel upgraded from plain totals text to compact visual cards + table.
- Cost presentation now uses two-decimal formatting in chart tooltips and series values.
- Cost summary strings now render major + cents text for readability
	(for example: `22 USD and 15 cents`) with translation-ready tokens.
- Relay settings UI now unlocks all form controls in admin/private-key edit mode (`input`, `select`, `textarea`), enabling currency selection changes.
- Demo/reset data initialization updated with realistic relay defaults (costs/power/currency) and schema alignment.

### Fixed
- Fixed relay settings read-path mismatch where SQLAlchemy rows could fall back to defaults in stats calculations.
	`load_relay_settings` now normalizes rows to dict-like access (`AttrDict`) so `.get(...)` works consistently.
- Fixed CI/unit failure path when `relay_settings` table is absent:
	schema helper now checks table existence before `ALTER TABLE`, preventing `no such table: relay_settings` errors.
- Improved integration test resilience by skipping Docker-dependent suites when Docker is unavailable in environment.
- Removed hard Redis dependency from sensor stats unit test by using local fake sorted-set behavior in test scope.

### Internationalization
- Added/updated translations for new relay settings/chart controls and updated R1 docs content across:
	- `translations/es/LC_MESSAGES/messages.po`
	- `translations/hi/LC_MESSAGES/messages.po`
	- `translations/zh/LC_MESSAGES/messages.po`
- Updated product/manual pages for R1 with cost and consumption analytics descriptions.

### Testing
- Updated unit tests for relay stats response/enrichment and period modes.
- Updated DB unit tests for relay schema checks and UTC day-splitting behavior.
- Test suite and coverage revalidated after fixes (coverage target above 70% maintained).

### Release Metadata
- Web `app.py` release version: `1.0.8`
- API `api.py` release version: `1.0.8`

## v1.0.7 - 2026-03-07

### Added
- New Chinese locale (`zh`) support across web routing and UI language selection.
- New locale normalization and preference resolution in `app.py` to map regional/browser variants (for example `zh-CN`, `es-419`, `hi-IN`) to supported app locales.
- New Chinese translation catalog scaffold at `translations/zh/LC_MESSAGES/messages.po`.
- New localized Chinese manual assets under `static/manuals/*_zh.png`.
- New S1 manual guidance for `Liters per cm` setting with quick estimate formula and translated strings.
- New preview image in README (`static/prod_img/s1_stats.png`).

### Changed
- Expanded supported languages in `app.py` from `en/es/hi` to `en/es/hi/zh`.
- Updated `templates/base2.html` language dropdown to include Chinese.
- Internationalized additional previously hardcoded UI text in:
	- `templates/manuals/s1.html`
	- `templates/manuals/r1.html`
	- `templates/products/r1.html`
	- `templates/relay_device_info.html`
	- `templates/add_sensor.html`
	- `templates/add_relay.html`
	- `templates/admin_dashboard.html`
	- `templates/invalid_device.html`
	- `templates/phone_verify.html`
- Updated `static/sitemap.xml` with Chinese localized URLs for key web, product, manual, and demo pages.
- Refreshed Spanish and Hindi catalogs (`translations/es/LC_MESSAGES/messages.po`, `translations/hi/LC_MESSAGES/messages.po`) to include new strings and template references from expanded i18n coverage.

### Fixed
- Resolved Jinja template runtime error in S1 manual by removing nested `trans` block usage.
- Removed malformed obsolete PO blocks that could trigger Babel compile warnings/errors in runtime and cron logs.
- Ensured Babel catalog compilation succeeds cleanly for `es`, `hi`, and `zh`.

### Internationalization
- Expanded multilingual coverage for manuals and device/admin flows, reducing English fallbacks in localized pages.
- Added translations for new S1 settings guidance (including `Liters per cm` estimate) in `es`, `hi`, and `zh`.
- Improved locale behavior so language cookie and browser language variants resolve to supported locales more reliably.

### Documentation
- README visual section updated with an additional S1 stats dashboard preview image.

## v1.0.6 - 2026-03-07

### Added
- Relay daily consumption analytics persisted in SQLite (`relay_daily_stats`) with helper methods in `db.py` to upsert runtime and liters by day.
- New web endpoint `/relay_consumption_stats` to return the last 15 days of relay usage/consumption for charting.
- Relay device page chart for estimated daily consumption (last 15 days), including 15-day total and current-day relay ON summary.
- Web and API endpoint `/release-version` to expose service release metadata in JSON format.
- Host firewall automation scripts and runbook docs for Cloudflare allowlist sync and fail2ban SSH protection.

### Changed
- `api.py` relay ingestion flow now sanitizes relay status values and persists ON runtime/liter increments using linked S1 `liters_per_cm` (counting only positive tank-liter increases).
- Sensor hourly charts (`templates/sensor_device_info.html`) were refined to show offline hours in a single visual flow with clearer styling, improved offline tooltips, and dynamic battery-axis ranges for both 24h and drilldown views.
- Web app global template context keeps `RELEASE_VERSION` available for UI display (footer and templates).
- CI behavior improvements for Redis-backed tests and coverage publishing in GitLab (`Coverage: XX%` output plus Cobertura artifact wiring).

### Fixed
- Battery/hourly chart regressions introduced during offline UX updates were resolved (including offline rendering consistency in drilldown and battery chart compatibility).
- Test doubles/mocks for Redis and settings-backed objects were aligned with runtime contracts to avoid noisy CI logs and false negatives.
- Datetime/day handling in relay daily stats persistence was adjusted for safer timezone-aware processing.

### Internationalization
- Added Spanish and Hindi translations for the new relay consumption chart UI strings and summaries.

### Documentation
- Updated architecture and runtime docs to describe relay daily stats persistence, chart behavior, and deployment/ops guardrails.
- Expanded deployment/firewall guidance under `docs/` and `scripts/firewall/README.md`.

### Release Metadata
- Web `app.py` release version: `1.0.6`
- API `api.py` release version: `1.0.6`

## v1.0.5 - 2026-02-28

### Added
- New endpoint `/sensor_stats_hour` to return raw per-sample data for a single hourly bucket (used for UI drilldowns).
- Frontend drilldown modal on the device page: click an hourly bar/point to open a detailed per-sample percent and voltage chart.
- Documentation: `docs/ai/SENSOR_STATS.md` describing ingestion, Redis storage, server-side hourly aggregation and frontend charting.

### Changed
- `app.py`: align server-side hourly buckets to hour boundaries so current-hour samples map to the appropriate bucket.
- `templates/sensor_device_info.html`: ensure fill % and battery charge values are displayed as integers, and fix hourly labels to use bucket end times.
- `.gitlab-ci.yml`: start `redis-server` in CI job containers and set `REDIS_HOST`/`REDIS_PORT` so unit tests can run against `127.0.0.1`.

### Added tests
- Unit tests for `/sensor_stats` and `/sensor_stats_hour` added under `tests/unit/test_sensor_stats_unit.py`.

### Notes
- The new drilldown depends on the `/sensor_stats_hour` endpoint and expects Redis history in `tin-history/{public_key}`. Run unit/integration tests or start a local Redis instance when validating UI behavior.


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
