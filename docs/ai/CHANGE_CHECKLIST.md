# Change Checklist (AI-safe)

Use this checklist before finishing runtime-impacting changes.

## 1) Topology integrity

- [ ] `docker/docker-compose.yml` remains coherent (service names, volumes, dependencies)
- [ ] Only Nginx exposes public ports (`80/443`) unless explicitly required
- [ ] Web/API host split still works at Nginx level

## 2) Env contract

- [ ] New env vars are added to `.env.example`
- [ ] `settings.py` and compose env mapping are consistent
- [ ] Docs mention new/changed env variables

## 3) Background jobs/reporting

- [ ] `ext_conf/crontab.ini` paths match container paths (`/app`, `/var/log/nginx`)
- [ ] Cron jobs source `docker/cron-env.sh` (or equivalent) so jobs don't run with a minimal env
- [ ] `cron` and `goaccess` shared volumes remain aligned

## 4) Validation

- [ ] `./scripts/docker_smoke_test.sh` passes locally
- [ ] If CI behavior changed, `.github/workflows/docker-smoke.yml` and `.gitlab-ci.yml` still align
- [ ] Sensor update contract still works: `/update` expects `key,distance,voltage` and returns body `OK` + `wpl`
- [ ] Relay update contract still works: `/relay-update` expects `key,status` and returns body `OK` + control headers (including `ACTION`)
- [ ] Demo simulator jobs (if enabled) still run in cron and route via Nginx API host split

## 5) Firewall hardening (host-level)

- [ ] `firewalld` changes were applied on VPS host (not Docker container shell)
- [ ] If Cloudflare proxied mode is enabled, `80/443` are restricted to Cloudflare IP ranges and weekly sync timer is active
- [ ] `22` remains open after firewall changes
- [ ] If ICMP hardening is enabled, ICMP/ICMPv6 drop rules are present
- [ ] If SSH brute-force hardening is enabled, `fail2ban` jail `sshd` is active with expected thresholds

## 6) Documentation updates

- [ ] `README.md` updated for user-facing behavior changes
- [ ] `docker/README.md` updated for runtime/network/TLS changes
- [ ] `docs/ai/*` updated if architecture or operations changed

## Non-goals (unless explicitly requested)

- Full SQL-server migration (project is SQLite-oriented)
- Publicly exposing internal app upstream ports
- Reintroducing legacy uWSGI flow
