# Layer Violations — Triage

This document tracks the 4 layer warnings emitted by
[`scripts/checks/lean_imports_audit.py`](../scripts/checks/lean_imports_audit.py).
Layer warnings are advisory; cycles would fail CI hard. The script currently
reports `0` cycles and `4` layer warnings (with `--strict-layering` they would
become errors).

To reproduce the warning list:

```bash
python3 scripts/checks/lean_imports_audit.py --show-violations
```

## Status legend

- `recommended` — already matches the recommended layering; no action needed.
- `acknowledged` — the violation is acknowledged and intentional (carve-out).
- `pending` — pending maintainer decision.
- `urgent` — needs urgent fix (e.g. risk of cycle, blocker for refactor).

## Layering reference

The layering rule, taken from `LAYER_RULES` in
[`lean_imports_audit.py`](../scripts/checks/lean_imports_audit.py):

| Source subtree         | Forbidden imports                                  | Rationale                                               |
| ---------------------- | -------------------------------------------------- | ------------------------------------------------------- |
| `NN.Spec.*`            | `NN.Runtime.*`, `NN.API.*`, `NN.Examples.*`, `NN.Tests.*` | Spec is the bottom layer.                          |
| `NN.IR.*`              | `NN.Runtime.*`, `NN.API.*`, `NN.Examples.*`, `NN.Tests.*` | IR sits below Runtime.                             |
| `NN.Floats.*`          | `NN.Runtime.*`, `NN.API.*`, `NN.Examples.*`, `NN.Tests.*` | Floats is a low-level numeric layer.               |
| `NN.Runtime.*`         | `NN.API.*`, `NN.Examples.*`, `NN.Tests.*`          | Runtime must not import the public facade.              |
| `NN.Proofs.*`          | `NN.API.*`, `NN.Examples.*`, `NN.Tests.*`          | Proofs cross-cut Spec/IR/Runtime but stay below API.    |
| `NN.MLTheory.*`        | `NN.API.*`, `NN.Examples.*`, `NN.Tests.*`          | Theory layer; same constraint as Proofs.                |
| `NN.Verification.*`    | `NN.Tests.*`, `NN.Examples.*`                      | Verification may import broadly but is a leaf relative to Examples/Tests. |
| `NN.API.*`             | `NN.Examples.*`, `NN.Tests.*`                      | API is the public facade.                               |

Big picture: `Spec / Floats → IR → Runtime → API`, with
`Proofs / MLTheory / Verification` orthogonal, and `Examples / Tests` at the
top as sinks only.

---

## Violation 1 — `NN.Floats.Arb.Oracle → NN.Runtime.External.Process`

**Status:** `pending`

**What:** `public import NN.Runtime.External.Process` at
[`NN/Floats/Arb/Oracle.lean:10`](../NN/Floats/Arb/Oracle.lean).

**Why it likely exists:**
`NN.Floats.Arb.Oracle` is a wrapper around an out-of-process Arb/FLINT oracle:
it spawns `python NN/Floats/Arb/arb_oracle.py`, parses the JSON it prints to
stdout, and exposes the parsed enclosure to the rest of the codebase
([`NN/Floats/Arb/Oracle.lean`](../NN/Floats/Arb/Oracle.lean), lines 16–35).
The actual subprocess plumbing (environment-variable overrides for the
executable, availability checks, "run and parse stdout as JSON" helpers) lives
in `NN.Runtime.External.Process` ([`NN/Runtime/External/Process.lean`](../NN/Runtime/External/Process.lean)),
which is filed under `NN.Runtime.*` because that is where the rest of the
external-process glue (Julia, etc.) lives. The Floats layer is supposed to be
purely numeric/algebraic, so reaching up into Runtime for `IO`/subprocess
helpers is the proximate cause of the warning.

**Severity:** **Soft.** There is no risk of a cycle here — `NN.Runtime.External.Process`
imports only `Lean.Data.Json` and `Lean`, so it cannot pull anything back down
into `NN.Floats.*`. The violation is architectural taste: it reflects that
"subprocess helpers" are not really *runtime* in the autograd/training sense,
they are infrastructure shared by both Floats oracles and Runtime backends.

