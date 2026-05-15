#!/usr/bin/env python3
r"""
Gondlin Lean 4 import-graph audit.

Scans every ``.lean`` file under ``NN/`` and answers two questions:

1.  Does the internal import graph contain any cycles? (HARD FAIL by default.)
2.  Does any module reach across Gondlin's architectural layering? Gondlin's
    conventional layering, going from low-level to high-level, is:

        Spec / Floats  ->  IR  ->  Runtime  ->  API
              \           \         \
               +-> Proofs / MLTheory / Verification (cross-cutting; above Spec/IR/Runtime)
                                            \
                                             +-> Examples / Tests (top, sinks only)

    Cross-layer violations are reported as warnings by default so that gradual
    cleanup is possible; ``--strict-layering`` promotes them to hard errors.

The script uses only the Python standard library and follows the same
comment/string masking strategy as ``scripts/checks/api_surface.py`` (read,
do not import) so a stray ``import`` inside a string literal or block comment
cannot leak into the graph.

CLI:

    --json              Emit the full graph metadata (modules, edges, layer
                        violations, cycles) as JSON. Implies machine output.
    --show-violations   In text mode, list every layer warning instead of just
                        counting them.
    --strict-layering   Treat layer warnings as errors (exit 1 if any).
    --graphviz          Emit a DOT file on stdout, internal nodes only.

Exit codes:

    0   No cycles; layering OK (or only warnings, in non-strict mode).
    1   Cycles detected, or layer violations under ``--strict-layering``.
    2   Usage/setup error (e.g. ``NN/`` not found).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Iterable


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NN_ROOT = REPO_ROOT / "NN"

# Anchored to start-of-line (after optional Lean 4 module-system prefixes:
# ``public ``, ``private ``, ``meta ``). Lean module names are dotted
# identifiers; we accept letters, digits, ``_`` and ``.``.
IMPORT_RE = re.compile(
    r"^(?:public\s+|private\s+|meta\s+)*import\s+([A-Za-z][\w.]*)"
)


# ---------------------------------------------------------------------------
# Comment / string masking (cloned from scripts/checks/api_surface.py — we do
# not import that module so this script stays self-contained.)
# ---------------------------------------------------------------------------


def _mask_comments_and_strings(text: str) -> str:
    """Replace Lean comments/docstrings/strings with spaces, preserving newlines.

    Block comments ``/- ... -/`` may nest. Line comments ``--`` run to
    end-of-line. String literals are masked so that the literal text
    ``"import X"`` inside a string cannot be mistaken for an import directive.
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
# Module-name resolution
# ---------------------------------------------------------------------------


def _module_of_path(path: pathlib.Path) -> str:
    """Convert a Lean source path under the repo root into a dotted module name."""
    rel = path.relative_to(REPO_ROOT)
    return ".".join(rel.with_suffix("").parts)


def _is_internal_module(module: str) -> bool:
    """An import is 'internal' if it is the top-level ``NN`` module or under it."""
    return module == "NN" or module.startswith("NN.")


