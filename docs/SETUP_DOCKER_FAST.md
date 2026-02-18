# Fast setup: from zero with Docker (test or real domain)

This guide is for new users with basic experience.
Goal: run WLP on a test or real domain using Docker.

## 1) Minimum requirements

- Docker Engine + Docker Compose plugin (`docker compose`).
- Ports `80` and `443` available on the host.
- Repository cloned locally.

Quick check:

```bash
docker --version
docker compose version
```

## 2) Prepare environment variables

From repo root:

```bash
cp .env.example .env
```

## 3) Pick your setup scenario

### Scenario A: local test domain (fast)

Use these values in `.env`:

```dotenv
APP_DOMAIN=https://localhost
API_DOMAIN=https://api.localhost
WLP_SERVER_NAME=localhost
WLP_API_SERVER_NAME=api.localhost
WLP_SSL_CERT_PATH=/etc/nginx/certs/localhost.crt
WLP_SSL_KEY_PATH=/etc/nginx/certs/localhost.key
```

Notes:
- The repo already includes local certs in `ext_conf/docker/certs/localhost.crt` and `localhost.key`.
- If you switch to another local hostname (for example `wlp.test`), provide certs with matching CN/SAN.

### Scenario B: real domain (basic production)

Example:
- web: `example.com`
- api: `api.example.com`

1. Point DNS A/AAAA for both hostnames to the same server.
2. Issue TLS certificates for both hostnames.
3. Place cert files in `ext_conf/docker/certs/` (or mount your own path) and update `.env`:

```dotenv
APP_DOMAIN=https://example.com
API_DOMAIN=https://api.example.com
WLP_SERVER_NAME=example.com
WLP_API_SERVER_NAME=api.example.com
WLP_SSL_CERT_PATH=/etc/nginx/certs/fullchain.pem
WLP_SSL_KEY_PATH=/etc/nginx/certs/privkey.pem
```

Project recommendation: keep API as a subdomain of the same base domain.

## 4) Start the stack

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

Expected services: `redis`, `app`, `nginx`, `cron`, `goaccess`.

## 5) Quick verification

Service status:

```bash
docker compose -f docker/docker-compose.yml ps
```

Official smoke test:

```bash
./scripts/docker_smoke_test.sh
```

Key checks from smoke test:
- `http -> https` redirect
- `GET /ping` on web host returns `PONG`
- `GET /link` on API host returns `FAIL` without params

## 6) Basic operations

Logs:

```bash
./docker/logs.sh
```

Stop:

```bash
./docker/down.sh
```

Rebuild only cron (after `ext_conf/crontab.ini` changes):

```bash
docker compose -f docker/docker-compose.yml up -d --build cron
```

## 7) Common issues

- **Nginx TLS does not start**: verify `WLP_SSL_CERT_PATH` / `WLP_SSL_KEY_PATH` and file availability in container.
- **API host shows web content**: verify `WLP_API_SERVER_NAME` and request `Host` header.
- **Real domain not reachable**: verify DNS and firewall/NAT for `80`/`443`.
- **`.env` changes not applied**: recreate with `docker compose -f docker/docker-compose.yml up -d --build`.
