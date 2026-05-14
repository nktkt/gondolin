"use client";

import { useMemo, useState } from "react";
import { motion } from "motion/react";
import { Circle, GitBranch, Layers } from "lucide-react";

import { dependencyData } from "@/lib/dependency-data";
import { cn } from "@/lib/utils";

/**
 * Interactive radial dependency graph of the Lean module *layers*.
 *
 * Layout: every layer node sits on a circle, so each inter-layer import
 * edge is a chord drawn as a quadratic bezier curved toward the centre.
 * 18 nodes — no force simulation needed, positions are pure trig.
 */

// ---------------------------------------------------------------------------
// Static derivation (module scope — independent of props/state)
// ---------------------------------------------------------------------------

const VIEW = 800; // square viewBox
const CENTER = VIEW / 2;
const RADIUS = 300; // node ring radius
const MIN_NODE = 9;
const MAX_NODE = 34;

type Category =
  | "spec"
  | "runtime"
  | "theory"
  | "examples"
  | "infra";

/** Group layers into a small, restrained palette of categories. */
const CATEGORY_OF: Record<string, Category> = {
  "NN.Spec": "spec",
  "NN.GraphSpec": "spec",
  "NN.IR": "spec",
  "NN.Tensor": "spec",
  "NN.Floats": "spec",
  "NN.Runtime": "runtime",
  "NN.API": "runtime",
  "NN.Entrypoint": "runtime",
  "NN.Proofs": "theory",
  "NN.MLTheory": "theory",
  "NN.Verification": "theory",
  "NN.Examples": "examples",
  "NN.Tests": "examples",
  "NN.CI": "infra",
  "Widgets": "infra",
  "blueprint": "infra",
  "Library": "infra",
  "NN": "infra",
};

const CATEGORY_META: Record<
  Category,
  { label: string; color: string }
> = {
  // Colours expressed as raw HSL so they theme consistently and read in
  // both light and dark mode.
  spec: { label: "Spec & IR", color: "hsl(217 91% 60%)" },
  runtime: { label: "Runtime & API", color: "hsl(160 84% 39%)" },
  theory: { label: "Proofs & Theory", color: "hsl(38 92% 50%)" },
  examples: { label: "Examples & Tests", color: "hsl(280 65% 60%)" },
  infra: { label: "Infra & Tooling", color: "hsl(220 9% 55%)" },
};

function categoryOf(layer: string): Category {
  return CATEGORY_OF[layer] ?? "infra";
}

type LayerNode = {
  layer: string;
  category: Category;
  color: string;
  x: number;
  y: number;
  /** node circle radius, scaled by lines of code */
  r: number;
  files: number;
  lines: number;
  selfLoop: number;
  inCount: number;
  outCount: number;
  /** total non-self edges incident to this node */
  degree: number;
};

type LayerLink = {
  id: string;
  src: string;
  dst: string;
  count: number;
  d: string;
  width: number;
};

// ---------------------------------------------------------------------------

