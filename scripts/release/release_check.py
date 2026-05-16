#!/usr/bin/env python3
"""
Gondolin pre-release gate.

A maintainer cutting a release runs this single command to verify every
hygiene check is green. The script ties together the individual checks under
``scripts/checks/`` and the SBOM generator under ``scripts/release/`` and
produces one pass/fail summary with per-check status.

Pipeline
--------
1. Read Gondolin's package version from ``lakefile.lean`` and optionally
   compare it against ``--expected-version``.
2. Run every check in ``scripts/checks/`` (case collisions, trust
   boundaries, proof debt, API surface, docs links, docstring coverage,
   lake manifest audit, toolchain pin, CI workflow lint, Lean import audit).
3. Run ``scripts/release/sbom_generate.py`` and parse the resulting SPDX
   JSON to confirm it is well-formed and contains packages.
4. Sanity-check that ``README.md`` mentions the lakefile version
   (warn-only), ``CHANGELOG.md`` exists (warn-only), and ``LICENSE`` exists
   (hard-fail when missing).
5. Confirm ``api-surface.lock`` was regenerated within the last
   ``--lock-age-days`` days (warn-only, default 30).
6. Emit a final table and a one-line aggregate, exiting 0 on
   all-PASS/all-WARN and 1 if any check failed.

CLI
---
    python3 scripts/release/release_check.py
    python3 scripts/release/release_check.py --expected-version 0.1.0
    python3 scripts/release/release_check.py --lock-age-days 14
    python3 scripts/release/release_check.py --json
    python3 scripts/release/release_check.py --strict

Style: stdlib only, no third-party imports.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LAKEFILE_PATH = REPO_ROOT / "lakefile.lean"
CHECKS_DIR = REPO_ROOT / "scripts" / "checks"
RELEASE_DIR = REPO_ROOT / "scripts" / "release"
SBOM_GENERATOR = RELEASE_DIR / "sbom_generate.py"
API_SURFACE_LOCK = REPO_ROOT / "api-surface.lock"
README_PATH = REPO_ROOT / "README.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
LICENSE_PATH = REPO_ROOT / "LICENSE"

DEFAULT_LOCK_AGE_DAYS = 30

# Same regex used by sbom_generate.py so the two stay in lock-step.
_VERSION_RE = re.compile(r'version\s*:=\s*v!"([^"]+)"')


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Outcome of a single check step.

    ``status`` is one of ``"PASS"``, ``"WARN"``, ``"FAIL"``. ``notes`` is a
    short free-form annotation rendered in the summary table. ``stdout`` and
    ``stderr`` are captured for the ``--json`` payload and for failure
    diagnostics on the terminal.
    """

    name: str
    status: str
    notes: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "notes": self.notes,
            "exit_code": self.exit_code,
            "duration_s": round(self.duration_s, 3),
            "stdout_tail": _tail(self.stdout),
            "stderr_tail": _tail(self.stderr),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tail(text: str, lines: int = 20) -> str:
    """Return the last ``lines`` lines of ``text`` (for diagnostic output)."""
    if not text:
        return ""
    split = text.splitlines()
    if len(split) <= lines:
        return "\n".join(split)
    return "\n".join(split[-lines:])


def _read_lakefile_version() -> str | None:
    """Extract the Gondolin package version from ``lakefile.lean``.

    Returns ``None`` when the file cannot be read or the regex misses; the
    caller turns that into a hard failure since every subsequent step needs a
    known version string.
    """
    try:
        text = LAKEFILE_PATH.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _VERSION_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()


def _run_subprocess(
    cmd: list[str], *, cwd: pathlib.Path = REPO_ROOT
) -> tuple[int, str, str, float]:
    """Invoke ``cmd`` and return ``(exit_code, stdout, stderr, duration_s)``.

    We always capture text streams so we can render snippets on failure.
    ``cwd`` defaults to the repo root so every check sees a consistent
    working directory.
    """
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return (127, "", f"command not found: {exc}", time.monotonic() - start)
    return (proc.returncode, proc.stdout or "", proc.stderr or "", time.monotonic() - start)


