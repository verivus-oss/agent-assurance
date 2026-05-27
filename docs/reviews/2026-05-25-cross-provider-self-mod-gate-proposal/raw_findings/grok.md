## Summary

**concrete_unresolvable_blocker** for P01 as written.

The proposal correctly identifies a real assurance gap (absence of provider attribution on `gate-decision` for self-modification cases) and correctly situates the motivation in the project's existing self-approval discipline. However, two sub-claims contain unresolvable defects at the proposal-text layer:

- P01-C1's core predicate ("subject of change is the producer agent's own harness or source code") is not definable from current artifact contents; it requires runtime knowledge that the `gate-decision` descriptor does not yet carry, and the proposal supplies no mechanism for mechanically injecting or verifying that predicate.
- P01-C2's flat MUST-at-all-tiers posture (including solo) is incoherent with the existing solo tier contract language that explicitly permits AI self-signing and single-signer gate decisions.

These are not "should be fixed in implementation" items; they are defects in the proposal text itself. The proposal must be revised (predicate formalization + tier coherence + migration guidance) before any implementation work or kind-descriptor edits begin. The other findings are incompletenesses or nits that would become blockers only if left unaddressed in a later implementation PR.

All claims below are tied to bytes inspected via direct `read_file`, `grep`, and shell commands against HEAD `8a63abbc430ef18b39d6449786f511b88f614ab7` (verified via `git rev-parse HEAD`).

## Starting-fact verification

1. **Partially correct, location overstated.** The principle "agent cannot validate own work" / "an agent cannot validate its own work" appears in research notes (`docs/research/2026-05-22-spec-foundations-research/prompts/00-user-messages.md:24`, `04-follow-up-agent-brief.md:64`, `05-follow-up-exa-deep-researchers.md:106`, `06-user-design-directives.md:66`, and README at line 150) and is referenced in the closed ISS-001 (`docs/issues/2026-05-23-ISS-001-self-approval-discipline.md:70-71` citing external `[[memory/project_gate_validation.md]]`). It does **not** appear in `SPEC.md` (zero matches via `grep -n 'cannot validate own work\|self-approval\|self approval' SPEC.md`) or anywhere in `profiles/agent-assurance/` (same grep, zero matches). It lives in operator/research memory and process-issue ledgers, not yet in normative profile or core prose. File:line evidence from executed `grep` + `read_file`.

2. **Confirmed.** `profiles/agent-assurance/gate-decision-kind.toml` exists (verified `ls -la` + `head -30`), declares `template_kind = "kind-descriptor"` and `describes_kind = "gate-decision"`, and contains the full `[kind]` contract. Descriptor path: `profiles/agent-assurance/gate-decision-kind.toml:1-235`.

3. **Confirmed.** Executed `grep -n 'provider\|model_family\|attribution\|proposing\|deciding' profiles/agent-assurance/gate-decision-kind.toml` returned zero matches. The `[decision]` table and all `[[kind.required_fields]]` / `[[kind.hard_invariants]]` (lines 81-158) contain no provider-attribution surface. Current shape is purely verdict + evidence_root + cited_bundles + failed_constraint_refs + override_refs + decided_at.

4. **Confirmed.** Every tier file declares `template_kind = "contract-declaration"` (e.g., `profiles/agent-assurance/tiers/solo.toml:11` via `grep`; `enterprise.toml`, `team.toml` etc. match). `tiers/README.md:5-10` explicitly states "Tiers are NOT a new `template_kind`; each tier file is a self-contained, validator-conformant `contract-declaration` instance." Inheritance is documented as "NOT a schema feature" (README:19-23). Verified by direct read + grep on all five *.toml.

5. **Confirmed.** `CONTRIBUTING.md:56-74` ("Review Discipline §1. No initiator self-approval") mandates independent review via `tools/review-request-dag.toml`, cites `[policy.approval]` forbidden/required bases, and points to ISS-001 + persisted `docs/reviews/` artefacts. The DAG itself (`tools/review-request-dag.toml:56-94`) encodes the exact rules. Verified by `read_file CONTRIBUTING.md:56-74` + `read_file tools/review-request-dag.toml:56-94`.

## P01-C1 (the rule)

**Classification: incomplete** (with one high-severity structural ambiguity).