**Resolution options:**

- **Option A — Move `NN.Runtime.External.Process` down a layer.**
  Rename to `NN.Util.External.Process` (or `NN.IO.External.Process`) and update
  the handful of importers (`NN.Floats.Arb.Oracle`, `NN.Runtime.External.Julia`,
  plus any other oracle wrappers). Refactor cost is small (file move + import
  renames). After the move, both `NN.Floats.*` and `NN.Runtime.*` can import it
  without crossing a layer.
- **Option B — Split `NN.Floats.Arb.Oracle` so the subprocess call lives outside `NN.Floats.*`.**
  Keep a pure `NN.Floats.Arb.OracleTypes` module for the parsed result type and
  the JSON decoder, and move the `run` / `runRequestJson` IO actions into
  `NN.Runtime.Arb.Oracle` (or similar). Floats then exports only pure data;
  Runtime wires it to the subprocess. This is cleaner but increases the
  refactor surface and changes the public namespace.
- **Option C — Carve out an exception in `LAYER_RULES`.**
  Replace `forbidden_prefixes=("NN.Runtime.", ...)` for `NN.Floats.*` with an
  allow-list that permits `NN.Runtime.External.Process` specifically. Justified
  if we accept that "External" is infrastructure rather than runtime. Low
  effort, but pushes the smell into the rule itself.

**Recommendation:** **Option A.** The import target is genuinely
infrastructure (no autograd / no Spec / no IR), the importer count is small,
and renaming preserves the existing API. Once moved, the rule stays strict and
no carve-out is needed.

---

## Violation 2 — `NN.IR.Semantics → NN.Runtime.Autograd.Gondlin.Random`

**Status:** `pending`

**What:** `public import NN.Runtime.Autograd.Gondlin.Random` at
[`NN/IR/Semantics.lean:11`](../NN/IR/Semantics.lean). Used at lines 485, 487,
496, 498 to evaluate the `randUniform` and `bernoulliMask` IR nodes:

```lean
let key := Runtime.Autograd.Gondlin.Random.keyOf seed i
let t : Tensor α n.outShape :=
  Runtime.Autograd.Gondlin.Random.uniform (α := α) key (s := n.outShape)
```

**Why it likely exists:**
`NN.IR.Semantics` is the denotational evaluator for the IR. The IR has
stochastic ops (`randUniform seed`, `bernoulliMask seed`) so the evaluator
needs a deterministic seeded PRNG. The PRNG implementation
([`NN/Runtime/Autograd/Gondlin/Random.lean`](../NN/Runtime/Autograd/Gondlin/Random.lean))
lives under `NN.Runtime.Autograd.Gondlin.*` because it was originally written
for `Gondlin.Session.dropout` (a Session-level training utility — see lines
37–40 of that file). The PRNG itself is **pure** — SplitMix64 mixing,
seed-threaded, no `IO` — so it has no real reason to live under Runtime; it
ended up there for organizational reasons (it ships with the Gondlin
runtime/training stack).

**Severity:** **Soft, but the most worth fixing of the four.** The function
being imported (`Random.keyOf`, `Random.uniform`, `Random.mask`) is pure and
its own imports are only `NN.Spec.Core.Context` and `NN.Spec.Core.Tensor.Core`
— both already below IR. So moving it down a layer is essentially a file move,
no transitive damage. Leaving it in Runtime is fragile: any future addition to
`NN.Runtime.Autograd.Gondlin.Random` that pulls in another Runtime module
would silently widen the IR→Runtime dependency surface.

**Resolution options:**

- **Option A — Move `NN.Runtime.Autograd.Gondlin.Random` down to `NN.Spec.Random` (or `NN.IR.Random`).**
  Its only imports are `NN.Spec.Core.Context` and `NN.Spec.Core.Tensor.Core`
  (already below IR), so the move is mechanical. Update importers:
  `NN.IR.Semantics` and any Session/Gondlin code that uses it (the file
  comment at line 37 mentions `Gondlin.Session.dropout`). After the move both
  IR and Runtime can import it without crossing a layer.
