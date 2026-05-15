#!/usr/bin/env python3
"""
Gondlin Lake manifest auditor.

`lake-manifest.json` is the lockfile-equivalent for Gondlin's Lake dependencies.
Drift between `lakefile.lean` and `lake-manifest.json` is a common source of
hard-to-reproduce build failures, especially when SHA pins in `lakefile.lean`
are bumped without re-running `lake update`. This script enforces the
properties we want to keep stable across commits:

1. The manifest is valid JSON with the top-level keys Lake actually writes.
2. The four Gondlin direct dependencies declared in `lakefile.lean`
   (`mathlib`, `doc-gen4`, `Comparator`, `lean4export`) all appear in the
   manifest's `packages` array.
3. Each direct dependency's `@ "..."` rev in `lakefile.lean` matches the
   corresponding `inputRev` (and, for SHA pins, the `rev`) in the manifest.
4. `mathlib` is the last `require` in `lakefile.lean`, per the in-file
   comment ("Keep `mathlib` last so Mathlib's dependency versions win").

The audit uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# Direct dependencies declared in `lakefile.lean`. These are the names we
# expect to find in the manifest, regardless of Lean's `«...»` escaping.
DIRECT_DEPS: tuple[str, ...] = ("mathlib", "doc-gen4", "Comparator", "lean4export")

# Lake escapes identifiers containing special characters (like the hyphen in
# `doc-gen4`) by wrapping them in `«...»` inside the manifest. Strip those
# guillemets when comparing names so the audit speaks the same language as
# `lakefile.lean`.
GUILLEMETS = ("«", "»")

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# `require <name> from git "<url>" @ "<rev>"` — `<name>` may carry `«...»`,
# the URL is a quoted string, and the rev is the part we want to pin. The
# pattern allows whitespace and newlines between tokens since `lakefile.lean`
# spreads its `require` directives across two lines.
REQUIRE_RE = re.compile(
    r"require\s+"
    r"(?P<name>\S+?)\s+"
    r"from\s+git\s+"
    r'"(?P<url>[^"]+)"\s*'
    r'@\s*"(?P<rev>[^"]+)"',
    re.MULTILINE,
)


@dataclass(frozen=True)
class Finding:
    """One manifest-audit warning or error."""

    level: str  # "ERROR" or "WARN"
    code: str
    message: str


@dataclass(frozen=True)
class RequireEntry:
    """One `require ... from git ... @ ...` declaration found in lakefile.lean."""

    name: str
    url: str
    rev: str
    line: int


def _strip_guillemets(name: str) -> str:
    """Drop Lean's `«...»` identifier escaping from a package name."""
    if name.startswith(GUILLEMETS[0]) and name.endswith(GUILLEMETS[1]):
        return name[1:-1]
    return name


def _read_lakefile_requires(lakefile: pathlib.Path) -> list[RequireEntry]:
    """Extract every `require ... from git "..." @ "..."` clause in order."""
    text = lakefile.read_text(encoding="utf-8")
    entries: list[RequireEntry] = []
    for m in REQUIRE_RE.finditer(text):
        # Line number of the `require` keyword, which is what humans expect
        # when this script flags a mismatch.
        line = text.count("\n", 0, m.start()) + 1
        entries.append(
            RequireEntry(
                name=_strip_guillemets(m.group("name")),
                url=m.group("url"),
                rev=m.group("rev"),
                line=line,
            )
        )
    return entries


