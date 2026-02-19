# Contributing

Thanks for helping improve WaterLevel.Pro.

## 1) Development setup

1. Create a local env file:
   - Copy `.env.example` to `.env`
2. Use Python 3.14 and install deps:
   - `python3.14 -m pip install -r requirements.txt`
3. Prepare demo DB:
   - `python3.14 scripts/reset_demo_db.py --sync-source`
4. Run Redis locally on port `6379`
5. Start apps:
   - Web: `python3.14 app.py`
   - API: `python3.14 api.py`

## 2) Docker setup (recommended)

1. Copy `.env.example` to `.env`
2. Start stack:
   - `docker compose -f docker/docker-compose.yml up --build`
3. Services:
   - Web: `https://localhost`
   - API: `https://api.localhost`

## 3) Coding guidelines

- Keep changes focused and minimal.
- Do not commit secrets, credentials, or private keys.
- Prefer environment variables for runtime configuration.
- Update docs when behavior/setup changes.

## 4) Pull requests

- Use a clear title and describe the user-visible impact.
- Include reproduction/testing steps.
- Mention any environment variable changes.
