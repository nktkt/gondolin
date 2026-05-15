# Gondlin Roadmap (2026–2029)

Status legend: ✅ done · 🟡 in progress · ⬜ not started · 🚧 blocked on external factor (time, hardware, organization).

This document is the project's living plan. Each subsection is a unit a PR can target. The "Exit
criteria" lines are the objective bar for declaring a phase complete. Maintainers should treat this
as authoritative and update it in the same PR that lands the implementation.

For trust boundaries and assumptions referenced below, see `TRUST_BOUNDARIES.md` and the
machine-readable mirror in `trust-boundaries.toml`.

## Current Position (2026-05-15)

- Version: `v0.1.0`, Lean toolchain `leanprover/lean4:v4.29.0`.
- Scale: 821 Lean files, ~260k lines, single `main` branch.
- Build: `lake build NN.Library`; tests via `lake test`; verification via `lake exe verify`.
- Backends: portable CPU stub + optional CUDA (`-K cuda=true`).
- Trust kernel: 2 axioms (`crown_oracle`, `instNonemptyBuffer`), 3 prop contracts, 2 opaque non-FFI
  declarations, 5 external numeric oracles.
- Hygiene: 10 Python checks in CI's `hygiene` job (case collisions, trust boundaries, proof debt,
  API surface, docs links, docstring coverage, manifest audit, toolchain pin, workflow lint,
  imports audit).

Health metrics (initial observation): `sorry`=0, `admit`=0, unauthorized axioms=0, NN/API docstring
coverage=84.4%, broken doc links=0, import cycles=0, layer warnings=4 (Floats→Runtime, IR→Runtime
×2, Verification→Examples).

---

## Phase 0 — Foundations Hardening (2026 Q2–Q3, `v0.1.x` → `v0.2.0`)

### 0.1 CI and build hygiene
- ✅ `push`/`pull_request` CI triggers; `hygiene` job runs before any Lean build.
- ✅ Mathlib cache fetch (`lake exe cache get`) baked into both `ci.yml` and `nightly.yml`.
- ✅ `lake-manifest.json` drift audit via `scripts/checks/lake_manifest_audit.py`.
- ✅ `lean-toolchain` pin audit via `scripts/checks/lean_toolchain_pin.py`.
- ✅ Workflow YAML structural lint via `scripts/checks/ci_workflow_lint.py`.
- ✅ Nightly `proof-debt.json` artifact, 90-day retention.
- ⬜ macOS matrix entry on CI (currently Linux only). Exit: CI green on both Ubuntu and macOS for
  CPU-stub builds within 45 minutes.

### 0.2 Documentation
- ✅ TRUST_BOUNDARIES.md mirrored as `trust-boundaries.toml` with three-way consistency check.
- ✅ Docstring coverage measured on NN/API at 84.4% (exceeds 80% target).
- ⬜ `docs-migration.md` describing the role split between `home_page/` (Jekyll), `docs-site/`
  (Next), Verso blueprint, and doc-gen4 API reference.
- ⬜ Verso guide reorganized into a 5-chapter arc: Getting Started → Spec → Runtime → Proof →
  Verification.
- ⬜ doc-gen4 build pinned in CI with cache. Exit: `make docs` completes under 10 minutes on a warm
  cache.

### 0.3 Developer experience
- ✅ VS Code dev container (`.devcontainer/`).
- ✅ `.editorconfig` for uniform formatting.
- ✅ Non-devcontainer setup script (`scripts/dev/setup.sh`).
- ✅ Local-shortcut `Makefile` (`make build/test/checks/docs/verify/setup/sbom/clean`).
- ⬜ JetBrains IDE configuration matching VS Code's Lean experience.

**Exit criteria:** all of 0.1, 0.2, 0.3 ⬜ items closed; CI median time under 30 minutes on warm
cache; zero unauthorized axioms; docstring coverage ≥80% sustained on every PR.

---

## Phase 1 — Public Surface Freeze (2026 Q3–Q4, `v0.2` → `v0.3`)

### 1.1 API freeze policy
- ✅ `api-surface.lock` initial snapshot (777 Tier 1 declarations) generated.
- ✅ CI diffs the live surface against the lock and fails on any drift.
- ⬜ `NN/API/` files split into `NN/API/Tier1/` (frozen) and `NN/API/Tier2/` (experimental). Convention:
  Tier 1 changes require a `BREAKING:` prefix in the PR title plus a manual lock-regeneration step.
