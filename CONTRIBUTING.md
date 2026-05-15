# Contributing to Gondlin

Thanks for helping improve Gondlin.
Good contributions usually improve one of four areas:

- make a mathematical definition or theorem clearer,
- add a useful operator, verifier fragment, backend hook, or example,
- improve tests, docs, or website walkthroughs,
- make a trust boundary easier to inspect.

If you are not sure where a change belongs, open an issue or draft PR. Small, concrete PRs are much
easier to review than one large branch that touches every layer at once.

## What Good PRs Look Like

A good Gondlin PR usually has one clear purpose. It might add one operator with its spec and
tests, one theorem with supporting lemmas, one example with a documented command, or one
trust-boundary clarification. Small changes are much easier to review than branches that touch the
API, runtime, proofs, and website at once.

## First Build

Gondlin is pinned by `lean-toolchain`. From a fresh checkout:

```bash
lake update
lake build
lake test
```

Common targets:

```bash
lake build NN.Library
DISABLE_EQUATIONS=1 lake build NN:docs
lake exe verify -- list
```

`import NN` is the everyday user facade. `import NN.Library` is the broad library umbrella for
specs, runtime, verification, and proofs, while still excluding executables and tests.

## Tests, Examples, and Verification

Run the curated test suite:

```bash
lake exe nn_tests_suite
```

Run a few small examples:

```bash
lake env lean --run NN/Examples/Quickstart/TensorBasics.lean
lake env lean --run NN/Examples/Quickstart/AutogradBasics.lean -- --dtype float
lake exe gondlin mlp --cpu --steps 10
```

Run verifier demos:

```bash
lake exe verify -- list
lake exe verify -- gondlin-ibp
```

When you add behavior, add at least one stabilizer: a theorem, a test, a small runnable example, or
a guide/API-doc note. For new operators, examples are useful, but they are not a substitute for the
shared semantics path described below.

## Documentation and Website

The website combines generated API docs, the Verso guide, import/dependency graphs, and a small
Jekyll site.

Build API docs:

```bash
rm -rf .lake/build/doc .lake/build/doc-data .lake/build/api-docs.db
DISABLE_EQUATIONS=1 lake build NN:docs
```

`DISABLE_EQUATIONS=1` keeps DocGen focused on declaration types, docstrings, module docs, source
links, and search data instead of rendering every generated equation lemma from Lean and Mathlib.

Build the Verso guide:

```bash
cd blueprint
lake exe blueprint-gen --output ../_out/blueprint
```

Preview the site locally:

```bash
cd home_page
bundle config set path vendor/bundle
bundle _2.3.14_ install
bundle _2.3.14_ exec jekyll serve --config _config.yml,_config_dev.yml
```

If native Ruby gems fail to build, install your distribution’s Ruby development package and build
tools.

## Trust Boundaries

Gondlin keeps three categories separate:

- Lean-checked definitions and theorems,
- executable Lean code and tests,
- external producers or runtimes such as CUDA, Python, solvers, datasets, and generated
  certificates.

When a contribution crosses one of those boundaries, name it plainly. Do not imply that a CUDA
kernel, Python script, checkpoint, dataset, or external certificate producer is trusted merely because
Lean checks the consumer side.

Relevant files:

- `TRUST_BOUNDARIES.md`
- `THIRD_PARTY_NOTICES.md`
- `NN/Examples/Verification/*`
- `scripts/verification/*`
- `csrc/cuda/*`

## Adding an Operator

Gondlin's safest extension path starts at the semantics and works outward. Prefer one operator
meaning shared by user code, graph execution, and verification. If an operator is deliberately
runtime-only or checker-only, say so in the file that introduces it.

Typical order:

1. Add the mathematical definition under `NN/Spec/Core/*` or `NN/Spec/Layers/*`.
2. If training or reverse-mode execution needs gradients for the operator, add its forward function
   and VJP contract under `NN/Spec/Autograd/*`.
3. If it is a graph primitive, extend `NN.IR.OpKind` and the denotation in `NN/IR/Semantics.lean`.
4. Update shape inference/checking in `NN/IR/Infer.lean` and related contract files.
5. Add runtime support under `NN/Runtime/*` when execution needs it.
6. If a verifier must reason about the operator, add propagation rules or certificate expectations
   under `NN/Verification/*` or `NN/MLTheory/*`.
7. Add a test or runnable example.

If an operator is intentionally only for execution or only for verification, document that boundary
instead of quietly slipping it into the shared semantics layer.

## Examples

Examples live under `NN/Examples/*`. Most model examples are runnable through:

```bash
lake exe gondlin <demo> [args...]
```

Direct Lean examples usually look like:

```bash
lake env lean --run NN/Examples/.../Foo.lean -- [args...]
```

Keep examples small enough to run, but not so artificial that readers cannot tell what they are
learning. If an example needs external data, make the path explicit and keep checked-in fixtures
small.

## Style and Proof Hygiene

Gondlin aims to keep `NN/` free of `sorry`.

