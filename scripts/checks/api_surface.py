#!/usr/bin/env python3
"""
Gondolin Tier 1 frozen API-surface check.

Gondolin's PyTorch-shaped public facade lives under `NN/API/`. Once that surface is published, the
maintainers want changes to be loud: CI should warn when any declaration head visible from
`NN/API/Public.lean` (and its transitive imports within `NN/API/`) is added, removed, or edited.

This script keeps the methodology lightweight:

  - It does not try to parse or pretty-print Lean type signatures (elaboration changes those for
    surface-irrelevant reasons; that path is a maintenance trap).
  - Instead, it captures a SHA-256 hash of the *whitespace-normalized declaration head* — the text
    from the keyword (`def`/`theorem`/...) up to `:=`, `where`, or end-of-line for single-line decls.
  - Module paths, fully qualified names, and kinds are recorded verbatim so diffs are readable.

Subcommands:
  - `--write` regenerate `api-surface.lock`.
  - `--check` diff the current scan against the lock and exit nonzero on any change.
  - `--json`  print the current scan as JSON.

The lock file uses fixed-width columns sorted by (kind, name) so review diffs stay readable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
API_ROOT = REPO_ROOT / "NN" / "API"
PUBLIC_ENTRY = API_ROOT / "Public.lean"
LOCK_PATH = REPO_ROOT / "api-surface.lock"

# Declaration kinds that count toward the Tier 1 surface. The order here is also the canonical
# sort order used when writing the lock file (kind padding column is fixed at 9 chars).
DECL_KINDS = ("abbrev", "class", "def", "inductive", "structure", "theorem")

# Modifiers that may precede the declaration keyword on the same logical line. `private` is handled
# separately (it excludes the declaration); the rest are stripped while we look for the keyword.
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

IMPORT_RE = re.compile(r"^\s*(?:public\s+)?import\s+([A-Za-z0-9_'.]+)\s*$")
NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z0-9_'.]+)\s*$")
END_RE = re.compile(r"^\s*end\s+([A-Za-z0-9_'.]+)\s*$")
SECTION_RE = re.compile(
    r"(?:@\[\s*expose\s*\]\s*)?(?:public\s+)?section\b(?:\s+([A-Za-z0-9_'.]+))?"
)
END_SECTION_RE = re.compile(r"^\s*end\s*(?:--.*)?$")
FILE_PUBLIC_SECTION_RE = re.compile(r"@\[\s*expose\s*\]\s*public\s+section\b")
TOP_LEVEL_PUBLIC_SECTION_RE = re.compile(r"^\s*public\s+section\b")

# ANSI escape sequences. Kept small and stdlib-only.
_ANSI_RESET = "\x1b[0m"
_ANSI_RED = "\x1b[31m"
_ANSI_GREEN = "\x1b[32m"
_ANSI_YELLOW = "\x1b[33m"
_ANSI_BOLD = "\x1b[1m"


@dataclass(frozen=True, order=True)
class Declaration:
    """One declaration in Gondolin's Tier 1 public API surface."""

    kind: str
    name: str  # fully qualified, including namespaces
    module: str  # dotted Lean module path
    head_hash: str  # `sha256:<hex>`
    path: str  # repo-relative source path
    line: int  # 1-based line number of the keyword


# ---------------------------------------------------------------------------
# Comment / string masking (same approach as repo_lint.py / dependency_audit.py)
# ---------------------------------------------------------------------------


def _mask_comments_and_strings(text: str) -> str:
    """Replace Lean comments/docstrings/strings with spaces, preserving newlines.

    Block comments (`/- ... -/`) nest. Line comments (`--`) run to end-of-line. String literals
    are masked so a stray `def` inside a string cannot register as a declaration.
    """

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
                # Be defensive: a missing closing quote should not mask the rest of the file.
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
# Module-path helpers and import traversal (NN/API/* only)
# ---------------------------------------------------------------------------