- The rule text is ambiguous on the self-modification predicate. "subject of change is the producer agent's own harness or source code" cannot be evaluated from the contents of any current DAG-TOML artifact (implementation-dag, traceability, gate-decision, etc.). No field currently records "producer agent identity", "harness boundary", or "source repo vs. agent harness" (confirmed by `grep -rn 'harness\|producer.*agent\|subject of change' SPEC.md core/ profiles/ --include="*.toml" --include="*.md" | grep -v review` yielding only tangential hits). This predicate requires runtime knowledge external to the artifact chain. Two conforming runtimes could therefore disagree on when the cross-provider rule triggers while both claiming conformance. (Severity: high; affects mechanical verifiability claim.)

- `gate-decision-kind.toml` currently has no provider-attribution field (confirmed above). Adding one is the correct surface. The proposal does not state whether the new field(s) would be unconditionally required on every `gate-decision` or only when the (undefined) self-mod predicate holds. The text says "MUST carry verifiable provider-attribution metadata" for self-mod cases only, but supplies no conditional vs. required shape. This is underspecified for a kind-descriptor edit. Cite: `profiles/agent-assurance/gate-decision-kind.toml:47-71` (current `[decision]` root shape) and 101-118 (required_fields).

- IJB tagging for any future field: per `SPEC.md:620-627` (table under §10.2), a new `[[kind.required_fields]]` or `[[kind.hard_invariants]]` entry on the gate-decision descriptor MUST be tagged `ijb_primitive = "constraint"`, `ijb_constraint_type = "structural"`. The proposal text does not yet declare the field, so this cannot be violated by the proposal itself, but any implementation that adds a bare string field without the tags would fail KD2. (Severity: medium; preemptive note.)

- No contradiction with `SPEC.md §5` hard invariants (verified `read_file SPEC.md:341-389`): the proposal touches none of the DAG inverse, single-producer, reference-resolution, or closure-cycle rules.

**File:line evidence:** `profiles/agent-assurance/gate-decision-kind.toml:1-235` (full read), `SPEC.md:620-627` (IJB KD table), `grep` runs cited above.

## P01-C2 (the scope justification)

**Classification: incomplete** (high-severity coherence defect with existing tier contracts).

- The multi-provider-only posture is not coherent with current tier prose. `profiles/agent-assurance/tiers/solo.toml:56-59` states "Gate decisions require exactly one signer (the author or designated agent)" and earlier contracts explicitly permit "AI agents MAY self-sign overrides at any severity_tier" (C02:32-33). The tier README (`profiles/agent-assurance/tiers/README.md:27`) describes solo as "Baseline. Self-sign overrides; any runtime kind; local log." A flat MUST that solo deployments "cannot achieve full assurance" directly contradicts the tier's declared contract surface. Either the tier files must be updated to mark the self-mod rule as unsatisfied at solo (or declare solo = partial assurance), or the proposal's "applied at ALL tiers (no ratchet)" language must be softened. Current bytes make the flat MUST unworkable. (Severity: high; concrete incoherence.)

- Rationale placement recommendation: the paragraph belongs in `profiles/agent-assurance/overview.md` (new "Scope and posture" subsection after line 68) **and** `SPEC.md` §6 (Extension model) as a profile-scope limitation note. It does **not** belong only in the profile; the "targets multi-provider deployments ONLY" claim is a top-level posture that affects how readers interpret the entire profile. Tiers/README.md should also receive a one-paragraph cross-reference. (Severity: medium.)

- Audience harmed: single-provider, air-gapped, regulated, or procurement-constrained users who adopted (or planned to adopt) the agent-assurance profile under the prior implicit assumption that it was achievable with one model family. The harm is real (profile becomes unusable for a documented audience) but the assurance gain is also real. The proposal text does not acknowledge or mitigate this; that absence is itself a defect. (Severity: medium.)

