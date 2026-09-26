// halcyon Copr mirror — the Cloudflare Worker that repo/halcyon-mirror.repo
// points at. Pass-through proxy: <worker>/<path> maps onto the Copr download
// tree and streams through Cloudflare's edge, which is dramatically faster
// than the direct route to Copr's S3-backed download path. No credentials,
// no storage, nothing to sync — it always reflects what Copr publishes.
//
// Deploy once: Cloudflare dashboard → Workers & Pages → Create application
// → Create Worker → "Start with Hello World!" → name it halcyon-mirror →
// Deploy → Edit code → paste this file → Deploy. Free plan, no card.
//
// Caching: RPMs are immutable, so GET responses cache at the edge for a
// year; repodata changes per build and caches for 5 minutes. Files over
// the free plan's 512 MB cache limit (texlive-fontsextra) simply skip the
// cache and always stream through. HEAD passes through untouched — the
// Cache API only stores GET responses. The upstream index pages emit
// absolute hrefs (/results/aahsnr-work/halcyon/...), so that path form is
// normalized — clicking links on a proxied listing works.

const UPSTREAM = "https://download.copr.fedorainfracloud.org/results/aahsnr-work/halcyon";
const PREFIX = "/results/aahsnr-work/halcyon";

function upstreamPath(pathname) {
  return pathname.startsWith(PREFIX + "/")
    ? pathname.slice(PREFIX.length)
    : pathname;
}

export default {
  async fetch(request) {
    if (request.method !== "GET" && request.method !== "HEAD")
      return new Response("GET/HEAD only", { status: 405 });

    if (request.method === "HEAD") {
      const h = await fetch(UPSTREAM + upstreamPath(new URL(request.url).pathname),
                            { redirect: "follow" });
      return new Response(null, { status: h.status, headers: h.headers });
    }

    const url = new URL(request.url);
    const p = upstreamPath(url.pathname);
    const cache = caches.default;
    const hit = await cache.match(request);
    if (hit) return hit;

    const upstream = await fetch(UPSTREAM + p, { redirect: "follow" });
    if (upstream.status !== 200) return upstream;
    const resp = new Response(upstream.body, upstream);
    resp.headers.set("Cache-Control", p.startsWith("/repodata/")
      ? "public, max-age=300" : "public, max-age=31536000, immutable");
    await cache.put(request, resp.clone());
    return resp;
  },
};
