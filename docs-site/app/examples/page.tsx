"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";

import { ExampleCard } from "@/components/site/example-card";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import { examples, type ExampleCategory } from "@/lib/examples-data";

type FilterValue = "all" | ExampleCategory;

interface FilterDef {
  value: FilterValue;
  label: string;
}

const filters: FilterDef[] = [
  { value: "all", label: "All" },
  { value: "quickstart", label: "Quickstart" },
  { value: "vision", label: "Vision" },
  { value: "sequence", label: "Sequence" },
  { value: "generative", label: "Generative" },
  { value: "rl", label: "RL" },
  { value: "operator-learning", label: "Operators" },
  { value: "verification", label: "Verification" },
  { value: "interop", label: "Interop" },
];

export default function ExamplesPage() {
  const [active, setActive] = useState<FilterValue>("all");

  const visible = useMemo(() => {
    if (active === "all") return examples;
    return examples.filter((e) => e.category === active);
  }, [active]);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 md:py-14">
      <header className="mb-8 flex flex-col gap-3">
        <h1 className="font-heading text-3xl font-semibold tracking-tight md:text-4xl">
          Examples
        </h1>
        <p className="max-w-2xl text-sm text-muted-foreground md:text-base">
          A curated gallery of runnable models, training loops, and verification
          fixtures shipped with TorchLean. Every entry maps to a single{" "}
          <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
            lake exe
          </code>{" "}
          invocation you can paste into your shell.
        </p>
      </header>

      <Tabs
        value={active}
        onValueChange={(value) => {
          if (typeof value === "string") {
            setActive(value as FilterValue);
          }
        }}
        className="gap-6"
      >
        <TabsList className="h-auto flex-wrap justify-start gap-1 bg-muted/60 p-1">
          {filters.map((f) => (
            <TabsTrigger key={f.value} value={f.value} className="h-7 px-3">
              {f.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {filters.map((f) => (
          <TabsContent key={f.value} value={f.value} className="mt-0">
            <AnimatePresence mode="wait">
              <motion.div
                key={f.value}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3"
              >
                {visible.map((example) => (
                  <ExampleCard key={example.slug} example={example} />
                ))}
              </motion.div>
            </AnimatePresence>
            {visible.length === 0 && (
              <p className="py-12 text-center text-sm text-muted-foreground">
                No examples in this category yet.
              </p>
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
