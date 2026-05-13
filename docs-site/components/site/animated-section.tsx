"use client";

import { motion, type Variants } from "motion/react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const variants: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  },
};

export function AnimatedSection({
  children,
  className,
  as: _as,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  /** Optional override for the rendered tag; unused but kept for API symmetry. */
  as?: "section" | "div";
  delay?: number;
}) {
  void _as;
  return (
    <motion.section
      className={cn("w-full", className)}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      variants={variants}
      transition={{ delay }}
    >
      {children}
    </motion.section>
  );
}

export default AnimatedSection;
