"use client";

import { motion } from "motion/react";

import { AnimatedSection } from "@/components/site/animated-section";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { dependencyData } from "@/lib/dependency-data";
import { cn } from "@/lib/utils";

const { summary, code_stats, top_fan_in, top_fan_out } = dependencyData;
const declarationCounts = code_stats.declaration_counts;

const headlineMetrics: { label: string; value: number }[] = [
  { label: "Modules", value: summary.modules },
  { label: "Import edges", value: summary.import_edges },
  { label: "Declarations", value: code_stats.declarations },
  {
    label: "Theorems & lemmas",
    value: (declarationCounts.theorem ?? 0) + (declarationCounts.lemma ?? 0),
  },
  { label: "Lines of code", value: code_stats.code_lines },
];

const declarationKinds = [
  "def",
  "theorem",
  "lemma",
  "structure",
  "instance",
  "abbrev",
  "inductive",
  "opaque",
  "class",
  "axiom",
] as const;

const sortedDeclarations = declarationKinds
  .map((kind) => ({ kind, count: declarationCounts[kind] ?? 0 }))
  .sort((a, b) => b.count - a.count);

const maxLayerLines = Math.max(
  1,
  ...code_stats.layer_sizes.map((layer) => layer.lines),
);

function HubList({
  title,
  caption,
  entries,
}: {
  title: string;
  caption: string;
  entries: { module: string; count: number }[];
}) {
  const maxCount = Math.max(1, ...entries.map((entry) => entry.count));
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{caption}</CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="flex flex-col gap-1.5">
          {entries.map((entry, index) => (
            <li
              key={entry.module}
              className="flex items-center gap-3 text-xs"
            >
              <span className="w-5 shrink-0 text-right tabular-nums text-muted-foreground/70">
                {index + 1}
              </span>
              <span className="min-w-0 flex-1 truncate font-mono text-foreground">
                {entry.module}
              </span>
              <span className="relative hidden h-1.5 w-16 shrink-0 overflow-hidden rounded-full bg-muted sm:block">
                <span
                  className="absolute inset-y-0 left-0 rounded-full bg-primary/60"
                  style={{ width: `${(entry.count / maxCount) * 100}%` }}
                />
              </span>
              <span className="w-9 shrink-0 text-right font-medium tabular-nums">
                {entry.count}
              </span>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

export function CodeStatsPanel({ className }: { className?: string }) {
  return (
    <div className={cn("flex w-full flex-col gap-10", className)}>
      <AnimatedSection className="flex flex-col gap-3">
        <h2 className="font-heading text-2xl font-semibold tracking-tight">
          Module graph &amp; stats
        </h2>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          A static snapshot of the TorchLean Lean module graph, extracted from
          the repository&apos;s dependency audit. It captures the shape of the
          codebase at audit time &mdash; how many modules and declarations
          exist, how the layers are sized, and which modules sit at the center
          of the import graph.
        </p>
      </AnimatedSection>

      {/* 1. Headline metric row */}
      <AnimatedSection
        delay={0.05}
        className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5"
      >
        {headlineMetrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ delay: 0.05 * index, duration: 0.4 }}
          >
            <Card size="sm" className="h-full">
              <CardContent className="flex flex-col gap-1">
                <span className="font-heading text-2xl font-semibold tabular-nums sm:text-3xl">
                  {metric.value.toLocaleString()}
                </span>
                <span className="text-xs text-muted-foreground">
                  {metric.label}
                </span>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </AnimatedSection>

      {/* 2. Layer sizes bar chart */}
      <AnimatedSection delay={0.05}>
        <Card>
          <CardHeader>
            <CardTitle>Layer sizes</CardTitle>
            <CardDescription>
              Lines of code per architectural layer, with file counts. Bars are
              normalized to the largest layer.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-1.5">
              {code_stats.layer_sizes.map((layer) => (
                <li
                  key={layer.layer}
                  className="flex items-center gap-3 text-xs"
                >
                  <span className="w-28 shrink-0 truncate font-mono text-foreground sm:w-40">
                    {layer.layer}
                  </span>
                  <span className="relative h-4 min-w-0 flex-1 overflow-hidden rounded bg-muted">
                    <span
                      className="absolute inset-y-0 left-0 rounded bg-primary/70"
                      style={{
                        width: `${Math.max(
                          (layer.lines / maxLayerLines) * 100,
                          1.5,
                        )}%`,
                      }}
                    />
                  </span>
                  <span className="w-16 shrink-0 text-right font-medium tabular-nums">
                    {layer.lines.toLocaleString()}
                  </span>
                  <span className="hidden w-16 shrink-0 text-right tabular-nums text-muted-foreground sm:block">
                    {layer.files.toLocaleString()} files
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </AnimatedSection>

      {/* 3. Declaration breakdown */}
      <AnimatedSection delay={0.05}>
        <Card>
          <CardHeader>
            <CardTitle>Declaration breakdown</CardTitle>
            <CardDescription>
              {code_stats.declarations.toLocaleString()} declarations across the
              codebase, by kind.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid grid-cols-1 gap-x-6 gap-y-1.5 sm:grid-cols-2">
              {sortedDeclarations.map(({ kind, count }) => (
                <div
                  key={kind}
                  className="flex items-center gap-3 border-b border-dashed border-border/60 py-1 last:border-0"
                >
                  <span className="flex-1 font-mono text-xs text-foreground">
                    {kind}
                  </span>
                  {kind === "axiom" ? (
                    <Badge variant="secondary" className="font-mono">
                      {count}
                    </Badge>
                  ) : (
                    <span className="text-sm font-medium tabular-nums">
                      {count.toLocaleString()}
                    </span>
                  )}
                </div>
              ))}
            </div>
            <Separator />
            <p className="text-xs leading-relaxed text-muted-foreground">
              <span className="font-medium text-foreground">
                Only {declarationCounts.axiom ?? 0} axioms.
              </span>{" "}
              The axiom count is the trust surface of the development &mdash;
              everything else is built up by definition and proof, so a small
              number here means very little is taken on faith.
            </p>
          </CardContent>
        </Card>
      </AnimatedSection>

      {/* 4. Import hubs */}
      <AnimatedSection delay={0.05} className="flex flex-col gap-3">
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <HubList
            title="Most depended-on"
            caption="Highest fan-in: how many modules import this one."
            entries={top_fan_in.slice(0, 10)}
          />
          <HubList
            title="Broadest importers"
            caption="Highest fan-out: how many modules this one imports."
            entries={top_fan_out.slice(0, 10)}
          />
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Fan-in measures how widely a module is reused &mdash; high fan-in
          modules are foundational and risky to change. Fan-out measures how
          much a module depends on &mdash; high fan-out modules are integration
          points that pull the graph together.
        </p>
      </AnimatedSection>
    </div>
  );
}

export default CodeStatsPanel;
