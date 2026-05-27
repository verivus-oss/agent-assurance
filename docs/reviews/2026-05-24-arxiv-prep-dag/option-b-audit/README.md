# Option B Audit — Codex, Iterated

**Purpose**: Independent audit of `proposed-mappings.toml` (the Opus-pre-pass corrective program for LL-001) by Codex with full access permissions and full MCP tool access.

**Posture**: Codex MUST verify every claim against the actual files. Codex MUST NOT accept any prose summary (in `proposed-mappings.toml.notes`, in any `README.md`, in `raw_findings/`, in `rebuttal_record.md`, or anywhere else) as evidence. Read the source. Run the validators. Run `rg` / `sqry` / `exa`. Approval must be based on inspected code, tests, docs, and persistent review evidence — not on intent, plan compliance claims, or "should be fixed" language.

**Iteration rule**: Loop until Codex returns `GATE DECISION: UNCONDITIONAL APPROVAL` or a concrete blocker list that cannot be resolved with evidence. If Claude (the orchestrator) disagrees with a Codex finding, Claude must respond with code/doc evidence — verbatim quotes and file paths — not assertion. Each iteration re-runs Codex with the prior verdict + the new evidence + the current artifact SHAs.

## Inputs Codex must read

| Artifact | Path | SHA-256 (at audit start) |
|---|---|---|
| Corrective program | `docs/reviews/2026-05-24-arxiv-prep-dag/fourth-pass/option-b/proposed-mappings.toml` | `d46253364305de05ce8934b0664c3d8956ce6193c1ed0b799dfb16fc515a6c6e` |
| Target DAG (round-3) | `arxiv-prep-agent-dag.toml` | `8f2b19f77a0c1e32e725d9ab9484965e5a601026696d7c3a37b6981668c6b383` |
| Pitfall corpus | `docs/reviews/2026-05-24-arxiv-prep-dag/arxiv-checklists-reference.txt` | `0e95cb3efc47c8d24dc7de309281f1c0e4adf7539af6ab1f3ca26204705d7851` |
| DAG kind descriptor | `core/implementation-dag-kind.toml` | (unchanged from HEAD) |
| Prior review trail (read for context) | `docs/reviews/2026-05-24-arxiv-prep-dag/{rebuttal_record.md, findings/*.toml, second-pass/raw_findings/codex.md, third-pass/raw_findings/codex.md, fourth-pass/raw_findings/codex.md, fourth-pass/option-b-opus-pass-prompt.md}` | (see git for current state) |

**HEAD commit**: `99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc`

**Untracked / modified files in scope** (relative to HEAD):
- `arxiv-prep-agent-dag.toml` (untracked, the target — round-3 patched)
- `docs/reviews/2026-05-24-arxiv-prep-dag/` (untracked, the full review trail)
- `tools/claim-analysis-document-review-dag.toml` (untracked, the review harness)

**Out of scope for this audit** (modified but unrelated to LL-001):
- `examples/proof-hello-world/*` (hello-world proof work)
- `paper/main.tex`, `paper/main_werner.tex`, `paper/references.bib` (paper work)
- `paper-hello-world/`, `docs/reviews/2026-05-23-*` (other review streams)

## Iterations

