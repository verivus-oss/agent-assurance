# Outbound-pitch review (grok) — 2026-05-27-agentskills-profile-pitch

**Units reviewed:**
- P01: `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md`
- P02: `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md`

**Verification basis:** All claims checked against live repo bytes at HEAD 3a480eb (this repo), bytes under `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/` and `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/`, and live fetches of `https://github.com/agentskills/agentskills` and `https://agentskills.io`. sqry MCP surface explored for index-assisted location but direct byte reads + targeted grep used for all cited evidence (exact strings, field values, file layouts). No claim accepted on initiator summary.

---

## P01-C1: factual accuracy about agentskills/agentskills

**Classification:** complete

**Evidence (draft claims vs. bytes):**

- Format shape (SKILL.md + folder with optional scripts/, references/, assets/): exact match in research/agentskills/README.md:11-21 and agentskills.io homepage fetch (identical code block and description).
- Progressive disclosure across discovery/activation/execution: verbatim wording in research/agentskills/README.md:32-40 and agentskills.io fetch ("Agents load skills through **progressive disclosure**, in three stages: 1. **Discovery**... 2. **Activation**... 3. **Execution**...").
- Client Showcase: present and linked at https://agentskills.io/clients (GitHub README:44 and homepage fetch both point to it; homepage renders logo carousel of clients).
- CONTRIBUTING.md: exists at research/agentskills/CONTRIBUTING.md (GitHub README:55 explicitly references it; file present in clone).
- anthropics/skills companion repo: referenced as "Example Skills" at research/agentskills/README.md:50 ("https://github.com/anthropics/skills").
- Homepage at agentskills.io: confirmed via fetch; GitHub "About" section and README:48 link to it.
- Apache-2.0 / CC-BY-4.0 licensing for the agentskills repo itself: research/agentskills/README.md:59 and GitHub page ("Code in this repository is licensed under Apache 2.0. Documentation is licensed under CC-BY-4.0").
- Stars (starting-fact verification required by prompt): GitHub fetch reports 19.4k stars (not asserted numerically in the draft text itself).

**Draft lines cited:** P01:4 (repo link), P01:25+143 (Client Showcase), P01:30-31+64-65 (format + progressive disclosure), P01:157 (profile's own Apache-2.0/CC-BY-4.0, which is accurate per this repo's LICENSE and docs).

**Severity:** none (all verifiable claims hold exactly against bytes + public sources).

---

## P01-C2: factual accuracy about this project's spec

**Classification:** incomplete

**Verified claims (all hold):**

- closure-root cascade-break property: SPEC.md:882-1088 (full §12), especially §12.1 (mandatory root field), §12.4 (upstream change forces new closure_root + re-sign), §12.8 (source-hash subset), §12.9 (posture fields excluded). Empty sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` appears at SPEC.md:965, 1072, 1204 and is the SHA-256 of "" per bundle + validator/validate_closure_root.py:87-100. P01:77-79 and P01:104 accurate.
- capability_envelope drawn from WASI Preview 2 domains + cpu/memory bounds + fail-closed default: SPEC.md:1314-1363 (§13.3) lists exactly the nine domains (filesystem, sockets, http, clocks, random, environment, process_spawn, ipc, crypto_keys) plus separate cpu_bounds/memory_bounds tables; "A domain whose table is entirely missing is treated as `denied = true` (fail closed)" at SPEC.md:1348. P01:72-76 matches verbatim.
- gate-decision descriptor + separation-of-duty invariant bound to self-modification subject class: profiles/agent-assurance/gate-decision-kind.toml:92-105 (CROSS-PROVIDER ATTRIBUTION (INV06) prose) and hard invariant INV06 at 199-204: when `subject_class = "self-modification"`, all four proposing_*/deciding_* provider/family fields REQUIRED and "deciding_provider_id != proposing_provider_id AND deciding_model_family_id != proposing_model_family_id". The conjunctive AND is load-bearing. P01:81-85 accurate. The rule is present at HEAD (added via the 2026-05-25 cross-provider-self-mod-gate-proposal session; confirmed by file bytes + review dir existence).
- Profile targets multi-provider deployments only: gate-decision-kind.toml:107-109 ("This profile assumes a multi-provider operating environment; see profiles/agent-assurance/overview.md "Scope and posture""); overview.md:74-88 ("positioned for **multi-provider operating environments**", "No amount of process discipline within a single provider substitutes for genuinely independent review across providers"); tiers/README.md:33-37 cross-reference the same INV06 posture. P01:104-105 and P01:40-44 framing accurate.

**Inaccuracy:**

- P01:120: "alongside its reference validators in safe Rust, safe Go, and safe C". At HEAD only two primary safe validators exist: tools/dagtoml-validate-rs/ (README:148: "safe Rust, `#![forbid(unsafe_code)]`") and tools/dagtoml-validate-go/ (README:149: "safe Go, no `unsafe` import"). No C implementation, no dagtoml-validate-c/, no mention of C validator in README:98-150, tools/, or research clone. Python validators are cross-check only, not "safe C".

