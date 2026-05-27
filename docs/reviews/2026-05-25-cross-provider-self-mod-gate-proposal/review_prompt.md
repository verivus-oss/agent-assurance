# Proposal review — cross-provider gate-decision for self-modification (2026-05-25)

Fresh-context reviewer. Proposal-stage review (no commit, no diff). The unit
under review is the text of the proposal in §"Proposal text" below.
Reviewers MUST verify every claim about current spec/profile state
against repo bytes at HEAD `8a63abb`.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- HEAD: `8a63abb`
- Bundle: `docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal/review_bundle.toml`

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept the initiator's summary as evidence.
File:line + severity for every finding. `forbidden_approval_bases`:
`stated_intent`, `plan_compliance_claim`, `should_be_fixed_language`.
Terminal: `unconditional_approval` or `concrete_unresolvable_blocker`.

## Context (verify, don't trust)

The proposal was prompted by reading MOSS (arXiv 2605.22794), a
self-evolving agent system that extends evolution from text-mutable
artifacts (skills, prompts, memory, workflows) to the agent's own
harness/source code. That sharpens the project's existing rule that
"the agent cannot validate its own work": when the producer agent IS
the subject of the change, same-model-family review materially weakens
the gate because the reviewer inherits the failure's training-data
blind spots.

The initiator further clarified the product scope: the agent-assurance
profile targets multi-provider deployments ONLY; single-provider users
cannot achieve full assurance. This converts the constraint from a
SHOULD with a tier ratchet to a flat MUST.

Reviewers MUST verify these starting facts against repo bytes:

1. The project already documents "agent cannot validate own work" as
   a principle. Confirm whether/where this is currently expressed in
   `SPEC.md`, `profiles/agent-assurance/`, or only in operator
   memory. Cite file:line.
2. The spec currently has a `gate-decision` kind in
   `profiles/agent-assurance/`. Confirm and cite the descriptor path.
3. The spec currently has NO field on `gate-decision` for verifiable
   provider attribution. Confirm by reading the descriptor.
4. The deployment tiers (`profiles/agent-assurance/tiers/*.toml`) are
   contract-declaration instances. Confirm.
5. The project's spec-change policy requires multi-LLM review via
   `tools/review-request-dag.toml`. Confirm.

## Proposal text

The proposal has three sub-claims. Treat them as P01-C1, P01-C2, P01-C3.

### P01-C1 — The rule

In the agent-assurance profile, add a new constraint:

> When a `gate-decision` artifact's subject of change is the producer
> agent's own harness or source code (a *self-modification* gate), the
> gate-decision MUST be issued by a model from a different provider
> and/or different model family than the agent that proposed the
> change. The `gate-decision` artifact MUST carry verifiable
> provider-attribution metadata identifying both the proposing
> provider and the deciding provider. The attribution MUST be
> mechanically verifiable from the artifact chain — not merely
> self-claimed in prose.

Strength: **MUST**, applied at **all tiers** (solo / team / group /
organization / enterprise — no ratchet). Self-modification gates are
the case; non-self-modification gates are unaffected by this rule.

### P01-C2 — The scope justification

In the agent-assurance profile rationale, state explicitly:

> This profile targets multi-provider deployments. Single-provider
> deployments (whether by procurement constraint, air-gap, regulated
> environment, or vendor lock-in) cannot satisfy the
> self-modification cross-provider rule and therefore cannot achieve
> full assurance under this profile. This is a posture choice, not a
> commercial steering decision: same-model-family review materially
> weakens the gate when the producer is the subject of the change,
> and no amount of process can substitute for genuinely independent
> review.

### P01-C3 — The role concept (agent-federator)

In the agent-assurance profile prose, introduce a runtime role
(NOT a new `template_kind`, NOT a new validator, NOT a VAP-specific
component name):

> An **agent-federator** is the runtime role responsible for (a)
> recording which provider produced a self-modification proposal,
> (b) routing the gate-decision request to a model from a different
> provider/family, and (c) attesting the provider attribution into
> the resulting `gate-decision` artifact so it is verifiable from
> the chain rather than self-claimed. The spec describes the
> contract (what attribution metadata must be present, how it is
> verified); the federator is one implementation shape. Multiple
> independent federator implementations are expected and welcome.