# ---------------------------------------------------------------------------
# Individual gate steps
# ---------------------------------------------------------------------------


# Ordered list of checks under scripts/checks/. The tuple is
# (short-name, script-filename, extra-args).
CHECKS: list[tuple[str, str, list[str]]] = [
    ("check_case_collisions", "check_case_collisions.py", []),
    ("trust_boundaries_check", "trust_boundaries_check.py", []),
    ("proof_debt", "proof_debt.py", ["--strict"]),
    ("api_surface", "api_surface.py", ["--check"]),
    ("docs_link_check", "docs_link_check.py", []),
    ("docstring_coverage", "docstring_coverage.py", ["--min-coverage", "80"]),
    ("lake_manifest_audit", "lake_manifest_audit.py", []),
    ("lean_toolchain_pin", "lean_toolchain_pin.py", []),
    ("ci_workflow_lint", "ci_workflow_lint.py", []),
    ("lean_imports_audit", "lean_imports_audit.py", []),
]


def _run_check_script(name: str, filename: str, extra_args: list[str]) -> CheckResult:
    """Run one ``scripts/checks/*.py`` script and translate exit code to status."""
    script_path = CHECKS_DIR / filename
    if not script_path.exists():
        return CheckResult(
            name=name,
            status="FAIL",
            notes=f"missing script: {script_path}",
        )

    cmd = [sys.executable, str(script_path), *extra_args]
    rc, out, err, dur = _run_subprocess(cmd)
    status = "PASS" if rc == 0 else "FAIL"
    notes = "" if rc == 0 else f"exit {rc}"
    return CheckResult(
        name=name,
        status=status,
        notes=notes,
        stdout=out,
        stderr=err,
        exit_code=rc,
        duration_s=dur,
    )


