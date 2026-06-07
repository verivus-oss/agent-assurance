## P01-C1: factual accuracy about agentskills/agentskills

Classification: complete.

Evidence:

- P01 correctly frames Agent Skills as `SKILL.md` plus a folder convention. The draft says the profile consumes `SKILL.md`, `name` and `description`, and `scripts/` / `references/` / `assets/` conventions at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:61-64`. The local agentskills README says a skill is a folder containing `SKILL.md`, with metadata `name` and `description`, and may bundle scripts, references, and assets at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:11-20`. The live homepage says the same at `https://agentskills.io/home:L59-L67`.
- P01 correctly names progressive disclosure across discovery / activation / execution at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:30-32` and `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:64`. The local README defines the three stages at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:30-40`; the live homepage mirrors this at `https://agentskills.io/home:L78-L85`.
- P01 correctly refers to a Client Showcase at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:24-26` and `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:142-145`. The local README links the Client Showcase at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:42-45`; the live homepage navigation includes Client Showcase at `https://agentskills.io/home:L21-L24`.
- P01 correctly points at GitHub Discussions as the intended channel and asks maintainers whether Discussions, Discord, or another venue is preferred at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:149-151`. The agentskills CONTRIBUTING file says proposals, questions, and feedback should start in Discussions at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/CONTRIBUTING.md:15-24`.
- P01 does not explicitly mention the anthropics/skills repo, but the starting fact is true: the agentskills README links "Example Skills" to `github.com/anthropics/skills` at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:46-51`.
- P01 correctly identifies the target repo and homepage. The draft links `agentskills/agentskills` at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:3-5`. The agentskills README links documentation to `https://agentskills.io` at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:46-49`, and the live homepage links the GitHub repo at `https://agentskills.io/home:L10-L11`.
- P01's licensing line for this proposed profile repo is separate from agentskills licensing at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:155-158`. The starting fact for agentskills licensing is verified: agentskills README says code is Apache 2.0 and docs are CC-BY-4.0 at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/README.md:57-59`; `LICENSE` is Apache 2.0 at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/LICENSE:2-4`; `docs/LICENSE` is Creative Commons Attribution 4.0 at `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills/docs/LICENSE:1-3`.
- Starting facts not used by the draft also verify: the live GitHub page showed `Star 19.4k` and `Fork 1.2k` at `https://github.com/agentskills/agentskills:L150-L155`, and languages Python 99.1% / Shell 0.9% at `https://github.com/agentskills/agentskills:L348-L351`.
- The requested duplicate-name check found only the two draft posts, this review prompt/bundle, job ids, and already-created raw findings under `docs/reviews/2026-05-27-agentskills-profile-pitch/`; I found no conflicting separate post or profile/core/spec content. The substantive draft occurrences are at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:4`, `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:4`, and `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:206`.

Severity: advisory; no factual defect found.

## P01-C2: factual accuracy about this project's spec

Classification: complete.

Evidence:

- P01's closure-root cascade-break claim at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:77-80` and `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:104-105` is supported by SPEC §12: upstream changes MUST break downstream hashes at `spec.md:883-894`, every conforming document must carry `closure_root` at `spec.md:896-904`, the empty-closure sentinel is defined at `spec.md:959-980`, and upstream hash/revocation changes force a different downstream `closure_root` and new signing ceremony at `spec.md:984-1009`.
- P01's capability-envelope claim at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:71-76` matches SPEC §13.3: the closed WASI Preview 2-derived domains are listed at `spec.md:1307-1328`; CPU and memory bounds are shown at `spec.md:1338-1344`; missing domains fail closed at `spec.md:1346-1362` and again at `spec.md:1509-1510`.
- P01's gate-decision separation-of-duty claim at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:81-85` matches `profiles/agent-assurance/gate-decision-kind.toml`. The descriptor describes `template_kind = "gate-decision"` at `profiles/agent-assurance/gate-decision-kind.toml:17-19`, documents `subject_class = "self-modification"` as the trigger at `profiles/agent-assurance/gate-decision-kind.toml:53-66`, and states that when the subject is self-modification the deciding provider AND deciding model family must differ from the proposing provider and model family at `profiles/agent-assurance/gate-decision-kind.toml:92-105`.
- The self-modification rule has landed as a hard invariant: INV06 at `profiles/agent-assurance/gate-decision-kind.toml:199-204` requires all four provider/model-family fields and both inequality predicates only when `decision.subject_class = "self-modification"`. The ontology backs `subject_class`, `provider_id`, and `model_family_id` at `profiles/agent-assurance/ontology.toml:339-374`.
- The multi-provider posture in P01 at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:40-44` and `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:132-138` is supported by the profile overview: the profile is positioned for multi-provider operating environments at `profiles/agent-assurance/overview.md:72-83`; same-model-family review is called structurally inadequate at `profiles/agent-assurance/overview.md:85-88`; single-provider deployments cannot achieve full assurance for self-modification gates at `profiles/agent-assurance/overview.md:90-103`.
- The draft's scope boundaries are accurate: it says the profile is a data format, not an execution runtime, at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:91-97`. SPEC §13 warns that `[kind.capability_envelope]` is a descriptor contract and missing domains fail closed, not an ad hoc runtime grant surface, at `spec.md:1501-1513`.

