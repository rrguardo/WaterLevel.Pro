#!/usr/bin/env bash
set -euo pipefail

CF_IPV4_URL="https://www.cloudflare.com/ips-v4"
CF_IPV6_URL="https://www.cloudflare.com/ips-v6"
IPSET_V4="wlp_cloudflare_v4"
IPSET_V6="wlp_cloudflare_v6"
DEFAULT_ZONE="public"
DRY_RUN=0
ZONE="${DEFAULT_ZONE}"

usage() {
  cat <<'EOF'
Usage: sync_cloudflare_firewalld.sh [--zone <zone>] [--dry-run]

Sync Cloudflare IPv4/IPv6 ranges into firewalld and restrict 80/443 to Cloudflare only.
Keeps SSH (22) open in the selected zone.

Options:
  --zone <zone>  Firewalld zone to manage (default: public)
  --dry-run      Print commands without applying firewall changes
  -h, --help     Show this help
EOF
}

log() {
  printf '[wlp-cf-fw] %s\n' "$*"
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
    return 0
  fi
  "$@"
}

query_expected() {
  local expected="$1"
  shift

  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd "$@"
    return 0
  fi

  if "$@" >/dev/null 2>&1; then
    if [[ "$expected" != "yes" ]]; then
      echo "Unexpected firewall state: expected '$expected' but command succeeded: $*" >&2
      exit 1
    fi
  else
    if [[ "$expected" != "no" ]]; then
      echo "Unexpected firewall state: expected '$expected' but command failed: $*" >&2
      exit 1
    fi
  fi
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$cmd" >&2
    exit 1
  fi
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
      --dry-run)
        DRY_RUN=1
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

ensure_firewalld_running() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    return 0
  fi
  systemctl is-active --quiet firewalld
}

fetch_ranges() {
  local url="$1"
  curl -fsSL --connect-timeout 10 --max-time 30 "$url" | sed '/^\s*$/d'
}

validate_ranges() {
  local family="$1"
  local data="$2"

  if [[ "$family" == "ipv4" ]]; then
    if ! grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$' <<<"$data"; then
      echo "Could not validate Cloudflare IPv4 ranges" >&2
      exit 1
    fi
  else
    if ! grep -Eq '^[0-9a-fA-F:]+/[0-9]+$' <<<"$data"; then
      echo "Could not validate Cloudflare IPv6 ranges" >&2
      exit 1
    fi
  fi
}

ipset_exists() {
  local name="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    return 1
  fi
  firewall-cmd --permanent --get-ipsets | tr ' ' '\n' | grep -Fxq "$name"
}

ensure_ipset() {
  local name="$1"
  local family="$2"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd firewall-cmd --permanent --new-ipset="$name" --type=hash:net --option=family="$family"
    return 0
  fi
  if ipset_exists "$name"; then
    return 0
  fi
  run_cmd firewall-cmd --permanent --new-ipset="$name" --type=hash:net --option=family="$family"
}

clear_ipset_entries() {
  local name="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd firewall-cmd --permanent --ipset="$name" --get-entries
    return 0
  fi

  mapfile -t entries < <(firewall-cmd --permanent --ipset="$name" --get-entries)
  for entry in "${entries[@]}"; do
    [[ -z "$entry" ]] && continue
    run_cmd firewall-cmd --permanent --ipset="$name" --remove-entry="$entry"
  done
}

populate_ipset() {
  local name="$1"
  local entries="$2"
  while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue
    run_cmd firewall-cmd --permanent --ipset="$name" --add-entry="$entry"
  done <<< "$entries"
}

ensure_rich_rule() {
  local rule="$1"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    if firewall-cmd --permanent --zone="$ZONE" --query-rich-rule="$rule" >/dev/null 2>&1; then
      return 0
    fi
  fi
  run_cmd firewall-cmd --permanent --zone="$ZONE" --add-rich-rule="$rule"
}

ensure_direct_rule() {
  local family="$1"
  local priority="$2"
  shift 2
  local args=("$@")

  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd firewall-cmd --direct --add-rule "$family" filter DOCKER-USER "$priority" "${args[@]}"
    return 0
  fi

  if firewall-cmd --direct --query-rule "$family" filter DOCKER-USER "$priority" "${args[@]}" >/dev/null 2>&1; then
    return 0
  fi

  if ! firewall-cmd --direct --add-rule "$family" filter DOCKER-USER "$priority" "${args[@]}" >/dev/null 2>&1; then
    log "Warning: could not apply optional $family DOCKER-USER rule; continuing without it."
  fi
}

