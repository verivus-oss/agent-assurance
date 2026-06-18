## P01-C1: factual accuracy about agentskills/agentskills

Classification: complete

Severity: advisory

Evidence:

- P01 says the proposed profile consumes the existing Agent Skills `SKILL.md` format and folder convention at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:16-18` and lists `SKILL.md`, `name` / `description`, `scripts/`, `references/`, `assets/`, and progressive disclosure at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:59-67`.
- The local agentskills clone says a skill is a folder containing `SKILL.md`, minimum `name` and `description` metadata, and optional scripts/references/assets at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:9-20`.
- The local agentskills clone defines progressive disclosure as Discovery / Activation / Execution at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:30-40`; the live homepage says the same at `https://agentskills.io/home:L78-L85`.
- P01 refers to the Client Showcase as the possible future listing surface at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:24-26` and `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:142-145`. The local README links the Client Showcase at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:42-45`; the live homepage navigation includes "Client Showcase" at `https://agentskills.io/home:L21-L24`.
- P01 links `agentskills/agentskills` at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:3-5`. The live GitHub page identifies the public repo as `agentskills/agentskills` at `https://github.com/agentskills/agentskills:L150-L155`.
- The starting facts not all used in P01 also verify: `CONTRIBUTING.md` exists and directs proposals/questions/feedback to Discussions at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/CONTRIBUTING.md:15-24`; the README links the `anthropics/skills` example-skills repo at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:46-51`; the README links docs at `https://agentskills.io` at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:46-49`.
- Agent Skills licensing verifies: the README says code is Apache 2.0 and docs are CC-BY-4.0 at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:57-59`; the repo `LICENSE` is Apache License 2.0 at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/LICENSE:2-4`; `docs/LICENSE` is Creative Commons Attribution 4.0 at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/docs/LICENSE:1-3`.
- Live GitHub metadata verifies the prompt's current public-state facts: `Star 19.4k` and `Fork 1.2k` appear at `https://github.com/agentskills/agentskills:L150-L155`, and languages are Python 99.1% / Shell 0.9% at `https://github.com/agentskills/agentskills:L348-L351`.
- The requested duplicate-name check found no conflicting non-review content. Current substantive occurrences are the two draft posts at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:4`, `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:4`, and `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:210`; the remaining hits are this review session's prompt, bundle, job IDs, and raw findings under `docs/reviews/2026-05-27-agentskills-profile-pitch/`.

## P01-C2: factual accuracy about this project's spec

Classification: complete

Severity: advisory

Evidence:

- P01's capability-envelope claim at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:71-76` matches SPEC §13.3. The spec says capability domains are drawn from WASI Preview 2 at `spec.md:1314-1316`, lists `filesystem`, `sockets`, `http`, `clocks`, `random`, `environment`, `process_spawn`, `ipc`, and `crypto_keys` at `spec.md:1318-1328`, defines separate CPU and memory bounds at `spec.md:1338-1344`, and says omitted domains fail closed at `spec.md:1346-1362` and `spec.md:1509-1510`.
- P01's closure-root cascade claim at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:77-80` and `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:104-105` is supported by SPEC §12. The spec says upstream changes MUST break downstream hashes at `spec.md:883-894`, requires `closure_root` on conforming documents at `spec.md:896-904`, defines the empty-closure sentinel at `spec.md:959-980`, and says upstream hash/revocation changes force a different downstream `closure_root` and fresh signing ceremony at `spec.md:984-1009`.
- P01's gate-decision separation-of-duty claim at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:81-85` matches `profiles/agent-assurance/gate-decision-kind.toml`: the descriptor names `gate-decision` at `profiles/agent-assurance/gate-decision-kind.toml:17-19`, shows `subject_class = "self-modification"` as the INV06 trigger at `profiles/agent-assurance/gate-decision-kind.toml:53-66`, and states the deciding provider AND deciding model family must both differ from the proposing provider/model family for self-modification at `profiles/agent-assurance/gate-decision-kind.toml:92-105` and `profiles/agent-assurance/gate-decision-kind.toml:199-204`.
- The supporting vocabulary exists: `subject_class` values are `downstream-change` and `self-modification` at `profiles/agent-assurance/ontology.toml:349-356`, with `self-modification` explicitly triggering INV06.
- P01's multi-provider posture at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:40-44` and `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:132-138` is supported by the profile overview: it is positioned for multi-provider environments at `profiles/agent-assurance/overview.md:72-83`; same-model-family review is called structurally inadequate at `profiles/agent-assurance/overview.md:85-88`; single-provider deployments cannot achieve full assurance for self-modification gates at `profiles/agent-assurance/overview.md:90-103`.
- The draft accurately keeps runtime concerns out of the format: P01 says the profile is a data format, not an execution runtime, at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:91-97`. SPEC §13 likewise treats the capability envelope as a descriptor contract and forbids ad hoc grant surfaces at `spec.md:1501-1513`.

## P01-C3: policy compliance

Classification: complete

Severity: advisory

Evidence:

- P01 does not propose Agent Skills core changes: it says the proposal "does not ask for changes to the Agent Skills core spec" and "Nothing in the core spec needs to move" at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:22-26`, and the "not being asked" list rejects changes to `SKILL.md`, discovery/activation/execution semantics, reserved names, and fields/directories at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:122-128`.
- P01 does not propose a JSON Schema sidecar. The only JSON Schema occurrence is the explicit negative at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:127`. This matches repo policy: `schemas/README.md:3-15` says the schema lives in TOML descriptors and ontology files and rejects a separate JSON Schema layer; `schemas/README.md:17-24` allows only future generated editor schemas from the TOML source of truth.
- P01 does not name VAP or a specific Verivus runtime/broker. Targeted grep over the draft found no `VAP`, `verivus.*runtime`, or `verivus.*broker` hits. The generic broker language is abstract and explicitly says the profile names no broker implementation at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:86-89`.
- P01 does not name a specific assurance-substrate implementation: it says a reference implementation exists but is deliberately not named at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:130-138`.
- P01 does not cite memory files or internal auto-memory evidence. The only targeted `memory` hit in the draft is `memory_bounds` at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:75`, which is a SPEC §13 resource-bound term.
- P01 carries no Claude/AI co-author trailer. The draft ends with author/spec/contact lines at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:153-158`; targeted grep found no `co-authored-by`, `generated with`, or `Claude Code` trailer.

