#!/usr/bin/env bash
# Developer setup for the Gondolin Lean 4 project.
#
# Companion to .devcontainer/post-create.sh for developers who are NOT using
# the devcontainer (e.g. a native macOS or Linux checkout). Idempotent: safe
# to re-run after the first invocation.
#
# This script intentionally does NOT modify the user's shell rc files.

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve the repository root regardless of the caller's cwd.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------
log() {
  printf '==> %s\n' "$*"
}

err() {
  printf 'ERROR: %s\n' "$*" >&2
}

# ---------------------------------------------------------------------------
# Detect OS for nicer messaging (no behavior difference yet).
# ---------------------------------------------------------------------------
UNAME_S="$(uname -s)"
case "$UNAME_S" in
  Darwin) OS_LABEL="macOS" ;;
  Linux)  OS_LABEL="Linux" ;;
  *)      OS_LABEL="$UNAME_S" ;;
esac
log "Detected platform: $OS_LABEL"
log "Repository root: $SCRIPT_DIR"

# ---------------------------------------------------------------------------
# 1. Verify lean-toolchain pin exists.
# ---------------------------------------------------------------------------
if [[ ! -f lean-toolchain ]]; then
  err "lean-toolchain file not found at $SCRIPT_DIR/lean-toolchain"
  err "This script must be run inside a Gondolin checkout."
  exit 2
fi

TOOLCHAIN="$(tr -d '[:space:]' < lean-toolchain)"
if [[ -z "$TOOLCHAIN" ]]; then
  err "lean-toolchain is empty; cannot determine Lean version."
  exit 2
fi
log "Pinned Lean toolchain: $TOOLCHAIN"

# ---------------------------------------------------------------------------
# 2. Ensure elan is installed.
# ---------------------------------------------------------------------------
if ! command -v elan >/dev/null 2>&1 && [[ ! -x "$HOME/.elan/bin/elan" ]]; then
  log "elan not found; installing from leanprover/elan..."
  if ! command -v curl >/dev/null 2>&1; then
    err "curl is required to bootstrap elan but is not on PATH."
    exit 3
  fi
  curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
else
  log "elan already installed; skipping bootstrap."
fi

# ---------------------------------------------------------------------------
# 3. Source elan into this script's environment (no rc file changes).
# ---------------------------------------------------------------------------
if [[ -f "$HOME/.elan/env" ]]; then
  # shellcheck disable=SC1091
  . "$HOME/.elan/env"
else
  err "Expected $HOME/.elan/env after elan install, but it is missing."
  exit 4
fi

if ! command -v elan >/dev/null 2>&1; then
  err "elan is still not on PATH after sourcing ~/.elan/env."
  exit 4
fi

# ---------------------------------------------------------------------------
# 4. Install + pin the toolchain pinned in lean-toolchain.
# ---------------------------------------------------------------------------
log "Installing Lean toolchain '$TOOLCHAIN' via elan..."
if ! elan toolchain install "$TOOLCHAIN"; then
  err "elan toolchain install failed for '$TOOLCHAIN'."
  exit 5
fi

log "Overriding repo-local toolchain to '$TOOLCHAIN'..."
if ! elan override set "$TOOLCHAIN"; then
  err "elan override set failed for '$TOOLCHAIN'."
  exit 5
fi

# ---------------------------------------------------------------------------
# 5. Fetch Mathlib cache. Soft-failure: building from source still works.
# ---------------------------------------------------------------------------
log "Fetching Mathlib oleans cache (lake exe cache get)..."
lake exe cache get || log "cache get failed; continuing (build will compile from source)."

# ---------------------------------------------------------------------------
# 6. Repo self-checks.
# ---------------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  err "python3 is required for repo self-checks but is not on PATH."
  exit 6
fi

log "Running proof-debt self-check (strict)..."
if ! python3 scripts/checks/proof_debt.py --strict; then
  err "proof_debt.py --strict failed."
  exit 7
fi

log "Running trust-boundaries self-check..."
if ! python3 scripts/checks/trust_boundaries_check.py; then
  err "trust_boundaries_check.py failed."
  exit 8
fi

# ---------------------------------------------------------------------------
# 7. Done. Print next-step banner.
# ---------------------------------------------------------------------------
cat <<'BANNER'

------------------------------------------------------------
 Gondolin developer setup complete.

 Suggested next steps:

   lake build NN.Library
   lake exe gondolin --help
   lake exe verify -- list

 Tip: elan was sourced only inside this script. To use Lean
 from your shell, add the following to your shell rc yourself:

   . "$HOME/.elan/env"
------------------------------------------------------------
BANNER