export default function LayerGraph() {
  const [hovered, setHovered] = useState<string | null>(null);
  const [pinned, setPinned] = useState<string | null>(null);

  const active = hovered ?? pinned;

  const { nodes, links, nodeByLayer } = useMemo(() => {
    const edges = dependencyData.layer_edges;
    const sizes = dependencyData.code_stats.layer_sizes;

    // Layers that actually participate in the inter-layer graph.
    const present = Array.from(
      new Set(edges.flatMap((e) => [e.src_layer, e.dst_layer])),
    );

    const sizeOf = new Map(sizes.map((s) => [s.layer, s]));
    const maxLines = Math.max(
      ...present.map((l) => sizeOf.get(l)?.lines ?? 1),
    );
    const minLines = Math.min(
      ...present.map((l) => sizeOf.get(l)?.lines ?? 1),
    );

    // Order nodes by category so related layers sit together on the ring,
    // then by size within a category.
    const catOrder: Category[] = [
      "spec",
      "runtime",
      "theory",
      "examples",
      "infra",
    ];
    const ordered = [...present].sort((a, b) => {
      const ca = catOrder.indexOf(categoryOf(a));
      const cb = catOrder.indexOf(categoryOf(b));
      if (ca !== cb) return ca - cb;
      const la = sizeOf.get(a)?.lines ?? 0;
      const lb = sizeOf.get(b)?.lines ?? 0;
      return lb - la;
    });

    const n = ordered.length;
    const nodes: LayerNode[] = ordered.map((layer, i) => {
      // Start at top (-90deg) and go clockwise.
      const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
      const size = sizeOf.get(layer);
      const lines = size?.lines ?? 1;
      const files = size?.files ?? 0;

      // sqrt scale so giant layers don't dwarf everything.
      const t =
        maxLines === minLines
          ? 0.5
          : (Math.sqrt(lines) - Math.sqrt(minLines)) /
            (Math.sqrt(maxLines) - Math.sqrt(minLines));
      const r = MIN_NODE + t * (MAX_NODE - MIN_NODE);

      const selfLoop =
        edges.find(
          (e) => e.src_layer === layer && e.dst_layer === layer,
        )?.count ?? 0;
      const inCount = edges
        .filter((e) => e.dst_layer === layer && e.src_layer !== layer)
        .reduce((sum, e) => sum + e.count, 0);
      const outCount = edges
        .filter((e) => e.src_layer === layer && e.dst_layer !== layer)
        .reduce((sum, e) => sum + e.count, 0);
      const degree = edges.filter(
        (e) =>
          e.src_layer !== e.dst_layer &&
          (e.src_layer === layer || e.dst_layer === layer),
      ).length;

      const cat = categoryOf(layer);
      return {
        layer,
        category: cat,
        color: CATEGORY_META[cat].color,
        x: CENTER + RADIUS * Math.cos(angle),
        y: CENTER + RADIUS * Math.sin(angle),
        r,
        files,
        lines,
        selfLoop,
        inCount,
        outCount,
        degree,
      };
    });

    const nodeByLayer = new Map(nodes.map((nd) => [nd.layer, nd]));

    // Inter-layer edges only — self loops excluded from the drawing.
    const interEdges = edges.filter((e) => e.src_layer !== e.dst_layer);
    const maxCount = Math.max(...interEdges.map((e) => e.count));

    const links: LayerLink[] = interEdges
      // draw fat edges first so thin ones land on top and stay visible
      .sort((a, b) => b.count - a.count)
      .map((e) => {
        const s = nodeByLayer.get(e.src_layer)!;
        const d = nodeByLayer.get(e.dst_layer)!;
        // Quadratic bezier whose control point is pulled toward the
        // centre — amount proportional to chord length so short chords
        // stay nearly straight and long ones bow inward.
        const mx = (s.x + d.x) / 2;
        const my = (s.y + d.y) / 2;
        const toCenterX = CENTER - mx;
        const toCenterY = CENTER - my;
        const cx = mx + toCenterX * 0.55;
        const cy = my + toCenterY * 0.55;
        const width =
          1 + (Math.sqrt(e.count) / Math.sqrt(maxCount)) * 5;
        return {
          id: `${e.src_layer}->${e.dst_layer}`,
          src: e.src_layer,
          dst: e.dst_layer,
          count: e.count,
          d: `M ${s.x.toFixed(1)} ${s.y.toFixed(1)} Q ${cx.toFixed(
            1,
          )} ${cy.toFixed(1)} ${d.x.toFixed(1)} ${d.y.toFixed(1)}`,
          width,
        };
      });

    return { nodes, links, nodeByLayer };
  }, []);

  const activeNode = active ? nodeByLayer.get(active) ?? null : null;

  // Pre-compute which layers are adjacent to the active one.
  const neighbors = useMemo(() => {
    if (!active) return null;
    const set = new Set<string>([active]);
    for (const l of links) {
      if (l.src === active) set.add(l.dst);
      if (l.dst === active) set.add(l.src);
    }
    return set;
  }, [active, links]);

  return (
    <div className="rounded-xl border bg-card text-card-foreground">
      <div className="flex flex-col gap-1 border-b px-5 py-4">
        <div className="flex items-center gap-2">
          <GitBranch className="size-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold tracking-tight">
            Layer dependency graph
          </h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Inter-layer imports across the Lean codebase. Hover or focus a
          layer to trace its dependencies; click to pin.
        </p>
      </div>

      <div className="grid gap-4 p-4 lg:grid-cols-[1fr_15rem]">
        {/* ---- SVG graph ------------------------------------------------ */}
        <div className="relative">
          <svg
            viewBox={`0 0 ${VIEW} ${VIEW}`}
            className="h-auto w-full select-none overflow-visible"
            role="group"
            aria-label="Interactive layer dependency graph"
          >
            {/* edges */}
            <g fill="none" strokeLinecap="round">
              {links.map((link) => {
                const incident =
                  active != null &&
                  (link.src === active || link.dst === active);
                const dimmed = active != null && !incident;
                return (
                  <motion.path
                    key={link.id}
                    d={link.d}
                    stroke={
                      incident
                        ? CATEGORY_META[
                            categoryOf(
                              link.src === active ? link.dst : link.src,
                            )
                          ].color
                        : "var(--muted-foreground)"
                    }
                    initial={false}
                    animate={{
                      opacity: dimmed ? 0.04 : incident ? 0.7 : 0.16,
                      strokeWidth: incident
                        ? link.width + 0.75
                        : link.width,
                    }}
                    transition={{ duration: 0.2, ease: "easeOut" }}
                  />
                );
              })}
            </g>

            {/* nodes */}
            <g>
              {nodes.map((node) => {
                const isActive = node.layer === active;
                const isNeighbor =
                  neighbors?.has(node.layer) ?? false;
                const dimmed = active != null && !isNeighbor;
                const isPinned = node.layer === pinned;

                // Place label outside the ring, anchored away from centre.
                const lx = CENTER + (RADIUS + node.r + 12) *
                  Math.cos(
                    Math.atan2(node.y - CENTER, node.x - CENTER),
                  );
                const ly = CENTER + (RADIUS + node.r + 12) *
                  Math.sin(
                    Math.atan2(node.y - CENTER, node.x - CENTER),
                  );
                const anchor: "start" | "middle" | "end" =
                  node.x < CENTER - 8
                    ? "end"
                    : node.x > CENTER + 8
                      ? "start"
                      : "middle";

                return (
                  <motion.g
                    key={node.layer}
                    tabIndex={0}
                    role="button"
                    aria-label={`${node.layer}: ${node.files} files, ${node.lines.toLocaleString()} lines`}
                    aria-pressed={isPinned}
                    className="cursor-pointer outline-none [&:focus-visible_circle]:stroke-foreground"
                    onMouseEnter={() => setHovered(node.layer)}
                    onMouseLeave={() => setHovered(null)}
                    onFocus={() => setHovered(node.layer)}
                    onBlur={() => setHovered(null)}
                    onClick={() =>
                      setPinned((p) =>
                        p === node.layer ? null : node.layer,
                      )
                    }
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setPinned((p) =>
                          p === node.layer ? null : node.layer,
                        );
                      }
                    }}
                    initial={false}
                    animate={{ opacity: dimmed ? 0.28 : 1 }}
                    transition={{ duration: 0.2, ease: "easeOut" }}
                  >
                    {/* pin ring */}
                    {isPinned && (
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={node.r + 5}
                        fill="none"
                        stroke={node.color}
                        strokeWidth={1.5}
                        strokeDasharray="3 3"
                        opacity={0.8}
                      />
                    )}
                    <motion.circle
                      cx={node.x}
                      cy={node.y}
                      fill={node.color}
                      stroke="var(--card)"
                      strokeWidth={2}
                      initial={false}
                      animate={{
                        r: isActive ? node.r + 3 : node.r,
                        fillOpacity:
                          isActive || isNeighbor ? 0.95 : 0.78,
                      }}
                      transition={{ duration: 0.2, ease: "easeOut" }}
                    />
                    <text
                      x={lx}
                      y={ly}
                      textAnchor={anchor}
                      dominantBaseline="middle"
                      className={cn(
                        "font-mono text-[13px] transition-colors",
                        isActive
                          ? "fill-foreground font-semibold"
                          : "fill-muted-foreground",
                      )}
                    >
                      {node.layer}
                    </text>
                  </motion.g>
                );
              })}
            </g>
          </svg>

          {/* hover/pin tooltip panel */}
          {activeNode && (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.18 }}
              className="pointer-events-none absolute left-3 top-3 w-52 rounded-lg border bg-popover/95 p-3 text-popover-foreground shadow-md backdrop-blur"
            >
              <div className="flex items-center gap-2">
                <span
                  className="size-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: activeNode.color }}
                />
                <span className="truncate font-mono text-xs font-semibold">
                  {activeNode.layer}
                </span>
              </div>
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                {CATEGORY_META[activeNode.category].label}
                {pinned === activeNode.layer ? " · pinned" : ""}
              </p>
              <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
                <div>
                  <dt className="text-muted-foreground">Files</dt>
                  <dd className="font-medium tabular-nums">
                    {activeNode.files.toLocaleString()}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Lines</dt>
                  <dd className="font-medium tabular-nums">
                    {activeNode.lines.toLocaleString()}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Imports out</dt>
                  <dd className="font-medium tabular-nums">
                    {activeNode.outCount.toLocaleString()}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Imports in</dt>
                  <dd className="font-medium tabular-nums">
                    {activeNode.inCount.toLocaleString()}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-muted-foreground">
                    Intra-layer imports
                  </dt>
                  <dd className="font-medium tabular-nums">
                    {activeNode.selfLoop.toLocaleString()}
                  </dd>
                </div>
              </dl>
            </motion.div>
          )}
        </div>

        {/* ---- Legend --------------------------------------------------- */}
        <div className="flex flex-col gap-4 text-xs lg:border-l lg:pl-4">
          <div className="flex flex-col gap-2">
            <span className="font-medium text-foreground">
              Layer groups
            </span>
            {(
              Object.entries(CATEGORY_META) as [
                Category,
                (typeof CATEGORY_META)[Category],
              ][]
            ).map(([key, meta]) => (
              <div key={key} className="flex items-center gap-2">
                <span
                  className="size-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: meta.color }}
                />
                <span className="text-muted-foreground">
                  {meta.label}
                </span>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-2 border-t pt-3">
            <span className="font-medium text-foreground">Reading it</span>
            <div className="flex items-start gap-2 text-muted-foreground">
              <Circle className="mt-0.5 size-3.5 shrink-0" />
              <span>Node size — lines of code in that layer.</span>
            </div>
            <div className="flex items-start gap-2 text-muted-foreground">
              <GitBranch className="mt-0.5 size-3.5 shrink-0" />
              <span>Edge width — number of cross-layer imports.</span>
            </div>
            <div className="flex items-start gap-2 text-muted-foreground">
              <Layers className="mt-0.5 size-3.5 shrink-0" />
              <span>
                Self-imports within a layer are omitted from the chords
                and shown in the hover panel instead.
              </span>
            </div>
          </div>

          <p className="border-t pt-3 text-[11px] leading-relaxed text-muted-foreground">
            {links.length} inter-layer edges across {nodes.length}{" "}
            layers.
          </p>
        </div>
      </div>
    </div>
  );
}