def _index_manifest_packages(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return manifest packages keyed by their (de-escaped) name."""
    by_name: dict[str, dict[str, Any]] = {}
    for pkg in manifest.get("packages", []):
        if not isinstance(pkg, dict):
            continue
        raw_name = pkg.get("name")
        if not isinstance(raw_name, str):
            continue
        by_name[_strip_guillemets(raw_name)] = pkg
    return by_name


def audit(root: pathlib.Path) -> dict[str, Any]:
    """Run every manifest-vs-lakefile check and return a JSON-ready report."""
    root = root.resolve()
    manifest_path = root / "lake-manifest.json"
    lakefile_path = root / "lakefile.lean"

    findings: list[Finding] = []
    schema_ok = False
    manifest: dict[str, Any] = {}
    packages_by_name: dict[str, dict[str, Any]] = {}
    requires: list[RequireEntry] = []

    # --- 1. Schema integrity --------------------------------------------------
    if not manifest_path.exists():
        findings.append(
            Finding("ERROR", "manifest-missing", f"missing file: {manifest_path}")
        )
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "ERROR",
                    "manifest-json",
                    f"lake-manifest.json failed to parse: {exc}",
                )
            )
        else:
            expected_keys = {"version", "packagesDir", "packages"}
            missing = sorted(expected_keys - set(manifest.keys()))
            if missing:
                findings.append(
                    Finding(
                        "ERROR",
                        "manifest-keys",
                        f"lake-manifest.json missing top-level keys: {missing}",
                    )
                )
            elif not isinstance(manifest.get("packages"), list):
                findings.append(
                    Finding(
                        "ERROR",
                        "manifest-packages-shape",
                        "lake-manifest.json `packages` is not an array",
                    )
                )
            else:
                schema_ok = True
                packages_by_name = _index_manifest_packages(manifest)

    # --- Parse lakefile.lean -------------------------------------------------
    if not lakefile_path.exists():
        findings.append(
            Finding("ERROR", "lakefile-missing", f"missing file: {lakefile_path}")
        )
    else:
        requires = _read_lakefile_requires(lakefile_path)

    # --- 2. Required direct deps present -------------------------------------
    if schema_ok:
        for dep in DIRECT_DEPS:
            if dep not in packages_by_name:
                findings.append(
                    Finding(
                        "ERROR",
                        "missing-direct-dep",
                        f"direct dependency `{dep}` declared in lakefile.lean but absent from lake-manifest.json",
                    )
                )

    # --- 3. Unexpected packages (warning-only) -------------------------------
    # Transitive deps legitimately show up in the manifest with `inherited: true`,
    # so we only warn about non-inherited packages that aren't one of our four
    # named direct deps.
    if schema_ok:
        for name, pkg in packages_by_name.items():
            if name in DIRECT_DEPS:
                continue
            if pkg.get("inherited", False):
                continue
            findings.append(
                Finding(
                    "WARN",
                    "unexpected-package",
                    f"manifest lists non-inherited package `{name}` that is not a declared direct dependency",
                )
            )

    # --- 4. Pinned revs in lakefile.lean must match the manifest -------------
    require_by_name = {r.name: r for r in requires}
    for dep in DIRECT_DEPS:
        req = require_by_name.get(dep)
        if req is None:
            # If a direct dep is missing from lakefile.lean entirely, that is
            # itself a serious drift signal — surface it as an error so the
            # caller doesn't silently lose a dependency.
            findings.append(
                Finding(
                    "ERROR",
                    "lakefile-missing-require",
                    f"lakefile.lean has no `require {dep} from git ...` directive",
                )
            )
            continue
        pkg = packages_by_name.get(dep)
        if pkg is None:
            # Already flagged above as `missing-direct-dep`; skip rev check.
            continue

        input_rev = pkg.get("inputRev")
        manifest_rev = pkg.get("rev")
        if SHA_RE.match(req.rev):
            # The lakefile pins a full SHA. Both `inputRev` and the resolved
            # `rev` should equal it verbatim; if not, someone bumped one place
            # and forgot the other.
            if input_rev != req.rev:
                findings.append(
                    Finding(
                        "ERROR",
                        "sha-pin-inputrev-mismatch",
                        f"`{dep}`: lakefile.lean pins SHA {req.rev} but manifest inputRev is {input_rev}",
                    )
                )
            if manifest_rev != req.rev:
                findings.append(
                    Finding(
                        "ERROR",
                        "sha-pin-rev-mismatch",
                        f"`{dep}`: lakefile.lean pins SHA {req.rev} but manifest rev is {manifest_rev}",
                    )
                )
        else:
            # Tag-style pin (e.g. `v4.29.0`): `inputRev` should match exactly.
            # The resolved `rev` is the SHA Lake picked for that tag and we
            # can't independently verify it without network access, so it is
            # left alone here.
            if input_rev != req.rev:
                findings.append(
                    Finding(
                        "ERROR",
                        "tag-pin-mismatch",
                        f"`{dep}`: lakefile.lean pins `{req.rev}` but manifest inputRev is `{input_rev}`",
                    )
                )

    # --- 5. mathlib must be the last `require` ------------------------------
    if requires:
        last_require_name = requires[-1].name
        if last_require_name != "mathlib":
            findings.append(
                Finding(
                    "ERROR",
                    "mathlib-not-last",
                    "`mathlib` must be the last `require` in lakefile.lean "
                    f"(found `{last_require_name}` last); see in-file comment about cache tooling",
                )
            )

    errors = sum(1 for f in findings if f.level == "ERROR")
    warnings = sum(1 for f in findings if f.level == "WARN")
    return {
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "direct_deps_checked": list(DIRECT_DEPS),
            "manifest_path": str(manifest_path),
            "lakefile_path": str(lakefile_path),
        },
        "requires": [asdict(r) for r in requires],
        "manifest_packages": sorted(packages_by_name.keys()),
        "findings": [asdict(f) for f in findings],
    }


def _render_human(report: dict[str, Any]) -> str:
    """Render the audit report as a human-readable plain-text block."""
    lines: list[str] = []
    s = report["summary"]
    lines.append("Gondlin Lake manifest audit")
    lines.append("===========================")
    lines.append(f"manifest:  {s['manifest_path']}")
    lines.append(f"lakefile:  {s['lakefile_path']}")
    lines.append(
        f"checked direct deps: {', '.join(s['direct_deps_checked'])}"
    )
    lines.append("")
    lines.append(f"errors:   {s['errors']}")
    lines.append(f"warnings: {s['warnings']}")
    lines.append("")
    if not report["findings"]:
        lines.append("All checks passed.")
    else:
        lines.append("Findings:")
        for f in report["findings"]:
            lines.append(f"  [{f['level']}] {f['code']}: {f['message']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    """Parse CLI flags, run the audit, and pick an exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=REPO_ROOT,
        help="repository root (default: the repo containing this script)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a machine-readable JSON report on stdout",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors (exit nonzero if any warning fires)",
    )
    args = parser.parse_args(argv)

    report = audit(args.root)
    if args.json:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(_render_human(report))

    errors = report["summary"]["errors"]
    warnings = report["summary"]["warnings"]
    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
