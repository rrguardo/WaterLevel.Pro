#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="sync_cloudflare_firewalld.sh"
TARGET_SCRIPT="/usr/local/sbin/${SCRIPT_NAME}"
SERVICE_PATH="/etc/systemd/system/wlp-cloudflare-firewall-sync.service"
TIMER_PATH="/etc/systemd/system/wlp-cloudflare-firewall-sync.timer"
REPO_SCRIPT_REL="scripts/firewall/${SCRIPT_NAME}"
ZONE="public"

usage() {
  cat <<'EOF'
Usage: install_cloudflare_firewalld_timer.sh [--zone <zone>]

Installs a weekly systemd timer that syncs Cloudflare IP ranges into firewalld,
restricting 80/443 to Cloudflare and keeping SSH open.

Options:
  --zone <zone>  Firewalld zone to manage (default: public)
  -h, --help     Show this help
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --zone)
        shift
        if [[ $# -eq 0 ]]; then
          echo "--zone requires a value" >&2
          exit 1
        fi
        ZONE="$1"
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown argument: $1" >&2
        usage >&2
        exit 1
        ;;
    esac
    shift
  done
}

main() {
  parse_args "$@"

  if [[ "$EUID" -ne 0 ]]; then
    echo "Run as root (or sudo)." >&2
    exit 1
  fi

  local repo_root
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  local src_script="${repo_root}/${REPO_SCRIPT_REL}"

  if [[ ! -f "$src_script" ]]; then
    echo "Source script not found: $src_script" >&2
    exit 1
  fi

  install -m 0755 "$src_script" "$TARGET_SCRIPT"

  cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=Sync Cloudflare IP ranges into firewalld for WLP
After=network-online.target firewalld.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=${TARGET_SCRIPT} --zone ${ZONE}
EOF

  cat > "$TIMER_PATH" <<'EOF'
[Unit]
Description=Weekly Cloudflare IP sync for WLP firewalld

[Timer]
OnCalendar=weekly
Persistent=true
RandomizedDelaySec=30m

[Install]
WantedBy=timers.target
EOF

  systemctl daemon-reload
  systemctl enable --now wlp-cloudflare-firewall-sync.timer
  systemctl start wlp-cloudflare-firewall-sync.service

  echo "Installed timer: wlp-cloudflare-firewall-sync.timer"
  echo "Check status with: systemctl status wlp-cloudflare-firewall-sync.service"
  echo "Check next run with: systemctl list-timers wlp-cloudflare-firewall-sync.timer"
}

main "$@"
