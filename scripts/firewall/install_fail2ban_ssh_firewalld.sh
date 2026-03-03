#!/usr/bin/env bash
set -euo pipefail

MAXRETRY="4"
FINDTIME="10m"
BANTIME="24h"
IGNOREIP="127.0.0.1/8 ::1"
JAIL_FILE="/etc/fail2ban/jail.d/wlp-sshd.local"

usage() {
  cat <<'EOF'
Usage: install_fail2ban_ssh_firewalld.sh [--maxretry N] [--findtime 10m] [--bantime 24h]

Install and configure fail2ban for SSH with firewalld bans.
Default policy bans an IP after more than 4 failed SSH auth attempts.

Options:
  --maxretry N     Failed attempts before ban (default: 4)
  --findtime VAL   Failure window (default: 10m)
  --bantime VAL    Ban duration (default: 24h)
  -h, --help       Show this help
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --maxretry)
        shift
        MAXRETRY="${1:-}"
        ;;
      --findtime)
        shift
        FINDTIME="${1:-}"
        ;;
      --bantime)
        shift
        BANTIME="${1:-}"
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

require_root() {
  if [[ "$EUID" -ne 0 ]]; then
    echo "Run as root (or sudo)." >&2
    exit 1
  fi
}

choose_banaction() {
  if [[ -f /etc/fail2ban/action.d/firewallcmd-rich-rules.conf ]]; then
    echo "firewallcmd-rich-rules"
    return
  fi
  if [[ -f /etc/fail2ban/action.d/firewallcmd-ipset.conf ]]; then
    echo "firewallcmd-ipset"
    return
  fi
  echo ""
}

main() {
  parse_args "$@"
  require_root

  dnf -y install fail2ban

  local banaction
  banaction="$(choose_banaction)"
  if [[ -z "$banaction" ]]; then
    echo "No fail2ban firewalld action found in /etc/fail2ban/action.d" >&2
    exit 1
  fi

  mkdir -p /etc/fail2ban/jail.d

  cat > "$JAIL_FILE" <<EOF
[DEFAULT]
ignoreip = ${IGNOREIP}
bantime = ${BANTIME}
findtime = ${FINDTIME}
maxretry = ${MAXRETRY}
backend = systemd
banaction = ${banaction}

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
EOF

  systemctl enable --now fail2ban
  systemctl restart fail2ban

  local tries=0
  until fail2ban-client ping >/dev/null 2>&1; do
    tries=$((tries + 1))
    if [[ "$tries" -ge 10 ]]; then
      echo "fail2ban did not become ready in time." >&2
      systemctl status fail2ban --no-pager || true
      exit 1
    fi
    sleep 1
  done

  fail2ban-client ping
  fail2ban-client status sshd

  echo "fail2ban SSH policy active. maxretry=${MAXRETRY}, findtime=${FINDTIME}, bantime=${BANTIME}, banaction=${banaction}"
}

main "$@"
