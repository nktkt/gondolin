/**
 * Minimal Cloudflare Worker for the TorchLean docs site.
 *
 * The site is built as a Next.js static export (`output: "export"`), so
 * almost everything is served directly from the `ASSETS` binding by the
 * Workers Static Assets runtime — including `html_handling: "auto-trailing-slash"`
 * and a `404.html` fallback. This Worker only:
 *
 *   1. Sends bare apex/www requests through ASSETS as-is.
 *   2. Adds long-lived caching headers for `/_next/static/*` (immutable, content-hashed).
 *   3. Redirects `www.torchlean.org/<path>` → `torchlean.org/<path>`.
 *
 * If you delete `main` from wrangler.jsonc, Workers will still serve the
 * site correctly — this file is purely for the canonical-host redirect
 * and asset cache headers.
 */

export interface Env {
  ASSETS: Fetcher;
}

const STATIC_PREFIX = "/_next/static/";
const APEX = "torchlean.org";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Canonicalise www → apex.
    if (url.hostname === `www.${APEX}`) {
      url.hostname = APEX;
      return Response.redirect(url.toString(), 308);
    }

    const response = await env.ASSETS.fetch(request);

    // Immutable cache headers for fingerprinted Next.js static chunks.
    if (url.pathname.startsWith(STATIC_PREFIX) && response.status === 200) {
      const headers = new Headers(response.headers);
      headers.set("Cache-Control", "public, max-age=31536000, immutable");
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    }

    return response;
  },
} satisfies ExportedHandler<Env>;