def _module_of_path(path: pathlib.Path) -> str:
    """Convert a Lean source path under the repo root into a dotted Lean module name."""
    return ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)


def _path_of_module(module: str) -> pathlib.Path:
    """Resolve a dotted Lean module name to an on-disk path under the repo root."""
    return REPO_ROOT.joinpath(*module.split(".")).with_suffix(".lean")


def _api_imports(masked: str) -> list[str]:
    """Yield imports that target modules under `NN.API.*` (Tier 1 facade transitive closure)."""
    out: list[str] = []
    for line in masked.splitlines():
        m = IMPORT_RE.match(line)
        if not m:
            continue
        target = m.group(1)
        if target == "NN.API" or target.startswith("NN.API."):
            out.append(target)
    return out


def _collect_api_modules(entry: pathlib.Path) -> list[pathlib.Path]:
    """BFS the `NN/API/` import closure starting at `entry`, sorted deterministically."""
    if not entry.exists():
        return []
    seen: set[pathlib.Path] = set()
    order: list[pathlib.Path] = []
    queue: list[pathlib.Path] = [entry.resolve()]
    while queue:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        order.append(path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        masked = _mask_comments_and_strings(text)
        for target in _api_imports(masked):
            child = _path_of_module(target)
            # Stay inside `NN/API/` — Tier 1 is the facade, not the runtime it sits on top of.
            if not child.exists():
                continue
            if API_ROOT not in child.resolve().parents and child.resolve() != API_ROOT:
                continue
            queue.append(child.resolve())
    order.sort()
    return order


# ---------------------------------------------------------------------------
# Declaration scanning
# ---------------------------------------------------------------------------


def _is_internal_file(text: str) -> bool:
    """Return True when the file opts out of the surface via `-- @internal` on the first line."""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Only line comments can mark a file as internal; block comments are documentation.
        return line.startswith("--") and "@internal" in line
    return False


def _file_has_expose_public_section(text: str) -> bool:
    """Detect the `@[expose] public section` pattern Gondolin uses for facade files."""
    return bool(FILE_PUBLIC_SECTION_RE.search(text))


def _strip_modifiers(prefix: str) -> tuple[bool, bool, str]:
    """Split a pre-keyword prefix into (is_private, is_explicit_public, residual).

    The residual is unused by the caller but kept for diagnostic clarity; the boolean flags are
    what gate whether a declaration is included.
    """
    tokens = prefix.split()
    is_private = False
    is_explicit_public = False
    leftover: list[str] = []
    for tok in tokens:
        if tok == "private":
            is_private = True
        elif tok in VISIBILITY_TOKENS:
            is_explicit_public = True
        elif tok in DECL_MODIFIERS:
            continue
        elif tok.startswith("@["):
            continue
        else:
            leftover.append(tok)
    return is_private, is_explicit_public, " ".join(leftover)


def _hash_head(head_text: str) -> str:
    """Hash the whitespace-normalized declaration head (keyword..terminator)."""
    normalized = " ".join(head_text.split()).strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


# Match `<modifiers> <keyword> <name>` at the start of a (masked) line. The keyword set is
# closed (DECL_KINDS); we capture the prefix separately to inspect for `private`/`public`.
_DECL_LINE_RE = re.compile(
    r"^(?P<prefix>(?:\s*(?:@\[[^\]]*\]|"
    + r"|".join(DECL_MODIFIERS + VISIBILITY_TOKENS + ("private",))
    + r")\s+)*)"
    r"(?P<kind>"
    + r"|".join(DECL_KINDS)
    + r")\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_'\.]*)"
)


def _declaration_head(masked_lines: list[str], start: int) -> tuple[str, int]:
    """Collect the declaration head text from line `start` up to `:=`, `where`, or `extends`.

    Returns the joined head text plus the 0-based line index where the head ends (inclusive).
    Multi-line heads are common in Lean; a single-line head ends at the source newline.
    """
    pieces: list[str] = []
    end_idx = start
    for j in range(start, len(masked_lines)):
        end_idx = j
        line = masked_lines[j]
        # Look for terminators that signal the body has started.
        cut_positions: list[int] = []
        for token in (":=", " where", "\tWhere"):
            idx = line.find(token)
            if idx != -1:
                cut_positions.append(idx)
        if "where" in line:
            # Word-boundary check so `whereabouts` (unlikely but cheap to guard) is not mistaken.
            for m in re.finditer(r"\bwhere\b", line):
                cut_positions.append(m.start())
        for m in re.finditer(r"\bextends\b", line):
            cut_positions.append(m.start())
        if cut_positions:
            cut = min(cut_positions)
            pieces.append(line[:cut])
            return " ".join(pieces).strip(), end_idx
        pieces.append(line)
        # Single-line `def foo := bar` is handled by the cut above; lines that end with `:=` at
        # exactly the end of the line are caught there too. Otherwise we keep accumulating.
    return " ".join(pieces).strip(), end_idx


def _scan_file(path: pathlib.Path) -> list[Declaration]:
    """Scan one Lean file under `NN/API/` and return its visible declarations."""
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
    # Track whether we are currently inside a `public section` block. The simple top-level
    # `@[expose] public section` becomes the file's default; nested explicit `public section`
    # blocks are tracked with a small stack so `end`/`end <name>` can pop them.
    section_stack: list[bool] = []
    namespace_stack: list[str] = []

    declarations: list[Declaration] = []

    i = 0
    while i < len(masked_lines):
        line = masked_lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Namespace tracking (mirrors proof_debt.py-style scanners).
        if m := NAMESPACE_RE.match(line):
            namespace_stack.append(m.group(1))
            i += 1
            continue
        if m := END_RE.match(line):
            target = m.group(1)
            # `end Foo` closes the matching namespace; we tolerate dotted names by popping the
            # longest matching suffix instead of failing on mismatches.
            target_parts = target.split(".")
            while target_parts and namespace_stack and namespace_stack[-1] == target_parts[0]:
                namespace_stack.pop()
                target_parts.pop(0)
            # If still leftover parts, fall through (could also be `end <section-name>`).
            if target_parts:
                # Possible explicit-section end; pop a section frame if any.
                if section_stack:
                    section_stack.pop()
            i += 1
            continue
        if END_SECTION_RE.match(line):
            if section_stack:
                section_stack.pop()
            i += 1
            continue

        # Explicit `public section` (with or without `@[expose]`) anywhere in the file pushes a
        # frame onto the stack.
        if TOP_LEVEL_PUBLIC_SECTION_RE.match(line):
            section_stack.append(True)
            i += 1
            continue

        # Declaration detection.
        m = _DECL_LINE_RE.match(line)
        if not m:
            i += 1
            continue

        is_private, is_explicit_public, _ = _strip_modifiers(m.group("prefix"))
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

        # Collect the declaration head from the masked text so terminators inside comments are
        # ignored, then hash the whitespace-normalized form.
        # Start the head with the keyword (drop any pre-keyword modifiers) so renaming
        # `noncomputable def foo` to `def foo` does not perturb the hash.
        head_pieces, end_idx = _declaration_head(masked_lines, i)
        keyword_pos = head_pieces.find(kind)
        head_from_keyword = head_pieces[keyword_pos:] if keyword_pos != -1 else head_pieces
        head_hash = _hash_head(head_from_keyword)

        declarations.append(
            Declaration(
                kind=kind,
                name=qualified,
                module=module,
                head_hash=head_hash,
                path=rel,
                line=i + 1,
            )
        )

        # Advance past the head; the body (if any) is irrelevant to surface tracking.
        _ = raw_lines  # keep reference for readability; not used after head collection
        i = max(i + 1, end_idx + 1)

    return declarations


# ---------------------------------------------------------------------------
# Lock-file format
# ---------------------------------------------------------------------------


_KIND_COL = 9
_NAME_COL = 60


def _format_lock(declarations: list[Declaration]) -> str:
    """Render the deterministic, line-sorted lock file."""
    sorted_decls = sorted(declarations, key=lambda d: (d.kind, d.name))
    header_lines = [
        "# Gondolin API surface lock",
        "# Regenerate with: python3 scripts/checks/api_surface.py --write",
        "# scan_root: NN/API",
        f"# total_declarations: {len(sorted_decls)}",
        "#",
    ]
    body_lines: list[str] = []
    for d in sorted_decls:
        # Always emit at least one space between adjacent fields, even when a kind/name overruns
        # the nominal column width. `structure` and `inductive` are 9 chars themselves, so without
        # this guard their rows would visually concatenate `structureName...` and the parser
        # could not recover the boundary by whitespace splitting.
        kind_col = d.kind.ljust(_KIND_COL) + (" " if len(d.kind) >= _KIND_COL else "")
        name_col = d.name.ljust(_NAME_COL) + (" " if len(d.name) >= _NAME_COL else "")
        body_lines.append(f"{kind_col}{name_col}{d.head_hash}")
    return "\n".join(header_lines + body_lines) + "\n"


def _parse_lock(text: str) -> list[Declaration]:
    """Parse a previously written lock file back into `Declaration` records.

    The lock omits source path and line (those are scan-time metadata that drift even when the
    surface is stable). Diffs only need `(kind, name, head_hash)`, so we synthesize empty values
    for the missing fields.
    """
    out: list[Declaration] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        # The hash is always the last whitespace-separated token (`sha256:<hex>` contains no
        # spaces), so splitting from the right is robust to long names that overflow the nominal
        # 60-char name column.
        parts = raw.rsplit(None, 1)
        if len(parts) != 2:
            continue
        prefix, rest = parts
        # The first token is the declaration kind; everything between it and the hash is the
        # fully-qualified name. Splitting once on whitespace is enough because Lean identifiers
        # never contain spaces.
        kind_name = prefix.split(None, 1)
        if len(kind_name) != 2:
            continue
        kind, name = kind_name[0].strip(), kind_name[1].strip()
        # Derive module from name conservatively: the canonical name is fully qualified, so the
        # module is the longest prefix that matches a known `NN.API.*` pattern. For diffing we do
        # not need it; leave empty.
        out.append(
            Declaration(
                kind=kind,
                name=name,
                module="",
                head_hash=rest,
                path="",
                line=0,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Diff and rendering
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SurfaceDiff:
    """Summary of changes between the lock file and a fresh scan."""

    added: list[Declaration]
    removed: list[Declaration]
    changed: list[tuple[Declaration, Declaration]]  # (old, new)

    @property
    def is_clean(self) -> bool:
        """Whether the scan matches the lock exactly."""
        return not (self.added or self.removed or self.changed)


def _diff(current: list[Declaration], locked: list[Declaration]) -> SurfaceDiff:
    """Compare the live scan against the stored lock by `(kind, name)` identity."""
    cur_index = {(d.kind, d.name): d for d in current}
    lock_index = {(d.kind, d.name): d for d in locked}

    added = [cur_index[k] for k in sorted(cur_index.keys() - lock_index.keys())]
    removed = [lock_index[k] for k in sorted(lock_index.keys() - cur_index.keys())]
    changed: list[tuple[Declaration, Declaration]] = []
    for k in sorted(cur_index.keys() & lock_index.keys()):
        if cur_index[k].head_hash != lock_index[k].head_hash:
            changed.append((lock_index[k], cur_index[k]))
    return SurfaceDiff(added=added, removed=removed, changed=changed)


def _resolve_color(flag: str) -> bool:
    """Resolve the `--color` flag, defaulting to TTY detection."""
    if flag == "always":
        return True
    if flag == "never":
        return False
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _paint(text: str, color: str, enabled: bool) -> str:
    """Wrap text in an ANSI color, no-op when colors are disabled."""
    if not enabled:
        return text
    return f"{color}{text}{_ANSI_RESET}"


def _render_diff(diff: SurfaceDiff, *, color: bool) -> str:
    """Format a human-readable, optionally colored diff summary."""
    if diff.is_clean:
        return _paint("API surface lock is up to date.", _ANSI_GREEN, color)

    lines: list[str] = []
    header = _paint("API surface drift detected:", _ANSI_BOLD, color)
    lines.append(header)
    lines.append(
        f"  added: {len(diff.added)}, removed: {len(diff.removed)}, changed: {len(diff.changed)}"
    )
    lines.append("")

    for d in diff.added:
        lines.append(_paint(f"+ {d.kind:9}{d.name}  {d.head_hash}", _ANSI_GREEN, color))
    for d in diff.removed:
        lines.append(_paint(f"- {d.kind:9}{d.name}  {d.head_hash}", _ANSI_RED, color))
    for old, new in diff.changed:
        lines.append(_paint(f"~ {new.kind:9}{new.name}", _ANSI_YELLOW, color))
        lines.append(_paint(f"    - {old.head_hash}", _ANSI_RED, color))
        lines.append(_paint(f"    + {new.head_hash}", _ANSI_GREEN, color))
    lines.append("")
    lines.append(
        "Run `python3 scripts/checks/api_surface.py --write` after a deliberate API change."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Top-level scan orchestrator
# ---------------------------------------------------------------------------


def scan_surface() -> list[Declaration]:
    """Scan Gondolin's Tier 1 API surface starting from `NN/API/Public.lean`."""
    modules = _collect_api_modules(PUBLIC_ENTRY)
    declarations: list[Declaration] = []
    for path in modules:
        declarations.extend(_scan_file(path))
    # Stable ordering for downstream consumers; the lock formatter re-sorts independently.
    declarations.sort(key=lambda d: (d.kind, d.name, d.module))
    return declarations


def _scan_to_json(declarations: list[Declaration]) -> str:
    """Serialize the scan as a deterministic JSON document."""
    payload = {
        "scan_root": "NN/API",
        "entry": "NN/API/Public.lean",
        "total_declarations": len(declarations),
        "declarations": [asdict(d) for d in declarations],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Parse CLI flags, run the requested mode, and return an exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write",
        action="store_true",
        help="Regenerate `api-surface.lock` from the current source tree.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Diff the current scan against the lock; exit nonzero on any change.",
    )
    mode.add_argument(
        "--json",
        action="store_true",
        help="Print the current scan as JSON.",
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="Color the `--check` diff (default: auto-detect via TTY / NO_COLOR).",
    )
    args = parser.parse_args(argv)

    if not PUBLIC_ENTRY.exists():
        print(
            f"api_surface: expected entry point at {PUBLIC_ENTRY.relative_to(REPO_ROOT)} "
            "(is the working directory inside Gondolin?)",
            file=sys.stderr,
        )
        return 2

    declarations = scan_surface()

    if args.json:
        try:
            sys.stdout.write(_scan_to_json(declarations))
        except BrokenPipeError:
            # Common when piping through `head`/`less`; nothing to do but exit cleanly.
            pass
        return 0

    if args.write:
        LOCK_PATH.write_text(_format_lock(declarations), encoding="utf-8")
        print(
            f"Wrote {LOCK_PATH.relative_to(REPO_ROOT)} "
            f"({len(declarations)} declaration(s))."
        )
        return 0

    # --check
    if not LOCK_PATH.exists():
        print(
            f"api_surface: missing lock file at {LOCK_PATH.relative_to(REPO_ROOT)}; "
            "run with `--write` to create it.",
            file=sys.stderr,
        )
        return 2

    locked = _parse_lock(LOCK_PATH.read_text(encoding="utf-8"))
    diff = _diff(declarations, locked)
    use_color = _resolve_color(args.color)
    print(_render_diff(diff, color=use_color))
    return 0 if diff.is_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
