import Link from "next/link";

import { siteConfig } from "@/lib/site-config";

type FooterLink = {
  title: string;
  href: string;
  external?: boolean;
};

type FooterColumn = {
  heading: string;
  links: FooterLink[];
};

const columns: FooterColumn[] = [
  {
    heading: "Project",
    links: [
      { title: "GitHub", href: siteConfig.github, external: true },
      { title: "arXiv", href: siteConfig.arxiv, external: true },
      {
        title: "Releases",
        href: `${siteConfig.github}/releases`,
        external: true,
      },
    ],
  },
  {
    heading: "Docs",
    links: [
      { title: "Guide", href: "/docs/guide/overview" },
      { title: "Verification", href: "/docs/verification/overview" },
      { title: "Examples", href: "/examples" },
      { title: "API reference", href: "/api/", external: true },
    ],
  },
  {
    heading: "Trust",
    links: [
      {
        title: "Trust boundaries",
        href: "/docs/governance/trust-boundaries",
      },
      {
        title: "Third-party",
        href: "/docs/governance/third-party",
      },
    ],
  },
];

function FooterLinkItem({ link }: { link: FooterLink }) {
  const className =
    "text-muted-foreground hover:text-foreground transition-colors";
  if (link.external) {
    return (
      <a
        href={link.href}
        target="_blank"
        rel="noopener noreferrer"
        className={className}
      >
        {link.title}
      </a>
    );
  }
  return (
    <Link href={link.href} className={className}>
      {link.title}
    </Link>
  );
}

export function Footer() {
  return (
    <footer className="border-t bg-background">
      <div className="mx-auto w-full max-w-screen-2xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-4">
          <div className="md:col-span-1">
            <p className="text-sm font-semibold tracking-tight text-foreground">
              {siteConfig.name}
            </p>
            <p className="mt-3 max-w-xs text-sm text-muted-foreground">
              {siteConfig.description.split(".")[0]}.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-8 md:col-span-3 md:grid-cols-3">
            {columns.map((column) => (
              <div key={column.heading}>
                <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
                  {column.heading}
                </p>
                <ul className="mt-3 space-y-2 text-sm">
                  {column.links.map((link) => (
                    <li key={`${column.heading}-${link.title}`}>
                      <FooterLinkItem link={link} />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-12 border-t pt-6 text-xs text-muted-foreground">
          <p>
            &copy; 2026 {siteConfig.name} contributors &middot; MIT License
          </p>
        </div>
      </div>
    </footer>
  );
}