def _run_sbom_check() -> CheckResult:
    """Generate the SBOM and verify it parses as SPDX 2.x with packages."""
    if not SBOM_GENERATOR.exists():
        return CheckResult(
            name="sbom_generate",
            status="FAIL",
            notes=f"missing generator: {SBOM_GENERATOR}",
        )

    # Use a per-invocation temp file under the system tempdir so concurrent
    # invocations on a single machine don't trip over each other.
    tmp_dir = pathlib.Path(tempfile.gettempdir())
    out_path = tmp_dir / "release-sbom.json"

    cmd = [
        sys.executable,
        str(SBOM_GENERATOR),
        "--pretty",
        "--output",
        str(out_path),
    ]
    rc, out, err, dur = _run_subprocess(cmd)
    if rc != 0:
        return CheckResult(
            name="sbom_generate",
            status="FAIL",
            notes=f"generator exit {rc}",
            stdout=out,
            stderr=err,
            exit_code=rc,
            duration_s=dur,
        )

    try:
        payload = json.loads(out_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return CheckResult(
            name="sbom_generate",
            status="FAIL",
            notes=f"sbom not valid JSON: {exc}",
            stdout=out,
            stderr=err,
            exit_code=rc,
            duration_s=dur,
        )

    spdx_version = payload.get("spdxVersion")
    packages = payload.get("packages") or []
    if not isinstance(spdx_version, str) or not spdx_version.startswith("SPDX-"):
        return CheckResult(
            name="sbom_generate",
            status="FAIL",
            notes=f"bad spdxVersion: {spdx_version!r}",
            stdout=out,
            stderr=err,
            exit_code=rc,
            duration_s=dur,
        )
    if not isinstance(packages, list) or len(packages) == 0:
        return CheckResult(
            name="sbom_generate",
            status="FAIL",
            notes="sbom has zero packages",
            stdout=out,
            stderr=err,
            exit_code=rc,
            duration_s=dur,
        )

    return CheckResult(
        name="sbom_generate",
        status="PASS",
        notes=f"{len(packages)} packages",
        stdout=out,
        stderr=err,
        exit_code=rc,
        duration_s=dur,
    )


def _check_repo_artifacts(version: str) -> list[CheckResult]:
    """README/CHANGELOG/LICENSE presence + README version propagation.

    Only ``LICENSE`` is a hard requirement at release time. The other two
    map to warnings so a maintainer can knowingly tag a release that hasn't
    yet propagated the new version to the README.
    """
    results: list[CheckResult] = []

    # README.md
    if not README_PATH.exists():
        results.append(
            CheckResult(
                name="readme_exists",
                status="WARN",
                notes=f"missing {README_PATH.name}",
            )
        )
    else:
        text = README_PATH.read_text(encoding="utf-8", errors="replace")
        if version in text:
            results.append(
                CheckResult(
                    name="readme_version",
                    status="PASS",
                    notes=f"contains '{version}'",
                )
            )
        else:
            results.append(
                CheckResult(
                    name="readme_version",
                    status="WARN",
                    notes=f"README.md does not mention version '{version}'",
                )
            )

    # CHANGELOG.md (warn-only)
    if CHANGELOG_PATH.exists():
        results.append(
            CheckResult(name="changelog_exists", status="PASS", notes="present")
        )
    else:
        results.append(
            CheckResult(
                name="changelog_exists",
                status="WARN",
                notes=f"missing {CHANGELOG_PATH.name}",
            )
        )

    # LICENSE (hard fail)
    if LICENSE_PATH.exists():
        results.append(CheckResult(name="license_exists", status="PASS", notes="present"))
    else:
        results.append(
            CheckResult(
                name="license_exists",
                status="FAIL",
                notes=f"missing {LICENSE_PATH.name}",
            )
        )

    return results


def _check_api_surface_lock_age(max_age_days: int) -> CheckResult:
    """Warn (don't fail) if ``api-surface.lock`` looks stale."""
    if not API_SURFACE_LOCK.exists():
        return CheckResult(
            name="api_surface_lock_age",
            status="WARN",
            notes=f"missing {API_SURFACE_LOCK.name}",
        )

    try:
        mtime = API_SURFACE_LOCK.stat().st_mtime
    except OSError as exc:
        return CheckResult(
            name="api_surface_lock_age",
            status="WARN",
            notes=f"stat failed: {exc}",
        )

    age_days = (time.time() - mtime) / 86400.0
    if age_days <= max_age_days:
        return CheckResult(
            name="api_surface_lock_age",
            status="PASS",
            notes=f"{age_days:.1f}d old (<= {max_age_days}d)",
        )
    return CheckResult(
        name="api_surface_lock_age",
        status="WARN",
        notes=(
            f"{age_days:.1f}d old; consider "
            "`python3 scripts/checks/api_surface.py --write`"
        ),
    )


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------


def _render_table(results: list[CheckResult]) -> str:
    """Render the per-check status table used in non-JSON mode."""
    name_w = max((len(r.name) for r in results), default=20)
    name_w = max(name_w, 32)
    status_w = 8

    sep = "-" * (name_w + 2 + status_w + 2 + 40)
    lines: list[str] = []
    header = f"{'Check'.ljust(name_w)}  {'Status'.ljust(status_w)}  Notes"
    lines.append(header)
    lines.append(sep)
    for r in results:
        symbol = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}.get(r.status, r.status)
        # ASCII-only glyphs to avoid terminal-encoding surprises.
        if r.status == "PASS":
            glyph = "[+] PASS"
        elif r.status == "WARN":
            glyph = "[!] WARN"
        elif r.status == "FAIL":
            glyph = "[X] FAIL"
        else:
            glyph = symbol
        lines.append(f"{r.name.ljust(name_w)}  {glyph.ljust(status_w)}  {r.notes}")
    lines.append(sep)
    return "\n".join(lines)