- **Option B — Split `NN.IR.Semantics` so the stochastic node cases live in a separate `NN.Runtime.IR.StochasticEval` module.**
  IR keeps the pure-deterministic evaluator; Runtime supplies an extension
  for `randUniform` / `bernoulliMask`. This is the textbook fix (open-recursion
  semantics) but requires plumbing an evaluator-dispatch hook through every
  caller of `eval`. High refactor cost.
- **Option C — Carve out `NN.Runtime.Autograd.Gondlin.Random` in `LAYER_RULES`.**
  Add it as an explicit allow-list entry for `NN.IR.*`. Justified by "this
  module is misfiled but moving it is risky / forthcoming." Low effort, but
  the misfiling is the actual root cause and a carve-out hides it.

**Recommendation:** **Option A.** The PRNG is pure and its imports already
sit below IR, so the move is trivial and removes the violation cleanly. Also
resolves Violation 3 indirectly if combined with that fix (see below).

---

## Violation 3 — `NN.IR.Semantics → NN.Runtime.Context`

**Status:** `pending`

**What:** `public import NN.Runtime.Context` at
[`NN/IR/Semantics.lean:10`](../NN/IR/Semantics.lean). The `Context` typeclass
is used pervasively as a parameter constraint, e.g.
`structure ConstFlat (α : Type) [Context α]` at line 84 and at every
evaluator definition (`evalConst`, `evalLinear`, `evalConv2D`, `eval`, …) —
40+ occurrences across the file.

**Why it likely exists:**
`NN.Runtime.Context` is the type-erased runtime value registry (`AnyTensor`,
`RuntimeContext`, `register_variable`, etc.) — see
[`NN/Runtime/Context.lean`](../NN/Runtime/Context.lean), lines 22–28. *But*
the `Context α` typeclass that `NN.IR.Semantics` actually uses is a much
narrower abstraction: it is the per-element-type "what does a scalar look
like" interface (an `Inhabited`-style typeclass; see the imports of
`NN.Runtime.Autograd.Gondlin.Random.lean` which pulls
`NN.Spec.Core.Context`). Most likely `Context` was originally defined in
`NN.Spec.Core.Context` and then re-exported (or aliased) under `NN.Runtime`,
and `NN.IR.Semantics` happens to import the Runtime copy. The IR really only
needs the underlying scalar-type typeclass; it does not need `AnyTensor` /
`RuntimeContext` at all.

**Severity:** **Soft, but possibly the easiest to fix.** No risk of a cycle.
If the `Context` typeclass that IR depends on is the same one defined in
`NN.Spec.Core.Context`, this is a one-line import change.

**Resolution options:**

- **Option A — Import `NN.Spec.Core.Context` directly instead of `NN.Runtime.Context`.**
  If, as suspected, `Context α` is already exposed by `NN.Spec.Core.Context`
  (which `NN.Runtime.Autograd.Gondlin.Random` imports), `NN.IR.Semantics` can
  switch its import. One-line change; the rest of the file is unaffected
  because the `Context α` typeclass surface is identical.
- **Option B — Move `NN.Runtime.Context` down to `NN.Spec.Runtime.Context` (or `NN.IR.Context`).**
  Heavier: `NN.Runtime.Context` defines `AnyTensor` and `RuntimeContext`, which
  *do* belong to the runtime layer conceptually. Splitting the scalar-type
  typeclass out from the runtime registry is essentially Option A in another
  form.
- **Option C — Carve out an exception in `LAYER_RULES`.**
  Add `NN.Runtime.Context` to an allow-list for `NN.IR.*`. Justified if the
  IR genuinely needs the runtime registry types. Based on the usage pattern
  (only the `Context α` typeclass appears in this file), this seems unlikely
  to be necessary.

**Recommendation:** **Option A**, conditional on a maintainer confirming that
the `Context` typeclass surface used by IR is the one in `NN.Spec.Core.Context`.
If not, fall back to **Option B** (extract the typeclass to a Spec module).
`<TBD: maintainer to confirm typeclass location>` before applying.

