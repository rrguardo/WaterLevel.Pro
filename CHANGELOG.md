# Changelog

All notable changes to this project are documented in this file.

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
