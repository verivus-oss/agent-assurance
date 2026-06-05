# Rebuttal record — 2026-05-27-agentskills-profile-pitch (iteration r1)

Per `tools/review-request-dag.toml [policy.evidence]`: when the
initiator responds to a reviewer finding, the response MUST cite
code or doc evidence (file + line), not assertion. This record
covers the codex findings dated 2026-05-27T13:22 UTC.

## Reviewer split

- **grok** — `unconditional_approval`; one advisory (P01:120 "safe C" overclaim — fixed pre-rebuttal)
- **mistral** — `unconditional_approval`; no findings
- **codex** — `concrete_unresolvable_blocker`: `P02-C2-invalid-gate-decision-example` plus `P02-C1-non-verbatim-quote`
- **gemini** — unavailable (TerminalQuotaError, ~9h)

Per `[policy.approval].forbidden_approval_bases`, majority among the
three available reviewers is NOT a basis for approval; the codex
findings must be engaged with on substance.

## Engagement

### P02-C1-non-verbatim-quote

**Finding:** the draft's quote at P02:56-57 dropped the `**must**`
Markdown emphasis present at the source.

**Verification against bytes:**
`/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills/skills/engineering/triage/SKILL.md:10`
reads: `Every comment or issue posted to the issue tracker during
triage **must** start with this disclaimer:`. The draft pre-fix
omitted the `**`.

**Disposition:** agreed. Codex is correct. Fixed at
`docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:57`
(restored `**must**`). Quote is now byte-verbatim.

**Secondary point (same finding):** codex also flagged
"in-production" at P02:27-29 as not byte-verifiable. The repo state
shows a complete, opinionated workflow but does not prove
production use. Fixed at
`docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:28`
("in-production" → "working").

### P02-C2-invalid-gate-decision-example

**Finding:** the draft introduced its example with "using the
existing `gate-decision-kind.toml` descriptor" but the shown TOML
omitted required fields, substituted non-descriptor names, used a
`subject_class` value outside the closed vocabulary without declaring
it as an extension, and presented a `fresh_session` rule that does
not appear in the descriptor or INV06.

**Verification against bytes:**

- `profiles/agent-assurance/gate-decision-kind.toml:120-163` lists
  the required fields. The pre-fix example was missing
  `meta.framework_profile`, `decision.verdict` (used `outcome`
  instead), `decision.evidence_root`, `decision.evidence_root_algorithm`,
  `decision.decided_at`, and the required
  `[[decision.cited_bundles]]` section. Codex is correct on every
  one of these.

- `profiles/agent-assurance/ontology.toml:349-356` constrains
  `subject_class` to `["downstream-change", "self-modification"]`.
  The vocabulary is `extensible = true`, but the notes require any
  new value to "state whether the new value triggers INV06" —
  declaration the pre-fix example did not make for
  `"issue-triage-promotion"`. Codex is correct.

- `profiles/agent-assurance/gate-decision-kind.toml:199-204` (INV06)
  triggers only on `subject_class = "self-modification"` and is
  silent on any "fresh session" or "context window" rule for other
  subject classes. The pre-fix prose at P02:157-166 fabricated such
  a rule. Codex is correct.

- The descriptor's ROOT SHAPE at
  `profiles/agent-assurance/gate-decision-kind.toml:38-76` uses flat
  `proposing_provider_id` / `proposing_model_family_id` /
  `deciding_provider_id` / `deciding_model_family_id` fields under
  `[decision]`, not the nested `[proposing_agent]` /
  `[deciding_provider]` tables the pre-fix example invented. Codex
  is correct.

**Disposition:** agreed in full. Codex is correct on all four
sub-points. Fixed at
`docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md:92-145`:
the TOML example now uses the actual descriptor fields (`verdict`,
`evidence_root`, `evidence_root_algorithm`, `decided_at`,
`framework_profile`, flat `proposing_*` / `deciding_*` under
`[decision]`, `[[decision.cited_bundles]]`, `subject_class =
"downstream-change"` for the ordinary triage case). The fabricated
`fresh_session` rule is removed entirely; the surrounding prose now
distinguishes only the descriptor-real cases:
`subject_class = "downstream-change"` (no INV06, optional
attribution, value comes from `evidence_root` binding) vs
`subject_class = "self-modification"` (INV06 fires, cross-provider
required). The `[disclaimer]` block is removed; the disclaimer is
replaced by the `evidence_root` + cited-bundle binding plus the
optional attribution fields.

**Cross-reference to grok's review:** grok classified P02-C2 as
`complete` on the grounds that the bundle scope permitted illustrative
fields. That reasoning was too lenient: the bundle allowed illustrative
*values* (e.g. session refs, hash placeholders) but not field
substitution (`outcome` for `verdict`), not out-of-vocabulary
subject_class without declaration, and not fabrication of rules
not in the descriptor (`fresh_session`). Codex's stricter reading
is the correct one and the fix conforms the example to the descriptor.

## Status after fixes

- P01: unchanged in this iteration (grok's advisory addressed
  pre-rebuttal at the user's request; codex independently classified
  P01-C1..C4 all `complete`).
- P02: changes applied; all codex findings addressed against bytes.
- Re-review queue: the bundle and prompt are unchanged; re-running
  the same four reviewers against the updated drafts will give a
  clean second iteration. Gemini remains quota-blocked for ~9h;
  three-reviewer panel is the minimum acceptable per prior session
  convention.

## Outcome

P02-C1 and P02-C2 transition from `incomplete` to `pending re-review`.
Pre-fix terminal_decision is NOT recorded; re-dispatch of the four
reviewers (or three, if gemini remains blocked) is the gating step
for the session's terminal status.
