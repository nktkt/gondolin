#!/usr/bin/env python3
"""
Gondlin docstring coverage check for the Tier 1 / Tier 2 public API.

Phase 0.2 of the roadmap targets >=80% docstring coverage on the public surface exposed by
`NN/API/Public.lean` and `NN/Library`. This script scans `.lean` files under `NN/API/` (configurable
via `--root`), enumerates the same set of visible declarations that `scripts/checks/api_surface.py`
treats as Tier 1 (`def`, `theorem`, `abbrev`, `class`, `structure`, `inductive`), and reports the
fraction that carry a Lean docstring (`/-- ... -/`) immediately above them.

A "docstring is present" means:
  - The non-blank source line(s) immediately above the declaration's first modifier line form a
    Lean block-doc-comment `/-- ... -/`.
  - Intervening attribute lines (`@[...]`) and `private`/`public`/`noncomputable`/`partial`-style
    modifier lines between the docstring and the keyword are tolerated; we walk upward through
    them and only the first non-modifier line above is checked.
  - `private` declarations are excluded from both the numerator and the denominator (matching
    `api_surface.py`'s visibility rules; the API surface is the only thing we promise to document).

Outputs:
  - Default: a human-readable table grouped by top-level module (e.g. `NN.API.Tensor`,
    `NN.API.Models`, ...), plus an overall summary line.
  - `--json`: machine-readable per-module and overall payload.
  - `--list-missing`: print fully qualified names of undocumented declarations, sorted.
  - `--min-coverage N`: exit nonzero if overall coverage < N percent (integer 0..100).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_ROOT = REPO_ROOT / "NN" / "API"

# Declaration kinds (same set as `api_surface.py`).
DECL_KINDS = ("abbrev", "class", "def", "inductive", "structure", "theorem")

# Modifiers that may precede the declaration keyword (same as `api_surface.py`).
DECL_MODIFIERS = (
    "noncomputable",
    "partial",
    "unsafe",
    "scoped",
    "local",
    "protected",
    "nonrec",
)

# Visibility tokens that may precede the declaration keyword. `public` keeps the decl in the
# surface even if the file has no `public section`.
VISIBILITY_TOKENS = ("public",)

# Tokens that are tolerated on lines between the docstring and the declaration keyword when we
# walk upward looking for the docstring. Anything not in this set (or `@[...]`) terminates the
# walk.
MODIFIER_TOKENS = set(DECL_MODIFIERS) | set(VISIBILITY_TOKENS) | {"private"}


NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z0-9_'.]+)\s*$")
END_RE = re.compile(r"^\s*end\s+([A-Za-z0-9_'.]+)\s*$")
END_SECTION_RE = re.compile(r"^\s*end\s*(?:--.*)?$")
FILE_PUBLIC_SECTION_RE = re.compile(r"@\[\s*expose\s*\]\s*public\s+section\b")
TOP_LEVEL_PUBLIC_SECTION_RE = re.compile(r"^\s*public\s+section\b")
ATTRIBUTE_LINE_RE = re.compile(r"^\s*@\[[^\]]*\]\s*$")


@dataclass(frozen=True, order=True)
class DocFinding:
    """One scanned declaration plus whether it carries an immediately-preceding docstring."""

    kind: str
    name: str  # fully qualified, including namespaces
    module: str  # dotted Lean module path
    path: str  # repo-relative source path
    line: int  # 1-based line number of the keyword
    has_docstring: bool


# ---------------------------------------------------------------------------
# Comment / string masking (copied from `api_surface.py` to keep this script
# stdlib-only and avoid cross-module imports between sibling lint scripts).
# ---------------------------------------------------------------------------


def _mask_comments_and_strings(text: str) -> str:
    """Replace Lean comments/docstrings/strings with spaces, preserving newlines."""
    out = list(text)
    n = len(text)
    i = 0
    block_depth = 0
    in_line_comment = False
    in_string = False

    while i < n:
        ch = text[i]

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            else:
                out[i] = " "
            i += 1
            continue

        if block_depth > 0:
            if text.startswith("/-", i):
                out[i] = " "
                if i + 1 < n:
                    out[i + 1] = " "
                block_depth += 1
                i += 2
                continue
            if text.startswith("-/", i):
                out[i] = " "
                if i + 1 < n:
                    out[i + 1] = " "
                block_depth -= 1
                i += 2
                continue
            if ch != "\n":
                out[i] = " "
            i += 1
            continue

        if in_string:
            if ch == "\n":
                in_string = False
                i += 1
                continue
            out[i] = " "
            if ch == "\\" and i + 1 < n:
                if text[i + 1] != "\n":
                    out[i + 1] = " "
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue

        if text.startswith("--", i):
            out[i] = " "
            if i + 1 < n:
                out[i + 1] = " "
            in_line_comment = True
            i += 2
            continue
        if text.startswith("/-", i):
            out[i] = " "
            if i + 1 < n:
                out[i + 1] = " "
            block_depth = 1
            i += 2
            continue
        if ch == '"':
            out[i] = " "
            in_string = True
            i += 1
            continue

        i += 1

    return "".join(out)


# ---------------------------------------------------------------------------
# Module-path helpers
# ---------------------------------------------------------------------------


def _module_of_path(path: pathlib.Path) -> str:
    """Convert a Lean source path under the repo root into a dotted Lean module name."""
    return ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)


def _top_level_module(module: str, scan_root: pathlib.Path) -> str:
    """Group declarations by their first segment under the scan root.

    For example, with scan root `NN/API`:
      - `NN.API.Tensor.Float` -> `NN.API.Tensor`
      - `NN.API.Common`       -> `NN.API.Common`
      - `NN.API.Models.MLP`   -> `NN.API.Models`
    """
    # Convert the scan root to a dotted prefix (e.g. `NN.API.`).
    root_parts = scan_root.relative_to(REPO_ROOT).parts
    prefix_dots = ".".join(root_parts)
    if not module.startswith(prefix_dots):
        # Files outside the prefix fall back to their own module name.
        return module
    tail = module[len(prefix_dots):].lstrip(".")
    if not tail:
        return module
    first = tail.split(".", 1)[0]
    return f"{prefix_dots}.{first}"


# ---------------------------------------------------------------------------
# Declaration scanning (mirrors `api_surface._scan_file`, plus docstring lookup)
# ---------------------------------------------------------------------------


def _is_internal_file(text: str) -> bool:
    """Return True when the file opts out via `-- @internal` on the first non-blank line."""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        return line.startswith("--") and "@internal" in line
    return False


def _file_has_expose_public_section(text: str) -> bool:
    """Detect the `@[expose] public section` pattern Gondlin uses for facade files."""
    return bool(FILE_PUBLIC_SECTION_RE.search(text))


def _strip_modifiers(prefix: str) -> tuple[bool, bool]:
    """Return `(is_private, is_explicit_public)` from the pre-keyword prefix."""
    tokens = prefix.split()
    is_private = False
    is_explicit_public = False
    for tok in tokens:
        if tok == "private":
            is_private = True
        elif tok in VISIBILITY_TOKENS:
            is_explicit_public = True
    return is_private, is_explicit_public


_DECL_LINE_RE = re.compile(
    r"^(?P<prefix>(?:\s*(?:@\[[^\]]*\]|"
    + r"|".join(DECL_MODIFIERS + VISIBILITY_TOKENS + ("private",))
    + r")\s+)*)"
    r"(?P<kind>"
    + r"|".join(DECL_KINDS)
    + r")\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_'\.]*)"
)


def _line_is_modifier_only(raw_line: str) -> bool:
    """Return True when a raw source line consists only of attribute(s) / declaration modifiers.

    Used while walking upward from a declaration keyword looking for the docstring: attribute lines
    like `@[simp, inline]` and bare modifier lines like `public` or `noncomputable` are tolerated
    between the docstring and the keyword.
    """
    stripped = raw_line.strip()
    if not stripped:
        return False
    if ATTRIBUTE_LINE_RE.match(raw_line):
        return True
    # Allow lines that are purely a sequence of recognized modifier tokens (rare in practice but
    # cheap to support — e.g. someone splits `noncomputable\ndef foo` across two lines).
    tokens = stripped.split()
    return bool(tokens) and all(tok in MODIFIER_TOKENS for tok in tokens)


def _has_preceding_docstring(raw_lines: list[str], decl_idx: int) -> bool:
    """Return True when a `/-- ... -/` block-doc-comment immediately precedes `decl_idx`.

    `decl_idx` is the 0-based index of the line containing the declaration keyword (after any
    leading attribute/modifier lines have already been collapsed onto the keyword line by the
    regex). We walk upward, skipping:
      - blank lines (a docstring may be separated from the keyword by blank lines? In Lean it
        must be immediately adjacent for `Lean.findDocString?` to pick it up — so we stop at the
        first blank line found between a candidate docstring and the keyword).
      - attribute-only lines and bare-modifier-only lines (these legitimately sit between a
        docstring and the keyword in Gondlin sources).

    The first non-modifier line we hit must end with `-/` and (after collecting upward) the
    matching opener must be `/--`.
    """
    j = decl_idx - 1
    # Step over attribute-only lines and modifier-only lines that may sit between docstring and
    # keyword. Blank lines between docstring and keyword are NOT tolerated (Lean's elaborator
    # would not attach the docstring in that case either).
    while j >= 0 and _line_is_modifier_only(raw_lines[j]):
        j -= 1
    if j < 0:
        return False

    # The immediately-preceding line must close a docstring block.
    line = raw_lines[j].rstrip()
    if not line.endswith("-/"):
        return False

    # Single-line `/-- ... -/` case.
    stripped = line.lstrip()
    if stripped.startswith("/--") and stripped.endswith("-/") and len(stripped) >= 5:
        return True

    # Multi-line case: walk upward until we find the opener. The opener must be `/--`
    # (three-character docstring marker, not a regular `/-` block comment).
    k = j - 1
    while k >= 0:
        opener = raw_lines[k].lstrip()
        # If we see a `/--` opener, success — even if other `/-` openers appeared between.
        # (Nested block comments inside a docstring are rare but possible.)
        if opener.startswith("/--"):
            return True
        # A regular `/-` (not `/--`) means the closing `-/` we saw belonged to a non-doc block
        # comment, so this declaration is undocumented.
        if opener.startswith("/-") and not opener.startswith("/--"):
            return False
        k -= 1
    return False


def _scan_file(path: pathlib.Path) -> list[DocFinding]:
    """Scan one Lean file and return docstring findings for visible declarations."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    if _is_internal_file(text):
        return []

    masked = _mask_comments_and_strings(text)
    masked_lines = masked.splitlines()
    raw_lines = text.splitlines()
    module = _module_of_path(path)
    rel = path.relative_to(REPO_ROOT).as_posix()

    file_default_public = _file_has_expose_public_section(text)
    section_stack: list[bool] = []
    namespace_stack: list[str] = []

    findings: list[DocFinding] = []

    i = 0
    while i < len(masked_lines):
        line = masked_lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if m := NAMESPACE_RE.match(line):
            namespace_stack.append(m.group(1))
            i += 1
            continue
        if m := END_RE.match(line):
            target = m.group(1)
            target_parts = target.split(".")
            while target_parts and namespace_stack and namespace_stack[-1] == target_parts[0]:
                namespace_stack.pop()
                target_parts.pop(0)
            if target_parts:
                if section_stack:
                    section_stack.pop()
            i += 1
            continue
        if END_SECTION_RE.match(line):
            if section_stack:
                section_stack.pop()
            i += 1
            continue

        if TOP_LEVEL_PUBLIC_SECTION_RE.match(line):
            section_stack.append(True)
            i += 1
            continue

        m = _DECL_LINE_RE.match(line)
        if not m:
            i += 1
            continue

        is_private, is_explicit_public = _strip_modifiers(m.group("prefix"))
        if is_private:
            i += 1
            continue

        in_public_section = bool(section_stack) and section_stack[-1]
        visible = is_explicit_public or in_public_section or file_default_public
        if not visible:
            i += 1
            continue

        kind = m.group("kind")
        local_name = m.group("name")
        qualified = ".".join([*namespace_stack, local_name]) if namespace_stack else local_name

        has_doc = _has_preceding_docstring(raw_lines, i)

        findings.append(
            DocFinding(
                kind=kind,
                name=qualified,
                module=module,
                path=rel,
                line=i + 1,
                has_docstring=has_doc,
            )
        )

        i += 1

    return findings


