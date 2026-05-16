# Security Policy

Gondolin is a Lean 4 framework for stating and checking mathematical claims about
neural-network artifacts. Security in this project means protecting the
soundness of those claims, the integrity of the artifacts that feed them, and
the isolation of code that runs untrusted Lean.

This policy describes what counts as a security issue, how to report one
privately, and the supply-chain hygiene that backs each release.

## Scope

The following are treated as security issues:

- **Soundness regressions** — a theorem becomes provable in `NN/` that should
  not be, including any path that lets `False` or an unintended specification
  contradiction be derived from the public facade.
- **Newly introduced unauthorized axioms** — any `axiom` declaration in `NN/`
  not allowlisted by `scripts/checks/repo_lint.py` and named in
  `TRUST_BOUNDARIES.md` and `trust-boundaries.toml`.
- **CUDA FFI memory safety** — use-after-free, out-of-bounds reads or writes,
  uninitialized device memory, or finalizer/free ordering bugs in `csrc/cuda/`.
- **Compromise of an external producer** — tampering with or impersonation of
  the CROWN oracle, the Arb / `python-flint` subprocess, the Julia subprocess,
  or the PyTorch import/export path in a way that causes Lean to accept a bogus
  certificate.
- **Supply chain issues in `lake-manifest.json` deps** — typosquats, unpinned
  revisions, or compromised upstream Lake packages reaching a build.
- **Comparator sandbox escape** — any way for an untrusted `Solution.lean`
  submitted through `lake exe verify -- judge` to break out of the `landrun`
  sandbox, read host state outside the allowlist, or influence the trusted
  `Challenge.lean` checker.

## Out of Scope

The following are not security issues and should go through normal issues or
PRs:

- Performance regressions.
- Lean elaboration speed.
- `doc-gen4` rendering bugs.
- Style or lint findings, including formatting drift caught by repository hygiene scripts.

## Reporting Flow

Report suspected vulnerabilities privately. Do **not** open a public GitHub
issue for an embargoed vulnerability.

Preferred channels:

1. **GitHub Security Advisories** on this repository, once the advisory surface
   is enabled.
2. **Email** `<TBD-security-email>` with a description, reproduction steps, and
   affected commits or releases.

We acknowledge new reports within **5 business days**. The default coordinated
disclosure window is **90 days** from acknowledgement; longer windows are
negotiated case by case when a fix requires upstream changes (Lean, Mathlib,
CUDA toolchain, comparator).

## Supply Chain Hygiene

Each PR and release run the following checks in CI before any Lean build:

- `scripts/checks/lake_manifest_audit.py` — detects drift between
  `lake-manifest.json` and the `require` lines in `lakefile.lean`, including
  pinned revisions and the mathlib-is-last invariant.
- `scripts/checks/lean_toolchain_pin.py` — verifies `lean-toolchain` is
  well-formed and that the pinned Lean version matches the mathlib and
  `doc-gen4` tag pins in `lakefile.lean` and the manifest.
- `scripts/release/sbom_generate.py` — produces a Software Bill of Materials
  per release covering Lake dependencies, the Lean toolchain, and recorded
  native dependencies.

PR-time CI also runs the soundness-adjacent checks:

- `scripts/checks/proof_debt.py --strict` — fails on any new `sorry`,
  `admit`, or non-allowlisted `axiom` in `NN/`.
- `scripts/checks/trust_boundaries_check.py` — keeps `TRUST_BOUNDARIES.md`,
  `trust-boundaries.toml`, and `repo_lint.py`'s `ALLOWED_AXIOMS` consistent.

A change that introduces a new axiom or weakens a Prop-valued contract must
land alongside updates to all three trust-boundary sources, or CI rejects it.

## Trust Boundaries Pointer

The authoritative trust inventory lives in:

- [`TRUST_BOUNDARIES.md`](TRUST_BOUNDARIES.md) — prose description of the
  kernel-level axioms, the Prop-valued runtime contracts, opaque
  declarations, the CUDA FFI surface, executable floating point, and external
  numeric oracles.
- [`trust-boundaries.toml`](trust-boundaries.toml) — machine-readable mirror
  consumed by `trust_boundaries_check.py`.

Read both before filing a soundness report so the report can name the exact
boundary it crosses.

## Comparator Sandbox

`lake exe verify -- judge` wraps `leanprover/comparator` to compare a trusted
`Challenge.lean` against an untrusted `Solution.lean`. Submissions run inside a
`landrun` sandbox launched by `scripts/sandbox/run_comparator.py`.

The sandbox enforces filesystem, network, and process isolation through
`landrun`. The comparator JSON config controls two additional policy levers:

- **Resource limits** — CPU time, memory, and wall-clock caps on the untrusted
  Lean process.
- **Import allowlist** — the set of modules a `Solution.lean` may `import`,
  preventing arbitrary access to runtime or FFI code from inside a submission.

Sandbox escapes, lax default limits, and accidentally over-broad import
allowlists are all in scope for this policy.

## Reproducible Builds

Gondolin pins its build inputs:

- [`lean-toolchain`](lean-toolchain) pins the Lean compiler version.
- [`lake-manifest.json`](lake-manifest.json) locks every transitive Lake
  dependency to a specific revision.
- The `hygiene` CI job runs all Python-only repository checks (including the
  manifest and toolchain audits above) before any Lean build starts, so drift
  fails fast and cannot reach a release artifact.

A clean checkout at a tagged release should produce the same proof set and the
same artifact metadata, modulo platform-dependent CUDA paths documented in
`TRUST_BOUNDARIES.md`.

## CVE Process

When a security fix lands:

1. The fix is committed under a clear changelog entry naming the affected
   surface (axiom, FFI path, oracle, sandbox).
2. If a CVE ID is assigned, the ID is recorded in the changelog entry and the
   GitHub Security Advisory.
3. A patch release is tagged off the affected release line.
4. `scripts/release/sbom_generate.py` is re-run and the updated SBOM is
   re-published alongside the patch release.

## Cryptographic Supply-Chain

Release signing (for example via `cosign` and the Sigstore transparency log)
is **not yet implemented**. Once configured, signatures will cover the source
tarball, the generated SBOM, and any published binary artifacts. Until then,
consumers should pin to a specific Git revision and verify the
`lake-manifest.json` lock locally.

Tracking placeholder: `<TBD-signing-plan>`.

## Acknowledgements

We credit reporters who follow this policy, with their permission, after the
fix ships.

- _No reports yet._
