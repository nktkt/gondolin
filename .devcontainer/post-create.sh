#!/usr/bin/env bash
# Idempotent post-create hook for the Gondlin devcontainer.
#
# Installs elan (Lean version manager), pins the toolchain declared in
# `lean-toolchain`, and warms the Mathlib build cache via `lake exe cache get`.
# Safe to re-run: elan installer is skipped if already present, and
# `cache get` failures are non-fatal so a stale cache will not block startup.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[gondlin] post-create starting in $REPO_ROOT"

# ---------------------------------------------------------------------------
# 1. Install elan (Lean toolchain manager) if not already on PATH.
# ---------------------------------------------------------------------------
if ! command -v elan >/dev/null 2>&1; then
  echo "[gondlin] installing elan ..."
  curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf \
    | sh -s -- -y --default-toolchain none
else
  echo "[gondlin] elan already installed: $(elan --version)"
fi

# Make elan visible to the current shell for the remaining steps.
if [ -f "$HOME/.elan/env" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.elan/env"
fi
export PATH="$HOME/.elan/bin:$PATH"

# ---------------------------------------------------------------------------
# 2. Install / pin the toolchain declared in `lean-toolchain`.
# ---------------------------------------------------------------------------
if [ -f "$REPO_ROOT/lean-toolchain" ]; then
  PINNED_TOOLCHAIN="$(tr -d '[:space:]' < "$REPO_ROOT/lean-toolchain")"
  echo "[gondlin] pinning Lean toolchain: ${PINNED_TOOLCHAIN}"
  elan toolchain install "${PINNED_TOOLCHAIN}"
  elan override set "${PINNED_TOOLCHAIN}"
else
  echo "[gondlin] WARNING: lean-toolchain not found; skipping toolchain install"
fi

# ---------------------------------------------------------------------------
# 3. Warm the Mathlib cache (best-effort; do not fail the container).
# ---------------------------------------------------------------------------
if command -v lake >/dev/null 2>&1; then
  echo "[gondlin] warming Mathlib build cache (lake exe cache get) ..."
  lake exe cache get || echo "[gondlin] cache get failed (non-fatal); continuing"
else
  echo "[gondlin] WARNING: lake not on PATH after elan install"
fi

# ---------------------------------------------------------------------------
# 4. Banner.
# ---------------------------------------------------------------------------
cat <<'BANNER'

============================================================
 Gondlin devcontainer ready -- try `lake build NN.Library`
============================================================

BANNER