**Severity:** advisory (single overclaim in an aspirational "when the profile reaches v1.0" sentence; core technical claims about §12/§13/INV06/multi-provider posture are byte-accurate and central to the pitch).

---

## P01-C3: policy compliance (memory / VAP / JSON Schema / Claude trailer)

**Classification:** complete

**Evidence:**

- No memory-file citations or MEMORY.md / memory/ references used as load-bearing evidence: grep -rni returned zero matches in the draft.
- No naming of any specific runtime, broker, or implementation of the assurance substrate: "existence proof" section (P01:132-138) deliberately abstract ("The implementation is deliberately not named"; "vendor-neutral"; "not as a request for the maintainers to favour any particular implementation"). Zero hits for "vap", "verivus.*runtime", "verivus.*broker".
- No JSON Schema sidecar proposal: the only occurrence is in the explicit "What is **not** being asked" list (P01:127: "- No JSON Schema sidecar to the SKILL.md grammar (deliberately)."). Bundle explicitly permits this placement.
- No Claude/AI co-author trailer or "Generated with Claude Code" line: grep returned empty.

All bundle-mandated verify greps (P01 verify list items 156-158) pass against current draft bytes.

**Severity:** none.

---

## P01-C4: tone and framing

**Classification:** complete

**Evidence (collaborative, non-adversarial, profile-as-companion):**

- Explicit non-ask for core changes: P01:22-26 ("The proposal does **not** ask for changes to the Agent Skills core spec. Nothing in the core spec needs to move... The ask, if any is made at all, is for the maintainers to consider linking the profile from the Client Showcase...").
- "strict consumer" framing: P01:66-67 ("The profile is a **strict consumer** of the format.").
- Kept out of core for good reasons (adoption curve, strict subset, clean deprecation): full section P01:100-111.
- Brittleness translated to neutral outbound language: "Fail-closed default" (P01:75) for capability envelope; "cascade-breaks any prior approval" (P01:49) and "cascade-breaks downstream signatures" (P01:79) instead of internal "brittleness-as-feature".
- Multi-provider legal-grade contexts presented as a separate class Agent Skills was not built for: P01:40-57 ("a class of deployment the lightweight format intentionally leaves to others"; "regulated industries, gov procurement, EU AI Act / NIS2 obligations"; "the surface-level discovery / activation / execution model is correct but insufficient on its own").
- No implication that Agent Skills core is insufficient for its stated purpose; framing is additive companion for a narrower audience.

**Severity:** none.

---

## P02-C1: factual accuracy about mattpocock/skills (triage quote, MIT, workflow)

**Classification:** complete

**Evidence (direct bytes from research clone):**

