"use client";

import { useEffect, useState } from "react";

import type { TocEntry } from "@/lib/toc";
import { cn } from "@/lib/utils";

export default function Toc({ entries }: { entries: TocEntry[] }) {
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    if (entries.length === 0) return;

    const elements = entries
      .map((entry) => document.getElementById(entry.id))
      .filter((el): el is HTMLElement => el !== null);

    if (elements.length === 0) return;

    // Order ids by document position so we can pick the topmost.
    const orderedIds = elements.map((el) => el.id);

    const observer = new IntersectionObserver(
      (observerEntries) => {
        setActiveId((current) => {
          const intersecting = observerEntries
            .filter((e) => e.isIntersecting)
            .map((e) => e.target.id)
            .sort((a, b) => orderedIds.indexOf(a) - orderedIds.indexOf(b));

          // Topmost intersecting heading wins; otherwise keep the last active.
          return intersecting[0] ?? current;
        });
      },
      { rootMargin: "0px 0px -70% 0px", threshold: 0 },
    );

    for (const el of elements) observer.observe(el);
    return () => observer.disconnect();
  }, [entries]);

  if (entries.length === 0) return null;

  return (
    <aside className="hidden xl:block w-56 shrink-0">
      <nav className="sticky top-20">
        <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          On this page
        </p>
        <ul className="space-y-2 text-sm">
          {entries.map((entry) => {
            const isActive = entry.id === activeId;
            return (
              <li key={entry.id}>
                <a
                  href={`#${entry.id}`}
                  onClick={(e) => {
                    const target = document.getElementById(entry.id);
                    if (!target) return;
                    e.preventDefault();
                    history.replaceState(null, "", `#${entry.id}`);
                    target.scrollIntoView({ behavior: "smooth" });
                    setActiveId(entry.id);
                  }}
                  className={cn(
                    "block leading-snug transition-colors hover:text-foreground",
                    entry.depth === 3 && "pl-3",
                    isActive
                      ? "text-foreground font-medium"
                      : "text-muted-foreground",
                  )}
                >
                  {entry.text}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
