export type DocCategory =
  | "guide"
  | "architecture"
  | "verification"
  | "runtime"
  | "floats"
  | "ir"
  | "examples"
  | "governance";

export type DocItem = {
  slug: string;
  title: string;
  description?: string;
};

export type NavSection = {
  title: string;
  category: DocCategory;
  items: DocItem[];
};

export const navigation: NavSection[] = [
  {
    title: "Guide",
    category: "guide",
    items: [
      { slug: "guide/overview", title: "Overview", description: "What TorchLean is and how its layers fit together." },
      { slug: "guide/quickstart", title: "Quickstart", description: "Clone, build, and run your first example in minutes." },
      { slug: "guide/api-surface", title: "Public API surface", description: "The recommended import facades." },
    ],
  },
  {
    title: "Architecture",
    category: "architecture",
    items: [
      { slug: "architecture/repository-map", title: "Repository map", description: "Where every subsystem lives." },
      { slug: "architecture/spec", title: "Spec layer", description: "Pure tensor, layer, and model definitions." },
      { slug: "architecture/spec-core", title: "Spec.Core tensors", description: "Shape utilities and the Context interface." },
      { slug: "architecture/spec-layers", title: "Spec.Layers", description: "Forward / backward specifications for layers." },
      { slug: "architecture/dependency-audit", title: "Dependency audit", description: "Modules, edges, hubs, longest chains." },
      { slug: "architecture/graphs", title: "Module graphs", description: "Interactive dependency-graph explorer." },
    ],
  },
  {
    title: "IR",
    category: "ir",
    items: [
      { slug: "ir/overview", title: "IR overview", description: "Op-tagged SSA/DAG, shape inference, denotation." },
    ],
  },
  {
    title: "Runtime",
    category: "runtime",
    items: [
      { slug: "runtime/overview", title: "Runtime overview", description: "Eager tape autograd, optimizers, training loops." },
      { slug: "runtime/pytorch", title: "PyTorch interop", description: "Weight round-trips and AD correspondence tests." },
      { slug: "runtime/cuda", title: "CUDA boundary", description: "Trusted native kernels, memory policy, sanitizers." },
    ],
  },
  {
    title: "Floats",
    category: "floats",
    items: [
      { slug: "floats/overview", title: "Three float views", description: "IEEE32Exec, FP32, NeuralFloat side-by-side." },
      { slug: "floats/fp32", title: "FP32 model", description: "Real-rounded float32 with error bounds." },
      { slug: "floats/neural-float", title: "NeuralFloat", description: "Generic rounding parameterised by radix/precision/exp." },
      { slug: "floats/ieee-exec", title: "IEEE32Exec", description: "Executable IEEE-754 binary32 kernel." },
      { slug: "floats/interval", title: "Interval arithmetic", description: "Quantized and FP32 interval utilities." },
      { slug: "floats/arb", title: "Arb / FLINT oracle", description: "External python-flint backend for high-quality enclosures." },
    ],
  },
  {
    title: "Verification",
    category: "verification",
    items: [
      { slug: "verification/overview", title: "Verification overview", description: "Certificate checkers and graph verifiers." },
      { slug: "verification/proofs", title: "Proofs library", description: "Spec ↔ IR ↔ runtime bridges and autograd theorems." },
      { slug: "verification/ml-theory", title: "ML theory", description: "CROWN/LiRPA, generative, learning, optimization, SSL." },
      { slug: "verification/crown", title: "CROWN bounds", description: "Affine and graph bound propagation." },
    ],
  },
  {
    title: "Examples",
    category: "examples",
    items: [
      { slug: "examples/overview", title: "Examples overview", description: "Maintained example surface by category." },
      { slug: "examples/quickstart", title: "Quickstart examples", description: "Tensor basics, autograd, MLPs, data loaders." },
      { slug: "examples/models", title: "Model zoo", description: "Vision, sequence, generative, RL, operator learning." },
      { slug: "examples/verification", title: "Verifier examples", description: "IBP, CROWN, LiRPA, PINN, splines, ODE corridors." },
    ],
  },
  {
    title: "Governance",
    category: "governance",
    items: [
      { slug: "governance/trust-boundaries", title: "Trust boundaries", description: "Axioms, contracts, FFI, external oracles." },
      { slug: "governance/ai-usage", title: "AI usage disclosure", description: "How AI tooling assists development." },
      { slug: "governance/third-party", title: "Third-party notices", description: "Datasets, fixtures, licensing." },
      { slug: "governance/contributing", title: "Contributing", description: "PR process, tests, style." },
    ],
  },
];

export function findDoc(slug: string): { section: NavSection; item: DocItem } | null {
  for (const section of navigation) {
    for (const item of section.items) {
      if (item.slug === slug) return { section, item };
    }
  }
  return null;
}

export function allDocSlugs(): string[] {
  return navigation.flatMap((s) => s.items.map((i) => i.slug));
}

export function adjacentDocs(slug: string): { prev: DocItem | null; next: DocItem | null } {
  const flat = navigation.flatMap((s) => s.items);
  const idx = flat.findIndex((i) => i.slug === slug);
  return {
    prev: idx > 0 ? flat[idx - 1] : null,
    next: idx >= 0 && idx < flat.length - 1 ? flat[idx + 1] : null,
  };
}
