#!/usr/bin/env python3
"""
Publish the current proof-debt snapshot to Jekyll's `_data/` directory.

Invokes `scripts/checks/proof_debt.py --format json` (the source of truth),
flattens the report into a small, template-friendly dict, and emits a
deterministic YAML file at `home_page/_data/proof_status.yml` so Jekyll
includes/layouts can render it via `site.data.proof_status`.

Stdlib-only by design: CI and contributors should not need PyYAML installed
just to refresh the website snapshot. A minimal YAML emitter handles the
specific data shape produced here (nested dicts, lists of dicts, primitive
scalars); it is deliberately not a general-purpose YAML writer.

Usage:
    python3 scripts/dev/update_proof_status.py
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PROOF_DEBT_SCRIPT = REPO_ROOT / "scripts" / "checks" / "proof_debt.py"
LAKEFILE = REPO_ROOT / "lakefile.lean"
OUTPUT_PATH = REPO_ROOT / "home_page" / "_data" / "proof_status.yml"

SCHEMA_VERSION = "1"


def _run_proof_debt() -> dict:
    """Execute `proof_debt.py --format json` and return the parsed report."""
    result = subprocess.run(
        ["python3", str(PROOF_DEBT_SCRIPT), "--format", "json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


_VERSION_RE = re.compile(r"version\s*:=\s*v!\"([^\"]+)\"")


def _parse_gondolin_version() -> str:
    """Extract the package `version` literal from `lakefile.lean`."""
    text = LAKEFILE.read_text(encoding="utf-8")
    m = _VERSION_RE.search(text)
    if not m:
        raise RuntimeError(f"Could not find `version := v!\"...\"` in {LAKEFILE}")
    return m.group(1)


def _utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string with second precision and Z suffix."""
    now = _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_payload(report: dict, version: str, timestamp: str) -> dict:
    """Reshape the raw proof-debt report into the Jekyll-friendly payload."""
    totals = report.get("totals", {})
    axioms = sorted(
        (
            {
                "name": a.get("qualified", a.get("name", "")),
                "file": a.get("file", ""),
                "line": int(a.get("line", 0)),
                "allowed": bool(a.get("allowed", False)),
            }
            for a in report.get("axioms", [])
        ),
        key=lambda a: (a["file"], a["line"], a["name"]),
    )

    unauthorized = report.get("unauthorized_axioms", [])
    healthy = (
        int(totals.get("sorry", 0)) == 0
        and int(totals.get("admit", 0)) == 0
        and len(unauthorized) == 0
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": timestamp,
        "gondolin_version": version,
        "summary": {
            "files_scanned": int(report.get("scanned_files", 0)),
            "sorry": int(totals.get("sorry", 0)),
            "admit": int(totals.get("admit", 0)),
            "axiom": int(totals.get("axiom", 0)),
            "opaque": int(totals.get("opaque", 0)),
            "unsafe": int(totals.get("unsafe", 0)),
            "native_decide": int(totals.get("native_decide", 0)),
        },
        "axioms": axioms,
        "healthy": healthy,
    }


# ---------------------------------------------------------------------------
# Tiny YAML emitter
#
# Covers exactly the shapes produced by `_build_payload`:
#   * top-level dict with primitive and dict values
#   * a list of dicts of primitives (the `axioms` block)
# Strings are quoted whenever they would otherwise be ambiguous to a YAML
# parser (leading special characters, embedded `:`, etc.). Booleans and ints
# render in their canonical forms so Jekyll/Liquid sees real types.
# ---------------------------------------------------------------------------

# Characters/prefixes that force string quoting to avoid YAML ambiguity.
_NEEDS_QUOTE_CHARS = set(":#&*!|>'\"%@`,{}[]")
_RESERVED_SCALARS = {
    "true",
    "false",
    "null",
    "yes",
    "no",
    "on",
    "off",
    "~",
    "",
}


def _is_plain_safe(s: str) -> bool:
    """Return True if `s` can be emitted as an unquoted YAML scalar."""
    if s in _RESERVED_SCALARS:
        return False
    if s != s.strip():
        return False
    if s[0] in "-?:,[]{}#&*!|>'\"%@`":
        return False
    # Strings that start with a digit (version literals, dates, etc.) are
    # quoted so they always round-trip as strings — never as ints/floats/dates.
    if s[0].isdigit():
        return False
    for ch in s:
        if ch in _NEEDS_QUOTE_CHARS:
            return False
        if ch == "\n" or ch == "\t":
            return False
    return True


