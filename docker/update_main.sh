#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

STASH_MSG="wlp-auto-stash-before-main-update-$(date +%Y%m%d-%H%M%S)"

echo "[wlp] Stashing local changes (including untracked)"
git stash push -u -m "$STASH_MSG" >/dev/null || true

LATEST_STASH="$(git stash list | grep -F "$STASH_MSG" | head -n1 | cut -d: -f1 || true)"

echo "[wlp] Fetching remote main"
git fetch origin main

echo "[wlp] Switching to main"
git checkout main

echo "[wlp] Applying remote state from origin/main"
git reset --hard origin/main

echo "[wlp] Stash info"

# Apply the stash if it was created
if [[ -n "$LATEST_STASH" ]]; then
  echo "[wlp] Created stash: $LATEST_STASH"
  git stash show --stat "$LATEST_STASH"
  echo "[wlp] Applying $LATEST_STASH to restore local changes..."
  git stash apply "$LATEST_STASH"
else
  echo "[wlp] No new stash entry was created (no local changes to stash)."
fi

echo "[wlp] Restarting docker services"
"$ROOT_DIR/docker/down.sh"
"$ROOT_DIR/docker/up.sh"

echo "[wlp] Done"
