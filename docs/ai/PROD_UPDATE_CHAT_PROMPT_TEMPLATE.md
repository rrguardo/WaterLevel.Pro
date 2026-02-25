# Production Update Chat Prompt Template (Safe Change Mode)

Use this prompt when asking the AI agent to apply changes on a **live VPS**.

## Prompt

```text
I want a PRODUCTION UPDATE on a live VPS for WaterLevel.Pro.

Read and use this file as the source of deploy context:
- docs/ai/DEPLOY_AGENT_INPUT.private.yaml

CRITICAL SAFETY RULES (must follow):
1) Database safety first:
   - Do NOT delete, recreate, truncate, or reset any production SQLite database.
   - Do NOT run scripts that can rewrite demo data (for example reset_demo_db.py) unless I explicitly request it.
   - Do NOT run `docker compose down -v`.
   - Do NOT remove or recreate data volumes.
   - Before any change that touches runtime, create a timestamped DB backup outside the container and report the path.

2) Runtime safety:
   - Keep downtime minimal.
   - Prefer targeted restarts (`docker compose up -d --force-recreate <service>`) over full-stack restarts.
   - Do NOT restart unrelated services.

3) Config safety:
   - Do NOT overwrite my existing `/opt/wlp/.env` with defaults.
   - Do NOT remove existing crontab entries.
   - Do NOT remove prior custom settings from environment, cron, certificates, or nginx config.
   - If a value is missing, propose exact line changes and apply only those lines.

4) Git/update safety:
   - Pull/update repository safely without deleting local operational files.
   - If there are local modifications on VPS, show a plan and ask before destructive git actions.
   - Never use hard reset or clean commands without explicit approval.

5) Test safety on production:
   - Do NOT run tests that may mutate production DB.
   - Run only read-only health checks unless I explicitly approve more.

Execution workflow:
A) Print a short change plan with risk level (low/medium/high) per step.
B) Print exact commands before running anything risky.
C) Execute in small steps with validation after each step.
D) If a step fails, stop and report rollback commands.
E) Return a final report with:
   - what changed
   - what was NOT changed
   - backup paths created
   - health check results

Proceed in SAFE PRODUCTION mode.
```

## Optional strict add-on

```text
Do not perform any action that can impact persisted data unless you first ask and I explicitly approve.
```