**File:line evidence:** `profiles/agent-assurance/tiers/solo.toml:21-60` (full contract set), `profiles/agent-assurance/tiers/README.md:1-68` (ladder + solo description), `read_file` + `grep` on tiers/*.toml.

## P01-C3 (the agent-federator role)

**Classification: incomplete** (low-severity naming/steering risk).

- Name collision: **verified absent**. Executed `grep -rni 'federator\|agent.federator\|agent_federator' --include="*.toml" --include="*.md" . | grep -v '2026-05-25-cross-provider-self-mod-gate-proposal'` returned zero matches in SPEC.md, core/, profiles/, validators/, examples/, docs/ (outside this review session's own prompt/bundle). Initiator claim confirmed by independent re-execution. (Process check pass.)

- "Role" framing vs. adapter-contract: does **not** fit `adapter-contract-kind.toml`. That kind is strictly for pure-function IJB-assertion emitters with declared `input_source`, `runtime_kind`, conformance fixtures, and hermeticity policy (read: `profiles/agent-assurance/adapter-contract-kind.toml:20-32, 87-135`). The federator concept (routing + attestation of provider identity into a gate-decision) is an orchestrator responsibility, not a tool-output-to-assertion adapter. Proposal correctly states "NOT a new template_kind, NOT ... adapter-contract". Using adapter-contract would be a category error. (Severity: low.)

- Steering risk: real but mitigated by the proposal's own language ("the federator is one implementation shape. Multiple independent federator implementations are expected and welcome"). Still, giving the concept a proper-noun label ("agent-federator") in normative profile prose creates a gravitational pull toward a named component or centralized broker topology. Safer wording: describe the **required contract** ("the runtime **must** record proposing-provider and deciding-provider attribution on self-mod `gate-decision` artifacts such that it is mechanically verifiable from the chain") without assigning a role name. This preserves the "multiple shapes welcome" intent without prescribing federation. (Severity: low.)

**File:line evidence:** `profiles/agent-assurance/adapter-contract-kind.toml:17-179` (full read), `grep` command output above, proposal text lines 94-102.

## No new defects

- Does **not** contradict any `SPEC.md §5` hard invariant (full read of 341-389 + 1102-1108; proposal is profile-level constraint on an existing kind, not a graph or closure change).
- Does **not** introduce JSON Schema dependency (proposal text explicitly avoids new kinds and sidecars; consistent with project memory `feedback_no_json_schema` and `SPEC.md §9` rationale).
- Does **not** propose any VAP-specific runtime name (text contains none; consistent with `reference_vap_architecture_20260522` memory).
- Does **not** create `*-kind.toml` vs. example drift (proposal stage; no kind files are being edited yet; future implementation PRs must update both per CONTRIBUTING.md:35-42).

All four checks pass on current proposal text.

## Process checks

- **Active-user migration/behavior-change guidance:** The proposal text contains **zero** guidance for existing profile users (solo deployments, single-provider teams, air-gapped environments). It converts a prior implicit "achievable with process" posture into an explicit "impossible for single-provider" posture without migration notes, tier carve-outs, or "partial assurance" labeling. Per `[policy.process_checks]` this is a required confirmation item; it is absent. (Finding: incomplete; should be present in any revised proposal.)

- **No historical dated spec retconned without link or correction note:** N/A at proposal stage. The proposal text itself does not retcon any prior dated spec language.

- **Claimed tests actually run with command output and status:** The initiator's `grep -rni 'federator'` claim was independently re-executed (see P01-C3 and Starting-fact 5). Command: `grep -rni 'federator\|agent.federator\|agent_federator' --include="*.toml" --include="*.md" . 2>/dev/null | grep -v '2026-05-25-cross-provider-self-mod-gate-proposal'`. Result: zero matches outside the review session documents. Claim holds. All other verify commands listed in review_bundle.toml:110-120 were executed during this review (git rev-parse, ls, cat, multiple greps).

## Terminal verdict

**concrete_unresolvable_blocker.**

The proposal cannot enter implementation because:
- P01-C1's triggering predicate is not mechanically evaluable from artifact contents under current spec bytes (`gate-decision-kind.toml:47-71`, absence of any producer/harness identity surface in SPEC.md or profile).
- P01-C2's "MUST at all tiers — solo cannot achieve full assurance" is directly contradicted by the solo tier's self-signing contract (`profiles/agent-assurance/tiers/solo.toml:32-33,56-59` and README:27).

Both are defects in the proposal text, not implementation details. Revision of the predicate formalization, tier coherence language, placement of the rationale, and addition of migration/behavior-change guidance is required before any `gate-decision-kind.toml` edit, profile prose change, or example update may begin.

All findings above rest on direct inspection of repo bytes at `8a63abbc430ef18b39d6449786f511b88f614ab7` and executed commands; none rest on stated_intent, plan_compliance_claim, or "should be fixed" language.
