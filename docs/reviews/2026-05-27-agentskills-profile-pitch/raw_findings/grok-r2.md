# Outbound-pitch review (grok r2) — 2026-05-27-agentskills-profile-pitch

**Iteration:** r2 (post-codex r1 findings + initiator fixes recorded in rebuttal_record.md)
**Units reviewed:**
- P01: `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md`
- P02: `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md`

**Verification basis:** All claims checked against current repo bytes at HEAD 3a480eb (this repo), exact bytes under `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/` and `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/`, and live fetches of `https://github.com/agentskills/agentskills` and `https://agentskills.io` performed during this review. Direct `read_file` + `grep` on the precise paths listed in the bundle verify list and in rebuttal_record.md were the primary evidence sources. The full rebuttal_record.md was read before any classification. sqry MCP was attempted for index-assisted location of triage/SKILL.md lines 10-14 and gate-decision-kind.toml fields but returned workspace-not-ready; all cited evidence was therefore confirmed via direct byte reads on the documented paths. No claim accepted on initiator summary or prior-review summaries. Classifications made afresh against the post-fix draft bytes present on disk at the time of this r2 pass.

The P01 "safe C" overclaim flagged in r1 has been removed; current P01:119-120 reads "safe Rust and safe Go" only. P02 received the three documented fixes (a) "in-production" → "working", (b) `**must**` restored in the quoted block, (c) gate-decision TOML fully rewritten to use only actual descriptor fields + correct subject_class + removal of fabricated `fresh_session` rule and `[disclaimer]` table.

---

## P01-C1: factual accuracy about agentskills/agentskills

**Classification:** complete

**Evidence (draft claims vs. bytes + live sources):**

- Format shape (SKILL.md + folder with optional scripts/, references/, assets/): exact match. research/agentskills/README.md:11-20 contains the identical code block and description; live https://agentskills.io fetch renders the same "At its core, a skill is a folder containing a `SKILL.md` file..." paragraph with the same four-item tree.
- Progressive disclosure across discovery/activation/execution: verbatim. research/agentskills/README.md:32-40 and the agentskills.io homepage fetch both contain: "Agents load skills through **progressive disclosure**, in three stages: 1. **Discovery**... 2. **Activation**... 3. **Execution**...".
- Client Showcase: present and linked. research/agentskills/README.md:44 links to https://agentskills.io/clients; the live homepage renders a scrolling logo carousel of clients under the exact heading "Where can I use Agent Skills?" and the navigation contains the /clients target.
- CONTRIBUTING.md: exists and governs proposals. research/agentskills/CONTRIBUTING.md:15-24 states "Proposals, Questions, and Feedback" belong in GitHub Discussions; the draft at P01:149-151 asks maintainers to name a preferred channel (Discord / Discussions / WG) and correctly defaults to Discussions.
- anthropics/skills companion repo: referenced as "Example Skills". research/agentskills/README.md:50 links "https://github.com/anthropics/skills" under the label "[Example Skills]".
- Homepage at agentskills.io: confirmed. research/agentskills/README.md:48 and the live site root both direct to it; GitHub "About" section and README:48 link to it.
- Apache-2.0 / CC-BY-4.0 licensing: exact. research/agentskills/README.md:59 states "Code in this repository is licensed under Apache 2.0. Documentation is licensed under CC-BY-4.0." Live GitHub page confirms the same; LICENSE file is Apache-2.0 and docs/LICENSE is CC-BY-4.0.
- Duplicate-name check (bundle-mandated): `grep -rni 'agentskills\|agent-skills' docs/` returns only the two draft posts under review, the review_prompt.md, review_bundle.toml, rebuttal_record.md, job_ids.toml, and the three prior r1 raw_findings files. No conflicting separate post or core/spec content exists elsewhere in docs/.

