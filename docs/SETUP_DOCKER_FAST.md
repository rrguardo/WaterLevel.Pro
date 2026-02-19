# FAST DOCKER SETUP (from zero)

This guide is for developers with little Docker experience.

Goal: run WaterLevel.Pro in minutes with Docker, verify it works, and understand what each step does.

---

## 0) What you need before starting

### Minimum requirements

- Git (to clone the repository).
- Docker Engine + Docker Compose plugin (`docker compose`).
- Ports `80` and `443` available on your machine/server.

### Quick checks

```bash
git --version
docker --version
docker compose version
```

If any command fails, install that tool first and run the checks again.

---

## 1) Clone the repository (required)

This step is required because the repo contains:

- `docker/docker-compose.yml` (container topology)
- `ext_conf/docker/nginx.conf.template` (web/api routing)
- scripts (`docker/up.sh`, `scripts/docker_smoke_test.sh`)
- cron config, static files, and demo database source

Commands:

```bash
git clone https://github.com/rrguardo/WaterLevel.Pro.git
cd WaterLevel.Pro
```

Optional (if you want a specific branch):

```bash
git checkout main
```

---

## 2) Create `.env` from the template

From the repo root:

```bash
cp .env.example .env
```

This creates your local environment variable file.

> Note: `docker/up.sh` can auto-create `.env` if missing, but creating it manually first is better for understanding what is configured.

---

## 3) Choose your setup scenario

### Scenario A: fast local setup (recommended first)

In `.env`, keep these values:

```dotenv
APP_DOMAIN=https://localhost
API_DOMAIN=https://api.localhost
WLP_SERVER_NAME=localhost
WLP_API_SERVER_NAME=api.localhost
WLP_SSL_CERT_PATH=/etc/nginx/certs/localhost.crt
WLP_SSL_KEY_PATH=/etc/nginx/certs/localhost.key
```

Notes:

- Local certs are already included in `ext_conf/docker/certs/`.
- If cert/key are missing, Nginx auto-generates a temporary self-signed cert.
- Browsers may show a TLS warning in local mode (normal with self-signed certs).

### Scenario B: real domain

Example:

- Web: `example.com`
- API: `api.example.com`

Checklist:

1. Point DNS A/AAAA for both hostnames to the same server.
2. Issue TLS certificates for both hostnames.
3. Place cert/key files and update `.env`.

Example values:

```dotenv
APP_DOMAIN=https://example.com
API_DOMAIN=https://api.example.com
WLP_SERVER_NAME=example.com
WLP_API_SERVER_NAME=api.example.com
WLP_SSL_CERT_PATH=/etc/nginx/certs/fullchain.pem
WLP_SSL_KEY_PATH=/etc/nginx/certs/privkey.pem
```

Project recommendation: keep API as a subdomain of the same base domain.

---

## 4) Start services

### Simple option (recommended)

```bash
./docker/up.sh
```

### Explicit Compose option

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

Expected services:

- `app`
- `nginx`
- `cron`
- `goaccess`

---

## 5) Verify everything works

Container status:

```bash
docker compose -f docker/docker-compose.yml ps
```

Official project smoke test:

```bash
./scripts/docker_smoke_test.sh
```

Smoke test checks:

- `http -> https` redirect
- web host (`/ping`) returns `PONG`
- api host (`/link` without params) returns `FAIL`

Quick manual checks:

- Web: `https://localhost`
- API: `https://api.localhost/link`

---

## 6) Useful day-to-day commands

View logs:

```bash
./docker/logs.sh
```

Stop stack:

```bash
./docker/down.sh
```

Rebuild only cron (after editing `ext_conf/crontab.ini`):

```bash
docker compose -f docker/docker-compose.yml up -d --build cron
```

---

## 7) Common issues (quick fixes)

- **Nginx TLS does not start**
  - Check `WLP_SSL_CERT_PATH` and `WLP_SSL_KEY_PATH`.
  - Ensure files exist at expected paths in the container.

- **`.env` changes are not applied**
  - Recreate with build:
  - `docker compose -f docker/docker-compose.yml up -d --build`

- **API host shows web content**
  - Check `WLP_API_SERVER_NAME` and confirm you are using the correct hostname.

- **Real domain is not reachable**
  - Check DNS and firewall/NAT for ports `80` and `443`.

---

## 8) Note about public image

By default, Compose uses `WLP_APP_IMAGE` (for example `rguardo/waterlevel-pro:latest`) and can also build locally (`docker/Dockerfile`) when using `--build`.

If you want to pre-pull the image:

```bash
docker pull rguardo/waterlevel-pro:latest
```