- ⬜ Deprecation shims: introduce `@[deprecated]` attribute usage convention in `NN.API.Adapters`;
  retain deprecated names for at least one minor version.

### 1.2 Tensor / model API ergonomics
- ⬜ Slicing sugar: `x[..., 0:3]` style notation for `NN.API.Tensor`. Likely a `macro_rules` block
  reusing Mathlib's `Range` syntax.
- ⬜ `NN.API.Models` module DSL: `Sequential` and `Module` re-expressed with `@[layer]` attribute
  for clearer model definitions.
- ⬜ `NN.API.Data` split into pure spec + side-effect runtime, with deterministic-test guarantees.

### 1.3 Storage and serialization
- ⬜ Weight format v1: `safetensors`-compatible header + Lean magic preamble.
- ⬜ `NN.Runtime.PyTorch` import/export tightened to: shape check → dtype check → `Prop` contract.
  Exit: bit-exact (FP32) round-trip for MLP/CNN/Transformer/ViT/ResNet against a reference PyTorch
  checkpoint.

**Exit criteria:** Tier 1 surface unchanged for one minor release cycle; deprecation policy
documented in CONTRIBUTING.md; all five reference models pass round-trip.

---

## Phase 2 — Proof Layer Consolidation (2026 Q4 → 2027 Q1, `v0.3` → `v0.4`)

### 2.1 Proof-debt visibility
- ✅ `scripts/checks/proof_debt.py` reports `sorry`/`admit`/`axiom`/`opaque` counts.
- ✅ Nightly JSON artifact published; `--baseline` mode supports regression detection.
- ⬜ `docs-site/proof-status` page consuming the nightly artifact and showing a time series.
- ⬜ Axiom allowlist cross-checked between `repo_lint.py`, `TRUST_BOUNDARIES.md`, and
  `trust-boundaries.toml` (already wired; sustain it).

### 2.2 Autograd correctness closure
- ⬜ Bridge theorem `autograd_runtime_agrees`: for every primitive op, `NN.Spec.Autograd`'s
  mathematical gradient matches `NN.Runtime.Autograd.Engine`'s VJP. Target coverage ≥95% of
  primitives; remainder documented as Prop contracts.
- ⬜ Non-differentiable-point policy (`ReLU` at 0, max-pool tie-break) formalized as a `Prop` class.

### 2.3 Float bridge strengthening
- ⬜ `NN/Floats/IEEEExec` complete for binary16, bfloat16, binary32, binary64.
- ⬜ `Float32Bridge.RuntimeFloat32MatchesIEEE32Exec` quality gate: 10⁹-sample differential fuzz
  between the executable model and `csrc/` C arithmetic.

### 2.4 Mathlib integration for analytic derivatives
- ⬜ `analytic_derivative_correct` bridge: NN-defined derivatives agree with `Mathlib.Analysis.Calculus.FDeriv`.

**Exit criteria:** primitive-op autograd coverage ≥95%; float bridge fuzz passes 10⁹ samples; at
least 3 Mathlib-bridged derivative theorems for canonical layers (Linear, Conv2D, Softmax).

---

## Phase 3 — Verification CLI as Product (2027 Q1–Q2, `v0.4` → `v0.5`)

### 3.1 Certificate format v1
- ⬜ `Certificate.v1` schema (JSON + optional `.lean` proof script) shared across Robustness, ODE,
  PINN, Geometry3D, Splines verifiers.
- ⬜ Migrate existing 4 verifier families to v1 with backward-compat readers for v0.

### 3.2 External solver adapters
- ⬜ α,β-CROWN bi-directional adapter; minimize `crown_oracle`'s scope.
- ⬜ `vnnlib` import/export for Marabou and nnenum compatibility.
- ⬜ VNN-COMP MNIST and CIFAR-10 benchmark: `lake exe verify -- vnnlib` matches the reference
  benchmark conclusions on CI.

### 3.3 Sandbox security
- ⬜ Comparator-backed `verify -- judge` subcommand with resource limits in
  `scripts/checks/comparator_policy.toml`.

**Exit criteria:** v1 certificate format adopted by all verifier families; 3 external solvers
integrated; VNN-COMP reference-match rate 100% on the configured benchmark slice.

---