def _emit_scalar(value: Any) -> str:
    """Render a primitive Python value as a single-line YAML scalar."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if value is None:
        return "null"
    s = str(value)
    if _is_plain_safe(s):
        return s
    # Use double quotes; escape backslashes and double quotes.
    escaped = s.replace("\\", "\\\\").replace("\"", "\\\"")
    return f"\"{escaped}\""


def _emit_mapping(d: dict, indent: int) -> list[str]:
    """Emit a dict at the given indentation. Caller controls key ordering."""
    pad = " " * indent
    lines: list[str] = []
    for k in d:
        v = d[k]
        key = str(k)
        if isinstance(v, dict):
            lines.append(f"{pad}{key}:")
            lines.extend(_emit_mapping(v, indent + 2))
        elif isinstance(v, list):
            if not v:
                lines.append(f"{pad}{key}: []")
                continue
            lines.append(f"{pad}{key}:")
            lines.extend(_emit_sequence(v, indent + 2))
        else:
            lines.append(f"{pad}{key}: {_emit_scalar(v)}")
    return lines


def _emit_sequence(items: list, indent: int) -> list[str]:
    """Emit a list at the given indentation. Items may be dicts or scalars."""
    pad = " " * indent
    lines: list[str] = []
    for item in items:
        if isinstance(item, dict):
            first = True
            for k in item:
                v = item[k]
                prefix = f"{pad}- " if first else f"{pad}  "
                first = False
                key = str(k)
                if isinstance(v, dict):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_emit_mapping(v, indent + 4))
                elif isinstance(v, list):
                    if not v:
                        lines.append(f"{prefix}{key}: []")
                    else:
                        lines.append(f"{prefix}{key}:")
                        lines.extend(_emit_sequence(v, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {_emit_scalar(v)}")
        else:
            lines.append(f"{pad}- {_emit_scalar(item)}")
    return lines


# Key order at the top level. Determines the visual layout of the YAML.
_TOP_ORDER = (
    "schema_version",
    "updated_at",
    "gondolin_version",
    "summary",
    "axioms",
    "healthy",
)

# Stable key order within the `summary` block.
_SUMMARY_ORDER = (
    "files_scanned",
    "sorry",
    "admit",
    "axiom",
    "opaque",
    "unsafe",
    "native_decide",
)

# Stable key order within each axiom entry.
_AXIOM_ORDER = ("name", "file", "line", "allowed")


def _ordered(d: dict, order: tuple[str, ...]) -> dict:
    """Return a new dict containing the keys of `d` in the requested order."""
    out: dict = {}
    for k in order:
        if k in d:
            out[k] = d[k]
    for k in d:
        if k not in out:
            out[k] = d[k]
    return out


def _render_yaml(payload: dict) -> str:
    """Render the payload using the project-specific key ordering."""
    ordered = _ordered(payload, _TOP_ORDER)
    if "summary" in ordered and isinstance(ordered["summary"], dict):
        ordered["summary"] = _ordered(ordered["summary"], _SUMMARY_ORDER)
    if "axioms" in ordered and isinstance(ordered["axioms"], list):
        ordered["axioms"] = [_ordered(a, _AXIOM_ORDER) for a in ordered["axioms"]]

    header = [
        "# Auto-generated by scripts/dev/update_proof_status.py.",
        "# Do not edit by hand: re-run the script to refresh this snapshot.",
        "# Source of truth: scripts/checks/proof_debt.py --format json",
        "",
    ]
    body = _emit_mapping(ordered, 0)
    return "\n".join(header + body) + "\n"


def main() -> int:
    """CLI entry point: refresh `home_page/_data/proof_status.yml`."""
    try:
        report = _run_proof_debt()
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"proof_debt.py failed: {e}\nstderr:\n{e.stderr}\n")
        return 1
    except json.JSONDecodeError as e:
        sys.stderr.write(f"proof_debt.py emitted invalid JSON: {e}\n")
        return 1

    version = _parse_gondolin_version()
    timestamp = _utc_now_iso()
    payload = _build_payload(report, version, timestamp)
    yaml_text = _render_yaml(payload)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(yaml_text, encoding="utf-8")
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
