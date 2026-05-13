"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, ExternalLink, FileText, Hash } from "lucide-react";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { rankResults, type SearchEntry } from "@/lib/search-index";
import { cn } from "@/lib/utils";

type CommandPaletteProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

function groupByCategory(entries: SearchEntry[]): Array<[string, SearchEntry[]]> {
  const map = new Map<string, SearchEntry[]>();
  for (const entry of entries) {
    const bucket = map.get(entry.category);
    if (bucket) bucket.push(entry);
    else map.set(entry.category, [entry]);
  }
  return Array.from(map.entries());
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = React.useState("");

  const results = React.useMemo(() => rankResults(query, 12), [query]);
  const grouped = React.useMemo(() => groupByCategory(results), [results]);

  // Reset the query whenever the palette closes so the next open is fresh.
  React.useEffect(() => {
    if (!open) {
      const t = setTimeout(() => setQuery(""), 150);
      return () => clearTimeout(t);
    }
  }, [open]);

  const handleSelect = React.useCallback(
    (entry: SearchEntry) => {
      onOpenChange(false);
      if (entry.external) {
        // Open external links in a new tab so we don't blow away the SPA.
        window.open(entry.href, "_blank", "noopener,noreferrer");
        return;
      }
      router.push(entry.href);
    },
    [onOpenChange, router]
  );

  return (
    <CommandDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Search documentation"
      description="Find pages, guides, and external references."
      className="overflow-hidden"
    >
      <CommandInput
        placeholder="Search docs…"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandEmpty>No results.</CommandEmpty>
        <AnimatePresence initial={false} mode="wait">
          <motion.div
            key={query || "__all__"}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -2 }}
            transition={{ duration: 0.12, ease: "easeOut" }}
          >
            {grouped.map(([category, entries]) => (
              <CommandGroup key={category} heading={category}>
                {entries.map((entry) => (
                  <CommandItem
                    key={entry.id}
                    value={`${entry.title} ${entry.description ?? ""} ${entry.keywords.join(" ")}`}
                    onSelect={() => handleSelect(entry)}
                    className="group/item gap-3"
                  >
                    <span
                      className={cn(
                        "flex size-6 shrink-0 items-center justify-center rounded-md border bg-muted/40 text-muted-foreground"
                      )}
                    >
                      {entry.external ? (
                        <ExternalLink className="size-3.5" />
                      ) : entry.href.startsWith("/docs/") ? (
                        <FileText className="size-3.5" />
                      ) : (
                        <Hash className="size-3.5" />
                      )}
                    </span>
                    <span className="flex min-w-0 flex-1 flex-col">
                      <span className="truncate text-sm text-foreground">
                        {entry.title}
                      </span>
                      {entry.description ? (
                        <span className="truncate text-xs text-muted-foreground">
                          {entry.description}
                        </span>
                      ) : null}
                    </span>
                    <ArrowRight className="ml-auto size-3.5 shrink-0 opacity-0 transition-opacity group-data-selected/command-item:opacity-100" />
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </motion.div>
        </AnimatePresence>
      </CommandList>
    </CommandDialog>
  );
}
