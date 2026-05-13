import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { adjacentDocs } from "@/lib/navigation";

export function Pager({ slug }: { slug: string }) {
  const { prev, next } = adjacentDocs(slug);

  return (
    <div className="grid grid-cols-2 gap-4 mt-12 pt-8 border-t">
      {prev ? (
        <Link
          href={`/docs/${prev.slug}`}
          className="group flex flex-col items-start gap-1 rounded-lg border bg-card p-4 text-sm transition-colors hover:bg-accent/50"
        >
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <ChevronLeft className="size-3" />
            Previous
          </span>
          <span className="font-medium text-foreground">{prev.title}</span>
        </Link>
      ) : (
        <div />
      )}
      {next ? (
        <Link
          href={`/docs/${next.slug}`}
          className="group flex flex-col items-end gap-1 rounded-lg border bg-card p-4 text-right text-sm transition-colors hover:bg-accent/50"
        >
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            Next
            <ChevronRight className="size-3" />
          </span>
          <span className="font-medium text-foreground">{next.title}</span>
        </Link>
      ) : (
        <div />
      )}
    </div>
  );
}

export default Pager;
