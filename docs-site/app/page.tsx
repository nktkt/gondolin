import Link from "next/link";
import { ArrowRight, ExternalLink } from "lucide-react";

import { AnimatedSection } from "@/components/site/animated-section";
import { CodePreview } from "@/components/site/code-preview";
import { FeatureGrid } from "@/components/site/feature-grid";
import { Hero } from "@/components/site/hero";
import { LayersDiagram } from "@/components/site/layers-diagram";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { siteConfig } from "@/lib/site-config";

export default function Home() {
  return (
    <div className="flex flex-col">
      <Hero />

      <AnimatedSection className="border-t border-border/60 bg-muted/20">
        <FeatureGrid />
      </AnimatedSection>

      <AnimatedSection className="border-t border-border/60">
        <div className="mx-auto max-w-screen-xl px-6">
          <LayersDiagram />
        </div>
      </AnimatedSection>

      <AnimatedSection className="border-t border-border/60">
        <div className="mx-auto grid max-w-screen-xl grid-cols-1 items-center gap-12 px-6 py-24 lg:grid-cols-2 lg:gap-16 lg:py-28">
          <div className="flex flex-col gap-5">
            <h2 className="text-balance text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              A single source, three executable views.
            </h2>
            <p className="text-pretty text-base leading-relaxed text-muted-foreground">
              Define a model once at the Spec layer. Lower it into the IR for
              analysis, run it through the eager autograd runtime, or feed it
              into a certificate checker — every layer agrees by construction.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button
                size="lg"
                variant="outline"
                render={<Link href="/docs/guide/api-surface" />}
              >
                Public API surface
                <ArrowRight aria-hidden />
              </Button>
            </div>
          </div>
          <CodePreview filename="Quickstart.lean" />
        </div>
      </AnimatedSection>

      <AnimatedSection className="border-t border-border/60 bg-muted/20">
        <div className="mx-auto max-w-screen-xl px-6 py-24 lg:py-28">
          <div className="flex flex-col items-start gap-6 rounded-2xl border border-border bg-card p-8 ring-1 ring-foreground/5 sm:p-12 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex max-w-2xl flex-col gap-3">
              <h2 className="text-balance text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                Ready to build a verified model?
              </h2>
              <p className="text-pretty text-base text-muted-foreground">
                The quickstart walks through cloning {siteConfig.name}, running
                your first training loop, and emitting a CROWN certificate in
                under ten minutes.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button size="lg" render={<Link href="/docs/guide/quickstart" />}>
                Start the quickstart
                <ArrowRight aria-hidden />
              </Button>
              <Button
                size="lg"
                variant="outline"
                render={
                  <a
                    href={siteConfig.github}
                    target="_blank"
                    rel="noopener noreferrer"
                  />
                }
              >
                GitHub repository
                <ExternalLink aria-hidden />
              </Button>
            </div>
          </div>

          <Separator className="my-12" />

          <div className="flex flex-col items-start justify-between gap-4 text-xs text-muted-foreground sm:flex-row sm:items-center">
            <span className="font-mono">
              {siteConfig.name} &middot; Lean 4 &middot; MIT licensed
            </span>
            <span className="font-mono">
              <a
                href={siteConfig.arxiv}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-foreground"
              >
                arXiv preprint
              </a>
            </span>
          </div>
        </div>
      </AnimatedSection>
    </div>
  );
}
