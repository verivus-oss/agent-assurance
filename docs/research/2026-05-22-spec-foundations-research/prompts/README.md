# Prompts — what was asked, by whom, with what parameters

This directory exists for **research reproducibility**. It records every
prompt sent during the dossier's preparation, in the order they were
issued, so any future reader can:

1. Verify the prompts didn't lead the answers
2. Re-run the queries (the prompts are verbatim)
3. Trace each response file back to the prompt that produced it

## Contents

- `00-user-messages.md` — the user's original requests, verbatim
- `01-first-wave-agent-brief.md` — combined Codex/Gemini/Grok brief sent in the first wave (IJB primitives + 5 other questions)
- `02-first-wave-exa-deep-researcher.md` — Exa Deep Researcher instructions for the IJB primitives prior-art study
- `03-first-wave-claude-exa-searches.md` — 11 Claude-driven Exa search queries that supplemented the delegated agents
- `04-follow-up-agent-brief.md` — combined Codex/Gemini/Grok brief sent in the second wave (Streams A/B/C/D)
- `05-follow-up-exa-deep-researchers.md` — 4 Exa Deep Researcher instruction sets (one per stream)
- `06-cli-config-changes.md` — `gemini mcp add` and `grok mcp add` commands run to enable Exa MCP for the two delegated CLIs that didn't have it

## Cross-reference: prompts → responses

| Prompt file | Sent to | Response file |
|---|---|---|
| `01-first-wave-agent-brief.md` | Codex | `../02-codex-with-exa.md` |
| `01-first-wave-agent-brief.md` | Gemini | `../03-gemini-with-exa.md` |
| `01-first-wave-agent-brief.md` | Grok | `../04-grok-with-exa.md` |
| `02-first-wave-exa-deep-researcher.md` | Exa Deep Researcher (`exa-research-pro`) | `../01-exa-deep-researcher.md` |
| `03-first-wave-claude-exa-searches.md` | Exa (Claude-driven) | `../05-claude-exa-searches.md` |
| `04-follow-up-agent-brief.md` | Codex | `../follow-up/codex-streams-a-b-c-d.md` |
| `04-follow-up-agent-brief.md` | Gemini | `../follow-up/gemini-streams-a-b-c-d.md` |
| `04-follow-up-agent-brief.md` | Grok | `../follow-up/grok-streams-a-b-c-d.md` |
| `05-follow-up-exa-deep-researchers.md` Stream A | Exa Deep (`exa-research`) | `../follow-up/exa-deep-a-kind-descriptor-drift.md` |
| `05-follow-up-exa-deep-researchers.md` Stream B | Exa Deep (`exa-research-pro`) | `../follow-up/exa-deep-b-legal-grade-attestation.md` |
| `05-follow-up-exa-deep-researchers.md` Stream C | Exa Deep (`exa-research`) | `../follow-up/exa-deep-c-separation-of-duty.md` |
| `05-follow-up-exa-deep-researchers.md` Stream D | Exa Deep (`exa-research`) | `../follow-up/exa-deep-d-format-selection.md` |

## Total spend (Exa Deep Researcher only)

| Research ID | Stream | Model | Cost | Searches |
|---|---|---|---|---|
| `r_01ks6fpjaqrsh8e4dz6y7tkx8j` | IJB primitives (first wave) | `exa-research-pro` | $1.16 | 36 |
| `r_01ks6k8dwpnrb5zqgenfvvj0cq` | B — legal-grade attestation | `exa-research-pro` | $2.22 | 64 |
| `r_01ks6k93rr0jn5kps3b70v98fm` | A — kind-descriptor drift | `exa-research` | $1.16 | 70 |
| `r_01ks6k9p13ym0bfj9x0ytbb1rd` | C — separation-of-duty | `exa-research` | $1.67 | 93 |
| `r_01ks6kackkhzfdckbt1e5a9zn5` | D — format selection | `exa-research` | $0.93 | 54 |
| **Total Exa Deep** | | | **$7.14** | **317** |

(Codex/Gemini/Grok CLI calls billed separately under their respective
API accounts; rough estimate is in low single-digit USD for the
combined six runs.)
