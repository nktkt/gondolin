#!/usr/bin/env python3
"""
Gondlin proof-debt scanner.

Walks Lean sources under `NN/` and counts proof-hygiene signals that we want to
keep at zero (or carefully bounded): `sorry`, `admit`, unallowlisted `axiom`s,
`opaque` declarations, `unsafe` declarations, and `native_decide` usages.

Stays lightweight and dependency-free (stdlib only) so it can run in CI and
locally without any setup. Intended to be invoked directly:

    python3 scripts/checks/proof_debt.py                 # text summary
    python3 scripts/checks/proof_debt.py --format json   # machine-readable
    python3 scripts/checks/proof_debt.py --strict        # CI gate
    python3 scripts/checks/proof_debt.py --baseline X    # regression guard
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Iterable


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# External trees that may exist in a developer checkout but are not part of
# Gondlin's core sources and must not affect proof-debt accounting.
VENDORED_DIR_NAMES = {
    "Two-Stage_Neural_Controller_Training",  # optional external checkout (alpha,beta-CROWN workflows)
    "PINN_verification",  # user-cloned external repo (gitignored)
}

# keep in sync with scripts/checks/repo_lint.py
ALLOWED_AXIOMS = {
    "NN/MLTheory/CROWN/Lyapunov/Oracle.lean": {"crown_oracle"},
    "NN/Runtime/Autograd/Engine/Cuda/Trusted.lean": {"instNonemptyBuffer"},
}


def _iter_lean_files() -> Iterable[pathlib.Path]:
    """Yield NN/ Lean files while skipping vendored and generated trees."""
    nn_root = REPO_ROOT / "NN"
    if not nn_root.exists():
        return
    for p in nn_root.rglob("*.lean"):
        if ".lake" in p.parts or ".git" in p.parts:
            continue
        if any(d in p.parts for d in VENDORED_DIR_NAMES):
            continue
        if "_out" in p.parts:
            continue
        yield p


def _line_col(text: str, idx: int) -> tuple[int, int]:
    """Translate a string offset into 1-based line and column coordinates."""
    line = text.count("\n", 0, idx) + 1
    last_nl = text.rfind("\n", 0, idx)
    col = idx - last_nl
    return line, col


def _mask_lean_comments_and_strings(text: str) -> str:
    """
    Return a same-length string where Lean comments/docstrings and string literals are replaced
    with spaces (newlines preserved).

    Lean block comments `/- ... -/` nest, so the scanner tracks nesting depth.
    Line comments `--` (including the docstring marker `---`) consume the rest of the line.
    """
    out = list(text)
    n = len(text)
    i = 0

    in_line_comment = False
    block_depth = 0
    in_string = False

    while i < n:
        ch = text[i]

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                i += 1
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
            if ch == "\n":
                i += 1
            else:
                out[i] = " "
                i += 1
            continue

        if in_string:
            if ch == "\n":
                in_string = False
                i += 1
                continue
            if ch == "\\" and i + 1 < n:
                out[i] = " "
                if text[i + 1] != "\n":
                    out[i + 1] = " "
                i += 2
                continue
            out[i] = " "
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


# Regexes operate over the masked text so they never trigger inside comments/strings.
_SORRY_RE = re.compile(r"\bsorry\b")
_ADMIT_RE = re.compile(r"\badmit\b")
_AXIOM_RE = re.compile(r"^\s*axiom\s+([A-Za-z0-9_'.]+)\b", flags=re.MULTILINE)
_UNSAFE_RE = re.compile(r"^\s*unsafe\s+(?:def|theorem|lemma|abbrev|opaque|instance|class|structure|inductive)\b", flags=re.MULTILINE)
_NATIVE_DECIDE_RE = re.compile(r"\bnative_decide\b")

# Top-level opaque: at column 0, or preceded only by `noncomputable` and/or `@[...]` attribute lists.
# Match an attribute prefix `@[...]` (possibly multiple), optional `noncomputable`, then `opaque NAME`.
_OPAQUE_LINE_RE = re.compile(
    r"^(?:@\[[^\]\n]*\]\s*)*(?:noncomputable\s+)?opaque\s+([A-Za-z0-9_'.]+)\b",
    flags=re.MULTILINE,
)

_NAMESPACE_OPEN_RE = re.compile(r"^\s*namespace\s+([A-Za-z0-9_'.]+)\b")
_END_RE = re.compile(r"^\s*end(?:\s+([A-Za-z0-9_'.]+))?\s*$")


def _qualified(stack: list[str], name: str) -> str:
    """Join the current namespace stack with the local declaration name."""
    if not stack:
        return name
    return ".".join(stack) + "." + name


def _scan_namespaces(masked: str) -> list[tuple[int, list[str]]]:
    """
    Build a (line_start_offset -> namespace_stack) mapping for the file.

    Returns a list of (offset, stack) checkpoints; callers binary-search this to
    determine the active namespace at any text offset.
    """
    checkpoints: list[tuple[int, list[str]]] = [(0, [])]
    stack: list[str] = []
    offset = 0
    for line in masked.splitlines(keepends=True):
        m_open = _NAMESPACE_OPEN_RE.match(line)
        m_end = _END_RE.match(line)
        if m_open:
            # `namespace A.B` pushes both `A` and `B` so qualified names are exact.
            for part in m_open.group(1).split("."):
                stack.append(part)
            checkpoints.append((offset + len(line), list(stack)))
        elif m_end:
            name = m_end.group(1)
            if name is None:
                if stack:
                    stack.pop()
            else:
                # Pop as many segments as the `end A.B` names, best-effort.
                parts = name.split(".")
                for _ in parts:
                    if stack:
                        stack.pop()
            checkpoints.append((offset + len(line), list(stack)))
        offset += len(line)
    return checkpoints


def _stack_at(checkpoints: list[tuple[int, list[str]]], offset: int) -> list[str]:
    """Return the namespace stack active at the given text offset."""
    # Linear scan is fine: checkpoints are bounded by the number of namespace/end lines.
    active: list[str] = []
    for cp_off, stk in checkpoints:
        if cp_off <= offset:
            active = stk
        else:
            break
    return active


def scan_file(path: pathlib.Path) -> dict:
    """Scan one Lean source file and return its proof-debt findings."""
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    masked = _mask_lean_comments_and_strings(text)
    rel = path.relative_to(REPO_ROOT).as_posix()

    checkpoints = _scan_namespaces(masked)

    sorries: list[dict] = []
    for m in _SORRY_RE.finditer(masked):
        line, col = _line_col(text, m.start())
        sorries.append({"file": rel, "line": line, "col": col})

    admits: list[dict] = []
    for m in _ADMIT_RE.finditer(masked):
        line, col = _line_col(text, m.start())
        admits.append({"file": rel, "line": line, "col": col})

    axioms: list[dict] = []
    allowed_here = ALLOWED_AXIOMS.get(rel, set())
    for m in _AXIOM_RE.finditer(masked):
        local_name = m.group(1)
        stk = _stack_at(checkpoints, m.start())
        qualified = _qualified(stk, local_name)
        line, _ = _line_col(text, m.start())
        axioms.append(
            {
                "name": local_name,
                "qualified": qualified,
                "file": rel,
                "line": line,
                "allowed": local_name in allowed_here,
            }
        )

    opaques: list[dict] = []
    for m in _OPAQUE_LINE_RE.finditer(masked):
        local_name = m.group(1)
        stk = _stack_at(checkpoints, m.start())
        qualified = _qualified(stk, local_name)
        line, _ = _line_col(text, m.start())
        opaques.append({"name": local_name, "qualified": qualified, "file": rel, "line": line})

    unsafes: list[dict] = []
    for m in _UNSAFE_RE.finditer(masked):
        line, _ = _line_col(text, m.start())
        unsafes.append({"file": rel, "line": line})

    natives: list[dict] = []
    for m in _NATIVE_DECIDE_RE.finditer(masked):
        line, col = _line_col(text, m.start())
        natives.append({"file": rel, "line": line, "col": col})

    return {
        "sorry": sorries,
        "admit": admits,
        "axiom": axioms,
        "opaque": opaques,
        "unsafe": unsafes,
        "native_decide": natives,
    }


def collect(report_files: bool = False) -> dict:
    """Walk the repo and aggregate proof-debt findings into a single report."""
    scanned = 0
    sorry_locs: list[dict] = []
    admit_locs: list[dict] = []
    axioms_all: list[dict] = []
    opaques_all: list[dict] = []
    unsafes_all: list[dict] = []
    natives_all: list[dict] = []

    for path in _iter_lean_files():
        scanned += 1
        try:
            findings = scan_file(path)
        except OSError:
            continue
        sorry_locs.extend(findings["sorry"])
        admit_locs.extend(findings["admit"])
        axioms_all.extend(findings["axiom"])
        opaques_all.extend(findings["opaque"])
        unsafes_all.extend(findings["unsafe"])
        natives_all.extend(findings["native_decide"])

    unauthorized_axioms = [a for a in axioms_all if not a["allowed"]]

    report = {
        "repo": "gondlin",
        "scanned_files": scanned,
        "totals": {
            "sorry": len(sorry_locs),
            "admit": len(admit_locs),
            "axiom": len(axioms_all),
            "opaque": len(opaques_all),
            "unsafe": len(unsafes_all),
            "native_decide": len(natives_all),
        },
        "axioms": axioms_all,
        "unauthorized_axioms": unauthorized_axioms,
        "sorry_locations": sorry_locs,
        "admit_locations": admit_locs,
        "opaque_locations": opaques_all,
        "unsafe_locations": unsafes_all,
        "native_decide_locations": natives_all,
    }
    return report


def render_text(report: dict) -> str:
    """Render the proof-debt report as a plain text summary."""
    lines: list[str] = []
    lines.append(f"Gondlin proof debt ({report['scanned_files']} Lean files scanned)")
    lines.append("")
    t = report["totals"]
    lines.append(f"  sorry          : {t['sorry']}")
    lines.append(f"  admit          : {t['admit']}")
    lines.append(f"  axiom          : {t['axiom']}")
    lines.append(f"  opaque         : {t['opaque']}")
    lines.append(f"  unsafe         : {t['unsafe']}")
    lines.append(f"  native_decide  : {t['native_decide']}")
    lines.append("")

    if report["axioms"]:
        lines.append("Axioms:")
        for a in report["axioms"]:
            tag = "OK" if a["allowed"] else "UNAUTHORIZED"
            lines.append(f"  [{tag}] {a['qualified']}  ({a['file']}:{a['line']})")
        lines.append("")

    if report["unauthorized_axioms"]:
        lines.append(f"UNAUTHORIZED AXIOMS: {len(report['unauthorized_axioms'])}")
        for a in report["unauthorized_axioms"]:
            lines.append(f"  {a['qualified']}  ({a['file']}:{a['line']})")
        lines.append("")

    if report["sorry_locations"]:
        lines.append("sorry locations:")
        for s in report["sorry_locations"]:
            lines.append(f"  {s['file']}:{s['line']}:{s['col']}")
        lines.append("")

    if report["admit_locations"]:
        lines.append("admit locations:")
        for s in report["admit_locations"]:
            lines.append(f"  {s['file']}:{s['line']}:{s['col']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _compare_baseline(current: dict, baseline_path: pathlib.Path) -> list[str]:
    """Return a list of regression messages versus a previously serialized report."""
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"failed to read baseline {baseline_path}: {e}"]

    regressions: list[str] = []
    base_totals = baseline.get("totals", {})
    cur_totals = current.get("totals", {})
    for key in ("sorry", "admit", "axiom", "opaque", "unsafe", "native_decide"):
        base = int(base_totals.get(key, 0))
        cur = int(cur_totals.get(key, 0))
        if cur > base:
            regressions.append(f"{key} increased: {base} -> {cur}")
    return regressions


def main() -> int:
    """CLI entry point for the proof-debt scanner."""
    ap = argparse.ArgumentParser(description="Gondlin proof-debt scanner.")
    ap.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on unauthorized axioms or any sorry/admit.",
    )
    ap.add_argument(
        "--baseline",
        type=pathlib.Path,
        default=None,
        help="Optional baseline JSON report; fail if any debt category regressed.",
    )
    args = ap.parse_args()

    report = collect()

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report), end="")

    exit_code = 0

    if args.strict:
        if report["unauthorized_axioms"]:
            print(
                f"FAIL: {len(report['unauthorized_axioms'])} unauthorized axiom(s).",
                file=sys.stderr,
            )
            exit_code = 1
        if report["totals"]["sorry"] > 0:
            print(f"FAIL: {report['totals']['sorry']} sorry occurrence(s).", file=sys.stderr)
            exit_code = 1
        if report["totals"]["admit"] > 0:
            print(f"FAIL: {report['totals']['admit']} admit occurrence(s).", file=sys.stderr)
            exit_code = 1

    if args.baseline is not None:
        regressions = _compare_baseline(report, args.baseline)
        if regressions:
            for r in regressions:
                print(f"REGRESSION: {r}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
