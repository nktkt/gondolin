import type { MDXComponents } from "mdx/types";
import { isValidElement, type ReactElement } from "react";
import type {
  AnchorHTMLAttributes,
  HTMLAttributes,
  OlHTMLAttributes,
  TableHTMLAttributes,
  ThHTMLAttributes,
  TdHTMLAttributes,
} from "react";

import { cn } from "@/lib/utils";
import { CodeBlock } from "@/components/site/code-block";

type HeadingProps = HTMLAttributes<HTMLHeadingElement>;

function HeadingAnchor({ id }: { id?: string }) {
  if (!id) return null;
  return (
    <a
      href={`#${id}`}
      aria-label="Link to this section"
      className="ml-2 text-muted-foreground/60 opacity-0 transition-opacity group-hover:opacity-100 hover:text-primary no-underline"
    >
      #
    </a>
  );
}

function H1({ className, children, id, ...rest }: HeadingProps) {
  return (
    <h1
      id={id}
      className={cn(
        "group scroll-mt-24 mt-2 mb-6 text-3xl md:text-4xl font-semibold tracking-tight text-foreground",
        className,
      )}
      {...rest}
    >
      {children}
      <HeadingAnchor id={id} />
    </h1>
  );
}

function H2({ className, children, id, ...rest }: HeadingProps) {
  return (
    <h2
      id={id}
      className={cn(
        "group scroll-mt-24 mt-10 mb-3 pb-2 text-2xl font-semibold tracking-tight text-foreground border-b border-border/60",
        className,
      )}
      {...rest}
    >
      {children}
      <HeadingAnchor id={id} />
    </h2>
  );
}

function H3({ className, children, id, ...rest }: HeadingProps) {
  return (
    <h3
      id={id}
      className={cn(
        "group scroll-mt-24 mt-8 mb-2 text-xl font-semibold tracking-tight text-foreground",
        className,
      )}
      {...rest}
    >
      {children}
      <HeadingAnchor id={id} />
    </h3>
  );
}

function H4({ className, children, id, ...rest }: HeadingProps) {
  return (
    <h4
      id={id}
      className={cn(
        "group scroll-mt-24 mt-6 mb-2 text-lg font-semibold tracking-tight text-foreground",
        className,
      )}
      {...rest}
    >
      {children}
      <HeadingAnchor id={id} />
    </h4>
  );
}

function Paragraph({ className, ...rest }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("leading-relaxed text-foreground/90 mb-4", className)}
      {...rest}
    />
  );
}

function Anchor({
  href,
  className,
  children,
  ...rest
}: AnchorHTMLAttributes<HTMLAnchorElement>) {
  const isExternal = typeof href === "string" && /^https?:\/\//.test(href);
  return (
    <a
      href={href}
      target={isExternal ? "_blank" : undefined}
      rel={isExternal ? "noopener noreferrer" : undefined}
      className={cn(
        "text-primary underline-offset-4 hover:underline",
        className,
      )}
      {...rest}
    >
      {children}
    </a>
  );
}

function UnorderedList({ className, ...rest }: HTMLAttributes<HTMLUListElement>) {
  return (
    <ul
      className={cn("my-4 ml-6 list-disc marker:text-muted-foreground", className)}
      {...rest}
    />
  );
}

function OrderedList({
  className,
  ...rest
}: OlHTMLAttributes<HTMLOListElement>) {
  return (
    <ol
      className={cn("my-4 ml-6 list-decimal marker:text-muted-foreground", className)}
      {...rest}
    />
  );
}

function ListItem({ className, ...rest }: HTMLAttributes<HTMLLIElement>) {
  return <li className={cn("mb-1 leading-relaxed", className)} {...rest} />;
}

function InlineCode({ className, ...rest }: HTMLAttributes<HTMLElement>) {
  return (
    <code
      className={cn(
        "bg-muted px-1 py-0.5 rounded font-mono text-sm",
        className,
      )}
      {...rest}
    />
  );
}

function PlainPre({ className, ...rest }: HTMLAttributes<HTMLPreElement>) {
  return (
    <pre
      className={cn(
        "bg-muted rounded-lg p-4 overflow-x-auto my-4 text-sm border border-border/60",
        className,
      )}
      {...rest}
    />
  );
}

type CodeChildProps = {
  className?: string;
  children?: unknown;
};

// With next-mdx-remote/rsc, `pre`'s children is a single
// <code className="language-xxx">{rawString}</code> element. We extract the
// raw code + language and hand it to the Shiki-backed CodeBlock instead of
// rendering the original <code> child (so InlineCode never wraps block code).
async function MdxPre({
  children,
  ...rest
}: HTMLAttributes<HTMLPreElement>) {
  if (!isValidElement(children)) {
    return <PlainPre {...rest}>{children}</PlainPre>;
  }

  const codeProps = (children as ReactElement<CodeChildProps>).props;
  const rawChildren = codeProps?.children;

  if (rawChildren == null) {
    return <PlainPre {...rest}>{children}</PlainPre>;
  }

  const rawCode = (
    typeof rawChildren === "string" ? rawChildren : String(rawChildren)
  ).replace(/\n$/, "");

  const className = codeProps?.className ?? "";
  const match = /language-([\w-]+)/.exec(className);
  const lang = match ? match[1] : "text";

  return <CodeBlock code={rawCode} lang={lang} />;
}

function Table({ className, ...rest }: TableHTMLAttributes<HTMLTableElement>) {
  return (
    <div className="my-6 w-full overflow-x-auto rounded-lg border border-border/60">
      <table
        className={cn("w-full text-sm border-collapse", className)}
        {...rest}
      />
    </div>
  );
}

function THead({ className, ...rest }: HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className={cn("bg-muted/60", className)} {...rest} />;
}

function TR({ className, ...rest }: HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(
        "border-b border-border/60 last:border-b-0 transition-colors hover:bg-muted/30",
        className,
      )}
      {...rest}
    />
  );
}

function TH({ className, ...rest }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        "px-4 py-2 text-left font-semibold text-foreground border-r border-border/60 last:border-r-0",
        className,
      )}
      {...rest}
    />
  );
}

function TD({ className, ...rest }: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={cn(
        "px-4 py-2 align-top text-foreground/90 border-r border-border/60 last:border-r-0",
        className,
      )}
      {...rest}
    />
  );
}

function Blockquote({
  className,
  ...rest
}: HTMLAttributes<HTMLQuoteElement>) {
  return (
    <blockquote
      className={cn(
        "my-4 border-l-4 border-primary/60 bg-muted/40 pl-4 pr-3 py-2 italic text-foreground/90 rounded-r-md",
        className,
      )}
      {...rest}
    />
  );
}

function HR({ className, ...rest }: HTMLAttributes<HTMLHRElement>) {
  return <hr className={cn("my-8 border-border/60", className)} {...rest} />;
}

function Strong({ className, ...rest }: HTMLAttributes<HTMLElement>) {
  return (
    <strong
      className={cn("font-semibold text-foreground", className)}
      {...rest}
    />
  );
}

export const mdxComponents: MDXComponents = {
  h1: H1,
  h2: H2,
  h3: H3,
  h4: H4,
  p: Paragraph,
  a: Anchor,
  ul: UnorderedList,
  ol: OrderedList,
  li: ListItem,
  code: InlineCode,
  pre: MdxPre,
  table: Table,
  thead: THead,
  tr: TR,
  th: TH,
  td: TD,
  blockquote: Blockquote,
  hr: HR,
  strong: Strong,
};