# ---------------------------------------------------------------------------
# Aggregation and reporting
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModuleCoverage:
    """Aggregated coverage stats for one top-level module group."""

    module: str
    covered: int
    total: int

    @property
    def percent(self) -> float:
        """Coverage percentage; 100.0 for empty groups so they do not skew the table."""
        if self.total == 0:
            return 100.0
        return 100.0 * self.covered / self.total


def _scan_root(root: pathlib.Path) -> list[DocFinding]:
    """Recursively scan all `.lean` files under `root` for visible declarations."""
    if not root.exists():
        return []
    findings: list[DocFinding] = []
    for path in sorted(root.rglob("*.lean")):
        findings.extend(_scan_file(path))
    findings.sort(key=lambda f: (f.module, f.name, f.kind))
    return findings


def _group_by_module(findings: list[DocFinding], scan_root: pathlib.Path) -> list[ModuleCoverage]:
    """Aggregate findings into top-level module buckets, sorted alphabetically."""
    buckets: dict[str, list[DocFinding]] = {}
    for f in findings:
        key = _top_level_module(f.module, scan_root)
        buckets.setdefault(key, []).append(f)
    out: list[ModuleCoverage] = []
    for module, items in buckets.items():
        covered = sum(1 for f in items if f.has_docstring)
        out.append(ModuleCoverage(module=module, covered=covered, total=len(items)))
    out.sort(key=lambda m: m.module)
    return out


