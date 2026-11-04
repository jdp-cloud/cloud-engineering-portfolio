# Dependency security

## Next.js November 2026 security release (16.4.5)

The web app pins `next` and `eslint-config-next` to 16.4.5. That is the November 3, 2026 security release, and 16.4.5 is the Active LTS patch. The release notes are at <https://nextjs.org/blog/november-2026-security-release>.

The notes list seven advisories. One is high. The other six are medium. The shared-shell advisory has no GHSA id in the release notes.

Checked against `apps/web` on this pin. Searches were `use cache`, `unstable_cache`, `cacheComponents`, `export const runtime = "edge"`, `NextResponse.cookies.set`, `next/image`, an `images` config, and any route that returns a fetched `Response` unchanged.

| GHSA ID | Severity | Summary | Applies to this app? |
| --- | --- | --- | --- |
| GHSA-mfr8-8qww-v76h | High | With Cache Components on, a public `use cache` function called both directly and from `unstable_cache` can serve one root-parameter value's cached result to another. | No. `next.config.ts` does not set `cacheComponents`. The only mention is a comment that it stays off. No file contains `use cache` or `unstable_cache`. |
| GHSA-vc7v-qv4w-wrv8 | Medium | Nested public `use cache` functions can store an outer entry before the inner function's root-parameter dependencies are recorded, and a later request for another root parameter can receive that content. | No. Cache Components are off, and no file contains `use cache`. |
| GHSA-rhh4-g77r-r9qj | Medium | Distinct binary arguments to a `use cache` function can share one cache identity, so one caller's result can be served to another. | No. No file contains `use cache`. |
| none | Medium | A self-hosted app on `next start`, with Cache Components enabled and Partial Prefetching disabled or unset, can store request-specific values in a shared page shell. A crafted URL can then poison that shell for other URLs. | No. The image runs the standalone server, which is self-hosted, but `cacheComponents` is not enabled. The app also has no dynamic route parameters. `app/page.tsx` and `app/healthz/route.ts` set `export const dynamic = "force-dynamic"`. |
| GHSA-pc58-hwjq-p385 | Medium | A self-hosted app that returns an attacker-controlled fetched `Response` unchanged can forward decompressed bytes with the original compressed framing headers. Behind an HTTP/1.1 reverse proxy that queues pipelined requests on one backend connection, those responses can be assigned to the wrong clients. | No. The only server route is `app/healthz/route.ts`, and it returns `Response.json` of a local object. `app/hello-from-api.tsx` calls `fetch("/api/hello")` in the browser and reads the JSON. It does not return that `Response` from a server route. |
| GHSA-f3mh-rxg3-f5g2 | Medium | An Edge route that sets a cookie with `NextResponse.cookies.set()` can copy the cookie into `x-middleware-set-cookie`, which same-origin JavaScript can read. | No. `app/page.tsx` and `app/healthz/route.ts` set `export const runtime = "nodejs"`. No file sets `export const runtime = "edge"`. No file calls `NextResponse.cookies.set`. |
| GHSA-7qx7-33qx-rqx2 | Medium | An attacker-controlled image from a permitted source can be misclassified as AVIF and bypass `images.dangerouslyAllowSVG: false`, so the optimizer decodes the bytes as SVG. | No. No file imports `next/image`. `next.config.ts` has no `images` config. `next-env.d.ts` only has the generated reference to `next/image-types/global`. |

None of the seven apply to the code as it is. We upgraded anyway. 16.4.5 is the supported version, and later code could start using these features.
