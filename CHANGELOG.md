# Changelog

All notable changes to Gondlin will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

The Tier 1 public API (everything under `NN/API/`, locked by `api-surface.lock`) is subject to
SemVer. Internal modules (`NN/Spec/`, `NN/Runtime/`, `NN/Proofs/`, etc.) may change without major
version bumps, though significant changes will be noted here.

## Versioning Policy

- **MAJOR** bump: Tier 1 API breaking change (removal, signature change, or semantics change for
  any declaration listed in `api-surface.lock`), addition of a new axiom to the trust kernel, or a
  major version bump of `lean-toolchain` (for example, `v4.x` → `v5.x`).
- **MINOR** bump: new features, new operators, new verifier families, new examples, or new Tier 1
  declarations — all in a backward-compatible way that does not change existing Tier 1 semantics.
- **PATCH** bump: bug fixes, proof improvements (including eliminating `sorry`/`admit`),
  documentation updates, performance improvements, and dependency bumps that keep the same public
  API and the same `lean-toolchain` pin.

## [Unreleased]

### Added
- `ROADMAP.md` committing the 2026–2029 plan in a phase-by-phase format with explicit exit
  criteria per phase.
- 10 Python hygiene checks under `scripts/checks/`: `check_case_collisions`,
  `trust_boundaries_check`, `proof_debt`, `api_surface`, `docs_link_check`, `docstring_coverage`,
  `lake_manifest_audit`, `lean_toolchain_pin`, `ci_workflow_lint`, `lean_imports_audit`.
- `scripts/release/sbom_generate.py` for SPDX 2.3 SBOM generation.
- `.devcontainer/` for VS Code dev container support (`devcontainer.json` and `post-create.sh`).
- `.editorconfig` for uniform formatting across editors.
- `Makefile` with developer shortcut targets (`build`, `test`, `checks`, `docs`, `verify`,
  `setup`, `sbom`, `clean`).
- `.github/workflows/nightly.yml` for daily proof-debt baseline tracking with 90-day artifact
  retention.
- `api-surface.lock` capturing 777 Tier 1 declarations under `NN/API/`.
- `trust-boundaries.toml` machine-readable mirror of `TRUST_BOUNDARIES.md`, cross-checked in CI.

### Changed
- `.github/workflows/ci.yml` now triggers on `push` and `pull_request` (previously
  `workflow_dispatch` only).
- CI adds a `hygiene` job that runs all Python checks before any Lean build.

## [0.1.0] — 2026-05-13

### Added
- Initial commit: gondlin (derived from TorchLean, MIT-licensed).
- Lean 4 framework for formalizing neural networks: typed tensors, model APIs,
  shared graph IR, runtime + autograd, finite-precision semantics, certificate
  checkers, optional CUDA backend with portable CPU stubs.
- Documentation surfaces: `home_page/` (Jekyll), `docs-site/` (Next.js static export deployed to
  Cloudflare Workers at torchlean.org), `blueprint/` (Verso-Blueprint), doc-gen4 API reference
  hosted at `/api`.
- `docs-site/` polish: Tailwind wired to the Geist font variable, syntax highlighting, on-page
  table of contents, SEO metadata, landing page, interactive module graph, citation block, and
  redesigned favicon.
- `lakefile.lean` adjustment: skip `-lm` on macOS so Lean's bundled `ld64.lld` does not choke on
  libm (which lives in `libSystem` on Darwin).
- README pointing to in-repo documentation sources rather than unpublished GitHub Pages URLs.

[Unreleased]: https://github.com/nktkt/gondlin/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nktkt/gondlin/releases/tag/v0.1.0