Severity: advisory; no factual defect found.

## P01-C3: policy compliance

Classification: complete.

Evidence:

- P01 does not propose changes to Agent Skills core: it says "does not ask for changes to the Agent Skills core spec" and "Nothing in the core spec needs to move" at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:22-26`, and repeats "No changes to SKILL.md" / discovery / activation / execution / reserved names at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:122-128`.
- P01 does not propose a JSON Schema sidecar. The only JSON Schema occurrence is the explicit "not being asked" item at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:127`. This matches repo policy: `schemas/README.md:3-15` says the machine-readable schema lives in TOML descriptors and ontology files, and that a separate JSON Schema layer was rejected; `schemas/README.md:17-24` says any future editor schemas should be generated Taplo-compatible artifacts, not a hand-authored parallel source of truth.
- P01 does not name VAP or any specific Verivus runtime/broker. Grep found no `vap`, `verivus.*runtime`, or `verivus.*broker` occurrences in the draft. The generic "agent broker" wording at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:86-89` is abstract and explicitly says the profile names no broker implementation.
- P01 does not name a specific substrate implementation. The existence proof says a reference implementation exists but is deliberately not named at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:130-138`.
- P01 does not cite memory files or internal-only evidence. The only `memory` occurrence in the policy grep is `memory_bounds` at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:75`, which is a SPEC §13 resource-bound field, not a memory-store citation.
- P01 carries no Claude/AI co-author trailer. The draft ends with the author/spec/contact lines at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:153-158`, and grep found no `co-authored-by`, `generated with`, or `Claude Code` trailer.

Severity: advisory; no policy defect found.

## P01-C4: tone and framing

Classification: complete.

Evidence:

- The proposal is framed as a separate, opt-in companion profile at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:16-25`.
- It explicitly says the Agent Skills format is scoped well and that baking assurance into core would defeat portability/adoption properties at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:30-35`.
- The "insufficient" language is scoped to a separate class of deployments, not to Agent Skills' stated purpose: the draft names multi-provider systems, downstream local verification, and mixed-trust regulated contexts at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:37-53`, then says the model is correct but insufficient for those contexts at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:55-57`.
- It positions the profile as a strict consumer of Agent Skills rather than a modification to it at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:59-67`.
- It avoids the internal "brittleness as feature" phrasing. The public-facing substitute is fail-closed / cascade-break language at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:75-80`.
- The ask is soft and collaborative: the draft asks for a sanity check and possible future listing after v1.0 at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:113-120`, then asks maintainers open questions about fit and preferred channel at `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md:140-151`.

Severity: advisory; no tone/framing defect found.

## P02-C1: factual accuracy about mattpocock/skills

Classification: incomplete.

Evidence:

- Blocking defect: P02 says it contains the SKILL.md lines 10-14 excerpt at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:53-60`, but the quote is not byte-for-byte verbatim. The source line is `Every comment or issue posted to the issue tracker during triage **must** start with this disclaimer:` at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:10`; the draft drops the `**must**` Markdown emphasis at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:56-57`. Source lines 12-14 also include a fenced code block around the disclaimer at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:12-14`; the draft uses its own code block at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:55-60`, but the emphasized `must` mismatch means the excerpt is not verbatim as claimed by the review prompt.
- Blocking defect: P02 calls `triage` an "in-production skill" at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:27-29`. I found repo bytes showing the skill exists and is a complete workflow, but not bytes proving production use. The local skill frontmatter describes its use cases at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:1-4`; that does not establish "in-production."
- The MIT license and Matt Pocock attribution are accurate: the draft attribution says the before excerpts come from Matt Pocock's `mattpocock/skills` corpus and labels it MIT at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:14-17`; the license file is MIT and copyrights Matt Pocock at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/LICENSE:1-4`.
- The two category roles and five state roles are accurate. P02 states them at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:36-40`; SKILL.md defines category roles `bug` / `enhancement` at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:21-27` and state roles `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:28-35`.
- The state-transition and invocation descriptions are accurate. P02 describes natural-language invocation, context gathering, optional grilling, and outcome application at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:40-45`; SKILL.md gives natural-language examples at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:42-50`, state transitions at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:40`, context gathering/grilling at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:61-70`, and outcome application at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:71-78`.
- The agent brief claim is accurate. P02 says `ready-for-agent` emits an agent brief whose shape is defined in `AGENT-BRIEF.md` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:43-45`; SKILL.md says `ready-for-agent` posts an agent brief at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:72`, and `AGENT-BRIEF.md` defines the brief as the authoritative structured comment and gives its template at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:1-4` and `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:37-66`.
- The "ADR-cited norms" and `.out-of-scope/` claims are defensible. The ADR classifies triage as a hard-dependency skill at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/docs/adr/0001-explicit-setup-pointer-only-for-hard-dependencies.md:1-10`; SKILL.md tells triage to respect ADRs and read `.out-of-scope/*.md` at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:63`; the `.out-of-scope/` guide defines the knowledge base and says it prevents re-litigation at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/OUT-OF-SCOPE.md:1-7`; the corpus has worked `.out-of-scope` entries at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/.out-of-scope/question-limits.md:1-14` and `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/.out-of-scope/mainstream-issue-trackers-only.md:7`.

Severity: blocking; the public post must either quote SKILL.md exactly, including Markdown emphasis, and remove/qualify "in-production" unless a byte source is added.

## P02-C2: factual accuracy about this project's spec

Classification: incomplete.

Evidence:

- The empty-closure sentinel in P02 is correct and is explicitly marked illustrative. P02 uses `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:97-103`; SPEC §12.1 defines that exact SHA-256 empty sentinel at `spec.md:959-980`.
- `template_kind = "gate-decision"` is real. P02 uses it at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:104-107`; the descriptor names `gate-decision` at `profiles/agent-assurance/gate-decision-kind.toml:17-19` and requires `meta.template_kind = "gate-decision"` at `profiles/agent-assurance/gate-decision-kind.toml:120-126`.
- Blocking defect: the illustrative block says it is using the existing `profiles/agent-assurance/gate-decision-kind.toml` descriptor at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:92-95`, but the shown TOML omits existing required fields and substitutes non-descriptor names without clearly marking them as non-conforming illustration. The descriptor requires `meta.framework_profile = "agent-assurance"` at `profiles/agent-assurance/gate-decision-kind.toml:127-133`; `decision.verdict`, `decision.evidence_root`, `decision.evidence_root_algorithm`, and `decision.decided_at` at `profiles/agent-assurance/gate-decision-kind.toml:134-157`; and at least one `[[decision.cited_bundles]]` at `profiles/agent-assurance/gate-decision-kind.toml:158-163`. P02 instead shows `outcome`, `subject_artifact`, `subject_sha256`, `from_state`, `to_state`, `[proposing_agent]`, `[deciding_provider]`, `[evidence]`, and `[disclaimer]` at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:109-147`. Those fields are not present in the descriptor root shape at `profiles/agent-assurance/gate-decision-kind.toml:38-76` and are not accepted by the current validator shape at `validators/validate_gate_decision.py:60-76` and `validators/validate_gate_decision.py:147-153`.
- Blocking defect: the draft's `subject_class = "issue-triage-promotion"` is clear that it is not self-modification, but it is not a currently valid descriptor value. P02 shows it at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:109-112`; the current ontology values are only `downstream-change` and `self-modification` at `profiles/agent-assurance/ontology.toml:349-356`; the validator rejects any present `subject_class` not in that vocabulary at `validators/validate_gate_decision.py:157-175`. The review bundle allowed an illustrative non-self-modification value, but the draft does not explicitly say this `subject_class` value is out-of-vocabulary / illustrative the way it does for the empty sentinel.
- Blocking defect: P02 presents a fresh-session rule for ordinary triage transitions as "the agent-assurance profile's separation-of-duty rule" at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:157-166`, but the current descriptor has no `session_id`, `fresh_session`, or context-window invariant. INV06 only requires provider/model-family separation when `decision.subject_class = "self-modification"` and says attribution fields are optional for any other `subject_class` at `profiles/agent-assurance/gate-decision-kind.toml:199-204`. The validator likewise only enforces the four provider/model-family fields when `subject_class == "self-modification"` at `validators/validate_gate_decision.py:177-254`.
- The self-modification sharpening itself is accurate. P02 says provider and model family must differ for self-modifying transitions at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:161-166`; the descriptor says the deciding provider AND deciding model family must both differ when the producer agent's own harness/source is being modified at `profiles/agent-assurance/gate-decision-kind.toml:92-105` and `profiles/agent-assurance/gate-decision-kind.toml:199-204`.

