# DAG-TOML Agent Readiness

The site is designed for both humans and coding agents.

## Discovery Files

- `/llms.txt`
- `/sitemap.md`
- `/sitemap.xml`
- `/robots.txt`
- `/.well-known/agent.json`
- `/.well-known/agent-skills/index.json`

## Retrieval Pattern

Agents should:

1. Fetch `/llms.txt`.
2. Use `/sitemap.md` to select a page.
3. Prefer Markdown mirrors for context windows.
4. Use repository source files for normative details.
5. Run validators locally before treating a DAG-TOML file as conforming.

## Site Constraints

- Static Cloudflare Pages target.
- No required client-side JavaScript.
- Semantic HTML.
- Markdown alternates for primary pages.
- Structured metadata on the home page.
