#!/usr/bin/env python3
"""Validate markdown links across Gondolin documentation.

Two link kinds are recognised:

1. Relative links (no URL scheme and not starting with ``#``):
   resolve relative to the containing file. The target must exist on disk;
   if it points to a directory, the directory must exist. Trailing slashes
   are tolerated. An anchor suffix (``#foo``) is emitted as a *warning*
   rather than an error -- verifying anchors needs a real markdown parser
   and is out of scope here.

2. HTTP(S) links: by default we only count them and print summary stats.
   With ``--fetch`` we issue best-effort ``urllib.request`` HEAD/GET probes
   (5 second timeout) and report any 4xx/5xx as broken.

Templated Jekyll links inside ``home_page/`` (``{% link foo.md %}`` and
``{{ site.baseurl }}/...``) are annotated as ``templated`` and skipped.

Stdlib only.

Examples
--------
    $ python3 scripts/checks/docs_link_check.py
    $ python3 scripts/checks/docs_link_check.py --fetch
    $ python3 scripts/checks/docs_link_check.py --strict-anchors --json
    $ python3 scripts/checks/docs_link_check.py --paths 'NN/**/*.md'
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------

# scripts/checks/docs_link_check.py  ->  repo root is two parents up.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Explicit list of top-level markdown files we always want to check.
EXPLICIT_FILES: list[str] = [
    "README.md",
    "CONTRIBUTING.md",
    "TRUST_BOUNDARIES.md",
    "AI_USAGE.md",
    "THIRD_PARTY_NOTICES.md",
    "NN/Examples/README.md",
    "NN/MLTheory/README.md",
    "NN/Verification/README.md",
]

# Directories that are globbed for *.md.
GLOB_DIRS: list[str] = [
    "home_page",
    "docs-site",
]

# Subdirectory names anywhere in the path that we always skip.
SKIP_DIR_NAMES: set[str] = {
    "node_modules",
    ".git",
    ".lake",
    ".wrangler",
    "dist",
    "build",
    ".next",
    ".astro",
    ".vercel",
}

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

# Inline markdown link: [text](target "optional title")
INLINE_LINK_RE = re.compile(
    r"""
    \[ (?P<text> [^\]]* ) \]   # [text]
    \(                          # (
        \s*
        (?P<target> [^)\s]+ )   #   target (no whitespace, no closing paren)
        (?: \s+ "[^"]*" )?      #   optional "title"
        \s*
    \)                          # )
    """,
    re.VERBOSE,
)

# Reference-style link declaration:   [label]: target "title"
REF_DEF_RE = re.compile(
    r"""^\s*\[ (?P<label> [^\]]+ ) \] :  \s*
        (?P<target> \S+ )
        (?: \s+ "[^"]*" )? \s*$""",
    re.VERBOSE,
)

# Reference-style link usage: [text][label] or [label][]
REF_USE_RE = re.compile(r"\[(?P<text>[^\]]+)\]\[(?P<label>[^\]]*)\]")

# Templated Jekyll-style link payloads we ignore.
JEKYLL_TEMPLATED_RE = re.compile(r"\{\{[^}]*\}\}|\{%[^%]*%\}")

URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+\-.]*:")
TRIPLE_BACKTICK_RE = re.compile(r"^\s*```")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class LinkRecord:
    file: str
    line: int
    text: str
    target: str
    kind: str          # "relative" | "http" | "templated" | "anchor" | "ref-missing"
    status: str        # "ok" | "broken" | "warning" | "skipped"
    detail: str = ""


@dataclass
class Report:
    files_scanned: int = 0
    links_total: int = 0
    by_kind: dict[str, int] = field(default_factory=dict)
    records: list[LinkRecord] = field(default_factory=list)

    def add(self, rec: LinkRecord) -> None:
        self.records.append(rec)
        self.links_total += 1
        self.by_kind[rec.kind] = self.by_kind.get(rec.kind, 0) + 1

    @property
    def broken(self) -> list[LinkRecord]:
        return [r for r in self.records if r.status == "broken"]

    @property
    def warnings(self) -> list[LinkRecord]:
        return [r for r in self.records if r.status == "warning"]


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def _path_is_skipped(p: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in p.parts)