| # | Job ID | Session ID | Started | Finished | Verdict |
|---|---|---|---|---|---|
| 1 | `546e71db-bdf0-470b-80bd-8188d9ae7abb` | `4e0895f8-dab3-4b22-bcbf-2cb2266dc30d` | 2026-05-23T00:30:52Z | 2026-05-23T00:35:42Z | **STILL BLOCKED** — 6 evidence-grounded defects; see `raw_findings/codex-iter-1.md`. |
| 2 | `79c7110a-a107-447e-bd13-634bf6946c28` | `e5483c41-48e3-4e7b-8f1a-a4c9b45d9d0d` | 2026-05-23T00:47:20Z | 2026-05-23T00:50:16Z | **STILL BLOCKED — 5/6 resolved** — see `raw_findings/codex-iter-2.md`. Residue: Defect 6 missed two earlier prose blocks (lines 8–12, 24–29); stale `target_dag_sha256`. |
| 3 | `7a15d87e-521d-467d-baa9-d6d7150c158e` | `c0f70ed8-dae0-4a27-b237-3a14dc4ea7da` | 2026-05-23T00:53:00Z | 2026-05-23T00:56:38Z | **STILL BLOCKED — 1 new** — Defect 6 fully resolved; Blocker B (stale SHA) resolved. New finding: existing `[policy.checklist_coverage]` entry `texlive_2025.minted_v3_and_hyperxmp` over-claims (U07 covers minted but not hyperxmp load-order). See `raw_findings/codex-iter-3.md`. |
| 4 | `97e22ae1-e4f3-4d3c-b9f4-13bad7bedffc` | `3265f985-7dae-4b8a-9686-de10de2908d0` | 2026-05-23T01:00:07Z | 2026-05-23T01:04:07Z | **CONDITIONAL APPROVAL** (1 condition) — see `raw_findings/codex-iter-4.md`. Condition: `trevorcampbell.flatten_and_4pass` row in `[policy.checklist_coverage]` claims `ART:compile-and-pdf-evidence` but neither U02 nor U07 produces it (U08 does). |
| 5 | `42531dbf-3b86-4cfa-831f-cf1347ac31d9` | `c2fbd327-ee3f-40de-9dd3-fe0360319f74` | 2026-05-23T01:06:59Z | 2026-05-23T01:08:29Z | **HALTED on HEAD drift** (1 min 30 s) — Codex correctly stopped before audit work because HEAD moved from `99e18dba…` to `99968260…` between iter-4 and iter-5. Audit-target SHAs all matched. The new commit ("Full count-mirror cleanup", unrelated review stream) does NOT touch the audit substrate. See `raw_findings/codex-iter-5.md`. |
| 6 | `804146fc-ae67-4913-8e1c-a120fa9f647d` | `caedd016-05f2-48af-b1e3-4f6fc1abc626` | 2026-05-23T01:10:48Z | 2026-05-23T01:13:06Z | **GATE DECISION: UNCONDITIONAL APPROVAL** — see `raw_findings/codex-iter-6.md`. All 6 iter-1 defects + Blocker C + iter-4 condition independently re-verified RESOLVED at the new SHAs. Exhaustive 9-row sweep PASS. HEAD-drift independently re-verified BENIGN. |

## Terminal Outcome

**The corrective program (`proposed-mappings.toml`, 42 items, 10 documented gaps) has Codex's UNCONDITIONAL APPROVAL** as a valid Option-B plan to close LL-001 on the round-3-narrowed DAG. The audit is complete.

**Final artefact SHAs (audit-approved state):**
- proposed-mappings.toml: `dc7ebf2564e9ef830ac64f8814d83f16800a04e3b17acc0695f4b07c0d287532`
- arxiv-prep-agent-dag.toml: `b8ee50dc2b5c5fca63fe1a7eeecb3934973b778f2f7cce2ca3ed3627191ce69d`
- corpus: `0e95cb3efc47c8d24dc7de309281f1c0e4adf7539af6ab1f3ca26204705d7851`
- HEAD: `99968260900b4503a7ed9709c35c55e72bff6cca`

**Total work**: 6 iterations, ~12 minutes of Codex wall time, ~409K tokens spent across the audit chain. Six iter-1 defects → resolved. One iter-3 finding → resolved. One iter-4 condition → met. One iter-5 disciplined halt → re-verified benign and re-launched. Iter-6 → unconditional approval.

**Iteration 1 runtime params**: `sandboxMode=danger-full-access` (full write/exec access per user direction), `mcpServers=["sqry","exa","ref_tools"]`, `idleTimeoutMs=1800000` (30 min), `createNewSession=true`. Polling cadence: every 90 seconds.
