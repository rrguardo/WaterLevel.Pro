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
7) Run real post-deploy checks, including:
   - ./scripts/docker_smoke_test.sh
   - web: /ping returns PONG
   - api: /link without params returns FAIL
8) If Cloudflare mode is enabled in the input, apply Cloudflare-aware validation and TLS assumptions.
    - If DNS automation is requested, require Custom API Token with at least:
       - Zone.DNS.Edit
       - Zone.Zone.Read
9) Return a concise execution report with:
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