## P01-C4: tone and framing

Classification: complete

Severity: advisory

Evidence:

- The proposal is framed as separate, optional, and additive at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:16-25`.
- It says the Agent Skills format is "scoped well" and that baking assurance into core would defeat portability and low per-skill cost at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:30-35`.
- The "insufficient" language is scoped to a separate deployment class rather than to Agent Skills' core purpose: P01 names multi-provider systems, downstream local verification, and mixed-trust regulated environments at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:37-53`, then says the model is correct but insufficient for those contexts at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:55-57`.
- P01 says the profile is a "strict consumer" and would not modify Agent Skills surfaces at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:59-67`.
- It avoids this repo's internal "brittleness as feature" phrasing; the outward language is fail-closed and cascade-break at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:75-80`.
- The ask is collaborative and bounded: P01 asks initially for a sanity check and possible future listing after v1.0 at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:113-120`, then asks maintainers about fit and preferred discussion channel at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:140-151`.

## P02-C1: factual accuracy about mattpocock/skills

Classification: complete

Severity: advisory

Evidence:

- P02 attributes the "before" excerpt to Matt Pocock's `mattpocock/skills` corpus and marks it MIT at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:14-17`. The local repo license is MIT at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/LICENSE:1-3`.
- P02 no longer claims "in-production"; it says "well-shaped, working skill" at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:28-30`. The local repo README says these are Matt Pocock's agent skills used every day for real engineering at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/README.md:11-19`, which supports "working."
- P02 describes `triage` as an opinionated state machine at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:36-45`. The source says `triage` moves issues through a small state machine at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:6-8`.
- The two category roles and five state roles in P02 at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:38-40` match the source roles at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:21-35`.
- The transition summary in P02 at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:40-45` matches the source invocation and transition flow at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:40-49` and outcome list at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:61-78`.
- The quoted disclaimer content now preserves the `**must**` emphasis in P02 at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:53-60`, matching the source wording at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:10-14`. The draft wraps the first source sentence for display, but the quoted words and Markdown emphasis are correct.
- The agent brief claim in P02 at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:43-45` matches `AGENT-BRIEF.md`, which says an agent brief is posted when an issue moves to `ready-for-agent` and is the authoritative specification an AFK agent works from at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:1-4`.
- The "tasteful" support is defensible against bytes: triage separates category vs state roles at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:21-36`; the ADR splits hard and soft setup dependencies and names `triage` as a hard dependency at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/docs/adr/0001-explicit-setup-pointer-only-for-hard-dependencies.md:1-10`; the source tells triage to read `.out-of-scope/*.md` and surface prior rejections at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:63-76`; `OUT-OF-SCOPE.md` explains persistent rejection records and avoiding re-litigation at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/OUT-OF-SCOPE.md:1-7` and `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/OUT-OF-SCOPE.md:70-93`.

## P02-C2: factual accuracy about this project's spec

Classification: complete

Severity: advisory

Evidence:

- P02 says the `ready-for-agent` transition would emit a `gate-decision` artifact using the existing descriptor at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:92-97`. The descriptor names `gate-decision` at `profiles/agent-assurance/gate-decision-kind.toml:17-19` and shows `template_kind = "gate-decision"` / `framework_profile = "agent-assurance"` in its root shape at `profiles/agent-assurance/gate-decision-kind.toml:38-46`.
- The P02 TOML example uses the required fields and section: `closure_root` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:100-103`, `meta.template_kind` and `meta.framework_profile` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:105-110`, `decision.verdict`, `decision.evidence_root`, `decision.evidence_root_algorithm`, and `decision.decided_at` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:112-116`, and `[[decision.cited_bundles]]` / `bundle_ref` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:132-139`.
- Those fields match descriptor-required fields at `profiles/agent-assurance/gate-decision-kind.toml:120-163`. The root shape also uses the same flat provider/model fields at `profiles/agent-assurance/gate-decision-kind.toml:47-69`.
- The closure-root placeholder is the canonical SHA-256 empty-closure sentinel at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:100-103`. SPEC §12 defines that exact sentinel at `spec.md:959-980`, and the draft clearly marks it illustrative rather than a real triage bundle root at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:100-102`.
- The `evidence_root` value in the example is 64 lowercase hex characters at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:114`, matching INV04's `^[0-9a-f]{64}$` requirement at `profiles/agent-assurance/gate-decision-kind.toml:185-188`.
- P02 uses `subject_class = "downstream-change"` for ordinary triage at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:117-121` and explains ordinary triage does not trigger INV06 at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:150-163`. The ontology declares `downstream-change` and `self-modification` as the current values at `profiles/agent-assurance/ontology.toml:349-356`, and the descriptor says only `subject_class = "self-modification"` triggers the four attribution fields plus both inequality predicates at `profiles/agent-assurance/gate-decision-kind.toml:199-204`.
- The example's same-provider/same-family values at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:127-130` are valid in context because the subject is `downstream-change`; INV06 explicitly leaves the four attribution fields optional and does not impose the inequality predicate when subject_class is absent or not `self-modification` at `profiles/agent-assurance/gate-decision-kind.toml:199-204`.
- The prior fabricated surface is gone. Targeted grep found no `fresh_session`, `[disclaimer]`, `outcome`, or `issue-triage-promotion` occurrences in the P02 TOML example; the current replacement is `verdict`, `evidence_root`, `evidence_root_algorithm`, `decided_at`, flat `proposing_*` / `deciding_*`, `[[decision.cited_bundles]]`, and `subject_class = "downstream-change"` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:112-139`.
- P02 correctly distinguishes SPEC-layer and runtime-layer work around evidence roots: the descriptor says validators MUST NOT resolve cited bundle content or verify the evidence-root hash at `profiles/agent-assurance/gate-decision-kind.toml:87-90`, while P02 frames the bundle hash/evidence-root discussion as what an assurance-profile run would emit alongside the artifact at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:132-139` and `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:175-185`.

## P02-C3: policy compliance

Classification: complete

Severity: advisory

Evidence:

- P02 attributes the excerpt in front matter to Matt Pocock's `mattpocock/skills` corpus and says it is MIT at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:14-17`. The local license confirms MIT and copyright Matt Pocock at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/LICENSE:1-3`.
- The quoted excerpt is visually attributed and bounded: P02 introduces it as lines 10-14 of `SKILL.md` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:53`, then shows the disclaimer block at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:55-60`.
- P02 does not propose Agent Skills core changes; it says the assurance profile consumes the `SKILL.md` format at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:23-32`, says the workflow/body/brief stay at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:85-90`, and lists `SKILL.md` itself under "Did not change" at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:167-173`.
- P02 has no JSON Schema proposal: targeted grep found no `json schema` or `json-schema` occurrences in the draft.
- P02 does not name VAP or a specific Verivus runtime/broker: targeted grep found no `VAP`, `verivus.*runtime`, or `verivus.*broker` occurrences. The `anthropic` / `claude` values at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:127-130` are descriptor vocabulary examples for provider/model attribution, not runtime or broker names.
- P02 does not cite memory files or internal auto-memory evidence: targeted grep found no `memory/` or `auto-memory` occurrences in the draft.
- P02 carries no Claude/AI co-author trailer. The draft ends with author/companion/spec/contact lines at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:207-212`; targeted grep found no `co-authored-by`, `generated with`, or `Claude Code` trailer. The prose example "Claude session on date X" at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:73-75` is part of the factual ambiguity example, not a trailer.

## P02-C4: tone and framing

Classification: complete

Severity: advisory

Evidence:

- P02 frames the delta as small, surgical, and additive at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:21-32`.
- It praises the existing workflow as "tasteful" and identifies concrete strengths: separation of concerns, ADR-cited norms, and `.out-of-scope/` precedent at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:47-51`.
- It explicitly avoids blaming the skill author: "Not because the skill author was careless" appears at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:79-83`, followed by the structural explanation that `SKILL.md` plus free-text comments intentionally has no field for the needed evidence.
- The load-bearing gap is specific, not vague: P02 names free text, same-agent attachment, no downstream verification, no signature, no model identifier, no session reference, no provider attribution, and no sha-binding at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:64-77`.
- The "what changed and what did not" section keeps the workflow unchanged and makes the additions parallel evidence artifacts at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:165-185`.
- The scope remains operator-focused, not a critique of `mattpocock/skills`: P02 says solo projects are fine with the disclaimer, while assurance-grade contexts need the extra binding, at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:196-205`.

## Terminal recommendation

unconditional_approval
