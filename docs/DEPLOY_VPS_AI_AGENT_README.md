# VPS Deployment Handoff Guide (AI-Agent Ready)

This document is a production-focused handoff format so users can provide complete deployment context in one message.

It is designed for:
- Fast VPS deployment execution
- Minimal back-and-forth in chat
- Clear Cloudflare-enabled or non-Cloudflare paths

## Table of contents

- [Scope](#scope)
- [Files you should use](#files-you-should-use)
- [Minimal required information](#minimal-required-information)
- [Cloudflare deployment choices](#cloudflare-deployment-choices)
- [Cloudflare API token (Free plan)](#cloudflare-api-token-free-plan)
- [Cloudflare dashboard (click-by-click, Free plan)](#cloudflare-dashboard-click-by-click-free-plan)
- [Security baseline (must keep)](#security-baseline-must-keep)
- [Chat handoff workflow (recommended)](#chat-handoff-workflow-recommended)
- [What the AI agent can do quickly after handoff](#what-the-ai-agent-can-do-quickly-after-handoff)
- [Post-deploy verification checklist](#post-deploy-verification-checklist)

## Scope

This guide targets the current WLP runtime model:
- Docker Compose runtime from `docker/docker-compose.yml`
- Host-based split through Nginx:
   - web host derived from `domain.web`
   - api host derived from `domain.api`
- Single-node SQLite + Redis model

## Files you should use

1. Fill this template:
   - [docs/ai/DEPLOY_AGENT_INPUT_TEMPLATE.yaml](ai/DEPLOY_AGENT_INPUT_TEMPLATE.yaml)
2. Keep a private copy with real secrets:
   - `docs/ai/DEPLOY_AGENT_INPUT.private.yaml` (ignored by git)
3. Paste this prompt in chat:
   - [docs/ai/DEPLOY_CHAT_PROMPT_TEMPLATE.md](ai/DEPLOY_CHAT_PROMPT_TEMPLATE.md)

## Minimal required information

### 1) Server access
- VPS public IP
- SSH port
- SSH user
- Auth method (`password` or `ssh_key`)

### 2) Domain routing
- Web domain (example: `example.com`)
- API domain (example: `api.example.com`)
- API must remain subdomain/same base domain as web
- This `domain.web` / `domain.api` pair is the single source for domain inputs

### 3) DNS and edge mode
- Cloudflare mode:
  - `disabled`
  - `dns_only`
  - `proxied`

### 4) TLS source
- `letsencrypt`
- `cloudflare_origin_cert`
- `provided_files`

### 5) Runtime env values
- Domain runtime values are derived from `domain.web` and `domain.api`
- `WLP_WEB_UPSTREAM`, `WLP_API_UPSTREAM`
- `WLP_SSL_CERT_PATH`, `WLP_SSL_KEY_PATH`

### 6) Email mode
- Test mode (`SMTP_TEST=true`) or production SMTP (`SMTP_TEST=false` + provider details)

## Cloudflare deployment choices

Assumed baseline in this guide: **Cloudflare Free plan**.
All required items below are compatible with Free.

### Option A: Cloudflare disabled
- DNS A/AAAA records point directly to VPS
- TLS terminates at VPS Nginx

### Option B: Cloudflare DNS only (gray cloud)
- Cloudflare manages DNS only
- Traffic still reaches VPS directly
- TLS terminates at VPS Nginx

### Option C: Cloudflare proxied (orange cloud)
- Cloudflare proxies traffic to VPS
- Recommended SSL mode: `Full (strict)`
- Use valid origin certificate on VPS (`cloudflare_origin_cert` or public cert)

## Cloudflare API token (Free plan)

Use a **custom API Token** (not Global API Key).

### Minimum token permissions for DNS automation

- `Zone / DNS / Edit`
- `Zone / Zone / Read`

### Optional token permissions (only if you want edge setting automation)

- `Zone / SSL and Certificates / Edit`
- `Zone / Zone Settings / Edit`

### Token scope

- Restrict token resources to a single zone:
   - `Include / Specific zone / <your-domain>`

### When token is required

- Required if the agent should create/update DNS records through Cloudflare API.
- Not required if you manage DNS and Cloudflare settings manually in dashboard.

### Recommended Cloudflare Free settings

- Proxy status for `@` and `api`: `Proxied` (orange cloud) for edge protection.
- SSL/TLS mode: `Full (strict)`.
- Always Use HTTPS: `On`.
- TLS cert on VPS: Cloudflare Origin Certificate or publicly trusted cert.
- Keep VPS firewall restricted to `22/80/443` only.

## Cloudflare dashboard (click-by-click, Free plan)

Use this sequence to avoid missing settings.

### 1) Add zone and verify nameservers

1. Cloudflare Dashboard -> **Add a Site**
2. Enter your root domain (example: `your-domain.com`)
3. Select **Free** plan
4. Continue and set Cloudflare nameservers at your registrar
5. Wait until zone status is **Active**

### 2) Create DNS records

Cloudflare Dashboard -> **DNS** -> **Records**:

1. Create `A` record for root (`@`) -> VPS IPv4
2. Create `A` record for `api` -> same VPS IPv4
3. For proxied mode, keep both records as **Proxied** (orange cloud)

### 3) Create API token (least privilege)

Cloudflare Dashboard -> **My Profile** -> **API Tokens** -> **Create Token** -> **Create Custom Token**:

Token permissions:
- `Zone / DNS / Edit`
- `Zone / Zone / Read`

Optional permissions (only if you automate edge settings):
- `Zone / SSL and Certificates / Edit`
- `Zone / Zone Settings / Edit`

Zone resources:
- `Include / Specific zone / your-domain.com`

Save token once; Cloudflare will show it only at creation time.

### 4) Configure SSL/TLS mode

Cloudflare Dashboard -> **SSL/TLS** -> **Overview**:

1. Set encryption mode to **Full (strict)**
2. Ensure your VPS origin cert/key path matches your `.env` values

### 5) Enable Always Use HTTPS

Cloudflare Dashboard -> **SSL/TLS** -> **Edge Certificates**:

1. Turn **Always Use HTTPS** = **On**

### 6) (Optional) Create Cloudflare Origin Certificate

Cloudflare Dashboard -> **SSL/TLS** -> **Origin Server** -> **Create Certificate**:

1. Generate private key and certificate
2. Add hostnames:
   - `your-domain.com`
   - `*.your-domain.com`
3. Install files on VPS and map them to:
   - `WLP_SSL_CERT_PATH`
   - `WLP_SSL_KEY_PATH`

### 7) Final validation

After deploy, verify:

- `https://your-domain.com/ping` contains `PONG`
- `https://api.your-domain.com/link` contains `FAIL`
- `docker compose -f docker/docker-compose.yml ps` shows all services healthy

## Security baseline (must keep)

- Public inbound: `22`, `80`, `443`
- Do not expose: `8000`, `8001`, `6379`
- Keep ingress centralized in Nginx only
- Never commit real credentials to git

## Chat handoff workflow (recommended)

1. Copy template to private file:
   - `cp docs/ai/DEPLOY_AGENT_INPUT_TEMPLATE.yaml docs/ai/DEPLOY_AGENT_INPUT.private.yaml`
2. Fill all fields in the private file
3. Use prompt from [docs/ai/DEPLOY_CHAT_PROMPT_TEMPLATE.md](ai/DEPLOY_CHAT_PROMPT_TEMPLATE.md)
4. In chat, include:
   - path to your filled private file
   - explicit permission to run real deploy commands

## What the AI agent can do quickly after handoff

- Validate completeness of deploy input
- Generate exact `.env` values
- Run Docker deployment sequence
- Run `./scripts/docker_smoke_test.sh`
- Report pass/fail and concrete fixes

## Post-deploy verification checklist

- `https://<web-domain>/ping` contains `PONG`
- `https://<api-domain>/link` contains `FAIL` (without params)
- API and web routes split correctly by host header
- Internal ports are not publicly reachable
