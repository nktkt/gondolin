#!/usr/bin/env python3
"""
Gondlin Lean toolchain pin auditor.

`lean-toolchain` is the source of truth for which `leanprover/lean4` release
this repository builds against. Bumping it without also updating Mathlib and
doc-gen4 pins in `lakefile.lean` / `lake-manifest.json` produces builds that
fail in subtle ways (orphan tactics, mismatched `Lean.Elab` signatures, etc.).

This script enforces the version-coherence invariant we want across the
three reproducibility files:

1. `lean-toolchain` is well-formed:
     - single line
     - matches `^leanprover/lean4:v\\d+\\.\\d+\\.\\d+(-rc\\d+)?$`.
2. `lakefile.lean`'s tag-style pins for `doc-gen4` and `mathlib`
   (`@ "v<X>.<Y>.<Z>"`) name the same Lean version as the toolchain.
   SHA-style pins are skipped because we can't cross-check them without
   network access.
3. `lake-manifest.json`'s `mathlib` package has `inputRev` equal to the
   toolchain version.

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

# `leanprover/lean4:v<major>.<minor>.<patch>` with optional `-rcN` suffix is
# the form `elan` accepts and is what Mathlib also uses, so we mirror it
# exactly here rather than allowing free-form text.
TOOLCHAIN_RE = re.compile(r"^leanprover/lean4:(v\d+\.\d+\.\d+(?:-rc\d+)?)$")

# Same `require ... from git "..." @ "..."` shape used by the manifest
# auditor. Capturing the rev directly is enough — we only care about
# `lakefile.lean` for tag-style pins of `mathlib` / `doc-gen4` here.
REQUIRE_RE = re.compile(
    r"require\s+"
    r"(?P<name>\S+?)\s+"
    r"from\s+git\s+"
    r'"(?P<url>[^"]+)"\s*'
    r'@\s*"(?P<rev>[^"]+)"',
    re.MULTILINE,
)

# Tag-style rev (e.g. `v4.29.0`, `v4.29.0-rc1`). Anything not matching this is
# treated as a SHA pin and intentionally skipped from cross-checks.
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+(?:-rc\d+)?$")

GUILLEMETS = ("«", "»")


@dataclass(frozen=True)
class Finding:
    """One toolchain-pin warning or error."""

    level: str  # "ERROR" or "WARN"
    code: str
    message: str


@dataclass(frozen=True)
class VersionRow:
    """One (file, version-string, status) row for the `--explain` matrix."""

    file: str
    where: str
    raw: str
    version: str | None
    note: str


def _strip_guillemets(name: str) -> str:
    """Drop Lean's `«...»` identifier escaping from a package name."""
    if name.startswith(GUILLEMETS[0]) and name.endswith(GUILLEMETS[1]):
        return name[1:-1]
    return name


def _read_toolchain(path: pathlib.Path) -> tuple[str | None, str | None, list[Finding]]:
    """Return (raw, version, findings) for `lean-toolchain`.

    `raw` is the trimmed file content; `version` is the `vX.Y.Z[-rcN]` segment
    when the file matches `TOOLCHAIN_RE`, otherwise `None`.
    """
    findings: list[Finding] = []
    if not path.exists():
        findings.append(
            Finding("ERROR", "toolchain-missing", f"missing file: {path}")
        )
        return None, None, findings

    text = path.read_text(encoding="utf-8")
    # Allow a single trailing newline (typical) but reject multi-line files
    # since downstream tooling reads only the first line.
    stripped = text.strip("\n")
    if "\n" in stripped:
        findings.append(
            Finding(
                "ERROR",
                "toolchain-multiline",
                f"lean-toolchain must be a single line; got {len(stripped.splitlines())} lines",
            )
        )
        return stripped, None, findings

    raw = stripped.strip()
    m = TOOLCHAIN_RE.match(raw)
    if not m:
        findings.append(
            Finding(
                "ERROR",
                "toolchain-format",
                f"lean-toolchain `{raw}` does not match `leanprover/lean4:vX.Y.Z[-rcN]`",
            )
        )
        return raw, None, findings

    return raw, m.group(1), findings


def _read_lakefile_requires(
    lakefile: pathlib.Path,
) -> list[tuple[str, str, int]]:
    """Return `(name, rev, line)` triples for every `require ... from git`."""
    if not lakefile.exists():
        return []
    text = lakefile.read_text(encoding="utf-8")
    out: list[tuple[str, str, int]] = []
    for m in REQUIRE_RE.finditer(text):
        name = _strip_guillemets(m.group("name"))
        rev = m.group("rev")
        line = text.count("\n", 0, m.start()) + 1
        out.append((name, rev, line))
    return out


