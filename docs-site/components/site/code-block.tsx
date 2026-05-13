import * as React from "react"

import { cn } from "@/lib/utils"
import { highlight } from "@/lib/shiki"
import { CopyButton } from "@/components/site/copy-button"

type CodeBlockProps = {
  code: string
  lang?: string
  filename?: string
  className?: string
}

const SHIKI_CSS = `
.shiki-wrapper pre.shiki { background: transparent; padding: 1rem; font-size: 0.875rem; line-height: 1.6; margin: 0; overflow-x: auto; }
.shiki-wrapper pre.shiki code { color: var(--shiki-light); background-color: transparent; display: block; min-width: max-content; }
.shiki-wrapper pre.shiki code span { color: var(--shiki-light); }
.dark .shiki-wrapper pre.shiki { background: transparent; }
.dark .shiki-wrapper pre.shiki code { color: var(--shiki-dark); background-color: var(--shiki-dark-bg) !important; }
.dark .shiki-wrapper pre.shiki code span { color: var(--shiki-dark) !important; background-color: var(--shiki-dark-bg) !important; }
`.trim()

export async function CodeBlock({
  code,
  lang,
  filename,
  className,
}: CodeBlockProps) {
  const language = lang ?? "text"
  const html = await highlight(code, language)

  return (
    <div
      className={cn(
        "group relative my-4 overflow-hidden rounded-lg border border-border bg-muted/30 text-sm",
        className,
      )}
    >
      <style>{SHIKI_CSS}</style>
      {filename ? (
        <div className="flex items-center justify-between gap-2 border-b border-border bg-muted/50 px-3 py-1.5">
          <span className="truncate font-mono text-xs text-muted-foreground">
            {filename}
          </span>
          <CopyButton text={code} className="size-7 -my-0.5" />
        </div>
      ) : (
        <CopyButton
          text={code}
          className="absolute top-2 right-2 z-10 size-7 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
        />
      )}
      <div
        className="shiki-wrapper prose-sm overflow-x-auto"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  )
}

export default CodeBlock