```bash
python3 scripts/checks/repo_lint.py
```

Project conventions:

- Prefer small modules with minimal imports.
- Add docstrings for user-facing definitions, structures, and theorems.
- Split expensive proofs into named lemmas instead of relying on huge `simp` or `aesop` calls.
- Keep executable demos and proof code separate when they have different trust assumptions.
- Avoid introducing axioms. If one is unavoidable, quarantine and document it.

## Local Checks

Gondlin ships a set of Python-only repository checks under `scripts/checks/`. They have no Lean
dependency and are cheap to run locally. CI runs all of them in the `hygiene` job before any Lean
build starts; the `slow_proofs` job is opt-in and only fires via `workflow_dispatch`.

- `proof_debt.py` — counts `sorry`/`admit`/`axiom`/`opaque`; target is zero sorries/admits and only
  allowlisted axioms.

  ```bash
  python3 scripts/checks/proof_debt.py --strict
  ```

- `api_surface.py` — Tier 1 frozen API-surface check; compares the live `NN/API/` facade against
  `api-surface.lock`.

  ```bash
  python3 scripts/checks/api_surface.py --check
  ```

- `trust_boundaries_check.py` — keeps `TRUST_BOUNDARIES.md`, `trust-boundaries.toml`, and
  `repo_lint.py`'s `ALLOWED_AXIOMS` consistent.

  ```bash
  python3 scripts/checks/trust_boundaries_check.py
  ```

- `docs_link_check.py` — validates markdown links across the repository.

  ```bash
  python3 scripts/checks/docs_link_check.py
  ```

- `docstring_coverage.py` — measures `/-- ... -/` coverage on the `NN/API/` facade; target is ≥80%.

  ```bash
  python3 scripts/checks/docstring_coverage.py --min-coverage 80
  ```

- `lake_manifest_audit.py` — detects drift between `lake-manifest.json` and the `require` lines in
  `lakefile.lean` (direct deps, pinned revisions, mathlib-is-last invariant).

  ```bash
  python3 scripts/checks/lake_manifest_audit.py
  ```

- `lean_toolchain_pin.py` — verifies `lean-toolchain` is well-formed and that the pinned Lean version
  matches the mathlib/doc-gen4 tag pins in `lakefile.lean` and the manifest.

  ```bash
  python3 scripts/checks/lean_toolchain_pin.py
  ```

- `ci_workflow_lint.py` — stdlib-only structural sanity check for `.github/workflows/*.yml`
  (required top-level keys, step shape, no tabs, `actions/*` version pinning).

  ```bash
  python3 scripts/checks/ci_workflow_lint.py
  ```

Run every Python check sequentially and report pass/fail:

```bash
fail=0; for c in \
  scripts/checks/proof_debt.py:--strict \
  scripts/checks/api_surface.py:--check \
  scripts/checks/trust_boundaries_check.py: \
  scripts/checks/docs_link_check.py: \
  scripts/checks/docstring_coverage.py:'--min-coverage 80' \
  scripts/checks/lake_manifest_audit.py: \
  scripts/checks/lean_toolchain_pin.py: \
  scripts/checks/ci_workflow_lint.py: \
; do s="${c%%:*}"; a="${c#*:}"; printf '== %s %s ==\n' "$s" "$a"; if python3 "$s" $a; then echo "PASS: $s"; else echo "FAIL: $s"; fail=1; fi; done; exit $fail
```

For environment setup, `.devcontainer/devcontainer.json` provisions a VS Code dev container with the
pinned Lean toolchain. Developers not using the devcontainer can run `scripts/dev/setup.sh` to
install elan, pin the toolchain from `lean-toolchain`, warm the Mathlib cache, and self-check the
repo. `.editorconfig` keeps indentation and line endings uniform across editors.

## Checking Untrusted Proofs

Gondlin includes a wrapper for `leanprover/comparator`, which can compare a trusted
`Challenge.lean` against an untrusted `Solution.lean` inside a `landrun` sandbox.

Prerequisite:

- Install `landrun` and make sure it is on `PATH`: https://github.com/Zouuup/landrun

Typical workflow:

1. Create a separate small Lake project with `Challenge.lean`, `Solution.lean`, and a comparator
   JSON config.
2. Make that project depend on Gondlin, for example:
   `require Gondlin from "/path/to/Gondlin"`.
3. Run:

```bash
python3 /path/to/Gondlin/scripts/sandbox/run_comparator.py ./config.json --project .
```

See `https://github.com/leanprover/comparator` for the JSON schema and default axiom allowlist
pattern.

## PR Checklist

- `lake build` succeeds from a clean checkout.
- Relevant tests, examples, or theorem checks were added.
- User-facing changes include docstrings and, when useful, guide or website notes.
- Trust boundaries are named rather than hidden.
- No new `sorry` appears in `NN/`.

## Questions

Open a GitHub issue or draft PR for bugs, proposals, or design questions. For general Lean/proof
questions, the Lean community Zulip is often the fastest place to ask:
https://leanprover.zulipchat.com/