---

## Violation 4 — `NN.Verification.CLI → NN.Examples.Verification`

**Status:** `pending`

**What:** `public import NN.Examples.Verification` at
[`NN/Verification/CLI.lean:10`](../NN/Verification/CLI.lean). The file is a
unified verification dispatcher (`lake exe verify -- <tool> [args...]`) and
registers ~10 example workflows by name: `LiRPA.MlpVerify.verifyCert`,
`PINN.Verify.run`, `Robustness.VerifyMarginCert.run`,
`Gondlin.GondlinIBP.main`, `VNNComp.MnistFcVerify.main`, etc.
(see lines 106–209).

**Why it likely exists:**
The CLI is a *registry*: every example workflow that we want to expose via
`lake exe verify` needs to be reachable from a single entry point. The
quickest way to do that is to have the CLI module import every example
directly and put its `main` / `verifyCert` into the `Tool` table. This
implements the desired functionality but treats Examples as a *library*, not
as a leaf — which is the architectural inversion the layering rule is meant
to prevent.

**Severity:** **Soft, but the most architecturally noisy of the four.** No
cycle risk (Examples don't import the CLI back), but it is the only violation
where the *direction* is inverted: a non-Example module imports an Example
module. This makes it harder to ever rule "Examples is a leaf" strictly, and
it means every Example workflow becomes a transitive build dependency of the
verify CLI.

**Resolution options:**

- **Option A — Move the example workflows' executable entry points into `NN.Verification.*`.**
  For each example currently registered, create a thin `NN.Verification.{X}.RunCert`
  module that exposes `verifyCert` / `main`, and leave the *demo data and
  walk-through prose* under `NN.Examples.Verification.{X}`. The CLI imports
  only `NN.Verification.*`. Examples may still import `NN.Verification.{X}.RunCert`
  if they want to run end-to-end. Highest refactor cost (~10 modules touched)
  but cleanest result.
- **Option B — Split `NN.Verification.CLI` into a core dispatcher and an example registry.**
  Keep `NN.Verification.CLI` (just the `Tool` record, the dispatcher loop,
  `parseArgs`). Move the example `Tool` table into
  `NN.Examples.Verification.CLI` (which lives under Examples and is therefore
  allowed to import both `NN.Verification.*` and `NN.Examples.*`). The
  `lake exe verify` binary's `main` lives in Examples and calls the dispatcher
  in Verification. Medium effort; preserves all current behavior.
- **Option C — Carve out `NN.Examples.Verification` in `LAYER_RULES` for `NN.Verification.CLI` specifically.**
  Most honest read: the verification CLI *is* a unified entry point for our
  example workflows, and there is no clean alternative without a Lean-side
  plugin registry. Document that `NN.Verification.CLI` is the registry and
  whitelist it. Low effort, but bakes the inversion in permanently.

**Recommendation:** **Option B.** Splitting the CLI into "dispatcher
mechanics" (stays in `NN.Verification.*`) and "example registry" (moves to
`NN.Examples.Verification.CLI`) cleanly resolves the inversion: Examples
imports Verification (which is allowed by the rule), not the other way
around. Option A is over-engineered for what is effectively a `Tool` lookup
table; Option C admits defeat unnecessarily.

---

## Future work

- Resolve the four violations above and then promote layer warnings to errors
  by running `python3 scripts/checks/lean_imports_audit.py --strict-layering`
  in CI. Today this would fail with `4` errors.
- After each resolution, re-run
  `python3 scripts/checks/lean_imports_audit.py --show-violations` to confirm
  the warning count drops monotonically.
- Consider also wiring `--strict-layering` into `scripts/checks/check.sh` once
  the count reaches zero.
- If Option C is chosen for any violation, document the carve-out in the
  rationale string of the corresponding `LayerRule` in
  [`lean_imports_audit.py`](../scripts/checks/lean_imports_audit.py) so the
  exception is self-documenting in the audit output.
