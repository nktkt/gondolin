import { FileEdit, MessageSquareWarning } from "lucide-react";

import { siteConfig } from "@/lib/site-config";

export function DocFooterMeta({ slug }: { slug: string }) {
  const editUrl = `${siteConfig.github}/blob/main/docs-site/content/${slug}.mdx`;
  const issueUrl = `${siteConfig.github}/issues/new`;

  return (
    <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t pt-6 text-sm text-muted-foreground">
      <a
        href={editUrl}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1.5 transition-colors hover:text-foreground"
      >
        <FileEdit aria-hidden className="size-3.5" />
        Edit this page on GitHub
      </a>
      <a
        href={issueUrl}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1.5 transition-colors hover:text-foreground"
      >
        <MessageSquareWarning aria-hidden className="size-3.5" />
        Report an issue
      </a>
    </div>
  );
}

export default DocFooterMeta;
