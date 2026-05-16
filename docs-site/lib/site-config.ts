export const siteConfig = {
  name: "TorchLean",
  shortName: "TorchLean Docs",
  description:
    "Formalizing Neural Networks in Lean. Typed tensors, IR, autograd, verification certificates, and finite-precision semantics — all in Lean 4.",
  url: "https://torchlean.org",
  ogImage: "https://torchlean.org/og.png",
  github: "https://github.com/nktkt/gondolin",
  arxiv: "https://arxiv.org/abs/2602.22631",
  navLinks: [
    { title: "Docs", href: "/docs/guide/overview" },
    { title: "Examples", href: "/examples" },
    { title: "API", href: "/api/", external: true },
    { title: "Verification", href: "/docs/verification/overview" },
    { title: "Trust", href: "/docs/governance/trust-boundaries" },
  ],
} as const;