def _read_manifest(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    """Return the parsed manifest, or `None` plus a finding when unreadable."""
    findings: list[Finding] = []
    if not path.exists():
        findings.append(
            Finding("ERROR", "manifest-missing", f"missing file: {path}")
        )
        return None, findings
    try:
        return json.loads(path.read_text(encoding="utf-8")), findings
    except json.JSONDecodeError as exc:
        findings.append(
            Finding("ERROR", "manifest-json", f"lake-manifest.json failed to parse: {exc}")
        )
        return None, findings


def audit(root: pathlib.Path) -> dict[str, Any]:
    """Run all toolchain-pin checks and return a JSON-ready report."""
    root = root.resolve()
    toolchain_path = root / "lean-toolchain"
    lakefile_path = root / "lakefile.lean"
    manifest_path = root / "lake-manifest.json"

    findings: list[Finding] = []
    rows: list[VersionRow] = []

    raw_toolchain, toolchain_version, tc_findings = _read_toolchain(toolchain_path)
    findings.extend(tc_findings)
    rows.append(
        VersionRow(
            file="lean-toolchain",
            where="(file content)",
            raw=raw_toolchain or "",
            version=toolchain_version,
            note="canonical Lean version" if toolchain_version else "unparseable",
        )
    )

    # --- lakefile.lean cross-check -------------------------------------------
    lakefile_requires = _read_lakefile_requires(lakefile_path)
    if not lakefile_path.exists():
        findings.append(
            Finding("ERROR", "lakefile-missing", f"missing file: {lakefile_path}")
        )

    # We only have a meaningful cross-check when the toolchain version parsed.
    for name, rev, line in lakefile_requires:
        if name not in {"mathlib", "doc-gen4"}:
            continue
        is_tag = bool(TAG_RE.match(rev))
        row = VersionRow(
            file="lakefile.lean",
            where=f"require {name} @ (line {line})",
            raw=rev,
            version=rev if is_tag else None,
            note="tag pin" if is_tag else "SHA pin (skipped from cross-check)",
        )
        rows.append(row)
        if not is_tag:
            continue
        if toolchain_version is None:
            # Without a parseable toolchain we can't say what "matches" means.
            continue
        if rev != toolchain_version:
            findings.append(
                Finding(
                    "ERROR",
                    "lakefile-tag-mismatch",
                    f"lakefile.lean pins `{name}` at `{rev}` but lean-toolchain is `{toolchain_version}`",
                )
            )

    # --- lake-manifest.json cross-check --------------------------------------
    manifest, m_findings = _read_manifest(manifest_path)
    findings.extend(m_findings)
    if manifest is not None:
        mathlib_pkg: dict[str, Any] | None = None
        for pkg in manifest.get("packages", []):
            if not isinstance(pkg, dict):
                continue
            if _strip_guillemets(str(pkg.get("name", ""))) == "mathlib":
                mathlib_pkg = pkg
                break
        if mathlib_pkg is None:
            findings.append(
                Finding(
                    "ERROR",
                    "manifest-no-mathlib",
                    "lake-manifest.json has no `mathlib` package entry",
                )
            )
        else:
            input_rev = mathlib_pkg.get("inputRev")
            is_tag = isinstance(input_rev, str) and bool(TAG_RE.match(input_rev))
            rows.append(
                VersionRow(
                    file="lake-manifest.json",
                    where="packages[mathlib].inputRev",
                    raw=str(input_rev),
                    version=input_rev if is_tag else None,
                    note="tag pin" if is_tag else "non-tag inputRev (skipped from cross-check)",
                )
            )
            if is_tag and toolchain_version is not None and input_rev != toolchain_version:
                findings.append(
                    Finding(
                        "ERROR",
                        "manifest-mathlib-mismatch",
                        f"lake-manifest.json mathlib inputRev `{input_rev}` "
                        f"differs from lean-toolchain `{toolchain_version}`",
                    )
                )

    errors = sum(1 for f in findings if f.level == "ERROR")
    warnings = sum(1 for f in findings if f.level == "WARN")
    return {
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "toolchain_raw": raw_toolchain,
            "toolchain_version": toolchain_version,
        },
        "version_matrix": [asdict(r) for r in rows],
        "findings": [asdict(f) for f in findings],
    }


def _render_human(report: dict[str, Any]) -> str:
    """Render the audit report as a human-readable plain-text block."""
    lines: list[str] = []
    s = report["summary"]
    lines.append("Gondlin Lean toolchain pin audit")
    lines.append("================================")
    lines.append(f"toolchain raw:     {s['toolchain_raw']!r}")
    lines.append(f"toolchain version: {s['toolchain_version']!r}")
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


def _render_explain(report: dict[str, Any]) -> str:
    """Print the per-source version matrix collected during the audit."""
    rows = report["version_matrix"]
    headers = ("file", "where", "raw", "version", "note")
    table: list[tuple[str, str, str, str, str]] = [headers]
    for r in rows:
        table.append(
            (
                str(r["file"]),
                str(r["where"]),
                str(r["raw"]),
                "" if r["version"] is None else str(r["version"]),
                str(r["note"]),
            )
        )
    widths = [max(len(row[i]) for row in table) for i in range(len(headers))]

    def _fmt(row: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    lines: list[str] = ["Version matrix:", _fmt(table[0]), _fmt(tuple("-" * w for w in widths))]
    for row in table[1:]:
        lines.append(_fmt(row))
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
        "--explain",
        action="store_true",
        help="print the (file, where, raw, version, note) matrix",
    )
    args = parser.parse_args(argv)

    report = audit(args.root)
    if args.json:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(_render_human(report))
        if args.explain:
            sys.stdout.write("\n")
            sys.stdout.write(_render_explain(report))

    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