## Phase 4 — Performance & GPU Track (2027 Q2–Q3, `v0.5` → `v0.6`) 🚧

### 4.1 CUDA backend maturation
- ⬜ Per-precision backend selector (`-K dgemm_backend=cublas|gondlin`).
- ⬜ Mixed precision dtype map (FP16/BF16/TF32) in `NN.Runtime.External.Dtype`.
- ⬜ Lean-side linear-API ownership for `Cuda.Buffer`; reduce `instNonemptyBuffer` axiom scope.

### 4.2 ROCm / Metal experimental branches 🚧
- ⬜ `csrc/rocm/` and `csrc/metal/` build with `-K backend=rocm|metal` (default off). Requires
  physical hardware access for verification.

### 4.3 IR optimization passes
- ⬜ Fusion / constant folding / dead-code elimination in `NN/IR`.
- ⬜ `pass_preserves_semantics` theorem for each pass.
- ⬜ Benchmark harness (`lake exe gondlin bench`) with CI-published comparisons to PyTorch.

**Exit criteria:** MLP/CNN/Transformer/ViT forward+backward ≥0.7× PyTorch (cuBLAS) on FP32; IR
passes deliver ≥1.2× speedup on a configured workload set.

---

## Phase 5 — Model & Domain Expansion (2027 Q3 → 2028 Q1, `v0.6` → `v0.8`)

### 5.1 Model zoo additions
- ⬜ Mamba / state-space
- ⬜ Diffusion (DDPM, EDM)
- ⬜ Flow Matching
- ⬜ Mixture-of-Experts (sparse routing)
- ⬜ Graph NN (GCN, GAT)
- ⬜ Neural ODE / CDE

Each addition must ship with: (i) Spec, (ii) Runtime, (iii) at least one non-trivial proven
property (e.g. equivariance, conservation).

### 5.2 Scientific ML
- ⬜ `NN.Verification.PINN` extended to multi-dimensional PDEs (heat, wave, Burgers).
- ⬜ `NN.Verification.ODE` extended to stiff ODEs + Lyapunov stability.
- ⬜ `NN.Verification.Geometry3D` extended to SDF and NeRF-style rasterizer verification.

### 5.3 Reinforcement learning
- ⬜ On-policy (PPO, A2C) and off-policy (DQN, SAC) algorithms in `NN.Runtime.RL`.
- ⬜ Bellman consistency + policy-gradient correctness theorems in `NN.Proofs.RL`.

### 5.4 Self-supervised / generative theory
- ⬜ Representation-collapse avoidance theorems for SimCLR/DINO-family losses.
- ⬜ Refined ELBO upper-bound theorems for diffusion models.

**Exit criteria:** 6 new model families fully integrated; PINN/ODE/Geometry3D extension theorems
proven; RL on-policy + off-policy complete with at least one Bellman theorem.

---

## Phase 6 — Compiler & Interop Maturity (2028 Q1–Q2, `v0.8` → `v0.9`)

### 6.1 ONNX / StableHLO export
- ⬜ `NN.IR` → ONNX (opset 18+) and StableHLO exporters.
- ⬜ Semantic-preservation `Prop` contracts in `NN/Proofs/IR/Export`.

### 6.2 TVM / IREE / XLA bridges (experimental)
- ⬜ Minimal runner adapters under `NN/Runtime/External/`.
- ⬜ Round-trip Examples/Interop tests for each backend.

### 6.3 PyTorch / JAX bridge
- ⬜ Full bidirectional PyTorch bridge (weights + arch + training loop).
- ⬜ Minimal JAX (`jax.numpy` + `flax`) bridge on an experimental branch.

### 6.4 Lean / Mathlib upgrade lane
- ⬜ Lean v4.30+ toolchain bump (`scripts/update-toolchain.sh`).
- ⬜ `module` / `public import` propagated across all modules.

**Exit criteria:** ONNX and StableHLO export with semantic-preservation contracts for the 5
reference models; PyTorch bridge round-trip parity; Lean toolchain upgradable as a routine
operation.

---

## Phase 7 — Community & Governance (2028 Q3–Q4, `v0.9` → `v1.0-rc`) 🚧

### 7.1 Governance 🚧
- ⬜ `GOVERNANCE.md` (Tier 1 API changes require 2 reviewers; Lean community liaison role).
- ⬜ Release train: bimonthly minors, immediate patches.
- ⬜ `SECURITY.md` reporting flow + CVE process.

