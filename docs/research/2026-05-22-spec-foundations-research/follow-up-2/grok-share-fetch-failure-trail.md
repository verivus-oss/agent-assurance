# Grok share URL fetch — diagnostic trail

Target: <https://grok.com/share/c2hhcmQtMi1jb3B5_8bddbdcc-14f9-4339-a313-b1c3c39724c0>

The share code's base64 prefix `c2hhcmQtMi1jb3B5` decodes to
`shard-2-copy` (a Grok internal designation), followed by a UUID
`8bddbdcc-14f9-4339-a313-b1c3c39724c0`.

## Attempt 1 — Grok CLI with Exa MCP (`web_fetch_exa`, `crawling_exa`)

Job ID: `5890cc4e-4893-498f-9849-386cb9684a20`. Duration: 51s.
Grok's exit message:

> The fetched content is incomplete at the root level — the entire
> message body is missing. ... The page at `https://grok.com/share/...`
> is a JavaScript-heavy single-page application. The static HTML shell
> served to non-browser fetchers contains only the `<title>` and a
> minimal heading. The actual conversation history is loaded
> dynamically (likely via client-side API calls or hydration after JS
> execution). None of the available content-fetching tools (exa MCP
> `web_fetch_exa`/`crawling_exa`, or the built-in `web_fetch`) execute
> JavaScript or perform browser-level rendering, so the conversation
> payload is inaccessible.

## Attempt 2 — `curl` with Mozilla user-agent

Response: 398KB of HTML, none of which contained conversation content
— only Next.js bundles and OG/Twitter metadata. Confirmed Grok's
diagnosis: pure client-side rendering.

The Next.js page DID contain three useful metadata items:

- `<title>Secure .toml Hosting on Cloudflare | Shared Grok Conversation</title>`
- `<meta property="og:description" content="this only partially covers it...  the issue is probably closer to achieving what is called zero trus...">`
- `<meta property="og:image" content=".../opengraph-image/...">` — an
  auto-generated PNG card with one rendered exchange in it.

## Attempt 3 — Probed `/api/share/`, `/api/conversations/share/`, `/api/v1/share/`

All returned `200 OK` with `Content-Type: text/html` — they were
absorbed by Next.js routing and returned the same client-side shell.
No public JSON API surfaced.

## Attempt 4 — Downloaded the OG image

PNG, 1200×630. Contained text from the most-recent exchange only:

User: "this only partially covers it... the issue is probably closer
to achieving what is called zero trust, sort of. the section below is..."

Grok: "Understood. Thank you for the correction. You're right — my
previous framing only captured part of it. The deeper issue is more
fundamental. Refined Core Insight..."

This confirmed the conversation's topic (secure .toml hosting + zero
trust) and signaled there was more content past this point.

## Attempt 5 — Headless Chrome render (SUCCEEDED)

Detected `/usr/bin/google-chrome` available. Ran:

```bash
google-chrome --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=15000 \
  --dump-dom "https://grok.com/share/c2hhcmQtMi1jb3B5_8bddbdcc-14f9-4339-a313-b1c3c39724c0" \
  > rendered.html
```

Result: 1.4MB rendered HTML. After stripping `<script>`, `<style>`,
and tags, and trimming cookie/footer chrome, the conversation
extracted to **83.5KB of clean text**. Saved as
[`grok-share-secure-toml-cloudflare-raw.md`](./grok-share-secure-toml-cloudflare-raw.md).

## Caveats for future work

- The extraction does not preserve explicit turn boundaries
  (user / Grok). Grok's share UI renders these visually but tags them
  with CSS classes that don't survive the strip-tags pass; a future
  refinement could parse the DOM with a proper HTML parser and
  preserve role markers.
- The render captured a single snapshot; if the conversation has
  expandable "Thought for N seconds" sections that load on demand,
  those may not all be present (a longer `--virtual-time-budget` or
  scrolling injection could be tried).
- Chrome warned about GPU/dbus subsystems but those did not block
  rendering. The job took ~15 seconds wall-clock.
