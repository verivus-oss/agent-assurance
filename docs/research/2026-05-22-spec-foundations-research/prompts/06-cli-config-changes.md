# CLI MCP-config changes made during this research

Two of the three delegated CLI agents did not have the Exa MCP server
registered locally. To enable the research, Exa was added to both. Codex
already had Exa configured before this session.

## Gemini

Before:

```
$ gemini mcp list
No MCP servers configured.
```

Command run:

```bash
gemini mcp add -s user exa /home/werner/.local/bin/exa-mcp-from-azure
```

After:

```
$ gemini mcp list
Configured MCP servers:
✓ exa: /home/werner/.local/bin/exa-mcp-from-azure  (stdio) - Connected
```

Persisted to `~/.gemini/settings.json` (user-scope config).

## Grok

Before:

```
$ grok mcp list
No MCP servers configured. Run `grok mcp add --help` to get started.
```

Command run:

```bash
grok mcp add exa --command /home/werner/.local/bin/exa-mcp-from-azure
```

After:

```
$ grok mcp list
  exa: /home/werner/.local/bin/exa-mcp-from-azure
```

Persisted to `~/.grok/config.toml`.

## Codex (no change needed)

Codex already had Exa configured in `~/.codex/config.toml`:

```toml
[mcp_servers.exa]
command = "/home/werner/.local/bin/exa-mcp-from-azure"
args = []
```

## Underlying MCP binary

All three CLIs point at the same binary:
`/home/werner/.local/bin/exa-mcp-from-azure`. That binary's
implementation is outside the scope of this research dossier; it
exposes the Exa search/research tools over MCP stdio.
