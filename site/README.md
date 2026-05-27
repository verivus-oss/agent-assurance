# DAG-TOML Site

Static Cloudflare Pages draft for the DAG-TOML specification.

Canonical draft hostname: `https://agent-assurance.dev`

Pages project name: `agent-assurance`

## Structure

- `index.html` and `index.md`: human and Markdown overview
- `spec/`: specification overview
- `profiles/`: profile overview
- `validators/`: validator overview
- `compare/`: protocol positioning
- `agent-readiness/`: machine-readable discovery notes
- `llms.txt`, `sitemap.md`, `sitemap.xml`, `robots.txt`: discovery files
- `.well-known/agent.json`, `.well-known/agent-skills/index.json`: agent metadata
- `/agent.json`, `/agent-skills.json`: rewrites for tools that check root-level manifests
- `ab02de421738fed7233351db2d3ab5f4a4fbddb8050cc6c977b2fc940b8c8a68.txt`: IndexNow ownership key

## Indexing

`robots.txt` points crawlers to `sitemap.xml`. The XML sitemap includes the HTML pages, Markdown mirrors, `llms.txt`, and agent metadata.

After deployment, submit changed URLs through IndexNow:

```sh
npm run site:indexnow
```

Google Search Console submission requires a verified property and OAuth credentials with the `webmasters` scope. Without those credentials, the site still exposes the sitemap through `robots.txt` for the next crawl.

## Local Check

```sh
npm run site:check
python3 -m http.server 4173 --directory site
```

Open `http://127.0.0.1:4173/`.

## Deploy

The repository includes a manual GitHub Actions workflow:

```text
.github/workflows/deploy-site.yml
```

It expects these repository secrets:

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

Cloudflare API MCP is configured in the local Claude MCP user scope, not exposed as a direct Codex MCP namespace in this session. A read-only Cloudflare API MCP inventory on 2026-05-27 found active zones for `agent-assurance.dev`, `agentassurance.dev`, `agent-assurance.io`, and `agentassurance.io`, and did not find a `verivus.com` zone or `dag-toml.verivus.com` DNS record/custom domain in the accessible account. Use `agent-assurance.dev` as canonical; reserve the non-hyphenated and `.io` variants as redirects after deployment.
