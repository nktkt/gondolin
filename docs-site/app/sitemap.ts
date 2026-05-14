import type { MetadataRoute } from "next";
import { siteConfig } from "@/lib/site-config";
import { allDocSlugs } from "@/lib/navigation";

// Required for `output: "export"` — generate sitemap.xml at build time.
export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteConfig.url;
  const lastModified = new Date();

  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: base,
      lastModified,
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${base}/examples`,
      lastModified,
      changeFrequency: "weekly",
      priority: 0.7,
    },
  ];

  const docRoutes: MetadataRoute.Sitemap = allDocSlugs().map((slug) => ({
    url: `${base}/docs/${slug}`,
    lastModified,
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  return [...staticRoutes, ...docRoutes];
}
