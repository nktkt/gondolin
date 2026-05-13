"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";

import { cn } from "@/lib/utils";
import { navigation } from "@/lib/navigation";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

export function MobileDocsNav() {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);

  return (
    <div className="md:hidden">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger
          render={
            <Button variant="ghost" size="icon-sm" aria-label="Open docs navigation">
              <Menu />
            </Button>
          }
        />
        <SheetContent side="left" className="p-0">
          <SheetHeader>
            <SheetTitle>Documentation</SheetTitle>
          </SheetHeader>
          <ScrollArea className="flex-1">
            <nav className="px-3 pb-6">
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
                        <li key={item.slug}>
                          <Link
                            href={href}
                            onClick={() => setOpen(false)}
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
        </SheetContent>
      </Sheet>
    </div>
  );
}

export default MobileDocsNav;
