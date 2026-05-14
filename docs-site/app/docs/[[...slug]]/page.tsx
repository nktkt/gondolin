import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { MDXRemote } from "next-mdx-remote/rsc";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";

import { loadDoc } from "@/lib/mdx";
import { extractToc } from "@/lib/toc";
import { allDocSlugs } from "@/lib/navigation";
import { mdxComponents } from "@/components/site/mdx-components";
import { siteConfig } from "@/lib/site-config";
import Pager from "@/components/site/pager";
import Toc from "@/components/site/toc";
import Breadcrumbs from "@/components/site/breadcrumbs";
import DocFooterMeta from "@/components/site/doc-footer-meta";

const DEFAULT_SLUG = "guide/overview";

function resolveSlug(slugParam: string[] | undefined): string {
  if (!slugParam || slugParam.length === 0) return DEFAULT_SLUG;
  return slugParam.join("/");
}

type PageParams = { slug?: string[] };

// `architecture/graphs` is served by a dedicated interactive route
// (app/docs/architecture/graphs/page.tsx), not from MDX content.
const EXPLICIT_ROUTE_SLUGS = new Set(["architecture/graphs"]);

export async function generateStaticParams(): Promise<PageParams[]> {
  return allDocSlugs()
    .filter((slug) => !EXPLICIT_ROUTE_SLUGS.has(slug))
    .map((slug) => ({ slug: slug.split("/") }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<PageParams>;
}): Promise<Metadata> {
  const { slug: slugParam } = await params;
  const slug = resolveSlug(slugParam);
  const doc = await loadDoc(slug);
  if (!doc) {
    return { title: `Not found · ${siteConfig.name}` };
  }
  return {
    title: doc.frontmatter.title,
    description: doc.frontmatter.description,
  };
}

export default async function DocPage({
  params,
}: {
  params: Promise<PageParams>;
}) {
  const { slug: slugParam } = await params;
  const slug = resolveSlug(slugParam);
  const doc = await loadDoc(slug);

  if (!doc) {
    notFound();
  }

  const toc = extractToc(doc.source);

  return (
    <div className="flex gap-10">
      <article className="min-w-0 flex-1 max-w-3xl">
        <Breadcrumbs slug={slug} />

        <header className="mt-4 mb-8">
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-foreground">
            {doc.frontmatter.title}
          </h1>
          {doc.frontmatter.description ? (
            <p className="mt-2 text-muted-foreground text-lg">
              {doc.frontmatter.description}
            </p>
          ) : null}
        </header>

        <div className="docs-prose">
          <MDXRemote
            source={doc.source}
            components={mdxComponents}
            options={{
              mdxOptions: {
                remarkPlugins: [remarkGfm],
                rehypePlugins: [
                  rehypeSlug,
                  [rehypeAutolinkHeadings, { behavior: "wrap" }],
                ],
              },
            }}
          />
        </div>

        <DocFooterMeta slug={slug} />

        <div className="mt-12">
          <Pager slug={slug} />
        </div>
      </article>

      <Toc entries={toc} />
    </div>
  );
}
