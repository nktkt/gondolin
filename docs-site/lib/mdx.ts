import "server-only";

import { promises as fs } from "node:fs";
import path from "node:path";
import matter from "gray-matter";

import { allDocSlugs } from "@/lib/navigation";

export type DocFrontmatter = {
  title: string;
  description?: string;
};

export type LoadedDoc = {
  frontmatter: DocFrontmatter;
  source: string;
};

const CONTENT_ROOT = path.join(process.cwd(), "content");

function resolveDocPath(slug: string): string {
  // Normalize: split on '/', strip empty segments, rejoin. Prevents directory traversal.
  const segments = slug
    .split("/")
    .map((s) => s.trim())
    .filter((s) => s.length > 0 && s !== "." && s !== "..");
  return path.join(CONTENT_ROOT, ...segments) + ".mdx";
}

export async function loadDoc(slug: string): Promise<LoadedDoc | null> {
  const filePath = resolveDocPath(slug);

  // Defense in depth: make sure the resolved path is still inside CONTENT_ROOT.
  const resolved = path.resolve(filePath);
  if (!resolved.startsWith(path.resolve(CONTENT_ROOT) + path.sep)) {
    return null;
  }

  let raw: string;
  try {
    raw = await fs.readFile(resolved, "utf8");
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      return null;
    }
    throw err;
  }

  const { data, content } = matter(raw);
  const fm = data as Partial<DocFrontmatter>;

  return {
    frontmatter: {
      title: fm.title ?? slug,
      description: fm.description,
    },
    source: content,
  };
}

export function listDocs(): { slug: string }[] {
  return allDocSlugs().map((slug) => ({ slug }));
}
