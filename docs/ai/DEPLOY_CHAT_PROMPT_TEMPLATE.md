# Deploy Chat Prompt Template (Fast Context)

Use this prompt when asking the AI agent to perform a real VPS deployment.

## Prompt

```text
I want a REAL VPS deployment (not mock tests) for WaterLevel.Pro.

Read and use this file as the single source of deploy input:
- docs/ai/DEPLOY_AGENT_INPUT.private.yaml

Required behavior:
1) Validate the file completeness and list missing fields (if any) in one pass.
2) If complete, generate the exact deployment plan and execute it step by step.
3) Use Docker Compose runtime from docker/docker-compose.yml.
4) Keep Nginx as the only public ingress (80/443).
5) Keep API on subdomain of same base domain.
6) Apply firewall baseline (allow 22/80/443; keep 8000/8001/6379 private).
7) Configure timezone:
   - Set VPS timezone via `timedatectl` to match `WLP_TZ`.
   - Ensure Docker services run with `TZ` from `WLP_TZ` and verify with `date` inside containers.
8) Run real post-deploy checks, including:
   - ./scripts/docker_smoke_test.sh
   - web: /ping returns PONG
   - api: /link without params returns FAIL
9) If Cloudflare mode is enabled in the input, apply Cloudflare-aware validation and TLS assumptions.
    - If DNS automation is requested, require Custom API Token with at least:
       - Zone.DNS.Edit
       - Zone.Zone.Read
   - Validate Cloudflare credentials using real zone operations (list DNS records and create/delete a temporary TXT), not only `/user/tokens/verify`.
   - Enforce Cloudflare edge cert coverage for all requested public hosts; if hostnames are deeper than one label (example: `api.sub.example.com`), require Advanced Certificate Manager or adjust hostnames to cert-covered pattern before finalizing.
   - If `tls.source=cloudflare_origin_cert` and `ssl_mode=full_strict`, ensure the origin `fullchain.pem` includes the Cloudflare Origin CA root appended (leaf + Origin CA root) to avoid Cloudflare 526 errors.
10) Enforce production SMTP readiness for alerts/device flows:
   - default to SMTP_TEST=false unless explicitly marked test-only
   - verify SPF, DKIM, DMARC records are configured
   - TXT record content must be in quotation marks (Cloudflare may auto-add quotes; it does not change behavior)
   - for minimal direct-send mode, SPF must include server.ip (ip4)
   - if smtp_dns.dkim_auto_generate_on_vps=true, generate DKIM keypair on VPS, set selector from smtp_dns.dkim_selector, and publish TXT via Cloudflare API
   - if smtp_dns.mode=cloudflare_api_managed, create/update those DNS records via Cloudflare API as DNS-only
11) Return a concise execution report with:
   - completed steps
   - failed steps
   - exact commands used
   - current blockers and next actions

Do not switch to unittest-only validation.
Proceed with real deployment flow.
```

## Optional addition for strict execution

```text
I authorize real command execution against the target VPS described in the input file.
```