Severity: blocking; the example currently reads as an approximate descriptor-backed TOML artifact but is not validator-compatible and does not clearly label the non-descriptor/fresh-session pieces as proposal-only illustration.

## P02-C3: policy compliance

Classification: complete.

Evidence:

- MIT attribution to Matt Pocock is present and accurate at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:14-17`; the source license is MIT and names Matt Pocock at `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/LICENSE:1-4`.
- The excerpt is visually attributed to the triage `SKILL.md` before the code block at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:53-60`, and the front matter attribution identifies the corpus at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:14-17`. The quote is not verbatim, which is covered under P02-C1, but attribution and visual separation are present.
- P02 does not propose changes to Agent Skills core. It says the assurance profile consumes the `SKILL.md` format and leaves the same workflow/artifacts in place at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:21-32`, and it says the `SKILL.md` file itself does not change at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:168-185`.
- P02 does not propose a JSON Schema sidecar. Grep found no `json schema` or `json-schema` occurrence in the draft.
- P02 does not name VAP or a specific Verivus runtime/broker. Grep found no `vap`, `verivus.*runtime`, or `verivus.*broker`. The `agent broker` wording at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:122`, `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:132`, and `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:144` is generic and does not identify an implementation.
- P02 does not cite memory files or internal-only evidence. Grep found no `memory` or `auto-memory` occurrence in the draft.
- P02 carries no Claude/AI co-author trailer. The draft ends with author/companion/spec/contact lines at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:203-208`, and grep found no `co-authored-by`, `generated with`, or `Claude Code` trailer.

Severity: advisory; no policy defect found apart from the quote-verbatim issue already classified under P02-C1.

## P02-C4: tone and framing

Classification: complete.

Evidence:

- P02 frames the delta as small, surgical, and additive at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:21-32`.
- P02 praises the existing workflow and avoids "doing it wrong" framing: it calls the skill well-shaped at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:27-32`, says the skill is tasteful and disciplined at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:47-51`, and explicitly says the issue is not author carelessness at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:79-83`.
- The load-bearing gap is specific rather than vague. P02 identifies free text, same-agent attachment, no signature, no model identifier, no session reference, no provider attribution, and no SHA binding at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:64-77`.
- P02 keeps the workflow unchanged and makes the assurance layer parallel/additive: it says the workflow, skill body, and agent brief stay at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:85-90`, and lists unchanged vs changed items at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:168-185`.
- P02 makes the audience boundary clear: solo projects can keep the disclaimer, while assurance-grade contexts need verifiable provenance at `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:192-201`.

Severity: advisory; no tone/framing defect found.

## Terminal recommendation

`concrete_unresolvable_blocker`: P02-C2-invalid-gate-decision-example, with P02-C1-non-verbatim-quote as an additional blocking defect.
