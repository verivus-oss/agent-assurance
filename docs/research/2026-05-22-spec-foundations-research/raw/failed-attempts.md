# Failed CLI attempts — verbatim error logs

Four CLI runs failed during dossier preparation. Each was retried after a
parameter adjustment; the final successful attempts produced the saved
reports. The errors themselves are recorded here because they document
real friction between the `llm-cli-gateway` MCP shim and the local CLI
versions installed on this machine, which future readers will need to
diagnose if they reproduce the workflow.

## 1. Codex first-wave attempt 1 — `--ask-for-approval` unsupported

Job ID: `70050462-e0d4-4ce7-aff9-e8ebe2c893c5`
Started: 2026-05-21T23:59:14Z
Failed: +30ms

stderr:

```
error: unexpected argument '--ask-for-approval' found

  tip: to pass '--ask-for-approval' as a value, use '-- --ask-for-approval'

Usage: codex exec [OPTIONS] [PROMPT]
       codex exec [OPTIONS] <COMMAND> [ARGS]

For more information, try '--help'.
```

Cause: the gateway emitted `--ask-for-approval` as a flag, but the
locally-installed Codex CLI (v0.132.0) does not accept it. The flag
is documented for newer Codex CLI builds; the gateway and local CLI
were out of sync.

Resolution: dropped the `askForApproval` parameter from the gateway
call. (Codex still ran in `--ask-for-approval never` mode by default
because of the local sandbox config.)

## 2. Codex first-wave attempt 2 — `--search` unsupported

Job ID: `44e9d88a-b3f3-4315-84a9-db506b24559a`
Started: 2026-05-22T00:01:09Z
Failed: +30ms

stderr:

```
error: unexpected argument '--search' found

  tip: to pass '--search' as a value, use '-- --search'

Usage: codex exec [OPTIONS] [PROMPT]
       codex exec [OPTIONS] <COMMAND> [ARGS]

For more information, try '--help'.
```

Cause: gateway emitted `--search` to enable web search. Local Codex
CLI did not recognize it. (Codex still has Exa available through its
own MCP config in `~/.codex/config.toml`, so search remained
available even without this flag.)

Resolution: dropped `search=true` from the gateway call.

## 3. Codex first-wave attempt 3 — SUCCEEDED

Job ID: `1d0bcb23-8199-4015-850c-0dae2c9d163b`
Duration: 414s. Output: `02-codex-with-exa.md`.

## 4. Grok first-wave attempt 1 — `reasoningEffort` rejected

Job ID: `3e2046c9-4c03-417e-b818-e065bbb1cc1a`
Started: 2026-05-21T23:59:42Z
Failed: +7.4s

stderr (truncated):

```
ERROR responses API error status=400 Bad Request error_message=Client
specified an invalid argument: Model grok-build does not support parameter
reasoningEffort.

Request URL: https://cli-chat-proxy.grok.com/v1/responses model_id=grok-build
```

Cause: gateway forwarded `reasoningEffort=high` but the `grok-build`
model on xAI's CLI proxy does not expose that parameter. Documentation
implied it should; the API surface had drifted.

Resolution: removed the `effort` field from the gateway call.

## 5. Grok first-wave attempt 2 — SUCCEEDED

Job ID: `471c8ac0-9d02-404c-beea-a9f95c2e6410`
Duration: 70s. Output: `04-grok-with-exa.md`.

## 6. Gemini transient 429s (recovered automatically)

Job ID: `a484d116-043c-4dd4-9d5e-9e139b8829d9`

stderr contained:

```
Attempt 1 failed with status 429. Retrying with backoff... _GaxiosError: [{
  "error": {
    "code": 429,
    "message": "No capacity available for model gemini-3.1-pro-preview on the server",
    ...
    "reason": "MODEL_CAPACITY_EXHAUSTED"
  }
}]
```

The Gemini CLI's internal backoff handled this; the job completed
successfully after the second attempt. The error is recorded here
because it indicates intermittent rate-limiting on the
`gemini-3.1-pro-preview` model; future re-runs may experience the same.

## 7. Gemini follow-up wave — 5x Exa rate-limit errors mid-run

Job ID: `a1bba74a-87ef-45c1-934c-48fadc1c1b94`

stderr contained:

```
Error executing tool mcp_exa_web_search_advanced_exa: Error: MCP tool 'web_search_advanced_exa' reported an error.
... (5 occurrences)
```

The Gemini CLI continued past these errors and produced complete output
using fewer Exa searches than originally requested. Output quality was
not noticeably affected; the diff is the smaller number of cited URLs in
some sections.

## Summary

| CLI | Wave | Attempts | Successes | Failure modes |
|---|---|---|---|---|
| Codex | first | 3 | 1 | gateway/CLI flag mismatch (×2) |
| Codex | follow-up | 1 | 1 | — |
| Gemini | first | 1 | 1 | transient 429 (auto-recovered) |
| Gemini | follow-up | 1 | 1 | Exa rate-limit (×5, recovered) |
| Grok | first | 2 | 1 | unsupported model parameter |
| Grok | follow-up | 1 | 1 | — |

Friction is concentrated at the gateway↔CLI flag boundary. The CLI
adapters in `llm-cli-gateway` lag behind upstream CLI releases.
Future reproductions should expect to drop flags that newer or older
local CLIs reject.
