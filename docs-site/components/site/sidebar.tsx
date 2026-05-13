"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";

import { cn } from "@/lib/utils";
import { navigation } from "@/lib/navigation";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:block w-64 shrink-0 border-r">
      <ScrollArea className="h-[calc(100svh-3.5rem)]">
        <nav className="px-3 py-6">
          {navigation.map((section, sectionIndex) => (
            <div key={section.category}>
              <div className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {section.title}
              </div>
              <ul className="flex flex-col gap-0.5">
                {section.items.map((item) => {
                  const href = `/docs/${item.slug}`;
                  const isActive = pathname === href;
                  return (
                    <li key={item.slug} className="relative">
                      {isActive && (
                        <motion.div
                          layoutId="sidebar-active"
                          className="absolute left-0 top-1 bottom-1 w-0.5 rounded-full bg-primary"
                          transition={{
                            type: "spring",
                            stiffness: 500,
                            damping: 40,
                          }}
                        />
                      )}
                      <Link
                        href={href}
                        className={cn(
                          "block rounded-md px-3 py-1.5 text-sm transition-colors",
                          isActive
                            ? "bg-accent text-accent-foreground font-medium"
                            : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                        )}
                      >
                        {item.title}
                      </Link>
                    </li>
                  );
                })}
              </ul>
              {sectionIndex < navigation.length - 1 && (
                <Separator className="my-3" />
              )}
            </div>
          ))}
        </nav>
      </ScrollArea>
    </aside>
  );
}

export default Sidebar;
