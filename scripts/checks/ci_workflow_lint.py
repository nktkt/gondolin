#!/usr/bin/env python3
"""
Gondolin CI workflow lint (stdlib-only).

Lightweight structural sanity check for ``.github/workflows/*.yml`` that does not
depend on PyYAML or actionlint. The intent is to catch trivially broken
workflows (missing ``jobs:``, tab indentation, unpinned actions) without
shipping a full YAML parser.

Checks
------
1. File is non-empty UTF-8 text.
2. Top-level keys (column 0, unindented, ending in ``:``) include ``name``,
   ``on``, and ``jobs``.
3. Under ``jobs:``, every job defines a ``steps:`` key.
4. Every step has either ``run:`` or ``uses:``.
5. No tab characters anywhere (YAML disallows tabs for indentation).
6. Lines longer than 200 characters are flagged as warnings.
7. ``actions/*`` references must be version-pinned (``@v4``, ``@main``, or a
   git SHA). Bare ``actions/checkout`` is flagged as a warning.

Parsing strategy: walk the file linearly tracking indentation depth so we can
identify which ``key:`` line lives at which conceptual level. We do NOT try to
be a full YAML parser; we just want enough structure to find jobs and steps.

CLI
---
- Default: scan all ``.github/workflows/*.yml`` and report findings.
- ``--strict``: warnings become errors (non-zero exit on any finding).
- ``--json``: structured output for tooling.
- ``--paths <glob>`` (repeatable): scan specific files only.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import re
import sys
from dataclasses import dataclass, asdict
from typing import Iterable


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# Versioned-ref pattern: @v1, @v1.2.3, @main, @master, or a 40-char hex SHA.
_VERSION_PIN_RE = re.compile(
    r"@(v\d+(?:\.\d+){0,2}|main|master|[0-9a-fA-F]{7,40})\b"
)

# `key:` (with optional inline value). We strip the trailing value before
# treating a line as a key node.
_KEY_LINE_RE = re.compile(r"^(\s*)([A-Za-z_][\w\-]*)\s*:(.*)$")

# `- key: value` (sequence element that introduces a mapping).
_SEQ_KEY_LINE_RE = re.compile(r"^(\s*)-\s+([A-Za-z_][\w\-]*)\s*:(.*)$")

# `- value` (plain sequence element with no mapping key).
_SEQ_PLAIN_RE = re.compile(r"^(\s*)-\s+(.*)$")

LINE_LENGTH_WARN = 200


@dataclass(frozen=True)
class Finding:
    """One workflow-lint finding."""

    level: str  # "ERROR" | "WARN"
    path: str  # repo-relative
    line: int | None
    message: str

    def render(self) -> str:
        """Format for terminal output."""
        if self.line is None:
            return f"{self.level}: {self.path}: {self.message}"
        return f"{self.level}: {self.path}:{self.line}: {self.message}"


# ---------------------------------------------------------------------------
# Minimal indent-tracking "parser"
# ---------------------------------------------------------------------------


@dataclass
class Node:
    """One key node identified by the structural scanner."""

    key: str
    indent: int
    line: int  # 1-based source line
    inline_value: str  # everything after ``key:`` on the same line (may be empty)
    children: list["Node"]
    is_seq_element: bool = False  # came from ``- key: ...``


def _scan_structure(text: str) -> list[Node]:
    """
    Walk the file linearly with an indent stack and return the forest of key
    nodes. Comments (``# ...``) and blank lines are skipped. Sequence-element
    keys (``- key: value``) are treated as keys whose indent is the column of
    the key character (so children align like a normal mapping).

    Limitations:
      - We do not parse flow-style mappings (``{a: 1, b: 2}``).
      - We do not parse multi-line scalars (``|`` / ``>`` blocks); their body
        lines simply do not match the key regex and are ignored, which is
        fine for our structural checks.
    """
    roots: list[Node] = []
    # Stack of (indent, node) pairs ordered by ascending indent.
    stack: list[tuple[int, Node]] = []

    in_block_scalar_indent: int | None = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        # Strip trailing whitespace for matching, but keep the original raw line
        # length / leading whitespace.
        stripped = raw.rstrip()
        if not stripped:
            continue
        # Skip whole-line comments.
        if stripped.lstrip().startswith("#"):
            continue

        # If we are inside a block scalar (``run: |``), skip until indentation
        # drops back to or below the introducing key's indent.
        leading = len(raw) - len(raw.lstrip(" "))
        if in_block_scalar_indent is not None:
            if leading > in_block_scalar_indent:
                continue
            in_block_scalar_indent = None
            # Fall through to re-process this line as structure.

        m_seq_key = _SEQ_KEY_LINE_RE.match(raw)
        m_key = _KEY_LINE_RE.match(raw) if not m_seq_key else None
        m_seq_plain = _SEQ_PLAIN_RE.match(raw) if (not m_seq_key and not m_key) else None

        if m_seq_key is not None:
            seq_indent = len(m_seq_key.group(1))
            # The ``-`` lives at column ``seq_indent``; the key starts two cols
            # later (``-`` + space). Treat the key's effective indent as
            # ``seq_indent + 2`` for child-attachment purposes.
            effective_indent = seq_indent + 2
            key = m_seq_key.group(2)
            inline_value = m_seq_key.group(3).strip()
            node = Node(
                key=key,
                indent=effective_indent,
                line=lineno,
                inline_value=inline_value,
                children=[],
                is_seq_element=True,
            )
            _attach(roots, stack, node)
            if _introduces_block_scalar(inline_value):
                in_block_scalar_indent = effective_indent
            continue

        if m_key is not None:
            indent = len(m_key.group(1))
            key = m_key.group(2)
            inline_value = m_key.group(3).strip()
            node = Node(
                key=key,
                indent=indent,
                line=lineno,
                inline_value=inline_value,
                children=[],
                is_seq_element=False,
            )
            _attach(roots, stack, node)
            if _introduces_block_scalar(inline_value):
                in_block_scalar_indent = indent
            continue

        if m_seq_plain is not None:
            # A bare sequence element like ``- '0 3 * * *'``. Not a key; ignore
            # for structural purposes.
            continue

        # Unrecognised line shape (continuation of a value, etc.); ignore.

    return roots


def _attach(
    roots: list[Node],
    stack: list[tuple[int, Node]],
    node: Node,
) -> None:
    """Attach ``node`` to the nearest parent whose indent is strictly smaller."""
    # Pop any siblings/deeper nodes off the stack.
    while stack and stack[-1][0] >= node.indent:
        stack.pop()
    if stack:
        stack[-1][1].children.append(node)
    else:
        roots.append(node)
    stack.append((node.indent, node))


def _introduces_block_scalar(inline_value: str) -> bool:
    """Detect ``key: |`` / ``key: >`` (with optional indicators)."""
    if not inline_value:
        return False
    # Allow ``|``, ``>``, ``|-``, ``>+``, etc. Stop at first whitespace/comment.
    head = inline_value.split("#", 1)[0].strip()
    return bool(head) and head[0] in "|>"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def _check_file(path: pathlib.Path) -> list[Finding]:
    """Run all structural checks on a single workflow file."""
    findings: list[Finding] = []
    rel = path.relative_to(REPO_ROOT).as_posix()

    try:
        raw = path.read_bytes()
    except OSError as e:
        findings.append(Finding("ERROR", rel, None, f"failed to read file: {e}"))
        return findings

    if not raw.strip():
        findings.append(Finding("ERROR", rel, None, "file is empty."))
        return findings

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        findings.append(Finding("ERROR", rel, None, f"file is not valid UTF-8: {e}"))
        return findings

    # Whitespace hygiene.
    for i, line in enumerate(text.splitlines(), start=1):
        if "\t" in line:
            findings.append(
                Finding("ERROR", rel, i, "tab character found (YAML disallows tabs for indentation).")
            )
        if len(line) > LINE_LENGTH_WARN:
            findings.append(
                Finding(
                    "WARN",
                    rel,
                    i,
                    f"line is {len(line)} chars (>{LINE_LENGTH_WARN}); consider wrapping.",
                )
            )

    roots = _scan_structure(text)
    top_keys = {n.key: n for n in roots}

    # Required top-level keys.
    for required in ("name", "on", "jobs"):
        if required not in top_keys:
            findings.append(
                Finding("ERROR", rel, None, f"missing required top-level key `{required}:`.")
            )

    # Each job must have a `steps:` key, and each step must have `run:` or `uses:`.
    jobs_node = top_keys.get("jobs")
    if jobs_node is not None:
        if not jobs_node.children:
            findings.append(
                Finding("ERROR", rel, jobs_node.line, "`jobs:` block has no jobs defined.")
            )
        for job in jobs_node.children:
            steps_node = next((c for c in job.children if c.key == "steps"), None)
            if steps_node is None:
                # ``uses:`` at the job level (reusable workflow) is also valid;
                # in that case `steps:` is forbidden. We only flag a missing
                # `steps:` if there is also no job-level `uses:`.
                has_uses = any(c.key == "uses" for c in job.children)
                if not has_uses:
                    findings.append(
                        Finding(
                            "ERROR",
                            rel,
                            job.line,
                            f"job `{job.key}` is missing a `steps:` key.",
                        )
                    )
                continue
            # Only sequence-element children represent step boundaries; the
            # other children are peers belonging to the previous step (because
            # the scanner attaches ``- name:`` as the step's first key node
            # and the subsequent ``uses:`` / ``run:`` / ``with:`` keys land at
            # the same indent under ``steps:``).
            step_elements = [c for c in steps_node.children if c.is_seq_element]
            if not step_elements:
                findings.append(
                    Finding(
                        "ERROR",
                        rel,
                        steps_node.line,
                        f"job `{job.key}` has a `steps:` key but no steps.",
                    )
                )
            for step in step_elements:
                step_keys = _collect_step_keys(step, steps_node)
                if "run" not in step_keys and "uses" not in step_keys:
                    findings.append(
                        Finding(
                            "ERROR",
                            rel,
                            step.line,
                            f"step (line {step.line}) has neither `run:` nor `uses:`.",
                        )
                    )
                # actions/* version-pin check.
                uses_value = step_keys.get("uses")
                if uses_value is not None:
                    _check_uses_pin(rel, step.line, uses_value, findings)

    return findings


def _collect_step_keys(step_node: Node, steps_node: Node) -> dict[str, str]:
    """
    Gather all key/value pairs that belong to the *same* step as ``step_node``.

    Because our scanner attaches ``- name:`` as a key node whose siblings (the
    other keys of that step mapping) are also direct children of ``steps_node``
    at the same indent, we walk forward from ``step_node`` in the steps_node's
    child list, stopping at the next sequence element (``is_seq_element``).
    """
    keys: dict[str, str] = {step_node.key: step_node.inline_value}
    siblings = steps_node.children
    try:
        idx = siblings.index(step_node)
    except ValueError:
        return keys
    for sib in siblings[idx + 1 :]:
        if sib.is_seq_element:
            break
        keys[sib.key] = sib.inline_value
    return keys


def _check_uses_pin(
    rel: str,
    line: int,
    uses_value: str,
    findings: list[Finding],
) -> None:
    """Warn if an ``actions/*`` reference is unpinned."""
    # Strip optional quoting.
    val = uses_value.strip().strip("'\"")
    if not val:
        return
    # Local actions (``./path``) and Docker refs (``docker://``) are exempt.
    if val.startswith("./") or val.startswith("docker://"):
        return
    if not val.startswith("actions/"):
        # Third-party actions are out of scope for this check.
        return
    if not _VERSION_PIN_RE.search(val):
        findings.append(
            Finding(
                "WARN",
                rel,
                line,
                f"`uses: {val}` is not version-pinned (expected `@vN`, `@main`, or a SHA).",
            )
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _iter_workflow_files(paths: list[str] | None) -> Iterable[pathlib.Path]:
    """Yield workflow files matching either ``paths`` globs or the default scan."""
    if paths:
        for pat in paths:
            # Allow both absolute and repo-relative globs.
            candidate = pathlib.Path(pat)
            if candidate.is_absolute():
                if candidate.exists():
                    yield candidate
                continue
            # Match against workflow dir entries.
            for entry in sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml")):
                rel = entry.relative_to(REPO_ROOT).as_posix()
                if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(entry.name, pat):
                    yield entry
        return

    if not WORKFLOWS_DIR.exists():
        return
    for entry in sorted(WORKFLOWS_DIR.glob("*.yml")):
        yield entry
    for entry in sorted(WORKFLOWS_DIR.glob("*.yaml")):
        yield entry


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(
        description="Gondolin CI workflow structural lint (stdlib-only)."
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    ap.add_argument(
        "--paths",
        action="append",
        default=None,
        metavar="GLOB",
        help="Limit scan to workflow files matching GLOB (repeatable).",
    )
    args = ap.parse_args(argv)

    all_findings: list[Finding] = []
    scanned: list[str] = []
    for path in _iter_workflow_files(args.paths):
        scanned.append(path.relative_to(REPO_ROOT).as_posix())
        all_findings.extend(_check_file(path))

    if args.strict:
        all_findings = [
            Finding("ERROR" if f.level == "WARN" else f.level, f.path, f.line, f.message)
            for f in all_findings
        ]

    errors = [f for f in all_findings if f.level == "ERROR"]
    warns = [f for f in all_findings if f.level == "WARN"]

    if args.json:
        payload = {
            "scanned": scanned,
            "findings": [asdict(f) for f in all_findings],
            "summary": {
                "errors": len(errors),
                "warnings": len(warns),
            },
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if not scanned:
            print("no workflow files found under .github/workflows/")
        for f in all_findings:
            print(f.render())
        if errors:
            print(f"\nFAILED: {len(errors)} error(s), {len(warns)} warning(s).")
        elif warns:
            print(f"\nOK (with warnings): {len(warns)} warning(s).")
        else:
            print(f"OK: scanned {len(scanned)} workflow file(s); no issues found.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