ensure_direct_rule_optional() {
  local family="$1"
  local priority="$2"
  shift 2
  local args=("$@")

  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd firewall-cmd --direct --add-rule "$family" filter DOCKER-USER "$priority" "${args[@]}"
    return 0
  fi

  if firewall-cmd --direct --query-rule "$family" filter DOCKER-USER "$priority" "${args[@]}" >/dev/null 2>&1; then
    return 0
  fi

  if ! firewall-cmd --direct --add-rule "$family" filter DOCKER-USER "$priority" "${args[@]}" >/dev/null 2>&1; then
    log "Warning: could not apply optional $family DOCKER-USER rule; continuing without it."
  fi
}

has_ipv6_docker_user_chain() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    return 0
  fi

  if ! command -v ip6tables >/dev/null 2>&1; then
    return 1
  fi

  ip6tables -S DOCKER-USER >/dev/null 2>&1
}

main() {
  parse_args "$@"

  require_command curl

  if [[ "$DRY_RUN" -eq 0 ]]; then
    require_command firewall-cmd
    require_command systemctl
  fi

  if [[ "$DRY_RUN" -eq 0 && "$EUID" -ne 0 ]]; then
    echo "Run as root (or use sudo)." >&2
    exit 1
  fi

  ensure_firewalld_running || {
    echo "firewalld is not active." >&2
    exit 1
  }

  log "Downloading Cloudflare IP ranges..."
  local cf_ipv4 cf_ipv6
  cf_ipv4="$(fetch_ranges "$CF_IPV4_URL")"
  cf_ipv6="$(fetch_ranges "$CF_IPV6_URL")"

  validate_ranges "ipv4" "$cf_ipv4"
  validate_ranges "ipv6" "$cf_ipv6"

  log "Applying rules in zone: $ZONE"

  run_cmd firewall-cmd --permanent --zone="$ZONE" --add-service=ssh
  run_cmd firewall-cmd --permanent --zone="$ZONE" --remove-service=http || true
  run_cmd firewall-cmd --permanent --zone="$ZONE" --remove-service=https || true
  run_cmd firewall-cmd --permanent --zone="$ZONE" --remove-port=80/tcp || true
  run_cmd firewall-cmd --permanent --zone="$ZONE" --remove-port=443/tcp || true

  ensure_ipset "$IPSET_V4" inet
  ensure_ipset "$IPSET_V6" inet6

  clear_ipset_entries "$IPSET_V4"
  clear_ipset_entries "$IPSET_V6"

  populate_ipset "$IPSET_V4" "$cf_ipv4"
  populate_ipset "$IPSET_V6" "$cf_ipv6"

  local rule_v4_http='rule family="ipv4" source ipset="wlp_cloudflare_v4" port protocol="tcp" port="80" accept'
  local rule_v4_https='rule family="ipv4" source ipset="wlp_cloudflare_v4" port protocol="tcp" port="443" accept'
  local rule_v6_http='rule family="ipv6" source ipset="wlp_cloudflare_v6" port protocol="tcp" port="80" accept'
  local rule_v6_https='rule family="ipv6" source ipset="wlp_cloudflare_v6" port protocol="tcp" port="443" accept'

  ensure_rich_rule "$rule_v4_http"
  ensure_rich_rule "$rule_v4_https"
  ensure_rich_rule "$rule_v6_http"
  ensure_rich_rule "$rule_v6_https"

  log "Applying Docker DNAT guard rules in DOCKER-USER..."
  ensure_direct_rule ipv4 0 -p tcp -m multiport --dports 80,443 -m set --match-set "$IPSET_V4" src -j ACCEPT
  ensure_direct_rule ipv4 1 -p tcp -m multiport --dports 80,443 -j DROP
  if has_ipv6_docker_user_chain; then
    ensure_direct_rule_optional ipv6 0 -p tcp -m multiport --dports 80,443 -m set --match-set "$IPSET_V6" src -j ACCEPT
    ensure_direct_rule_optional ipv6 1 -p tcp -m multiport --dports 80,443 -j DROP
  else
    log "Skipping optional IPv6 DOCKER-USER rules (chain not available)."
  fi

  run_cmd firewall-cmd --reload

  log "Verifying resulting firewall state..."
  query_expected yes firewall-cmd --zone="$ZONE" --query-service=ssh
  query_expected no firewall-cmd --zone="$ZONE" --query-service=http
  query_expected no firewall-cmd --zone="$ZONE" --query-service=https
  query_expected yes firewall-cmd --zone="$ZONE" --query-rich-rule="$rule_v4_http"
  query_expected yes firewall-cmd --zone="$ZONE" --query-rich-rule="$rule_v4_https"
  query_expected yes firewall-cmd --zone="$ZONE" --query-rich-rule="$rule_v6_http"
  query_expected yes firewall-cmd --zone="$ZONE" --query-rich-rule="$rule_v6_https"

  log "Done. 80/443 now restricted to Cloudflare IPs in zone '$ZONE'; SSH remains allowed."
}

main "$@"