### 7.2 Permanent docs hosting
- ⬜ GitHub Pages enabled; README's `nktkt.github.io/gondlin/` URLs resolve.
- ⬜ `torchlean.org` (current `docs-site`) vs a potential `gondlin.dev` role split documented.

### 7.3 Education and outreach 🚧
- ⬜ Graduate-level course notes in `docs-site/courses/formal-nn`.
- ⬜ Quickstart notebooks redistributed via Jupyter (Lean kernel).
- ⬜ Conference submissions to ITP, CPP, and NeurIPS workshops.

### 7.4 License and redistribution
- ✅ Minimal SPDX 2.3 SBOM generator (`scripts/release/sbom_generate.py`) — 18 packages.
- ⬜ Weight redistribution ethics policy (`MODELS_POLICY.md`).

**Exit criteria:** governance live, Pages-hosted docs reachable, SBOM attached to every release,
at least one accepted publication or invited talk.

---

## Phase 8 — `v1.0` Release (2029 Q1) 🚧

### 8.1 Release criteria
- ⬜ Tier 1 API stable for ≥12 months.
- ⬜ Axiom count remains at the documented two (or has a clear mathematical-dependency
  replacement).
- ⬜ Reference model forward+backward ≥0.8× PyTorch.
- ⬜ VNN-COMP reference match = 100% on the configured benchmark slice.
- ⬜ API docstring coverage ≥80% (already met at 84.4%); guide complete in 5 chapters; exercise
  set of ≥30 problems.

### 8.2 Milestone outputs
- ⬜ Peer-reviewed paper at ITP or CPP describing the framework as a whole.
- ⬜ `lake new gondlin-project` template; new projects reach `lake build` success in under 60
  seconds.

---

## Phase 9 — Beyond `v1.0` (post-2029)

Research-frontier candidates, to be selected at planning time rather than committed in advance.

| Theme | Motivation | Formalization focus |
| --- | --- | --- |
| Large-scale pretraining numerical behavior | LLM loss landscape | optimizer stochastic dynamics, Lyapunov analysis |
| Circuit-level interaction verification (mechanistic interpretability) | Safety research | semantic equivalence of sub-circuits |
| Quantized / low-bit inference correctness | Edge deployment | INT8/INT4/posit/log-domain bridges |
| Federated learning + differential privacy | Real-world deployment | DP-SGD stochastic invariants |
| Distributed training semantics | Scale | all-reduce / pipeline-parallel sync invariants |
| Symbolic + numerical differentiation convergence | Scientific ML | full Mathlib analysis bridge |
| Active learning / experimental design | Data efficiency | acquisition-function optimality |
| Neural ODE / SDE closed-form stability | Scientific ML | Lyapunov / Itô invariants |
| Verified compiler to CUDA PTX | Performance with guarantees | semantic-preservation to PTX |

---

## Cross-cutting commitments (every phase)

1. **Axiom minimization.** New `axiom` requires ≥2 reviewer approvals and an entry in
   `TRUST_BOUNDARIES.md` and `trust-boundaries.toml`.
2. **Benchmark continuity.** `docs-site/benchmarks` updated by CI; perf regressions surface on PRs.
3. **Dependency hygiene.** Mathlib, Lean toolchain, doc-gen4, Comparator, lean4export reviewed
   quarterly.
4. **Doc freshness.** Link checker and Verso build run on every `main` push.
5. **Reproducibility.** `lake-manifest.json` drift fails CI; toolchain pin verified.

## Immediate next 30 days

| # | Task | Status |
| --- | --- | --- |
| 1 | CI green on `push`/`PR` | ✅ |
| 2 | `proof_debt.json` baseline tracked | ✅ (via nightly) |
| 3 | `api-surface.lock` initial generation | ✅ |
| 4 | Docs link checker | ✅ |
| 5 | `trust-boundaries.toml` machine-readable | ✅ |
| 6 | devcontainer + setup script | ✅ |
| 7 | Layer-violation triage (4 known warnings) | ⬜ |
| 8 | macOS CI matrix entry | ⬜ |
| 9 | docs-migration.md drafted | ⬜ |
| 10 | `NN/API/Tier1/` vs `Tier2/` split | ⬜ |

When updating this file: re-run `make checks` after edits, and bump the "Current Position" date.