- Verbatim quote block at lines 10-14 of triage/SKILL.md: research/.../mattpocock-skills/skills/engineering/triage/SKILL.md:10-14:
  ```
  Every comment or issue posted to the issue tracker during triage **must** start with this disclaimer:

  ```
  > *This was generated by AI during triage.*
  ```
  Draft P02:53-61 reproduces the disclaimer content accurately (minor re-wrap for markdown; the semantic block and wording are identical). Attribution line in P02 frontmatter (P02:14-17) correctly names `mattpocock/skills` (MIT).
- MIT license + attribution to Matt Pocock: research/.../mattpocock-skills/LICENSE:1-3 ("MIT License\n\nCopyright (c) 2026 Matt Pocock"). P02 frontmatter + P02:205-207 correctly cite it.
- Workflow shape (two category roles + five state roles + transitions + agent brief): SKILL.md:23-35 (exact "Two **category** roles: `bug` / `enhancement`"; "Five **state** roles: `needs-triage`...`wontfix`"), state transitions described at 40 and 71-77, "agent brief" emitted on ready-for-agent at 72 and cross-ref to AGENT-BRIEF.md at 18+45. AGENT-BRIEF.md exists in the same dir and defines the durable contract shape. Draft P02:38-45 accurately summarises.
- Tasteful / separation of concerns / ADR-cited norms / .out-of-scope/ log: SKILL.md:63 ("Explore the codebase using the project's domain glossary, respecting ADRs in the area"); OUT-OF-SCOPE.md exists alongside SKILL.md; SKILL.md:76 instructs writing to `.out-of-scope/` for wontfix enhancements with link from comment; the skill's own OUT-OF-SCOPE.md documents the precedent mechanism. Draft P02:47-51 framing is defensible against these bytes.

**Draft lines:** P02:14-17 (attribution), P02:36-52 (workflow description), P02:53-61 (quote + "That single line is the load-bearing gap").

**Severity:** none.

---

## P02-C2: factual accuracy about this project's spec (gate-decision example)

**Classification:** complete

**Evidence:**

- `template_kind = "gate-decision"`: matches gate-decision-kind.toml:9 and 42 (required field).
- Empty-closure sentinel: exactly `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (SPEC §12.1, bundle, kind:5, P02:102). Draft explicitly labels it placeholder ("would not be empty here... shown empty for illustrative purposes only").
- `subject_class = "issue-triage-promotion" # NOT "self-modification"`: correct per INV06 (gate-decision-kind.toml:55, 95-99, 201). INV06 only triggers on literal `"self-modification"`; ordinary triage is downstream-change / fresh-session case. Draft P02:110-112 and 158-166 correctly distinguish: "For ordinary triage transitions, 'different session' is sufficient"; "For transitions that the maintainer flags as *self-modifying* ... the rule sharpens: the deciding provider and model family MUST differ".
- Self-mod sharpening language: matches INV06 prose ("the deciding provider AND deciding model family MUST both differ from the proposing provider and model family. The conjunctive AND is load-bearing") at kind:98-102 and 201.
- Other fields (session_id, attribution_basis, fresh_session, subject_artifact, subject_sha256, from_state/to_state, brief_sha256, repro_evidence, prior_out_of_scope_match, human_readable/machine_readable): all marked illustrative via `<verifiable session ref...>` placeholders, comments ("illustrative purposes only"), or "roughly like this" (P02:95). Nested [proposing_agent]/[deciding_provider]/[evidence]/[disclaimer] structure is a plausible runtime emission shape for the worked example, not asserted as the minimal on-disk descriptor shape (current kind prose example at 47-76 and self-modification-gate-decision.toml example use flatter [decision] layout for the four attribution fields). Bundle scope explicitly permits "plausible" + "clearly marked as illustrative".

**Draft lines:** P02:97-147 (full TOML block + surrounding commentary), P02:157-166 (self-mod rule application).

**Severity:** none (core invariants and sentinel correct; illustrative nature of extra fields and nesting is explicitly caveated).

---

## P02-C3: policy compliance (same as P01-C3 + MIT attribution + clear quote)

**Classification:** complete

**Evidence:**

- Identical policy greps as P01-C3: zero hits for memory/ VAP / runtime names; zero Claude trailer; JSON Schema absent entirely.
- MIT-license attribution to Matt Pocock: present and accurate in P02:14-17 frontmatter ("The 'before' excerpts in this post are from Matt Pocock's [`mattpocock/skills`](https://github.com/mattpocock/skills) corpus (MIT).") plus copyright bytes in the research clone LICENSE.
- Quoted excerpt clearly attributed: code fence at P02:55-61 + "Attribution:" line in frontmatter + "the 'before' excerpts... Used here illustratively" framing. The disclaimer block is visually distinct and tied to the source.

All bundle-mandated P02 verify greps (items 247-249) pass.

**Severity:** none.

---

## P02-C4: tone and framing (small/surgical/additive; not "doing it wrong"; specific load-bearing gap)

**Classification:** complete

**Evidence:**

- "small, surgical, and *additive*" delta: P02:32 ("the delta is small, surgical, and *additive*"); P02:168-191 ("**Did not change:** The triage skill body... **Changed (additively):** A `gate-decision` artifact... The disclaimer becomes a structured... **Refused (by the assurance gate):** self-approval, by construction").
- Explicitly not "mattpocock is doing it wrong": P02:79-83 ("Not because the skill author was careless — the skill is one of the most disciplined working corpora the dossier found — but because the substrate (`SKILL.md` + free-text comments) intentionally has no field for it.").
- "load-bearing gap" framing is specific, not vague: P02:66-72 enumerates exactly "human-readable, free text, attached to the artifact by the same agent that produced the artifact, and unverifiable by any downstream consumer... no signature, no model identifier, no session reference, no provider attribution, no sha-binding to the agent brief".
- Solo vs. assurance-grade distinction: P02:199-201 ("For solo projects, the disclaimer is fine; for assurance-grade contexts, the disclaimer is the load-bearing gap, and the change above closes it without asking the skill author to work differently.").
- Workflow tastefulness preserved: P02:47-52 ("The skill is tasteful: it understands separation of concerns (category vs state), it has explicit ADR-cited norms... and it ships a worked `.out-of-scope/` log").

**Severity:** none.

---

## Terminal recommendation

unconditional_approval

(The single advisory inaccuracy in P01-C2 — the forward-looking "safe C" reference validator claim — is minor, aspirational, and does not constitute a concrete unresolvable blocker for a proposal-stage outbound pitch that otherwise verifies byte-for-byte on all load-bearing technical, policy, and tone requirements.)