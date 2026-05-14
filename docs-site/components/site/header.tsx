import Link from "next/link";
import { Menu, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";
import { siteConfig } from "@/lib/site-config";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/site/theme-toggle";
import { SearchButton } from "@/components/site/search-button";

function GitHubIcon({ className }: { className?: string }) {
  // lucide-react in this project does not ship the GitHub brand icon, so we
  // inline a minimal mark that inherits currentColor for theming.
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      className={cn("size-4", className)}
    >
      <path d="M12 .5C5.73.5.75 5.48.75 11.75c0 4.96 3.22 9.16 7.69 10.65.56.1.77-.24.77-.54 0-.27-.01-1.16-.02-2.1-3.13.68-3.79-1.34-3.79-1.34-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 1.72 2.63 1.22 3.27.93.1-.73.39-1.22.71-1.5-2.5-.28-5.13-1.25-5.13-5.55 0-1.23.44-2.24 1.15-3.03-.12-.28-.5-1.42.11-2.97 0 0 .94-.3 3.08 1.16a10.7 10.7 0 0 1 5.6 0c2.14-1.46 3.08-1.16 3.08-1.16.61 1.55.23 2.69.11 2.97.72.79 1.15 1.8 1.15 3.03 0 4.31-2.63 5.26-5.14 5.54.4.35.76 1.04.76 2.1 0 1.51-.01 2.73-.01 3.1 0 .3.2.65.78.54 4.46-1.49 7.68-5.69 7.68-10.65C23.25 5.48 18.27.5 12 .5Z" />
    </svg>
  );
}

function NavLinks({
  className,
  itemClassName,
  onNavigate,
}: {
  className?: string;
  itemClassName?: string;
  onNavigate?: () => void;
}) {
  const itemClasses = cn(
    "rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
    itemClassName
  );

  return (
    <nav className={cn("flex items-center gap-1", className)}>
      {siteConfig.navLinks.map((link) =>
        "external" in link && link.external ? (
          // `/api/` is a statically-hosted DocGen4 tree, not a Next.js
          // route — needs a full-page navigation, not client routing.
          <a
            key={link.href}
            href={link.href}
            onClick={onNavigate}
            className={itemClasses}
          >
            {link.title}
          </a>
        ) : (
          <Link
            key={link.href}
            href={link.href}
            onClick={onNavigate}
            className={itemClasses}
          >
            {link.title}
          </Link>
        )
      )}
    </nav>
  );
}

export function Header() {
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 w-full max-w-screen-2xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        {/* Wordmark */}
        <Link
          href="/"
          className="flex items-center gap-2 text-sm font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 rounded-md"
        >
          <span className="flex size-6 items-center justify-center rounded-md bg-gradient-to-br from-primary/80 to-primary/40 text-primary-foreground shadow-sm">
            <Sparkles className="size-3.5" />
          </span>
          <span className="text-foreground">{siteConfig.name}</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden flex-1 items-center justify-center md:flex">
          <NavLinks />
        </div>

        {/* Right cluster */}
        <div className="flex flex-1 items-center justify-end gap-2 md:flex-none">
          <div className="hidden md:block">
            <SearchButton />
          </div>
          <Button
            variant="ghost"
            size="icon"
            aria-label="GitHub repository"
            render={
              <a
                href={siteConfig.github}
                target="_blank"
                rel="noopener noreferrer"
              />
            }
          >
            <GitHubIcon />
          </Button>
          <ThemeToggle />

          {/* Mobile menu */}
          <div className="md:hidden">
            <Sheet>
              <SheetTrigger
                render={
                  <Button variant="ghost" size="icon" aria-label="Open menu">
                    <Menu className="size-4" />
                  </Button>
                }
              />
              <SheetContent side="right" className="w-72">
                <SheetHeader>
                  <SheetTitle>Navigation</SheetTitle>
                </SheetHeader>
                <div className="px-2 pb-4">
                  <NavLinks
                    className="flex-col items-stretch gap-0.5"
                    itemClassName="block px-3 py-2 text-base"
                  />
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
}
