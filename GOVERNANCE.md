# Gondlin Governance

> ⚠️ DRAFT — This document is a proposal. Final policy is set by the project
> maintainers. Until adopted by an explicit vote/merge, anything below is a
> recommendation, not authoritative project policy.

This document proposes how Gondlin is governed: who can do what, how API
and trust-boundary changes are reviewed, how releases are cut, how
disagreements are resolved, and how the document itself is amended. It
complements [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`TRUST_BOUNDARIES.md`](TRUST_BOUNDARIES.md).

## Roles

Gondlin recognizes four roles. Roles describe review authority, not status;
one person may hold more than one over time.

**Maintainer.** Responsible for project direction, release cuts, and final
review of changes to the frozen Tier 1 API, trust boundaries, axioms, and
governance. Maintainers can merge PRs, cut releases, edit
`api-surface.lock`, amend `TRUST_BOUNDARIES.md`, and update the axiom
allowlist in `scripts/checks/repo_lint.py`. They cannot unilaterally change
the license, toolchain pin, governance, or axiom set; those require the
votes described below. Maintainers are added or removed by the procedure
in [Maintainer additions and removal](#maintainer-additions-and-removal).

**Reviewer.** Trusted contributor with sustained review history in one
or more subtrees (for example `NN/Spec`, `NN/Runtime`, `NN/Proofs`,
`NN/MLTheory`, `NN/Verification`, `csrc/cuda`). Reviewers can approve
PRs in their area and shepherd contributions through the standard
checks. They cannot merge PRs touching the frozen Tier 1 API, axioms,
trust boundaries, the toolchain pin, or governance without maintainer
sign-off. Nominated by a maintainer and confirmed by lazy consensus.
Reviewer status lapses after twelve months of inactivity and may be
reinstated by a maintainer.

**Contributor.** Anyone who opens an issue or PR. Contributors can propose
any change covered by [`CONTRIBUTING.md`](CONTRIBUTING.md). They cannot
self-approve or merge their own PRs. Contributor status is implicit.

**Lean Community Liaison (optional).** A named contact who carries
proof, tactic, or Mathlib questions between Gondlin and the broader Lean
prover community (Zulip, Mathlib, doc-gen4, comparator maintainers). The
liaison has no merge authority by virtue of the role and may serve as an
outside voice in [conflict resolution](#conflict-resolution). Filled by
maintainer consensus; may be left vacant.

## API tiers and change policy

Gondlin distinguishes a frozen public API from internal modules. The
boundary is mechanically enforced by
`python3 scripts/checks/api_surface.py --check` against `api-surface.lock`.

**Tier 1 — frozen API (`NN/API/`).** The public facade imported via
`import NN.API.Public`. Changes that add, remove, or alter signatures here
require:

- two maintainer approvals,
- regeneration of `api-surface.lock` in the same PR,
- a PR title prefixed with `BREAKING:` when an existing declaration changes
  signature, is removed, or changes semantics in a user-visible way,
- a docstring on every new user-facing declaration (see
  `scripts/checks/docstring_coverage.py`).

Purely additive changes still require two approvals and a lock update, but
do not need the `BREAKING:` prefix.

**Tier 2 — experimental.** Modules and CLI surfaces explicitly marked
experimental (for example new verifier subcommands, new examples, and new
runtime knobs that are off by default). A single maintainer approval is
sufficient. The PR description should call out compatibility implications.
Promotion of a Tier 2 surface to Tier 1 is itself a Tier 1 change.

**Internal — `NN/Spec`, `NN/Runtime`, `NN/Proofs`, `NN/IR`, `NN/GraphSpec`,
`NN/Floats`, `NN/MLTheory`, `NN/Verification`, `NN/Examples`, `csrc/`,
`scripts/`.** Standard review: one approval from a maintainer or area
reviewer, all required checks green. Internal refactors that visibly
affect Tier 1 are treated as Tier 1.

## Axiom policy

Gondlin treats Lean axioms as load-bearing trust assumptions, not as
ordinary code. The allowlist lives in `scripts/checks/repo_lint.py` under
`ALLOWED_AXIOMS`, mirrored in [`TRUST_BOUNDARIES.md`](TRUST_BOUNDARIES.md)
and `trust-boundaries.toml`.

Adding a new axiom requires, in the same PR:

1. **Maintainer approval** on the axiom itself, independent of the rest
   of the PR.
2. **Trust-boundary entry** in `TRUST_BOUNDARIES.md` naming the axiom,
   the file it lives in, the assumption it encodes, and why it cannot be
   discharged inside Lean.
3. **Manifest entry** in `trust-boundaries.toml`.
4. **Allowlist update**: the exact axiom name added to `ALLOWED_AXIOMS`
   in `scripts/checks/repo_lint.py`.

CI enforces all four through `scripts/checks/trust_boundaries_check.py`
and `scripts/checks/repo_lint.py`. Removing an axiom follows the inverse
procedure and is encouraged.

## Release train

SemVer applies to the Tier 1 API only. Tier 2, experimental, and
internal modules may change between releases without a major bump.

- **Minor (`v0.x` → `v0.x+1`).** Bimonthly cadence (target: first Monday
  of every other month) when CI is green on `main`. May include additive
  Tier 1 changes and arbitrary internal changes.
- **Patch (`v0.x.y` → `v0.x.y+1`).** Cut immediately when a fix is ready
  for a regression, broken build, security issue, or trust-boundary
  clarification. Must not change the Tier 1 API surface beyond what
  `api-surface.lock` already records.
- **Major.** Reserved for charter-level direction shifts (for example a
  stable `v1.0` Tier 1 freeze). Treated as a charter-level decision under
  [Decision-making](#decision-making).

Release notes name every `BREAKING:` PR, every axiom added or removed,
every toolchain bump, and every trust-boundary change since the prior
release.

## Deprecation policy

User-visible Tier 1 declarations are deprecated with Lean's
`@[deprecated]` attribute before removal. Each deprecation must:

- name a successor declaration or describe the migration path in the
  attribute message,
- remain in the codebase for at least one full minor release after the
  release in which the deprecation first ships,
- continue to compile and pass tests during the retention window.

Removing a deprecated declaration counts as a Tier 1 change and uses the
`BREAKING:` PR title prefix. Tier 2 and experimental declarations may be
removed without a deprecation cycle, but the PR description should call
out the removal.

## Decision-making

Most changes use **lazy consensus**: a PR with the required approvals and
green checks may be merged after a reasonable review window if no
maintainer or area reviewer objects. An unresolved objection from a
maintainer blocks merge.

**Charter-level decisions** require an explicit vote of the maintainer
team recorded on a tracking issue or PR. A simple majority carries; ties
are resolved by a follow-up vote after a 7-day discussion window.
Charter-level decisions include:

- toolchain version bump (`lean-toolchain`, mathlib tag, doc-gen4 tag),
- license change,
- changes to this governance document,
- adding or removing an axiom,
- adding or removing a maintainer,
- declaring a `v1.0` Tier 1 freeze.

## Conflict resolution

Disagreements escalate in order, stopping at the first level that
resolves them:

1. **Contributor and reviewer** discuss on the PR or issue thread.
2. If unresolved, a **maintainer** is pinged to weigh in.
3. If still unresolved, the **maintainer team** decides by the procedure
   above.
4. If the maintainer team cannot reach a decision, an **outside
   arbitrator** is consulted — either the Lean Community Liaison or an
   external project advisor named on the tracking issue. The role is
   advisory; the final decision still rests with the maintainer team, but
   the reasoning is recorded.

Conduct issues follow the same path and may be raised privately to any
maintainer.

## Maintainer additions and removal

The current maintainer team is:

- `<TBD>` (lead maintainer)
- `<TBD>`
- `<TBD>`

Adding a maintainer is a charter-level decision. Any maintainer may
nominate a contributor or reviewer with a sustained record across more
than one subtree. The nomination is opened as a tracking issue,
discussed for at least 7 days, and decided by maintainer vote.

Removing a maintainer is also charter-level and may be triggered by:

- the maintainer's own resignation (effective immediately on request),
- twelve months of inactivity (no merged PRs, reviews, or releases),
- a request by another maintainer for cause, decided by vote of the
  remaining maintainers; the maintainer under discussion does not vote.

Emeritus status is available to former maintainers and carries no merge authority.

## AI assistance disclosure

Per [`AI_USAGE.md`](AI_USAGE.md), Gondlin treats AI assistance as a
limited support tool, not a source of truth. PRs that used AI assistance
for proof drafting, code generation, refactoring, debugging, or
documentation should say so in the PR description, naming the tool and
where it was used. The author remains responsible for every line they
submit; AI-assisted PRs are reviewed against the same standards as any
other PR. Project-wide AI policy changes follow [Amendments](#amendments).

## Amendments

This document is amended by PR. Non-trivial amendments — anything beyond
typo fixes, link repair, or rewording that does not change policy —
require:

- at least two maintainer approvals,
- a 7-day comment window after the PR is opened, during which any
  maintainer may request further discussion,
- a tracking issue when the diff alone does not convey the intent.

Trivial amendments use the standard internal review rule. Until adopted
by explicit maintainer vote, the DRAFT banner remains in place and
nothing here is authoritative policy.
