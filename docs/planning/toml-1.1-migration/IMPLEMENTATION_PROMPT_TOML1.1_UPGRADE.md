# Implementation prompt — TOML 1.1 upgrade

A self-contained prompt for a fresh session to implement the TOML 1.0 → 1.1
migration scoped by this pack, following the project's review/governance
process. Paste everything in the fenced block below as the session's task.

---

```
Implement the TOML 1.0 → 1.1 migration for the agent-assurance repo, following the project's
review/governance process. A complete DAG-TOML scoping pack already exists and is authoritative.

## Start here
Read these first — they define the scope, the work units, and the hard constraints:
- docs/planning/toml-1.1-migration/README.md                  (pack index + status)
- docs/planning/toml-1.1-migration/01_spec.md                 (normative requirements R1–R5)
- docs/planning/toml-1.1-migration/03_implementation_plan.md  (decomposition rationale + risks)
- docs/planning/toml-1.1-migration/implementation-dag.toml    (the 8-unit work DAG, U01–U08)
- docs/planning/toml-1.1-migration/contract-declaration.toml  (contracts C01–C04)
- docs/planning/toml-1.1-migration/readiness-gate.toml        (gates G01/G02)
- docs/planning/toml-1.1-migration/rollback-plan.toml

## The one constraint that governs everything (R1 / contract C01)
The repo's foundational invariant is that the Rust, Go, and Python PRIMARY parsers agree
byte-for-byte on every conformance fixture. Today they are split across TOML versions:
Rust `toml` has a 1.1 line (1.1.x+spec-1.1.0, already used by tools/dagtoml-rdf), but the Go
primary (BurntSushi/toml) and the Python reference (stdlib `tomllib`) are TOML 1.0. Adopting
1.1 in one parser while the others stay 1.0 manufactures the exact divergence the conformance
suite exists to catch. THEREFORE: TOML 1.1 may land only if all three primaries reach 1.1 in
lockstep.

## Execution order — DO NOT skip the gate
Work the DAG in dependency order. The gate is real, not ceremony:
1. U01 parser-availability-spike — survey TOML 1.1 support for Go BurntSushi (which release, at
   what toml-test spec level) and for Python (identify a 1.1-capable, hash-pinnable replacement
   for stdlib tomllib; assess its supply-chain/maintenance posture). Rust 1.1 is already proven.
   Write the findings to docs/planning/toml-1.1-migration/research/01-parser-availability-survey.md.
2. U02 parity go/no-go decision — record GO only if a viable 1.1 parser exists for ALL THREE
   primaries (Go must also preserve the no-`unsafe` safe-tools policy). If any cannot, record
   NO-GO in research/02-parity-decision.md, STOP, and report the blocker. Do NOT bump any parser.
   ** This decision is a STOP/GO point — surface it to me before proceeding past it. **
3. Only on GO: U03 (Rust→1.1), U04 (Go→1.1), U05 (Python→1.1) — independent, may parallelize.
4. U06 conformance-harness-1.1 — flip toml-test to `-toml 1.1.0`, fold in the toml-test-decode-rs
   shim work, retitle the CI step. (Under the 1.0 corpus, the 1.1 parser "fails" 9 invalid cases
   like `17:45` and `"\x33"` — those become valid at 1.1; the flip is what makes them pass.)
5. U07 spec-document-1.1-audit — for EVERY TOML 1.1 feature that newly becomes parseable, add an
   explicit permit/forbid disposition to spec.md (R4 / contract C03). A feature may not enter the
   conforming surface by parser default alone.
6. U08 cross-impl verification — rs/go/py agree on the full toml-test 1.1 corpus AND the dagtoml
   corpus, with an empty known-divergences baseline.

## Process discipline (non-negotiable)
- VALIDATE LOCALLY before every push. The pack README lists the commands; minimally:
  build the rs + go primaries, run `python3 validators/validate_closure_root.py --discover .`,
  `make dagtoml-conformance`, the toml-conformance targets, and the kind-specific validators.
  rs/go/py MUST agree — a divergence is a blocker, not a skiplist entry.
- CROSS-LLM REVIEW GATE for every validator/spec/DAG-TOML change (use the cross-llm-review skill /
  the gtwy or llm-cli-gateway MCP gateway). Dispatch Codex + Gemini + Grok with full repo access
  and the real diff + a verification report. Reviewers must verify claims against the code/docs
  themselves, not your summary. Poll every 90s if grants aren't durable. If you disagree with a
  finding, rebut with file:line / doc / test evidence, never assertion. Iterate to UNCONDITIONAL
  approval or a concrete unresolvable blocker. Do not seek approval on intent / plan-compliance /
  "should be fixed" language.
- NO SELF-APPROVAL. You author the work; you do not approve it. The CODEOWNERS approval is a human
  act from me (verivus-open). Never submit a GitHub approval via my account.
- OPEN PRs AS THE BOT, not verivus-open. verivus-open is my code-owner approval account and GitHub
  forbids approving your own PR — a verivus-open-authored PR is unapprovable and stalls. Create PRs
  with `GH_CONFIG_DIR=/home/werner/.config/gh-verivusOSS-releases gh pr create ...`. Pushing
  branches is fine under the default account; only PR AUTHORSHIP must be the bot.
- EVERY PR updates CHANGELOG.md under [Unreleased].
- NEVER add a Claude/AI co-author trailer (no `Co-Authored-By: Claude`, no "Generated with") to any
  commit, PR, or comment. Hard rule.
- Do not cite operator-private memory/ files as load-bearing evidence in repo artifacts.
- Branch protection dismisses stale reviews; if you push after approval, it must be re-approved.
- Keep PRs scoped per unit (or per coherent unit-cluster) so each is independently reviewable and
  revertable, matching the DAG. Land them in dependency order.

## Done means
U08 records rs/go/py agreement on the TOML 1.1 corpus with an empty known-divergences baseline,
spec.md carries an explicit disposition for every 1.1 feature, CHANGELOG is updated, every PR
passed the cross-LLM gate and CI, and the readiness-gate G02 status reflects the outcome. If U02
is NO-GO, "done" is the negative outcome: blocker recorded, no parser changes landed, repo stays
uniformly TOML 1.0.

Update the pack's unit `status` fields and readiness-gate status as you progress. Start by reading
the pack, then do U01.
```
