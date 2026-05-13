import { createHighlighter, type Highlighter } from "shiki"

let highlighterPromise: Promise<Highlighter> | null = null

export function getHighlighter() {
  if (!highlighterPromise) {
    highlighterPromise = createHighlighter({
      themes: ["github-dark-default", "github-light-default"],
      langs: [
        "bash",
        "shell",
        "lean",
        "lean4",
        "python",
        "typescript",
        "tsx",
        "javascript",
        "json",
        "yaml",
        "toml",
        "diff",
        "text",
      ],
    })
  }
  return highlighterPromise
}

export async function highlight(code: string, lang: string): Promise<string> {
  const h = await getHighlighter()
  const loaded = h.getLoadedLanguages() as string[]
  const resolved = loaded.includes(lang) ? lang : "text"
  return h.codeToHtml(code, {
    lang: resolved,
    themes: { light: "github-light-default", dark: "github-dark-default" },
    defaultColor: false,
  })
}
