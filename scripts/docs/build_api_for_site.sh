#!/usr/bin/env bash
# Generate the DocGen4 API reference into `docs-site/public/api/`.
#
# `docs-site` is a Next.js static export (`output: "export"`) deployed to
# Cloudflare Workers as torchlean.org. `public/api/` is copied verbatim into
# `out/api/` at `next build` time. We do NOT commit the generated tree; this
# script regenerates it before each deploy so the live site stays in sync with
# the current Lean source.
#
# Mirrors the DocGen portion of `scripts/docs/build_site.sh` (which targets the
# Jekyll site under `home_page/docs/`), but writes to the docs-site path
# instead.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "==> Building Lean modules"
lake build

echo "==> Building DocGen API docs (DISABLE_EQUATIONS=1)"
# Lake does not include DISABLE_EQUATIONS in the docInfo trace, so remove the
# cached DocGen DB/data before rebuilding. Otherwise Lake may replay stale
# noisy docInfo artifacts with equations rendered.
rm -rf .lake/build/doc .lake/build/doc-data .lake/build/api-docs.db
DISABLE_EQUATIONS=1 lake build NN:docs

echo "==> Copying DocGen output to docs-site/public/api"
rm -rf docs-site/public/api
cp -r .lake/build/doc docs-site/public/api
find docs-site/public/api -name "*.trace" -delete
find docs-site/public/api -name "*.hash" -delete

echo "==> Stripping dependency subtrees"
# DocGen emits per-module HTML for every transitively-imported library
# (Mathlib alone is ~400MB). The public site only documents Gondlin's own
# NN/ surface, so drop dependency subtrees to keep the deployed assets
# small (Cloudflare Workers has a 25MB per-file cap). Root-level entry
# pages (Aesop.html, Init.html, etc.) are kept so the module list renders;
# clicking them just won't drill into the dependency tree, which matches
# the previously-committed shape of this directory.
for dep in Mathlib Std Init Lean Lake Aesop Batteries Plausible Qq \
           ProofWidgets LeanSearchClient ImportGraph declarations; do
  rm -rf "docs-site/public/api/$dep"
done

echo "==> Polishing DocGen output for the site"
python3 scripts/docs/polish_docgen.py --docs docs-site/public/api

echo "==> Done: docs-site/public/api is ready for next build"
