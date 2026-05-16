/**
 * Cloudflare Worker for the Gondolin docs site.
 *
 * The site is a Next.js static export (`output: "export"`) served from the
 * `ASSETS` binding, plus a statically-hosted DocGen4 API reference under
 * `/api/`. Those two have conflicting URL conventions:
 *
 *   - Next.js export emits `out/docs/x.html` and links to it as `/docs/x`
 *     (extensionless).
 *   - DocGen4 emits `out/api/.../Foo.html` and links to it with the
 *     explicit `.html` extension.
 *
 * Cloudflare's built-in `html_handling` modes can satisfy only one of those
 * (e.g. `auto-trailing-slash` 307-redirects every `.html` request, which
 * breaks DocGen4's relative link graph). So `html_handling` is set to
 * `"none"` in wrangler.jsonc and this Worker does the mapping itself:
 *
 *   1. www → apex canonical 308 redirect.
 *   2. Serve the asset as requested.
 *   3. On a miss, for an extensionless path, retry `<path>.html` then
 *      `<path>/index.html` — this powers the Next.js clean URLs while
 *      leaving DocGen4's explicit `.html` URLs untouched.
 *   4. Final miss → `/404.html`.
 *   5. Long-lived immutable caching for fingerprinted `/_next/static/*`.
 */

export interface Env {
  ASSETS: Fetcher;
}

const STATIC_PREFIX = "/_next/static/";
const APEX = "torchlean.org";

function hasFileExtension(pathname: string): boolean {
  const lastSlash = pathname.lastIndexOf("/");
  return pathname.slice(lastSlash + 1).includes(".");
}

function withImmutableCache(response: Response, pathname: string): Response {
  if (!pathname.startsWith(STATIC_PREFIX) || response.status !== 200) {
    return response;
  }
  const headers = new Headers(response.headers);
  headers.set("Cache-Control", "public, max-age=31536000, immutable");
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // 1. Canonicalise www → apex.
    if (url.hostname === `www.${APEX}`) {
      url.hostname = APEX;
      return Response.redirect(url.toString(), 308);
    }

    // 2. Try the asset exactly as requested.
    const direct = await env.ASSETS.fetch(request);
    if (direct.status !== 404) {
      return withImmutableCache(direct, url.pathname);
    }

    // 3. Miss + extensionless path → retry common static-export shapes.
    const { pathname } = url;
    if (!hasFileExtension(pathname)) {
      const candidates = pathname.endsWith("/")
        ? [`${pathname}index.html`]
        : [`${pathname}.html`, `${pathname}/index.html`];

      for (const candidate of candidates) {
        const candidateUrl = new URL(url);
        candidateUrl.pathname = candidate;
        const res = await env.ASSETS.fetch(new Request(candidateUrl, request));
        if (res.status !== 404) {
          return withImmutableCache(res, candidate);
        }
      }
    }

    // 4. Final miss → the static 404 page.
    const notFoundUrl = new URL(url);
    notFoundUrl.pathname = "/404.html";
    const notFound = await env.ASSETS.fetch(new Request(notFoundUrl, request));
    if (notFound.status === 200) {
      return new Response(notFound.body, {
        status: 404,
        statusText: "Not Found",
        headers: notFound.headers,
      });
    }
    return direct;
  },
} satisfies ExportedHandler<Env>;