def _imports_of(path: pathlib.Path) -> list[str]:
    """Return the imports declared in ``path`` (after masking comments/strings)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    masked = _mask_comments_and_strings(text)
    out: list[str] = []
    for line in masked.splitlines():
        m = IMPORT_RE.match(line)
        if not m:
            continue
        out.append(m.group(1))
    return out


# ---------------------------------------------------------------------------
# Layering rules
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LayerRule:
    """A single layering invariant for a Gondlin source subtree.

    ``source_prefix`` matches the dotted module path that the rule applies to
    (e.g. ``"NN.Spec."``). ``forbidden_prefixes`` is the list of import
    prefixes the source must *not* depend on.
    """

    source_prefix: str
    forbidden_prefixes: tuple[str, ...]
    rationale: str


LAYER_RULES: tuple[LayerRule, ...] = (
    LayerRule(
        source_prefix="NN.Spec.",
        forbidden_prefixes=("NN.Runtime.", "NN.API.", "NN.Examples.", "NN.Tests."),
        rationale="Spec is the bottom layer; it must not depend on Runtime/API/Examples/Tests.",
    ),
    LayerRule(
        source_prefix="NN.IR.",
        forbidden_prefixes=("NN.Runtime.", "NN.API.", "NN.Examples.", "NN.Tests."),
        rationale="IR sits below Runtime; it must not depend on Runtime/API/Examples/Tests.",
    ),
    LayerRule(
        source_prefix="NN.Floats.",
        forbidden_prefixes=("NN.Runtime.", "NN.API.", "NN.Examples.", "NN.Tests."),
        rationale="Floats is a low-level numeric layer; it must not depend on Runtime/API/Examples/Tests.",
    ),
    LayerRule(
        source_prefix="NN.Runtime.",
        forbidden_prefixes=("NN.API.", "NN.Examples.", "NN.Tests."),
        rationale="Runtime must not import the public facade or Examples/Tests.",
    ),
    LayerRule(
        source_prefix="NN.Proofs.",
        forbidden_prefixes=("NN.API.", "NN.Examples.", "NN.Tests."),
        rationale="Proofs sit above Spec/IR/Runtime; they must not import API/Examples/Tests.",
    ),
    LayerRule(
        source_prefix="NN.MLTheory.",
        forbidden_prefixes=("NN.API.", "NN.Examples.", "NN.Tests."),
        rationale="MLTheory is a theory layer; it must not import API/Examples/Tests.",
    ),
    LayerRule(
        source_prefix="NN.Verification.",
        forbidden_prefixes=("NN.Tests.", "NN.Examples."),
        rationale="Verification may import broadly but is a leaf relative to Examples/Tests.",
    ),
    LayerRule(
        source_prefix="NN.API.",
        forbidden_prefixes=("NN.Examples.", "NN.Tests."),
        rationale="API is the public facade; it must not import Examples or Tests.",
    ),
)


@dataclass(frozen=True)
class LayerViolation:
    """One ``source -> target`` edge that crosses a layering boundary."""

    source: str
    target: str
    rule: LayerRule


def _check_layering(
    edges: Iterable[tuple[str, str]],
) -> list[LayerViolation]:
    """Return every edge that crosses a layering invariant, in stable order."""
    violations: list[LayerViolation] = []
    for src, tgt in edges:
        for rule in LAYER_RULES:
            if not src.startswith(rule.source_prefix):
                continue
            for forbidden in rule.forbidden_prefixes:
                if tgt.startswith(forbidden):
                    violations.append(LayerViolation(src, tgt, rule))
                    break
    violations.sort(key=lambda v: (v.source, v.target))
    return violations


# ---------------------------------------------------------------------------
# Cycle detection (iterative Tarjan SCC)
# ---------------------------------------------------------------------------


def _tarjan_sccs(graph: dict[str, list[str]]) -> list[list[str]]:
    """Return every strongly-connected component, using iterative Tarjan.

    The classical recursive presentation can blow the Python recursion limit on
    the >800-file Gondlin tree, so we drive the DFS by an explicit work stack.
    Returned SCCs are in reverse topological order; we re-sort the list by
    minimum member name for deterministic output.
    """
    index_counter = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    result: list[list[str]] = []

    # Iterative DFS: each work-stack frame is (node, iterator-over-neighbors).
    for root in graph:
        if root in indices:
            continue
        work: list[tuple[str, list[str], int]] = []
        # Initialize the root frame.
        indices[root] = index_counter[0]
        lowlinks[root] = index_counter[0]
        index_counter[0] += 1
        stack.append(root)
        on_stack.add(root)
        work.append((root, graph.get(root, []), 0))

        while work:
            node, neighbors, i = work[-1]
            if i < len(neighbors):
                work[-1] = (node, neighbors, i + 1)
                child = neighbors[i]
                if child not in graph:
                    # External (e.g. Mathlib) — not part of the SCC computation.
                    continue
                if child not in indices:
                    indices[child] = index_counter[0]
                    lowlinks[child] = index_counter[0]
                    index_counter[0] += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, graph.get(child, []), 0))
                elif child in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[child])
            else:
                # Post-order: propagate lowlink to caller, then pop component if
                # we are at the root of an SCC.
                if lowlinks[node] == indices[node]:
                    component: list[str] = []
                    while True:
                        w = stack.pop()
                        on_stack.discard(w)
                        component.append(w)
                        if w == node:
                            break
                    component.sort()
                    result.append(component)
                work.pop()
                if work:
                    parent_node = work[-1][0]
                    lowlinks[parent_node] = min(lowlinks[parent_node], lowlinks[node])

    result.sort(key=lambda c: c[0])
    return result


def _cycles(
    graph: dict[str, list[str]],
) -> list[list[str]]:
    """Return every SCC of size > 1 plus any self-loops.

    A self-loop (``import M`` inside file ``M``) is a 1-node SCC with an edge
    back to itself; Tarjan with ``elif child in on_stack`` already detects this
    because ``child == node`` and ``node`` is on the stack while expanding.
    Belt-and-braces, we also flag explicit self-edges that Tarjan classifies
    as singleton SCCs because the iterative loop visits the neighbor only after
    re-entering the frame.
    """
    sccs = _tarjan_sccs(graph)
    cycles: list[list[str]] = []
    for scc in sccs:
        if len(scc) > 1:
            cycles.append(scc)
            continue
        # Singleton SCC: only a cycle if the node has an explicit self-edge.
        node = scc[0]
        if node in graph.get(node, []):
            cycles.append(scc)
    return cycles


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


@dataclass
class ImportGraph:
    """Resolved import graph for the ``NN/`` tree."""

    # All internal modules (one per ``.lean`` file under NN/, plus the top-level NN itself).
    modules: list[str] = field(default_factory=list)
    # Adjacency list: source-module -> list of target modules.
    # ``internal_edges`` only contains edges where the target is also a known
    # internal module; this is the graph we run cycle detection on.
    internal_edges: dict[str, list[str]] = field(default_factory=dict)
    # ``mathlib_edges`` counts (source, target) pairs where the target starts
    # with ``Mathlib`` — tracked separately and excluded from the layering and
    # cycle checks because Mathlib is an upstream dependency.
    mathlib_edges: list[tuple[str, str]] = field(default_factory=list)
    # ``other_external_edges`` captures imports such as ``Lean.``, ``Std.``,
    # ``Init.``, etc. — kept for the JSON dump so a reader can see "this many
    # imports went outside both Gondlin and Mathlib".
    other_external_edges: list[tuple[str, str]] = field(default_factory=list)


def build_graph() -> ImportGraph:
    """Walk ``NN/`` and assemble the resolved import graph."""
    if not NN_ROOT.exists():
        raise FileNotFoundError(f"Gondlin NN/ tree not found at {NN_ROOT}")

    # Discover every internal Lean file. We include the top-level ``NN.lean``
    # (resolved as module ``NN``) plus everything under ``NN/``.
    files: list[pathlib.Path] = []
    top_level = REPO_ROOT / "NN.lean"
    if top_level.exists():
        files.append(top_level)
    for path in sorted(NN_ROOT.rglob("*.lean")):
        files.append(path)

    modules = sorted({_module_of_path(p) for p in files})
    module_set = set(modules)

    internal_edges: dict[str, list[str]] = {m: [] for m in modules}
    mathlib_edges: list[tuple[str, str]] = []
    other_external_edges: list[tuple[str, str]] = []

    for path in files:
        src = _module_of_path(path)
        seen_targets: set[str] = set()
        for target in _imports_of(path):
            # Self-imports are degenerate; record them so cycle detection can fire.
            if target in seen_targets:
                continue
            seen_targets.add(target)

            if _is_internal_module(target):
                # Only record internal edges that resolve to a known file. If a
                # target does not correspond to an on-disk file, it is almost
                # always a typo or stale import — surface it under
                # ``other_external_edges`` so a maintainer can audit it.
                if target in module_set:
                    internal_edges[src].append(target)
                else:
                    other_external_edges.append((src, target))
                continue

            if target == "Mathlib" or target.startswith("Mathlib."):
                mathlib_edges.append((src, target))
                continue

            other_external_edges.append((src, target))

    # Deduplicate adjacency lists while preserving insertion order.
    for src in internal_edges:
        seen: set[str] = set()
        deduped: list[str] = []
        for tgt in internal_edges[src]:
            if tgt in seen:
                continue
            seen.add(tgt)
            deduped.append(tgt)
        internal_edges[src] = deduped

    return ImportGraph(
        modules=modules,
        internal_edges=internal_edges,
        mathlib_edges=mathlib_edges,
        other_external_edges=other_external_edges,
    )


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _format_text(
    graph: ImportGraph,
    cycles: list[list[str]],
    violations: list[LayerViolation],
    *,
    show_violations: bool,
    strict: bool,
) -> str:
    """Human-readable summary of the audit."""
    total_internal = sum(len(v) for v in graph.internal_edges.values())
    lines: list[str] = []
    lines.append("Gondlin Lean import audit")
    lines.append(f"  modules:        {len(graph.modules)}")
    lines.append(f"  internal edges: {total_internal}")
    lines.append(f"  mathlib edges:  {len(graph.mathlib_edges)}")
    lines.append(f"  other external: {len(graph.other_external_edges)}")
    lines.append(f"  cycles:         {len(cycles)}")
    lines.append(
        f"  layer issues:   {len(violations)} "
        f"({'errors' if strict else 'warnings'})"
    )

    if cycles:
        lines.append("")
        lines.append("Cycles (each line lists the modules in an SCC):")
        for c in cycles:
            lines.append("  - " + " -> ".join(c) + " -> " + c[0])

    if violations:
        if show_violations:
            lines.append("")
            label = "ERROR" if strict else "warn"
            lines.append("Layering issues:")
            for v in violations:
                lines.append(
                    f"  [{label}] {v.source}  ->  {v.target}    ({v.rule.rationale})"
                )
        else:
            lines.append("")
            lines.append("Pass --show-violations to list every layering issue.")

    return "\n".join(lines) + "\n"


def _format_json(
    graph: ImportGraph,
    cycles: list[list[str]],
    violations: list[LayerViolation],
) -> str:
    """Full machine-readable dump suitable for piping into ``jq``/``json.tool``."""
    payload = {
        "summary": {
            "module_count": len(graph.modules),
            "internal_edge_count": sum(len(v) for v in graph.internal_edges.values()),
            "mathlib_edge_count": len(graph.mathlib_edges),
            "other_external_edge_count": len(graph.other_external_edges),
            "cycle_count": len(cycles),
            "layer_violation_count": len(violations),
        },
        "modules": graph.modules,
        "internal_edges": {
            src: sorted(tgts) for src, tgts in graph.internal_edges.items()
        },
        "mathlib_edges": sorted(
            [{"source": s, "target": t} for s, t in graph.mathlib_edges],
            key=lambda e: (e["source"], e["target"]),
        ),
        "other_external_edges": sorted(
            [{"source": s, "target": t} for s, t in graph.other_external_edges],
            key=lambda e: (e["source"], e["target"]),
        ),
        "cycles": cycles,
        "layer_violations": [
            {
                "source": v.source,
                "target": v.target,
                "source_prefix": v.rule.source_prefix,
                "rationale": v.rule.rationale,
            }
            for v in violations
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _format_graphviz(graph: ImportGraph) -> str:
    """DOT file for the internal-only graph; nodes labeled by short module name.

    Designed for ``dot -Tsvg`` on a developer machine. We deliberately omit
    Mathlib edges so the diagram stays legible — there are typically dozens of
    Mathlib imports per file.
    """
    lines = [
        "digraph GondlinImports {",
        "  rankdir=LR;",
        '  graph [splines=true, overlap=false];',
        '  node [shape=box, fontname="Helvetica", fontsize=10];',
    ]
    # Cluster nodes by their second-level subtree (e.g. ``NN.Spec``, ``NN.IR``)
    # so the output is readable. Top-level ``NN`` lives in its own cluster.
    clusters: dict[str, list[str]] = {}
    for module in graph.modules:
        parts = module.split(".")
        cluster_key = parts[1] if len(parts) > 1 else "(root)"
        clusters.setdefault(cluster_key, []).append(module)

    for cluster, members in sorted(clusters.items()):
        safe = cluster.replace("-", "_")
        lines.append(f'  subgraph cluster_{safe} {{')
        lines.append(f'    label="NN.{cluster}";')
        lines.append('    style=rounded;')
        for module in sorted(members):
            lines.append(f'    "{module}";')
        lines.append("  }")

    for src in sorted(graph.internal_edges):
        for tgt in sorted(graph.internal_edges[src]):
            lines.append(f'  "{src}" -> "{tgt}";')

    lines.append("}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Parse CLI flags, run the audit, return an exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the audit as JSON (machine-readable).",
    )
    parser.add_argument(
        "--show-violations",
        action="store_true",
        help="List every layering issue in text mode (default: counts only).",
    )
    parser.add_argument(
        "--strict-layering",
        action="store_true",
        help="Treat layering issues as errors (exit 1 if any).",
    )
    parser.add_argument(
        "--graphviz",
        action="store_true",
        help="Emit a DOT file on stdout (internal nodes only).",
    )
    args = parser.parse_args(argv)

    try:
        graph = build_graph()
    except FileNotFoundError as exc:
        print(f"lean_imports_audit: {exc}", file=sys.stderr)
        return 2

    cycles = _cycles(graph.internal_edges)
    violations = _check_layering(
        (src, tgt)
        for src, tgts in graph.internal_edges.items()
        for tgt in tgts
    )

    if args.graphviz:
        sys.stdout.write(_format_graphviz(graph))
        return 0

    if args.json:
        sys.stdout.write(_format_json(graph, cycles, violations))
    else:
        sys.stdout.write(
            _format_text(
                graph,
                cycles,
                violations,
                show_violations=args.show_violations,
                strict=args.strict_layering,
            )
        )

    # Exit policy:
    #   - cycles ALWAYS fail (cycles break Lean's build, never warnings).
    #   - layering issues fail only under --strict-layering.
    if cycles:
        return 1
    if violations and args.strict_layering:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
