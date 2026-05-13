import {
  Calculator,
  Cpu,
  FlaskConical,
  GitBranch,
  Layers,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Feature = {
  title: string;
  description: string;
  icon: LucideIcon;
};

const features: Feature[] = [
  {
    title: "Typed tensors and model APIs",
    description:
      "A small public facade over spec, runtime, and training keeps imports stable while the internals evolve.",
    icon: Layers,
  },
  {
    title: "Op-tagged graph IR",
    description:
      "A shared SSA/DAG with shape inference and denotational semantics — the bridge between specs and execution.",
    icon: GitBranch,
  },
  {
    title: "Eager autograd runtime",
    description:
      "Tape-based reverse-mode AD with optimizers, training loops, and PyTorch interop for weight round-trips.",
    icon: Cpu,
  },
  {
    title: "Three float views",
    description:
      "Executable IEEE32, a real-rounded FP32 model, and a generic NeuralFloat parameterised by radix and precision.",
    icon: Calculator,
  },
  {
    title: "Certificate checkers",
    description:
      "IBP, CROWN/LiRPA, PINN residuals, and ODE corridors plugged into Lean-verified verification workflows.",
    icon: ShieldCheck,
  },
  {
    title: "Reproducible examples",
    description:
      "Quickstarts, a model zoo, training curves, and dataset integration — every example builds in CI.",
    icon: FlaskConical,
  },
];

export function FeatureGrid({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "mx-auto max-w-screen-xl px-6 py-24 lg:py-28",
        className,
      )}
    >
      <div className="mb-12 flex flex-col gap-3">
        <h2 className="text-balance text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          What&apos;s in the box.
        </h2>
        <p className="max-w-2xl text-pretty text-base text-muted-foreground">
          Six subsystems that compose into a verified-by-construction
          neural-network stack. Each is documented, tested, and importable on
          its own.
        </p>
      </div>

      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ title, description, icon: Icon }) => (
          <li key={title}>
            <Card className="h-full border transition-shadow hover:shadow-md">
              <CardHeader className="gap-3">
                <span
                  aria-hidden
                  className="inline-flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/15"
                >
                  <Icon className="size-4.5" />
                </span>
                <CardTitle className="text-base">{title}</CardTitle>
                <CardDescription className="leading-relaxed">
                  {description}
                </CardDescription>
              </CardHeader>
            </Card>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default FeatureGrid;
