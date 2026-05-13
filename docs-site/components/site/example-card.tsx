"use client";

import { motion } from "motion/react";
import { Terminal } from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Example, ExampleCategory } from "@/lib/examples-data";

const categoryLabels: Record<ExampleCategory, string> = {
  quickstart: "Quickstart",
  vision: "Vision",
  sequence: "Sequence",
  generative: "Generative",
  rl: "Reinforcement Learning",
  "operator-learning": "Operator Learning",
  verification: "Verification",
  interop: "Interop",
};

export interface ExampleCardProps {
  example: Example;
  className?: string;
}

export function ExampleCard({ example, className }: ExampleCardProps) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 320, damping: 24 }}
      className={cn("group/example h-full", className)}
    >
      <Card className="h-full">
        <CardHeader className="gap-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base">{example.title}</CardTitle>
            <Badge variant="secondary" className="shrink-0 text-[10px]">
              {categoryLabels[example.category]}
            </Badge>
          </div>
          <CardDescription className="leading-relaxed">
            {example.blurb}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {example.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {example.tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="text-[10px] font-normal text-muted-foreground"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          )}
          <div className="relative">
            <pre
              className={cn(
                "overflow-x-auto rounded-md bg-muted/60 px-3 py-2 text-[11px] leading-relaxed",
                "font-mono text-foreground/80 ring-1 ring-foreground/5",
              )}
            >
              <code>{example.command}</code>
            </pre>
            <motion.span
              initial={{ opacity: 0 }}
              whileHover={{ opacity: 1 }}
              className={cn(
                "pointer-events-none absolute right-2 top-2 flex items-center gap-1",
                "rounded bg-background/80 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground",
                "opacity-0 transition-opacity duration-200 group-hover/example:opacity-100",
              )}
              aria-hidden
            >
              <Terminal className="size-3" />
              copy
            </motion.span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default ExampleCard;
