import type { ReactNode } from "react";

import Sidebar from "@/components/site/sidebar";
import MobileDocsNav from "@/components/site/mobile-docs-nav";

export default function DocsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto max-w-screen-2xl px-4 lg:px-6 flex gap-6">
      <Sidebar />
      <div className="min-w-0 flex-1 py-8 lg:py-12">
        <MobileDocsNav />
        {children}
      </div>
    </div>
  );
}
