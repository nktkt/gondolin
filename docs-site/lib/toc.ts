import GithubSlugger from "github-slugger";

export type TocEntry = { depth: 2 | 3; text: string; id: string };

const HEADING_RE = /^(#{1,6})\s+(.*?)\s*$/;
const FENCE_RE = /^\s*(`{3,}|~{3,})/;

/**
 * Strip the inline markdown we actually use in headings:
 * inline code (`code`), bold (**x**), italic (*x*), and links ([text](url) -> text).
 * Intentionally minimal — correct for this repo's content, not a full markdown parser.
 */
function stripInlineMarkdown(input: string): string {
  let text = input;
  // Links: [text](url) -> text
  text = text.replace(/\[([^\]]*)\]\([^)]*\)/g, "$1");
  // Inline code: `code` -> code
  text = text.replace(/`([^`]*)`/g, "$1");
  // Bold: **x** or __x__ -> x
  text = text.replace(/\*\*([^*]+)\*\*/g, "$1");
  text = text.replace(/__([^_]+)__/g, "$1");
  // Italic: *x* or _x_ -> x
  text = text.replace(/\*([^*]+)\*/g, "$1");
  text = text.replace(/_([^_]+)_/g, "$1");
  return text.trim();
}

/**
 * Extract an ordered "On this page" table of contents from raw markdown source.
 * Only h2 (`## `) and h3 (`### `) ATX headings are included; h1 and h4+ are skipped.
 * Heading-like lines inside fenced code blocks (``` or ~~~) are ignored.
 *
 * `id`s are produced with a fresh `github-slugger` instance so they match exactly
 * what `rehype-slug` generates when the same document is rendered.
 */
export function extractToc(markdownSource: string): TocEntry[] {
  const slugger = new GithubSlugger();
  const entries: TocEntry[] = [];

  let fenceMarker: string | null = null;
  const lines = markdownSource.split(/\r?\n/);

  for (const line of lines) {
    const fenceMatch = FENCE_RE.exec(line);
    if (fenceMatch) {
      const marker = fenceMatch[1][0]; // "`" or "~"
      if (fenceMarker === null) {
        // Opening fence.
        fenceMarker = marker;
      } else if (fenceMarker === marker) {
        // Closing fence (must match the opening fence char).
        fenceMarker = null;
      }
      continue;
    }

    if (fenceMarker !== null) {
      // Inside a fenced code block — ignore everything.
      continue;
    }

    const headingMatch = HEADING_RE.exec(line);
    if (!headingMatch) continue;

    const depth = headingMatch[1].length;
    if (depth !== 2 && depth !== 3) continue;

    // Strip trailing closing `#`s (ATX closed form), then inline markdown.
    const rawText = headingMatch[2].replace(/\s*#+\s*$/, "");
    const text = stripInlineMarkdown(rawText);
    if (text.length === 0) continue;

    const id = slugger.slug(text);
    entries.push({ depth: depth as 2 | 3, text, id });
  }

  return entries;
}
