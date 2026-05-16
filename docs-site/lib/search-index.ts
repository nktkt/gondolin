import { navigation } from "@/lib/navigation";
import { siteConfig } from "@/lib/site-config";

export type SearchEntry = {
  id: string;
  title: string;
  description?: string;
  category: string;
  href: string;
  keywords: string[];
  external?: boolean;
};

function makeEntry(
  id: string,
  title: string,
  category: string,
  href: string,
  description?: string,
  extraKeywords: string[] = [],
  external = false
): SearchEntry {
  const keywords = [
    title,
    ...title.split(/\s+/).filter(Boolean),
    category,
    ...extraKeywords,
  ];
  return { id, title, description, category, href, keywords, external };
}

const docEntries: SearchEntry[] = navigation.flatMap((section) =>
  section.items.map((item) =>
    makeEntry(
      `doc:${item.slug}`,
      item.title,
      section.title,
      `/docs/${item.slug}`,
      item.description,
      [item.slug, section.title]
    )
  )
);

const topLevelEntries: SearchEntry[] = [
  makeEntry(
    "page:home",
    "Home",
    "Site",
    "/",
    "The Gondolin landing page.",
    ["landing", "index", "start"]
  ),
  makeEntry(
    "page:examples",
    "Examples",
    "Site",
    "/examples",
    "Curated examples across tensors, autograd, models, and verification.",
    ["demo", "samples", "gallery"]
  ),
  makeEntry(
    "page:github",
    "GitHub repository",
    "External",
    siteConfig.github,
    "View the Gondolin source on GitHub.",
    ["source", "code", "repository", "git"],
    true
  ),
];

export const searchIndex: SearchEntry[] = [...topLevelEntries, ...docEntries];

function normalize(s: string): string {
  return s.toLowerCase();
}

export function rankResults(query: string, limit = 8): SearchEntry[] {
  const q = normalize(query).trim();
  if (!q) {
    return searchIndex.slice(0, limit);
  }

  const scored: Array<{ entry: SearchEntry; score: number }> = [];

  for (const entry of searchIndex) {
    const title = normalize(entry.title);
    const description = normalize(entry.description ?? "");
    const keywordHaystack = normalize(entry.keywords.join(" "));

    let score = 0;

    if (title.startsWith(q)) {
      score = 100;
    } else if (title.includes(q)) {
      score = 75;
    } else if (description.includes(q)) {
      score = 50;
    } else if (keywordHaystack.includes(q)) {
      score = 25;
    } else {
      continue;
    }

    // small boost for shorter titles (more specific matches)
    score -= Math.min(title.length, 40) * 0.1;

    scored.push({ entry, score });
  }

  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, limit).map((s) => s.entry);
}
