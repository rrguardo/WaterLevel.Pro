# Changelog

All notable changes to this project are documented in this file.

## 2026-02-20

### Added
- AI deploy metadata template for low-input agents in `docs/ai/DEPLOY_AGENT_METADATA_TEMPLATE.yaml`.
- Local Docker resync helper script `docker/resync.sh` for rebuilding/recreating runtime services without removing volumes.
- Environment-driven tracking controls (`WLP_ENABLE_TRACKING`, `WLP_GA_MEASUREMENT_ID`, `WLP_TWITTER_PIXEL_ID`, `WLP_ENABLE_ADSENSE`, `WLP_ADSENSE_CLIENT_ID`).
- Secure SMTP configuration knobs (`SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_STARTTLS`, `SMTP_USE_SSL`, `SMTP_TIMEOUT_SECONDS`).

### Changed
- `base2.html` now injects analytics/ads scripts only when explicitly enabled via environment.
- `base2-tracking.js` now initializes providers dynamically from runtime config instead of hardcoded IDs.
- `email_tools.py` now supports secure SMTP delivery with STARTTLS/SSL, optional authentication, and connection timeout.
- Docs index and runtime docs updated to include deploy agent metadata and local resync workflow.
- `.env.example` and `README.md` env references expanded for tracking and secure SMTP settings.

### Security
- Tracking defaults remain opt-in for open-source deployments.
- Firewall baseline documented for deploy agents (public: 22/80/443; internal services kept private).
