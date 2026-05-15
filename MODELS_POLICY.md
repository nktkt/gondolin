# Models Policy — Neural-Network Weight Redistribution and Artifact Ethics

> ⚠️ DRAFT — This is a proposed policy. Maintainers may adopt, revise, or
> reject it. Until merged with an explicit policy decision, projects shipping
> weights should err on the side of caution.

## Why This Exists

Gondlin can import and export PyTorch weights (see
[`NN/Examples/README.md`](NN/Examples/README.md), `Interop/PyTorch/Roundtrip.lean`)
and ships fixtures that demonstrate verified properties of trained models. Any
shipped weight is more than a binary blob: pre-trained parameters can (a) encode
unintended intellectual property from training data, (b) memorize personally
identifiable information present in the corpus, (c) embed biases that become
harmful when used in downstream deployment contexts, and (d) violate the
license terms of upstream models from which they are derived. Even tiny example
weights deserve the same provenance and licensing attention as code, because
their distribution carries the same legal and ethical weight as the underlying
training set.

## Categories of Weights

The following categories define how a weight artifact may be produced, stored,
and shipped. Every weight tracked by this project must be assigned to exactly
one category in its accompanying metadata.

- **Toy** — Randomly initialized parameters with no real training, or training
  on trivially synthetic data generated inside this repository. Toy weights
  carry no IP risk from upstream sources and may be shipped inline in the
  repository, embedded in source files, or generated at build time.
- **Reference** — Trained on a well-known public dataset with a permissive,
  redistribution-compatible license (MNIST, CIFAR-10, Tiny Shakespeare,
  scikit-learn `load_digits`, and similar). Reference weights may be shipped
  as repository fixtures when accompanied by complete provenance metadata
  (see "Training Data Provenance").
- **Derived** — Fine-tuned, distilled, pruned, quantized, or otherwise produced
  from an upstream pre-trained model (for example ResNet, BERT, GPT-2,
  Llama, Mistral). Derived weights inherit upstream license terms and may not
  be shipped inside this repository unless the upstream license unambiguously
  permits redistribution and every transitive dependency is documented.
- **External** — Third-party weights that Gondlin examples reference, load, or
  import from a remote source but never redistribute. The reference is to the
  upstream artifact; the user fetches it themselves.

## What We Ship

The `NN/Examples/` directory is restricted to weights in the **Toy** and
**Reference** categories. Derived weights live outside this repository in a
separate release channel (working name: `gondlin-weights`) with its own
LICENSE, NOTICE, and per-artifact provenance file. External weights are
referenced only by URL and checksum, never copied into the tree.

Bundled fixtures already documented in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) (the "Bundled Demo
Fixtures" section) are the canonical list of acceptable in-repo artifacts.
Any new in-repo weight must be added to that table at the same time it is
added to the source tree.

## License Inheritance

Weights derived from a licensed upstream model inherit the upstream
restrictions in addition to Gondlin's MIT license on the surrounding code.
A few illustrative cases:

- ResNet-50 reference checkpoints are typically released under Apache-2.0;
  redistribution requires preserving the NOTICE file and attribution.
- GPT-2 code is MIT-licensed, but the trained GPT-2 weights distributed by
  OpenAI are subject to OpenAI's separate model terms; the Gondlin GPT-2
  tokenizer reference in `THIRD_PARTY_NOTICES.md` does not authorize
  redistributing GPT-2 weights themselves.
- Llama, Mistral, and similar community models ship under bespoke licenses
  with usage restrictions (acceptable use policies, named-entity carve-outs,
  commercial-use thresholds). Treat these as Derived and host externally.

The Gondlin Software Bill of Materials must list weight provenance with the
same rigor as source-code dependencies. A weight is a dependency.

## Training Data Provenance

Every **Reference**-tier weight shipped in this repository must document, in
a sibling `.provenance.json` file next to the weight artifact:

- `dataset_name` — Canonical dataset name (for example `CIFAR-10`).
- `dataset_license` — SPDX identifier or short license name and URL.
- `train_script` — Repository-relative path to the script that produced the
  weight, including any CLI flags required to reproduce it.
- `commit` — Git commit SHA of the `train_script` at the time the weight was
  produced, plus the Gondlin version (`lean-toolchain` pin and Lake manifest
  revision) it was built against.
- `random_seed` — Seed and any non-determinism notes required for byte-exact
  or numerically-close reproduction.

Reference weights without complete provenance must not be merged.

## PII and Memorization

For any weight trained on data that could plausibly contain personally
identifiable information, the provenance file must additionally describe
the filter applied to the training corpus (deduplication, PII scrubbing,
named-entity removal, source-allowlist, or "none — corpus is curated and
public"). When in doubt, prefer well-curated public datasets with documented
collection methodology over scraped or user-generated content. Weights
trained on uncurated web-scale corpora are **Derived** at minimum and
require explicit maintainer review before being referenced from any
shipped example.

## Bias and Fairness

Weights shipped to demonstrate "interesting" classification, generation, or
decision behavior must surface known biases in their accompanying README or
provenance notes. When an example deliberately shows a misclassification,
an adversarial example, a stereotype, or any other failure mode, the
surrounding documentation must state explicitly that the output is
educational and is not endorsed behavior. The `BugZoo/` directory model
(checked versions of common ML failure modes) is the right template:
failure-mode examples are first-class, but the failure must be named.

Verification fixtures that establish robustness, monotonicity, or fairness
properties should state precisely which property is verified and which are
not, so that a passing `lake exe verify` run is not mistaken for a general
endorsement.

## Deprecation

When a previously-shipped weight is found to be problematic (license issue,
PII leak, harmful bias, upstream takedown), it must be removable without
breaking the historical provenance trail. The mechanism:

- A top-level `weights-revoked.json` file lists withdrawn artifacts by
  SHA-256 hash, withdrawal date, withdrawal reason category, and a short
  human-readable note.
- The offending file is removed from the working tree in the same change.
- Examples and tests that referenced the artifact are updated to use a
  replacement Toy or Reference weight, or are removed.
- CI gates on `weights-revoked.json`: any shipped weight whose hash appears
  in the revoked list fails the build.

Historical git history is not rewritten; the deprecation record is the
public statement.

## Verification-Targeted Weights

When weights are shipped as fixtures for `lake exe verify` (for example
under `NN/Examples/Verification/`), the fixture is part of the verification
claim, not an endorsement of the model. A robustness certificate for a
specific small classifier proves a property of that exact parameter set; it
does not claim the model is useful, fair, accurate, or fit for any
deployment. Verification fixtures must:

- Be the minimum size needed to exhibit the property under test.
- Carry a `verification_claim` field in their provenance file naming the
  exact theorem, certificate, or checker output they support.
- Be flagged explicitly as fixtures in the surrounding example so a reader
  cannot mistake the verified property for a generalized guarantee.

## Open Questions

Items the maintainer must decide before this document moves out of DRAFT:

- Should the `gondlin-weights` external release channel be a separate Git
  repository, a GitHub Release attached to the main repo, or a Hugging Face
  organization? <TBD>
- What is the exact CI mechanism that enforces the in-repo Toy/Reference
  restriction (file-size gate, extension allowlist, manifest match)? <TBD>
- Does the provenance format reuse an existing standard (Model Cards,
  Croissant, MLflow) or stay project-specific JSON? <TBD>
- Who is the designated reviewer for weight additions, and is a second
  reviewer required when the category is Derived? <TBD>
- What is the disclosure timeline once a revocation-worthy issue is
  reported (private window before public revocation entry)? <TBD>