def _format_table(modules: list[ModuleCoverage], overall: ModuleCoverage) -> str:
    """Render the coverage table for terminal output."""
    if not modules:
        return "docstring_coverage: no declarations found.\n"

    name_w = max(len("module"), max(len(m.module) for m in modules))
    header = f"{'module'.ljust(name_w)}  {'covered':>8}  {'total':>6}  {'percent':>8}"
    sep = "-" * len(header)
    lines = [header, sep]
    for m in modules:
        lines.append(
            f"{m.module.ljust(name_w)}  "
            f"{m.covered:>8}  "
            f"{m.total:>6}  "
            f"{m.percent:>7.1f}%"
        )
    lines.append(sep)
    lines.append(
        f"{'OVERALL'.ljust(name_w)}  "
        f"{overall.covered:>8}  "
        f"{overall.total:>6}  "
        f"{overall.percent:>7.1f}%"
    )
    return "\n".join(lines) + "\n"


def _format_json(
    findings: list[DocFinding],
    modules: list[ModuleCoverage],
    overall: ModuleCoverage,
    scan_root: pathlib.Path,
) -> str:
    """Render the coverage report as a stable JSON document."""
    payload = {
        "scan_root": scan_root.relative_to(REPO_ROOT).as_posix(),
        "overall": {
            "covered": overall.covered,
            "total": overall.total,
            "percent": round(overall.percent, 2),
        },
        "modules": [
            {
                "module": m.module,
                "covered": m.covered,
                "total": m.total,
                "percent": round(m.percent, 2),
            }
            for m in modules
        ],
        "declarations": [asdict(f) for f in findings],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _missing_names(findings: list[DocFinding]) -> list[str]:
    """Return fully qualified names of undocumented declarations, sorted."""
    return sorted({f.name for f in findings if not f.has_docstring})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Parse CLI flags, run the requested mode, and return an exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=DEFAULT_ROOT,
        help=(
            "Directory to scan recursively for `.lean` files "
            f"(default: {DEFAULT_ROOT.relative_to(REPO_ROOT).as_posix()})."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report instead of the human table.",
    )
    parser.add_argument(
        "--list-missing",
        action="store_true",
        help="Print fully qualified names of undocumented declarations (sorted).",
    )
    parser.add_argument(
        "--min-coverage",
        type=int,
        default=None,
        metavar="N",
        help="Exit nonzero if overall coverage < N percent (integer 0..100).",
    )
    args = parser.parse_args(argv)

    if args.min_coverage is not None and not (0 <= args.min_coverage <= 100):
        print(
            f"docstring_coverage: --min-coverage must be in 0..100 (got {args.min_coverage}).",
            file=sys.stderr,
        )
        return 2

    # Resolve the scan root: accept both absolute paths and paths relative to the repo root for
    # ergonomic CLI use (e.g. `--root NN/Library`).
    root = args.root
    if not root.is_absolute():
        root = (REPO_ROOT / root).resolve()
    else:
        root = root.resolve()

    if not root.exists():
        print(
            f"docstring_coverage: scan root does not exist: {root}",
            file=sys.stderr,
        )
        return 2

    findings = _scan_root(root)
    modules = _group_by_module(findings, root)
    covered_total = sum(1 for f in findings if f.has_docstring)
    overall = ModuleCoverage(module="OVERALL", covered=covered_total, total=len(findings))

    if args.json:
        try:
            sys.stdout.write(_format_json(findings, modules, overall, root))
        except BrokenPipeError:
            pass
    else:
        try:
            sys.stdout.write(_format_table(modules, overall))
            if args.list_missing:
                missing = _missing_names(findings)
                if missing:
                    sys.stdout.write("\nUndocumented declarations:\n")
                    for name in missing:
                        sys.stdout.write(f"  {name}\n")
                else:
                    sys.stdout.write("\nNo undocumented declarations.\n")
        except BrokenPipeError:
            pass

    if args.min_coverage is not None and overall.total > 0:
        if overall.percent < args.min_coverage:
            print(
                f"docstring_coverage: overall {overall.percent:.1f}% < required "
                f"{args.min_coverage}%.",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