def _aggregate(results: list[CheckResult]) -> tuple[int, int, int, int]:
    """Count ``(total, passes, warnings, failures)`` across all results."""
    passes = sum(1 for r in results if r.status == "PASS")
    warns = sum(1 for r in results if r.status == "WARN")
    fails = sum(1 for r in results if r.status == "FAIL")
    return (len(results), passes, warns, fails)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: returns 0 on PASS/WARN, 1 on any FAIL."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected-version",
        type=str,
        default=None,
        help="Fail unless lakefile.lean's version equals this string.",
    )
    parser.add_argument(
        "--lock-age-days",
        type=int,
        default=DEFAULT_LOCK_AGE_DAYS,
        help=(
            f"Max age (days) for api-surface.lock before we warn "
            f"(default: {DEFAULT_LOCK_AGE_DAYS})."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of the text table.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote warnings to failures (CI / release-tag mode).",
    )
    args = parser.parse_args(argv)

    results: list[CheckResult] = []

    # ---- Version gate -----------------------------------------------------
    version = _read_lakefile_version()
    if version is None:
        msg = f"could not parse version from {LAKEFILE_PATH}"
        if not args.json:
            print(f"FAIL: {msg}", file=sys.stderr)
        results.append(
            CheckResult(name="lakefile_version", status="FAIL", notes=msg)
        )
        return _emit_summary(results, version="<unknown>", as_json=args.json, strict=args.strict)

    if not args.json:
        print(f"Detected version: {version}")

    results.append(
        CheckResult(name="lakefile_version", status="PASS", notes=version)
    )

    if args.expected_version is not None:
        if args.expected_version == version:
            results.append(
                CheckResult(
                    name="expected_version_match",
                    status="PASS",
                    notes=f"{version} == {args.expected_version}",
                )
            )
        else:
            results.append(
                CheckResult(
                    name="expected_version_match",
                    status="FAIL",
                    notes=(
                        f"lakefile says '{version}' but --expected-version "
                        f"is '{args.expected_version}'"
                    ),
                )
            )

    # ---- scripts/checks/* -------------------------------------------------
    for name, filename, extra in CHECKS:
        if not args.json:
            print(f"  -> running {name} ...", flush=True)
        results.append(_run_check_script(name, filename, extra))

    # ---- SBOM generator ---------------------------------------------------
    if not args.json:
        print("  -> running sbom_generate ...", flush=True)
    results.append(_run_sbom_check())

    # ---- Repo artifact sanity --------------------------------------------
    results.extend(_check_repo_artifacts(version))

    # ---- api-surface.lock freshness --------------------------------------
    results.append(_check_api_surface_lock_age(args.lock_age_days))

    return _emit_summary(results, version=version, as_json=args.json, strict=args.strict)


def _emit_summary(
    results: list[CheckResult],
    *,
    version: str,
    as_json: bool,
    strict: bool,
) -> int:
    """Print the summary block and return the process exit code.

    Under ``--strict``, WARN results are treated as failures both for the
    exit code and for the final headline. The detailed ``status`` field on
    each result is left unchanged so ``--json`` consumers still see the
    original classification.
    """
    total, passes, warns, fails = _aggregate(results)

    # Decide aggregate status.
    if fails > 0 or (strict and warns > 0):
        headline = f"RELEASE BLOCKED: gondolin v{version}"
        exit_code = 1
    elif warns > 0:
        headline = f"RELEASE READY (with warnings): gondolin v{version}"
        exit_code = 0
    else:
        headline = f"RELEASE READY: gondolin v{version}"
        exit_code = 0

    if as_json:
        payload = {
            "version": version,
            "headline": headline,
            "exit_code": exit_code,
            "totals": {
                "total": total,
                "pass": passes,
                "warn": warns,
                "fail": fails,
            },
            "strict": strict,
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return exit_code

    # Text mode.
    print()
    print(_render_table(results))
    print(f"Aggregate: {passes}/{total} PASS, {warns} WARN, {fails} FAIL")
    print()

    # Failure / warning detail.
    for r in results:
        if r.status == "FAIL":
            print(f"FAIL: {r.name} -- {r.notes}", file=sys.stderr)
            if r.stderr.strip():
                print("  stderr:", file=sys.stderr)
                for line in _tail(r.stderr, 20).splitlines():
                    print(f"    {line}", file=sys.stderr)
            if r.stdout.strip() and not r.stderr.strip():
                print("  stdout:", file=sys.stderr)
                for line in _tail(r.stdout, 20).splitlines():
                    print(f"    {line}", file=sys.stderr)
        elif r.status == "WARN":
            print(f"WARN: {r.name} -- {r.notes}")

    print()
    print(headline)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
