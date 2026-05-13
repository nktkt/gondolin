"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";

import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/site/theme-provider";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = theme === "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      <span className="relative inline-flex size-4 items-center justify-center">
        <AnimatePresence initial={false} mode="wait">
          {mounted && isDark ? (
            <motion.span
              key="moon"
              initial={{ opacity: 0, rotate: -90, scale: 0.75 }}
              animate={{ opacity: 1, rotate: 0, scale: 1 }}
              exit={{ opacity: 0, rotate: 90, scale: 0.75 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <Moon className="size-4" />
            </motion.span>
          ) : (
            <motion.span
              key="sun"
              initial={{ opacity: 0, rotate: 90, scale: 0.75 }}
              animate={{ opacity: 1, rotate: 0, scale: 1 }}
              exit={{ opacity: 0, rotate: -90, scale: 0.75 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <Sun className="size-4" />
            </motion.span>
          )}
        </AnimatePresence>
      </span>
    </Button>
  );
}