**Draft lines cited:** P01:4 (repo link), P01:25+143 (Client Showcase), P01:30-31+64-65 (format + progressive disclosure), P01:157 (profile's own Apache-2.0/CC-BY-4.0).

**Severity:** none (every claim holds exactly against the live GitHub page, the agentskills.io homepage fetch, and the research clone bytes).

---

## P01-C2: factual accuracy about this project's spec

**Classification:** complete

**Verified claims (all hold against current bytes):**

- closure-root cascade-break property + empty sentinel: SPEC.md:882-1088 (§12 full), especially §12.1 (mandatory root field), §12.4 (upstream change forces new closure_root + re-sign). The exact sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` appears at SPEC.md:965, 1072, 1204 and is recorded in the bundle as SHA-256(""). P01:77-79 and P01:104 accurate.
- capability_envelope drawn from WASI Preview 2 domains + cpu/memory bounds + fail-closed default: SPEC.md:1314-1363 (§13.3) lists exactly the nine domains (filesystem, sockets, http, clocks, random, environment, process_spawn, ipc, crypto_keys) plus cpu_bounds/memory_bounds tables; "A domain whose table is entirely missing is treated as `denied = true` (fail closed)" at SPEC.md:1348. P01:72-76 matches verbatim.
- gate-decision descriptor + separation-of-duty invariant bound to self-modification subject class: profiles/agent-assurance/gate-decision-kind.toml:92-105 (CROSS-PROVIDER ATTRIBUTION (INV06) prose) and hard invariant INV06 at 199-204: when `subject_class = "self-modification"`, all four proposing_*/deciding_* provider/family fields REQUIRED and "deciding_provider_id != proposing_provider_id AND deciding_model_family_id != proposing_model_family_id". The conjunctive AND is load-bearing. The rule is present at HEAD (added 2026-05-25). P01:81-85 accurate.
- Profile targets multi-provider deployments only: gate-decision-kind.toml:107-109 ("This profile assumes a multi-provider operating environment"); overview.md:74-88 ("positioned for **multi-provider operating environments**", "No amount of process discipline within a single provider substitutes for genuinely independent review across providers"). P01:104-105 and P01:40-44 framing accurate.
- Reference validators in safe Rust and safe Go (the fixed claim): README.md:99 and 120 identify tools/dagtoml-validate-rs/ as "Primary safe-Rust validator" with `#![forbid(unsafe_code)]` (tools/dagtoml-validate-rs/src/main.rs:27) and tools/dagtoml-validate-go/ as "Primary safe-Go validator" with "no `unsafe` import" (README.md:149). No C implementation exists. The pre-rebuttal advisory is resolved; current P01:119-120 claims only the two that actually exist.

**Severity:** none (all load-bearing technical claims are byte-accurate; the single prior advisory has been removed).

---

## P01-C3: policy compliance (memory / VAP / JSON Schema / Claude trailer)

**Classification:** complete

**Evidence:**

- No memory-file citations or MEMORY.md / memory/ references used as load-bearing evidence: `grep -rni` returned zero matches in the draft for any internal memory store. The only "memory" token is `memory_bounds` at P01:75 (a SPEC §13 field name).
- No naming of any specific runtime, broker, or implementation of the assurance substrate: "existence proof" section (P01:132-138) deliberately abstract ("The implementation is deliberately not named"; "vendor-neutral"; "not as a request for the maintainers to favour any particular implementation"). Zero hits for "vap", "verivus.*runtime", "verivus.*broker". Generic phrase "an agent broker must do to attest" at P01:86-89 is scoped as a contract description, not a named implementation.
- No JSON Schema sidecar proposal: the only occurrence is the explicit "What is **not** being asked" list item (P01:127: "- No JSON Schema sidecar to the SKILL.md grammar (deliberately)."). Bundle explicitly permits this placement; schemas/README.md confirms the project rejected a hand-authored JSON Schema layer.
- No Claude/AI co-author trailer or "Generated with Claude Code" line: `grep` returned empty on the draft. The file ends at P01:158-159 with only the human author / spec / contact block.

All bundle-mandated verify greps (items 156-158) pass against current draft bytes.

**Severity:** none.

---

## P01-C4: tone and framing

**Classification:** complete

**Evidence (collaborative, non-adversarial, profile-as-companion):**

- Explicit non-ask for core changes: P01:22-26 ("The proposal does **not** ask for changes to the Agent Skills core spec. Nothing in the core spec needs to move... The ask, if any is made at all, is for the maintainers to consider linking the profile from the Client Showcase...").
- "strict consumer" framing: P01:66-67 ("The profile is a **strict consumer** of the format.").
- Kept out of core for good reasons (adoption curve, strict subset, clean deprecation): full section P01:100-111.
- Brittleness translated to neutral outbound language: "Fail-closed default" (P01:75) for capability envelope; "cascade-breaks any prior approval" (P01:49) and "cascade-breaks downstream signatures" (P01:79) instead of internal jargon.
- Multi-provider legal-grade contexts presented as a separate class Agent Skills was not built for: P01:40-57 ("a class of deployment the lightweight format intentionally leaves to others"; "regulated industries, gov procurement, EU AI Act / NIS2 obligations"; "the surface-level discovery / activation / execution model is correct but insufficient on its own").
- No implication that Agent Skills core is insufficient for its stated purpose; framing is additive companion for a narrower audience. The pitch asks only for a sanity check and possible future showcase listing after v1.0 (P01:113-120 + 140-151).

**Severity:** none.

---

## P02-C1: factual accuracy about mattpocock/skills (triage quote, MIT, workflow)

**Classification:** complete

**Evidence (direct bytes from research clone + post-fix draft):**

- Verbatim quote block at lines 10-14 of triage/SKILL.md, including Markdown emphasis: research/.../mattpocock-skills/skills/engineering/triage/SKILL.md:10-14 now reads exactly:
  ```
  Every comment or issue posted to the issue tracker during triage **must** start with this disclaimer:

  ```
  > *This was generated by AI during triage.*
  ```
  Post-fix draft P02:56-60 reproduces the block with the `**must**` restored and the fenced disclaimer intact. The pre-fix omission of the emphasis (codex r1 finding) is resolved.
- "working skill" (not "in-production"): post-fix P02:28 uses "one well-shaped, working skill (Matt Pocock's `triage`)" — accurate; the repo bytes show a complete, opinionated workflow (SKILL.md:1-104) but the draft no longer claims production deployment.
- MIT license + attribution to Matt Pocock: research/.../mattpocock-skills/LICENSE:1-3 ("MIT License\n\nCopyright (c) 2026 Matt Pocock"). Post-fix P02 frontmatter (P02:14-17) correctly names the corpus and license; the same attribution line appears at P02:209-212.
- Workflow shape (two category roles + five state roles + transitions + agent brief + ADR norms + .out-of-scope/ log): SKILL.md:23-35 (exact "Two **category** roles: `bug` / `enhancement`"; "Five **state** roles: `needs-triage`...`wontfix`"), state transitions at 40 and 71-78, `ready-for-agent` emits agent brief cross-ref to AGENT-BRIEF.md at 72 and 18+45. ADR-cited norms at 63; .out-of-scope/ precedent mechanism documented in OUT-OF-SCOPE.md and SKILL.md:76. Post-fix P02:38-52 and 47-51 accurately summarise without rhetorical inflation.
- The "load-bearing gap" characterisation is defensible: the only attestation emitted is the free-text disclaimer at SKILL.md:10-14; no sha, no provider id, no model family, no content binding — exactly as enumerated at post-fix P02:66-72.

**Draft lines:** P02:14-17 (attribution), P02:28 (working), P02:36-52 (workflow), P02:53-61 (quote + gap), P02:205-207 (solo vs assurance-grade).

**Severity:** none (all post-fix claims hold byte-for-byte; the two codex r1 defects are gone).

---

## P02-C2: factual accuracy about this project's spec (gate-decision example)

**Classification:** complete

**Evidence (post-fix draft vs. current descriptor + ontology + SPEC):**

- `template_kind = "gate-decision"`: matches gate-decision-kind.toml:9 (meta), 42 (root shape example), and [[kind.required_fields]] at 120-126.
- Empty-closure sentinel: exactly `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (SPEC §12.1, bundle line 18, kind:5). Post-fix P02:100-103 explicitly labels it "shown as the empty-closure sentinel for illustrative purposes only."
- `subject_class = "downstream-change"`: correct default per descriptor:53-56 and ontology.toml:352. INV06 (kind:199-204) triggers *only* on literal `"self-modification"`. Post-fix P02:117-121 and 152-163 correctly distinguish: ordinary triage uses downstream-change (attribution optional); only self-modification fires the conjunctive cross-provider rule.
- All fields in the post-fix TOML block (P02:99-140) are present in the descriptor root shape (kind:38-76) or required sections (kind:120-163): meta.framework_profile (127-133), decision.verdict / evidence_root / evidence_root_algorithm / decided_at (134-157), [[decision.cited_bundles]] (158-163), flat proposing_provider_id etc. under [decision] (58-66). No fabricated nested [proposing_agent] / [disclaimer] tables, no `outcome`, no `fresh_session`, no `session_id`.
- The prose at post-fix P02:150-163 accurately describes the descriptor's INV06 scope without inventing rules for non-self-mod cases.
- Rebuttal cross-reference to r1 classification: the rebuttal_record.md:100-107 states that grok r1 classified P02-C2 complete "on the grounds that the bundle scope permitted illustrative fields" and that "That reasoning was too lenient: the bundle allowed illustrative *values* ... but not field substitution (`outcome` for `verdict`), not out-of-vocabulary subject_class without declaration, and not fabrication of rules not in the descriptor (`fresh_session`)." This characterization is fair against the pre-fix bytes (the state that existed when r1 was written). The codex r1 evidence (codex.md:88-91) listed exactly the defects that the rebuttal later recorded as fixed at P02:92-145: missing framework_profile / verdict / evidence_* / decided_at / cited_bundles; nested tables instead of flat attribution fields; subject_class outside the ontology closed set without extension declaration; invented fresh_session rule and [disclaimer] table. The current post-fix bytes contain none of those defects. The r1 leniency is therefore accurately described by the rebuttal when measured against the bytes that were under review at r1 time.

**Draft lines:** P02:92-145 (full TOML + "Every field below is one the descriptor already defines"), P02:150-163 (INV06 application), P02:117-121 (subject_class comment).

**Severity:** none (the example is now validator-shape conformant and the surrounding prose does not fabricate descriptor rules).

---

## P02-C3: policy compliance (same as P01-C3 + MIT attribution + clear quote)

**Classification:** complete

**Evidence:**

- Identical policy greps as P01-C3: zero hits for memory/VAP/runtime names or Claude trailer in the post-fix draft. No JSON Schema mention at all.
- MIT-license attribution to Matt Pocock: present and accurate in P02:14-17 frontmatter ("The 'before' excerpts in this post are from Matt Pocock's [`mattpocock/skills`](https://github.com/mattpocock/skills) corpus (MIT).") plus the exact copyright bytes in the research clone LICENSE.
- Quoted excerpt clearly attributed: code fence at post-fix P02:55-61 + "Attribution:" line in frontmatter + "Used here illustratively, with no implication of endorsement" framing. The disclaimer block is visually distinct and tied to the source SKILL.md:10-14.

All bundle-mandated P02 verify greps (items 247-249) pass against current bytes.

**Severity:** none.

---

## P02-C4: tone and framing (small/surgical/additive; not "doing it wrong"; specific load-bearing gap)

**Classification:** complete

**Evidence:**

- "small, surgical, and *additive*" delta: post-fix P02:32 ("the delta is small, surgical, and *additive*"); P02:167-195 ("**Did not change:** The triage skill body... **Changed (additively):** A `gate-decision` artifact... The free-text disclaimer is replaced by that binding... **Refused (by the assurance gate):** ... by construction.").
- Explicitly not "mattpocock is doing it wrong": post-fix P02:79-83 ("Not because the skill author was careless — the skill is one of the most disciplined working corpora the dossier found — but because the substrate (`SKILL.md` + free-text comments) intentionally has no field for it.").
- "load-bearing gap" framing is specific, not vague: post-fix P02:66-72 enumerates exactly "human-readable, free text, attached to the artifact by the same agent that produced the artifact, and unverifiable by any downstream consumer... no signature, no model identifier, no session reference, no provider attribution, no sha-binding to the agent brief".
- Solo vs. assurance-grade distinction preserved: post-fix P02:198-205 ("For solo projects, the disclaimer is fine; for assurance-grade contexts, the disclaimer is the load-bearing gap, and the change above closes it without asking the skill author to work differently.").
- Workflow tastefulness preserved: post-fix P02:47-52 ("The skill is tasteful: it understands separation of concerns (category vs state), it has explicit ADR-cited norms... and it ships a worked `.out-of-scope/` log").

**Severity:** none.

---

## Terminal recommendation

unconditional_approval

(The r1 advisory on P01 has been removed by the pre-rebuttal edit. The two codex r1 blockers on P02 have been resolved by the documented fixes; the post-fix bytes satisfy the stricter descriptor-conformance reading. The rebuttal's cross-reference to the r1 P02-C2 classification is fair when measured against the pre-fix bytes that existed at r1 time. All eight sub-claims are now complete with no remaining defects of any severity.)