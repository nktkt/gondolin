#!/usr/bin/env python3
"""
Trust-boundary consistency checker.

Cross-validates three sources of truth about Gondlin's trust surface:

  1. `TRUST_BOUNDARIES.md`        - the human-readable trust inventory.
  2. `trust-boundaries.toml`      - the machine-readable mirror of (1).
  3. `scripts/checks/repo_lint.py`'s `ALLOWED_AXIOMS` dict - the
     enforcement allowlist used by the repo linter.

The three views must agree on which Lean axioms exist, in which file they
live, and that each axiom is mentioned by name in the prose document.

Exit code is 0 when consistent, nonzero with a diff otherwise.

Usage:
  python3 scripts/checks/trust_boundaries_check.py
  python3 scripts/checks/trust_boundaries_check.py --json
  python3 scripts/checks/trust_boundaries_check.py --show
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys
import tomllib
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

TRUST_TOML = REPO_ROOT / "trust-boundaries.toml"
TRUST_MD = REPO_ROOT / "TRUST_BOUNDARIES.md"
REPO_LINT_PY = REPO_ROOT / "scripts" / "checks" / "repo_lint.py"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_toml() -> dict[str, Any]:
    """Parse `trust-boundaries.toml` with the stdlib `tomllib`."""
    with TRUST_TOML.open("rb") as f:
        return tomllib.load(f)


def load_md() -> str:
    """Read `TRUST_BOUNDARIES.md` as text."""
    return TRUST_MD.read_text(encoding="utf-8")


def load_allowed_axioms_from_repo_lint() -> dict[str, set[str]]:
    """
    Extract the `ALLOWED_AXIOMS` dict from `repo_lint.py` by static AST parse.

    The dict is a `dict[str, set[str]]` literal at module scope; we walk the
    module AST, find the assignment, and `ast.literal_eval` each key/value.
    No code from repo_lint.py is executed.
    """
    src = REPO_LINT_PY.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(REPO_LINT_PY))

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = node.targets
        if len(targets) != 1:
            continue
        tgt = targets[0]
        if not isinstance(tgt, ast.Name) or tgt.id != "ALLOWED_AXIOMS":
            continue
        if not isinstance(node.value, ast.Dict):
            raise RuntimeError(
                "ALLOWED_AXIOMS in repo_lint.py is not a dict literal; cannot statically parse."
            )
        out: dict[str, set[str]] = {}
        for k_node, v_node in zip(node.value.keys, node.value.values):
            if k_node is None:
                raise RuntimeError("ALLOWED_AXIOMS contains dict-unpacking; unsupported.")
            key = ast.literal_eval(k_node)
            value = ast.literal_eval(v_node)
            if not isinstance(key, str):
                raise RuntimeError(f"ALLOWED_AXIOMS key must be str; got {type(key).__name__}.")
            if not isinstance(value, (set, frozenset)):
                # `ast.literal_eval` returns a `set` for `{...}` literals.
                raise RuntimeError(
                    f"ALLOWED_AXIOMS[{key!r}] must be a set literal; got {type(value).__name__}."
                )
            out[key] = set(value)
        return out

    raise RuntimeError("Could not find `ALLOWED_AXIOMS = {...}` in repo_lint.py.")


# ---------------------------------------------------------------------------
# Cross-checks
# ---------------------------------------------------------------------------


def toml_axiom_pairs(toml: dict[str, Any]) -> set[tuple[str, str]]:
    """Return the set of `(axiom_name, file)` pairs declared in the TOML."""
    pairs: set[tuple[str, str]] = set()
    for entry in toml.get("axiom", []):
        name = entry.get("name")
        file = entry.get("file")
        if not isinstance(name, str) or not isinstance(file, str):
            raise RuntimeError(f"malformed [[axiom]] entry: {entry!r}")
        pairs.add((name, file))
    return pairs


def repo_lint_axiom_pairs(allowed: dict[str, set[str]]) -> set[tuple[str, str]]:
    """Convert `ALLOWED_AXIOMS` (file -> {names}) into `(name, file)` pairs."""
    pairs: set[tuple[str, str]] = set()
    for file, names in allowed.items():
        for name in names:
            pairs.add((name, file))
    return pairs


def md_mentions(md: str, name: str) -> bool:
    """Return True iff the axiom `name` appears as a token in the markdown."""
    # Backtick-quoted in the doc, but be tolerant.
    return name in md


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def run_check() -> tuple[int, dict[str, Any]]:
    """Run all checks and return `(exit_code, report)`."""
    report: dict[str, Any] = {
        "ok": True,
        "errors": [],
        "counts": {},
    }

    toml = load_toml()
    md = load_md()
    allowed = load_allowed_axioms_from_repo_lint()

    toml_pairs = toml_axiom_pairs(toml)
    lint_pairs = repo_lint_axiom_pairs(allowed)

    only_in_toml = sorted(toml_pairs - lint_pairs)
    only_in_lint = sorted(lint_pairs - toml_pairs)

    if only_in_toml:
        report["errors"].append(
            {
                "kind": "axiom_only_in_toml",
                "detail": "axioms declared in trust-boundaries.toml but missing from ALLOWED_AXIOMS",
                "items": [{"name": n, "file": f} for (n, f) in only_in_toml],
            }
        )
    if only_in_lint:
        report["errors"].append(
            {
                "kind": "axiom_only_in_repo_lint",
                "detail": "axioms in ALLOWED_AXIOMS but missing from trust-boundaries.toml",
                "items": [{"name": n, "file": f} for (n, f) in only_in_lint],
            }
        )

    # Each axiom in the TOML must be mentioned by name in the MD.
    md_missing: list[dict[str, str]] = []
    for name, file in sorted(toml_pairs):
        if not md_mentions(md, name):
            md_missing.append({"name": name, "file": file})
    if md_missing:
        report["errors"].append(
            {
                "kind": "axiom_not_in_md",
                "detail": "axioms in trust-boundaries.toml not mentioned by name in TRUST_BOUNDARIES.md",
                "items": md_missing,
            }
        )

    # Each axiom file must actually exist in the repo.
    missing_files: list[dict[str, str]] = []
    for name, file in sorted(toml_pairs):
        p = REPO_ROOT / file
        if not p.exists():
            missing_files.append({"name": name, "file": file})
    if missing_files:
        report["errors"].append(
            {
                "kind": "axiom_file_missing",
                "detail": "axiom file referenced from trust-boundaries.toml does not exist",
                "items": missing_files,
            }
        )

    report["counts"] = {
        "axioms": len(toml.get("axiom", [])),
        "prop_contracts": len(toml.get("prop_contract", [])),
        "opaque_non_ffi": len(toml.get("opaque_non_ffi", [])),
        "external_oracles": len(toml.get("external_oracle", [])),
    }

    if report["errors"]:
        report["ok"] = False
        return 1, report
    return 0, report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_human(report: dict[str, Any]) -> None:
    """Pretty-print the report for a terminal."""
    counts = report["counts"]
    if report["ok"]:
        print(
            "trust boundaries consistent: "
            f"{counts['axioms']} axioms, "
            f"{counts['prop_contracts']} prop contracts, "
            f"{counts['opaque_non_ffi']} opaque non-FFI, "
            f"{counts['external_oracles']} external oracles."
        )
        return

    print("trust boundaries INCONSISTENT:")
    for err in report["errors"]:
        print(f"  - {err['kind']}: {err['detail']}")
        for item in err["items"]:
            if "file" in item:
                print(f"      * {item['name']}  ({item['file']})")
            else:
                print(f"      * {item['name']}")


def _show_toml() -> None:
    """Dump the parsed TOML as pretty JSON for inspection."""
    toml = load_toml()
    json.dump(toml, sys.stdout, indent=2, default=lambda o: sorted(o) if isinstance(o, set) else str(o))
    sys.stdout.write("\n")


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="Validate Gondlin trust-boundary consistency.")
    ap.add_argument("--json", action="store_true", help="Emit a JSON report.")
    ap.add_argument(
        "--show",
        action="store_true",
        help="Dump the parsed trust-boundaries.toml as JSON and exit.",
    )
    args = ap.parse_args()

    if args.show:
        _show_toml()
        return 0

    code, report = run_check()
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        _print_human(report)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
