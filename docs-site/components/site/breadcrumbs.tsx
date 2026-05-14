import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { findDoc } from "@/lib/navigation";

export function Breadcrumbs({ slug }: { slug: string }) {
  const found = findDoc(slug);

  return (
    <nav
      aria-label="Breadcrumb"
      className="flex items-center gap-1.5 text-sm text-muted-foreground"
    >
      <Link
        href="/docs/guide/overview"
        className="transition-colors hover:text-foreground"
      >
        Docs
      </Link>

      {found ? (
        <>
          <ChevronRight aria-hidden className="size-3.5 shrink-0" />
          {found.section.items.length > 0 ? (
            <Link
              href={`/docs/${found.section.items[0].slug}`}
              className="transition-colors hover:text-foreground"
            >
              {found.section.title}
            </Link>
          ) : (
            <span>{found.section.title}</span>
          )}
          <ChevronRight aria-hidden className="size-3.5 shrink-0" />
          <span className="text-foreground">{found.item.title}</span>
        </>
      ) : null}
    </nav>
  );
}

export default Breadcrumbs;
