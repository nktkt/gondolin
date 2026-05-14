import type { Metadata } from "next";

import { siteConfig } from "@/lib/site-config";
import Breadcrumbs from "@/components/site/breadcrumbs";
import Pager from "@/components/site/pager";
import LayerGraph from "@/components/site/layer-graph";
import CodeStatsPanel from "@/components/site/code-stats-panel";

const SLUG = "architecture/graphs";

export const metadata: Metadata = {
  title: "Module graphs",
  description:
    "An interactive view of the TorchLean Lean module graph — inter-layer import structure, codebase statistics, and dependency hubs.",
};

export default function GraphsPage() {
  return (
    <div className="flex gap-10">
      <article className="min-w-0 flex-1 max-w-3xl">
        <Breadcrumbs slug={SLUG} />

        <header className="mt-4 mb-8">
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-foreground">
            Module graphs
          </h1>
          <p className="mt-2 text-muted-foreground text-lg">
            An interactive view of the {siteConfig.name} Lean module graph —
            inter-layer import structure, codebase statistics, and dependency
            hubs.
          </p>
        </header>

        <div className="docs-prose">
          <p className="leading-relaxed text-foreground/90 mb-4">
            {siteConfig.name} is organized into layers that import one another
            in a deliberate order: pure <code>NN.Spec</code> definitions flow
            into the <code>NN.IR</code> graph, the <code>NN.Runtime</code>{" "}
            executes them, and <code>NN.Proofs</code> /{" "}
            <code>NN.MLTheory</code> / <code>NN.Verification</code> tie the
            executable and mathematical sides together. The graph below is a
            static snapshot of that structure, generated from the repository
            dependency audit.
          </p>

          <h2 className="group scroll-mt-24 mt-10 mb-3 pb-2 text-2xl font-semibold tracking-tight text-foreground border-b border-border/60">
            Inter-layer dependency graph
          </h2>
          <p className="leading-relaxed text-foreground/90 mb-4">
            Each node is a top-level layer; each chord is an import edge between
            two different layers. Hover or focus a node to isolate its
            dependencies; click to pin the selection.
          </p>
          <div className="my-6">
            <LayerGraph />
          </div>

          <h2 className="group scroll-mt-24 mt-10 mb-3 pb-2 text-2xl font-semibold tracking-tight text-foreground border-b border-border/60">
            Codebase statistics
          </h2>
          <div className="my-6">
            <CodeStatsPanel />
          </div>
        </div>

        <div className="mt-12">
          <Pager slug={SLUG} />
        </div>
      </article>
    </div>
  );
}
