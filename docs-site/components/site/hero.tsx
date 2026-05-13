"use client";

import { motion, type Variants } from "motion/react";
import { ArrowRight, ExternalLink } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { siteConfig } from "@/lib/site-config";
import { CodePreview } from "@/components/site/code-preview";

const HEADLINE = "Formalizing Neural Networks in Lean.";

const containerVariants: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.07, delayChildren: 0.15 },
  },
};

const wordVariants: Variants = {
  hidden: { opacity: 0, y: 18, filter: "blur(6px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
  },
};

const fadeVariants: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  },
};

export function Hero() {
  const words = HEADLINE.split(" ");
  // Subhead: first two sentences of the site description.
  const subhead = siteConfig.description
    .split(/(?<=\.)\s+/)
    .slice(0, 2)
    .join(" ");

  return (
    <section
      className="relative isolate overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-background to-background py-24 lg:py-32"
    >
      <div className="mx-auto grid max-w-screen-xl grid-cols-1 items-center gap-12 px-6 lg:grid-cols-2 lg:gap-16">
        <motion.div
          className="flex flex-col gap-6"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          <motion.div variants={fadeVariants}>
            <Badge variant="outline" className="font-mono text-[11px] tracking-wide">
              Lean 4 &middot; MIT &middot; v0.1.0
            </Badge>
          </motion.div>

          <motion.h1
            className="text-balance text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl"
            variants={containerVariants}
            aria-label={HEADLINE}
          >
            {words.map((word, i) => (
              <motion.span
                key={`${word}-${i}`}
                className="mr-[0.25em] inline-block"
                variants={wordVariants}
              >
                {word}
              </motion.span>
            ))}
          </motion.h1>

          <motion.p
            className="max-w-xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg"
            variants={fadeVariants}
          >
            {subhead}
          </motion.p>

          <motion.div
            className="mt-2 flex flex-wrap items-center gap-3"
            variants={fadeVariants}
          >
            <Button size="lg" render={<Link href="/docs/guide/overview" />}>
              Read the docs
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
              View on GitHub
              <ExternalLink aria-hidden />
            </Button>
          </motion.div>
        </motion.div>

        <motion.div
          className="relative"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.35, ease: [0.22, 1, 0.36, 1] }}
        >
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          >
            <CodePreview />
          </motion.div>
          <div
            aria-hidden
            className="pointer-events-none absolute -inset-8 -z-10 rounded-3xl bg-primary/10 blur-3xl"
          />
        </motion.div>
      </div>
    </section>
  );
}

export default Hero;
