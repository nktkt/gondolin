"use client";

import * as React from "react";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { CommandPalette } from "@/components/site/command-palette";

type SearchButtonProps = {
  className?: string;
};

export function SearchButton({ className }: SearchButtonProps) {
  const [open, setOpen] = React.useState(false);

  // Global Cmd/Ctrl-K toggles the palette from anywhere on the page.
  React.useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        aria-label="Search documentation"
        className={cn(
          "relative inline-flex h-8 min-w-[10rem] items-center gap-2 px-2.5 pr-1.5 text-muted-foreground hover:text-muted-foreground",
          "sm:min-w-[14rem] md:min-w-[16rem]",
          className
        )}
      >
        <Search className="size-3.5 shrink-0 opacity-70" aria-hidden="true" />
        <span className="flex-1 text-left text-xs font-normal">
          Search docs…
        </span>
        <kbd
          className={cn(
            "pointer-events-none hidden h-5 select-none items-center gap-0.5 rounded border border-border/70 bg-muted/60 px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:inline-flex"
          )}
          aria-hidden="true"
        >
          <span className="text-[11px] leading-none">⌘</span>
          <span className="leading-none">K</span>
        </kbd>
      </Button>
      <CommandPalette open={open} onOpenChange={setOpen} />
    </>
  );
}
