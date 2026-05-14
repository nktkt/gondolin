"use client";

import { motion } from "motion/react";

import { cn } from "@/lib/utils";

type Layer = {
  module: string;
  description: string;
  /** Tailwind classes for the band background tint. */
  tint: string;
};

const layers: Layer[] = [
  {
    module: "NN.API",
    description: "Public facade — model, tensor, data, training",
    tint: "bg-primary/10",
  },
  {
    module: "NN.Spec / NN.GraphSpec",
    description:
      "Pure math: tensors, layers, models, typed architectures",
    tint: "bg-primary/8",
  },
  {
    module: "NN.IR",
    description: "Op-tagged SSA/DAG graph, shape inference, denotation",
    tint: "bg-primary/[0.06]",
  },
  {
    module: "NN.Runtime",
    description:
      "Eager autograd, optimizers, training loops, PyTorch/CUDA bridges",
    tint: "bg-muted/60",
  },
  {
    module: "NN.Floats",
    description:
      "IEEE32Exec · FP32 · NeuralFloat finite-precision semantics",
    tint: "bg-muted/80",
  },
  {
    module: "NN.Proofs / NN.MLTheory / NN.Verification",
    description: "Bridges, CROWN/LiRPA, certificate checkers",
    tint: "bg-muted",
  },
];

export function LayersDiagram() {
  return (
    <section className="mx-auto max-w-screen-xl px-6 py-24 lg:py-28">
      <div className="mb-10 flex flex-col gap-3">
        <h2 className="text-balance text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          One source, every layer.
        </h2>
        <p className="max-w-2xl text-pretty text-base text-muted-foreground">
          From the public API down to finite-precision float semantics — a
          single Lean 4 codebase, each layer building on the one below it.
        </p>
      </div>

      <div className="flex flex-col gap-2">
        {layers.map((layer, i) => (
          <motion.div
            key={layer.module}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{
              duration: 0.5,
              delay: i * 0.08,
              ease: [0.22, 1, 0.36, 1],
            }}
            className={cn(
              "flex flex-col gap-1 rounded-xl border border-border/60 px-5 py-4 sm:flex-row sm:items-center sm:gap-6",
              layer.tint,
            )}
          >
            <span className="shrink-0 font-mono text-sm font-medium text-foreground sm:w-72">
              {layer.module}
            </span>
            <span className="text-sm text-muted-foreground">
              {layer.description}
            </span>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

export default LayersDiagram;
