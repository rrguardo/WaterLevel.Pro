# Requesting new features with GitHub Copilot (VS Code)

This guide is for people with **little to no development experience** who want to ask GitHub Copilot to add or change something in WaterLevel.Pro.

The goal is to help you write a request Copilot can actually implement, safely, without guessing.

## What you need

- VS Code installed
- The **GitHub Copilot** extension enabled in VS Code
- This repo opened in VS Code (Folder: `WaterLevel.Pro`)
- Optional (recommended): Docker Desktop / Docker Engine (so you can test the change)

## 60‑second overview (how to ask)

When asking Copilot for a feature, always include:

1) **What** you want (one sentence)
2) **Where** it should appear (page/URL/template name if you know it)
3) **Rules** / acceptance criteria (bullet list)
4) **What not to change** (important!)
5) **How to test** (what should you click / what endpoint should respond)

If you don’t know file names, that’s fine — Copilot can search the workspace.

## Safety note (important)

Do **not** paste secrets into chat:
- Cloudflare tokens
- SMTP passwords
- `.env` contents
- Device private keys

Instead say: “The secret already exists on the VPS as an env var named `XYZ`.”

## Recommended workflow (non‑developer friendly)

### Step 1 — Describe the feature in plain language

Example:

- “On the relay device page, make the ON/OFF control look like a toggle switch again (not a plain checkbox).”

### Step 2 — Add acceptance criteria

Good acceptance criteria are concrete and testable:

- Looks like a toggle switch (not a checkbox)
- Still works with the same click behavior
- Does not change backend behavior
- Works on mobile and desktop

### Step 3 — Ask Copilot with a “do not change” clause

Example prompt for Copilot Chat:

> Please restore the rocker-style ON/OFF visualization for the relay switch.
> 
> Constraints:
> - Do not change any backend routes or API behavior
> - Only adjust templates/CSS as needed
> - Keep existing element IDs used by JS (e.g. `Switch`)
> 
> Acceptance criteria:
> - The ON/OFF control is visually a toggle again
> - No JS errors in console
> 
> Please make the code changes directly in the repo.

### Step 4 — Let Copilot implement and then run quick checks

If you have Docker:

- Start stack: `docker compose -f docker/docker-compose.yml up -d --build`
- Smoke test: `./scripts/docker_smoke_test.sh`

If you don’t have Docker, you can still review the change by opening the affected HTML/CSS files.

### Step 5 — Ask Copilot to summarize and list exactly what changed

Example prompt:

> Summarize what you changed, which files, and how to verify it in the browser.

## Feature request template (copy/paste)

Paste this into Copilot Chat and fill in the blanks:

> **Feature**: <one sentence>
> 
> **Where**: <page/URL or description>
> 
> **Why**: <one sentence>
> 
> **Acceptance criteria**:
> - [ ] ...
> - [ ] ...
> 
> **Constraints**:
> - Don’t change: ...
> - Must keep: ...
> 
> **Test plan**:
> - Open: ...
> - Click: ...
> - Expect: ...

## Simple feature request example (copy/paste)

This is an intentionally small request that Copilot can implement in one pass.

> **Feature**: Hide the global footer when the device page is rendered inside an iframe.
> 
> **Where**: `GET /device_info?public_key=demo&smallversion=1` (this is used as an embedded chart in the relay page).
> 
> **Why**: When embedded, the footer takes extra space and looks like duplicate branding inside the iframe.
> 
> **Acceptance criteria**:
> - [ ] When `smallversion=1` is present, the HTML response does **not** include the footer text `Open-source base project`.
> - [ ] Normal pages (without `smallversion=1`) keep the footer unchanged.
> - [ ] No backend behavior changes (only template logic).
> 
> **Constraints**:
> - Don’t change: routing, endpoints, database, or API behavior.
> - Must keep: existing template inheritance and layout.
> 
> **Test plan**:
> - Open: `/device_info?public_key=demo&smallversion=1` and confirm footer is gone.
> - Open: `/device_info?public_key=demo` and confirm footer is still visible.

## Tips that make Copilot succeed

- Prefer “**exact behaviors**” over “make it better”.
- If it’s a UI change, include a screenshot and say what page it’s from.
- If it’s an API change, include example request/response.
- If you have a production contract (like `/ping` → `PONG`), mention it.

## Common WaterLevel.Pro pointers (optional)

- Web UI entrypoint: `app.py`
- Device/API entrypoint: `api.py`
- Docker runtime contract: `docker/docker-compose.yml`
- Nginx host routing: `ext_conf/docker/nginx.conf.template`
- Smoke test contract: `scripts/docker_smoke_test.sh`