## What to verify

For each sub-claim, classify as **complete**, **incomplete**, or
**unverifiable**, with file:line evidence and severity.

### P01-C1 (the rule)

- Is the rule unambiguous? Could two runtimes implement it differently
  and both believe they conform? If so, what wording would tighten it?
- Is "subject of change is the producer agent's own harness or source
  code" a definable predicate from artifact contents, or does it
  require runtime knowledge the artifact doesn't carry?
- Does the existing `gate-decision-kind.toml` need a new required
  field, or is this an additive optional field constrained only when
  the self-modification predicate holds? Cite the descriptor file:line.
- Does the IJB primitive tagging for any new field follow rules
  KD1–KD3 (constraint, structural)? Cite `SPEC.md §10`.

### P01-C2 (the scope justification)

- Is the multi-provider-only posture coherent with existing tier
  prose? Read `profiles/agent-assurance/tiers/README.md` and
  `profiles/agent-assurance/tiers/solo.toml` and report whether
  solo tier as currently written can coherently include a MUST
  that solo deployments can't satisfy without external help.
- Does the rationale paragraph need to live in `SPEC.md`,
  `profiles/agent-assurance/` README, or both? Make a recommendation
  with file path and section.
- Is there an audience for whom this posture is harmful? Name them
  and assess whether the harm outweighs the assurance gain.

### P01-C3 (the agent-federator role)

- Does the name "agent-federator" collide with existing terminology
  anywhere in `SPEC.md`, `core/`, or `profiles/`? (The initiator
  ran `grep -rni 'federator'` and reported zero matches — verify.)
- Is "role" the right framing, or should this be expressed as an
  `adapter-contract` instance (the spec already has adapter machinery
  for runtime interchange)? Read
  `profiles/agent-assurance/adapter-contract-kind.toml` and report
  whether the federator's contract fits, partially fits, or doesn't fit
  that kind.
- Is there a risk that naming "agent-federator" in the spec
  inadvertently steers toward a single implementation shape (e.g.,
  centralized broker vs. peer-to-peer attestation)? If so, what
  wording would describe the contract without prescribing topology?

### No new defects (against current spec posture)

- Does the proposal contradict any existing hard invariant in
  `SPEC.md §5`? Cite.
- Does it introduce any JSON Schema dependency? (It should NOT —
  see project memory `feedback_no_json_schema`.) Verify by reading
  the proposal text above.
- Does it propose any VAP-specific runtime name? (It should NOT —
  see project memory `reference_vap_architecture_20260522`.)
- Does it create drift between `*-kind.toml` and an example
  without updating both? (Currently no kind file is being edited
  in this proposal stage, but any future implementation must.)

### Process checks (per `[policy.process_checks]`)

- Active-user migration/behavior-change guidance — does the proposal
  include or imply guidance for existing users of the profile? Should
  it?
- No historical dated spec retconned without link or correction note —
  N/A at proposal stage; flag if the proposal text itself retcons
  anything.
- Claimed tests actually run with command output and status — the
  initiator's `grep -rni 'federator'` claim MUST be independently
  rerun and reported.

## Required output (no prefatory chit-chat)

1. `## Summary` — terminal classification for P01.
2. `## Starting-fact verification` — confirm or correct each of the
   five starting facts above, with file:line.
3. `## P01-C1 (the rule)` — findings + classification + file:line.
4. `## P01-C2 (the scope justification)` — findings + classification +
   file:line.
5. `## P01-C3 (the agent-federator role)` — findings + classification +
   file:line.
6. `## No new defects` — confirmation or list of new defects.
7. `## Process checks` — one per `[policy.process_checks]` item.
8. `## Terminal verdict` — `unconditional_approval` or
   `concrete_unresolvable_blocker`. Rationale tied to bytes /
   executed commands. (At proposal stage, "approval" means: the
   proposal as stated is ready to enter implementation; "blocker"
   means: something in the proposal text must change before any
   implementation work begins.)

Persistence: your verbatim response will be saved to
`docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal/raw_findings/<your_model_name>.md`.

Start with `## Summary`.