def discover_files(restrict_globs: list[str] | None) -> list[Path]:
    """Return the de-duplicated list of markdown files to scan."""
    found: list[Path] = []

    if restrict_globs:
        # Walk the repo and match against each glob.
        all_md = []
        for root, dirs, files in os.walk(REPO_ROOT):
            # In-place prune skip dirs for speed.
            dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]
            for name in files:
                if name.endswith(".md"):
                    all_md.append(Path(root) / name)
        for md in all_md:
            rel = md.relative_to(REPO_ROOT).as_posix()
            if any(fnmatch.fnmatch(rel, g) for g in restrict_globs):
                found.append(md)
    else:
        # Explicit files.
        for rel in EXPLICIT_FILES:
            p = REPO_ROOT / rel
            if p.is_file():
                found.append(p)
        # Globbed directories.
        for d in GLOB_DIRS:
            base = REPO_ROOT / d
            if not base.is_dir():
                continue
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]
                for name in files:
                    if name.endswith(".md"):
                        p = Path(root) / name
                        if not _path_is_skipped(p):
                            found.append(p)

    # De-duplicate while preserving order.
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in found:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


# ---------------------------------------------------------------------------
# Link extraction
# ---------------------------------------------------------------------------


def _strip_inline_code(line: str) -> str:
    """Replace inline-code spans with spaces so links inside are skipped."""
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def extract_links(text: str) -> tuple[list[tuple[int, str, str]], dict[str, str]]:
    """Return (inline_links, reference_definitions).

    inline_links is a list of (line_number, text, target).
    reference_definitions maps lowercased label -> target.
    """
    inline: list[tuple[int, str, str]] = []
    refs: dict[str, str] = {}
    in_fence = False
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if TRIPLE_BACKTICK_RE.match(raw_line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = _strip_inline_code(raw_line)

        # Reference-style definition lines.
        m = REF_DEF_RE.match(line)
        if m:
            refs[m.group("label").strip().lower()] = m.group("target").strip()
            continue

        # Inline links.
        for mm in INLINE_LINK_RE.finditer(line):
            inline.append((lineno, mm.group("text"), mm.group("target").strip()))

        # Reference-style usages -- record the (text, label) pairs as inline
        # links once we know the ref table. We do that after the loop, so
        # stash them on `refs` temporarily by re-walking below.

    # Second pass: resolve reference-style usages using refs table.
    ref_uses: list[tuple[int, str, str]] = []
    in_fence = False
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if TRIPLE_BACKTICK_RE.match(raw_line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = _strip_inline_code(raw_line)
        # Skip definition lines.
        if REF_DEF_RE.match(line):
            continue
        for mm in REF_USE_RE.finditer(line):
            label = (mm.group("label") or mm.group("text")).strip().lower()
            target = refs.get(label, "")
            ref_uses.append((lineno, mm.group("text"), target or f"[unresolved:{label}]"))

    return inline + ref_uses, refs


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def classify(target: str) -> str:
    if not target:
        return "ref-missing"
    if target.startswith("[unresolved:"):
        return "ref-missing"
    if JEKYLL_TEMPLATED_RE.search(target):
        return "templated"
    if target.startswith("#"):
        return "anchor"
    if URL_SCHEME_RE.match(target):
        scheme = target.split(":", 1)[0].lower()
        if scheme in ("http", "https"):
            return "http"
        return "scheme-other"
    return "relative"


def validate_relative(target: str, source: Path) -> tuple[str, str]:
    """Return (status, detail). status in {ok, broken, warning}."""
    # Split off anchor.
    anchor = ""
    bare = target
    if "#" in bare:
        bare, anchor = bare.split("#", 1)
    # Strip trailing slash for filesystem lookup, but keep info for dir check.
    looks_like_dir = bare.endswith("/")
    bare = bare.rstrip("/")

    if bare == "":
        # Pure anchor like "#foo" (shouldn't reach here -- classify handles it).
        return ("warning", f"anchor-only: #{anchor}")

    resolved = (source.parent / bare).resolve()
    if resolved.exists():
        if looks_like_dir and not resolved.is_dir():
            return ("broken", f"expected dir, found file: {resolved}")
        if anchor:
            return ("warning", f"target ok; anchor '#{anchor}' not verified")
        return ("ok", "")
    return ("broken", f"missing: {resolved}")


def validate_http(target: str, timeout: float) -> tuple[str, str]:
    req = urllib.request.Request(target, method="HEAD",
                                 headers={"User-Agent": "gondolin-docs-link-check/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            code = resp.status
    except urllib.error.HTTPError as e:
        # Some servers reject HEAD; retry with GET before declaring broken.
        if e.code in (403, 405, 501):
            try:
                req2 = urllib.request.Request(
                    target, method="GET",
                    headers={"User-Agent": "gondolin-docs-link-check/1.0"})
                with urllib.request.urlopen(req2, timeout=timeout) as resp:  # noqa: S310
                    code = resp.status
            except Exception as e2:  # noqa: BLE001
                return ("broken", f"http error on GET retry: {e2}")
        else:
            return ("broken", f"http {e.code}")
    except Exception as e:  # noqa: BLE001 -- urllib raises many flavors
        return ("broken", f"http error: {e}")
    if 400 <= code < 600:
        return ("broken", f"http {code}")
    return ("ok", f"http {code}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run(args: argparse.Namespace) -> Report:
    report = Report()
    files = discover_files(args.paths)
    report.files_scanned = len(files)

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            report.add(LinkRecord(
                file=str(f.relative_to(REPO_ROOT)),
                line=0, text="", target="",
                kind="relative", status="broken",
                detail=f"could not read: {e}",
            ))
            continue

        links, _refs = extract_links(text)
        rel_file = str(f.relative_to(REPO_ROOT))
        for lineno, txt, target in links:
            kind = classify(target)
            rec = LinkRecord(
                file=rel_file, line=lineno, text=txt, target=target,
                kind=kind, status="ok",
            )
            if kind == "templated":
                rec.status = "skipped"
                rec.detail = "Jekyll template"
            elif kind == "anchor":
                rec.status = "warning"
                rec.detail = "in-page anchor not verified"
            elif kind == "ref-missing":
                rec.status = "broken"
                rec.detail = "unresolved reference label"
            elif kind == "scheme-other":
                rec.status = "skipped"
                rec.detail = "non-http scheme"
            elif kind == "relative":
                status, detail = validate_relative(target, f)
                rec.status = status
                rec.detail = detail
            elif kind == "http":
                if args.fetch:
                    status, detail = validate_http(target, args.timeout)
                    rec.status = status
                    rec.detail = detail
                else:
                    rec.status = "skipped"
                    rec.detail = "http (use --fetch to verify)"
            report.add(rec)
    return report


def format_table(report: Report) -> str:
    out: list[str] = []
    out.append(f"Scanned {report.files_scanned} markdown file(s); "
               f"{report.links_total} link(s) total.")
    out.append("Counts by kind: " +
               ", ".join(f"{k}={v}" for k, v in sorted(report.by_kind.items())))

    if report.broken:
        out.append("")
        out.append(f"BROKEN ({len(report.broken)}):")
        for r in report.broken:
            out.append(f"  {r.file}:{r.line}  [{r.kind}]  -> {r.target}")
            if r.detail:
                out.append(f"      {r.detail}")
    else:
        out.append("")
        out.append("No broken links.")

    if report.warnings:
        out.append("")
        out.append(f"WARNINGS ({len(report.warnings)}):")
        for r in report.warnings[:40]:
            out.append(f"  {r.file}:{r.line}  [{r.kind}]  -> {r.target}  ({r.detail})")
        if len(report.warnings) > 40:
            out.append(f"  ... and {len(report.warnings) - 40} more")

    return "\n".join(out)


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check markdown links in Gondolin docs.")
    p.add_argument("--fetch", action="store_true",
                   help="actually fetch http(s) URLs and verify status codes")
    p.add_argument("--strict-anchors", action="store_true",
                   help="treat anchor warnings as failures")
    p.add_argument("--paths", action="append", default=None,
                   metavar="GLOB",
                   help="restrict to files matching this glob "
                        "(repeatable, relative to repo root)")
    p.add_argument("--json", action="store_true",
                   help="emit machine-readable JSON instead of a table")
    p.add_argument("--timeout", type=float, default=5.0,
                   help="HTTP timeout in seconds (default 5)")
    args = p.parse_args(argv)

    report = run(args)

    if args.json:
        payload = {
            "files_scanned": report.files_scanned,
            "links_total": report.links_total,
            "by_kind": report.by_kind,
            "broken": [asdict(r) for r in report.broken],
            "warnings": [asdict(r) for r in report.warnings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_table(report))

    rc = 0
    if report.broken:
        rc = 1
    if args.strict_anchors and report.warnings:
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
