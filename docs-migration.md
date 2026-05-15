# Gondlin Documentation Migration

## Goal

Gondlin's documentation is currently split across four independent surfaces, each
with its own toolchain, audience, and deployment story. This file is the single
place that says where each kind of content belongs, how the surfaces link to each
other, and what the consolidation plan looks like. If you are adding a tutorial,
a marketing blurb, a proof sketch, an API note, or a governance policy and you
are not sure which tree it belongs in, read the decision rules below before
writing.

## The Four Surfaces

| Surface | Technology | Primary audience | Build command | Hosted URL |
|---|---|---|---|---|
| `home_page/` | Jekyll | Drive-by visitors, press, prospective users | `cd home_page && bundle exec jekyll serve` | `https://nktkt.github.io/gondlin/` (planned, GitHub Pages) |
| `docs-site/` | Next.js 16 (static export) | End users reading tutorials and interactive docs | `cd docs-site && bun run build` | `https://torchlean.org` |
| `blueprint/GondlinBlueprint/Guide/` | Verso-Blueprint | Researchers reading the formal exposition of the proof effort | `cd blueprint && lake build blueprint-gen` | Local-only; published under `/blueprint/` on the Pages site when enabled |
| `.lake/build/doc/` | doc-gen4 | Lean developers needing per-declaration API reference | `DISABLE_EQUATIONS=1 lake build NN:docs` | Local-only; published under `/docs/` on the Pages site when enabled |

## Decision Rules

Pick the surface that matches the *purpose* of the content, not the file format
you are most comfortable with.

- End-user marketing, project landing, "what is Gondlin" → `home_page/`.
  Anything a non-user needs to see before deciding to install lives here. Keep
  it light; do not put walkthroughs here.
- End-user docs, tutorials, runnable examples, interactive content →
  `docs-site/` (`content/` subtree, MDX). This is the long-term home for
  everything a user reads after they have decided to try Gondlin: installation,
  guides, recipes, architecture overviews, governance pages, examples.
- Long-form formal exposition, blueprint of proofs, chapter-style mathematical
  narrative → `blueprint/GondlinBlueprint/Guide/`. Use this when the content is
  primarily structured around theorems, definitions, and their dependencies and
  benefits from Verso's cross-references back into Lean.
- API reference auto-generated from Lean docstrings → doc-gen4. Do not hand-write
  API reference pages elsewhere; instead improve `/-- ... -/` docstrings on the
  declaration and rebuild.
- Trust, governance, release policy, contribution rules, third-party notices,
  AI usage disclosure → top-level `*.md` in the repo root (`TRUST_BOUNDARIES.md`,
  `CONTRIBUTING.md`, `AI_USAGE.md`, `THIRD_PARTY_NOTICES.md`, `ROADMAP.md`,
  `CITATION.cff`). These are the source of truth and should be linked from
  `docs-site/` rather than duplicated.

## Cross-linking Convention

Each surface owns its content and links outward when it needs material from
another surface. None of them re-host another surface's text.

- `home_page/` links to `docs-site/` for any "learn more" call-to-action and to
  the Pages-hosted `/docs/` and `/blueprint/` directories for API and blueprint
  entry points.
- `docs-site/` (torchlean.org) is the canonical entry point for end-user
  documentation. Its `/api` route points at the doc-gen4 output (currently the
  Pages `/docs/` URL once enabled; in development, the local `.lake/build/doc/`
  tree). Its governance and trust pages link back to the root `*.md` files via
  GitHub permalinks so the rendered prose tracks the repository commit.
- `blueprint/` cross-references into Lean declarations through Verso; outbound
  HTML links from the rendered guide should point at doc-gen4 declaration URLs,
  not at rewritten copies inside `docs-site/`.
- doc-gen4 output does not link out by hand; rely on module-doc `/-! ... -/`
  blocks and `@[deprecated]` notes for any inline pointers.
- The repo root `README.md` links to all four surfaces and is the only place
  that needs to enumerate every URL; other documents should reach the surfaces
  through the README or through `docs-site/`.

## Migration Plan

Today both `home_page/` and `docs-site/` carry end-user content. Specifically,
`home_page/` still hosts `manual.md`, `start/`, `verify/`, `cuda/`, and an
`examples/` walkthrough, while `docs-site/content/` covers the same ground in
`guide/`, `examples/`, `runtime/`, `architecture/`, `floats/`, `ir/`,
`verification/`, and `governance/`. The intended end state is:

1. `docs-site/` becomes the only home for user-facing prose and tutorials.
   Anything substantive in `home_page/manual.md`, `home_page/start/`,
   `home_page/verify/`, `home_page/cuda/`, and `home_page/examples/` should be
   ported into the matching `docs-site/content/` subtree, with the original
   pages reduced to redirects pointing at `https://torchlean.org/...`.
2. `home_page/` retains only what is genuinely landing-page material: the index,
   the brand assets under `assets/media/brand/`, and the proxy directories
   (`docs/`, `blueprint/`, `graphs/`, `importgraph/`) populated by CI from the
   doc-gen4 and Verso builds.
3. The doc-gen4 and Verso outputs continue to be staged into `home_page/docs/`
   and `home_page/blueprint/` for the Pages publish, until the Pages site is
   either retired in favor of `torchlean.org/api` and `torchlean.org/blueprint`
   or formally adopted as the long-term host for those two surfaces.
4. Governance and trust files stay at the repo root; `docs-site/content/governance/`
   should pull from those files at build time rather than maintain a parallel
   copy.

Order of operations matters: port content into `docs-site/` first, verify the
torchlean.org build, add redirects on the Jekyll side, and only then delete the
original Markdown. Do not drop content from `home_page/` before the equivalent
page exists and is reachable on `torchlean.org`.

## Open Questions

- Should the Jekyll site be retired entirely once `docs-site/` reaches parity,
  or kept as a lightweight landing page that defers everything else to
  `torchlean.org`?
- Where does the changelog live? Repo-root `CHANGELOG.md`, a `docs-site/`
  release-notes section, or GitHub Releases as the source of truth with the
  others linking to it?
- Does the doc-gen4 output get its own subdomain (`api.torchlean.org`) once the
  Pages URL is no longer the primary host, or stay nested under
  `torchlean.org/api`?
- Should `blueprint/` ship a published HTML build on every tagged release, or
  only on `main`? This affects whether end-user links to the guide should be
  versioned.
- Who owns the cross-surface link audit? `scripts/checks/docs_link_check.py`
  covers in-repo Markdown; there is no equivalent that walks the rendered HTML
  on `torchlean.org` and the Pages site for dead cross-surface links.
