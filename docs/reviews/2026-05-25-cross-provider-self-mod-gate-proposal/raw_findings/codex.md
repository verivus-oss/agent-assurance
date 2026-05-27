## Summary

P01 terminal classification: **incomplete**.

The proposal is directionally coherent, but P01-C1 has a concrete blocker before implementation: the rule is not mechanically precise enough to produce one conforming implementation. Specifically, `different provider and/or different model family` is ambiguous, and the self-modification predicate is not currently derivable from `gate-decision` artifact contents.

## Starting-fact verification

1. **Corrected**: "agent cannot validate own work" is not currently a SPEC/profile rule. It is documented in process material: `CONTRIBUTING.md:56-62` says contributors must not issue approving terminal verdicts for their own spec-surface changes, and `tools/review-request-dag.toml:56-64` excludes the initiator from the standard reviewer set. `docs/issues/2026-05-23-ISS-001-self-approval-discipline.md:66-71` references operator memory text, but that is not `SPEC.md` or `profiles/agent-assurance/`.

2. **Confirmed**: `gate-decision` is a profile kind. `SPEC.md:104-106` lists it, and the descriptor is `profiles/agent-assurance/gate-decision-kind.toml:1-18`.

3. **Confirmed**: current `gate-decision` has no verifiable provider-attribution field. Its root shape only has verdict, evidence root/algorithm, decided timestamp, cited bundles, failed constraints, and overrides at `profiles/agent-assurance/gate-decision-kind.toml:47-60`; required fields are only `meta.template_kind`, `meta.framework_profile`, `decision.verdict`, `decision.evidence_root`, `decision.evidence_root_algorithm`, `decision.decided_at`, and cited bundles at `profiles/agent-assurance/gate-decision-kind.toml:81-123`.

4. **Confirmed**: deployment tiers are `contract-declaration` instances. `profiles/agent-assurance/tiers/README.md:3-10` says tiers are self-contained validator-conformant `contract-declaration` instances; `profiles/agent-assurance/tiers/solo.toml:9-11` declares `template_kind = "contract-declaration"`.

5. **Confirmed**: spec-change policy requires independent review via `tools/review-request-dag.toml`. `CONTRIBUTING.md:56-68` requires independent reviewers under that workflow; `tools/review-request-dag.toml:66-94` defines verification and approval bases.

## P01-C1 (the rule)

Classification: **incomplete**.

Finding C1-F1, severity **high**: the phrase "different provider and/or different model family" is ambiguous. Given the multi-provider posture, one runtime could require only provider difference while another permits same-provider/different-family or different-provider/same-family. Tighten to a single predicate, e.g. `deciding_provider_id MUST differ from proposing_provider_id AND deciding_model_family_id MUST differ from proposing_model_family_id; absence or unverifiable attribution fails the self-modification gate.` Current profile vocabularies for `gate-decision` do not define provider or model-family attribution; existing gate-decision vocabularies are only verdict/evidence-root and authority operands at `profiles/agent-assurance/ontology.toml:212-228` and `profiles/agent-assurance/ontology.toml:284-327`.

Finding C1-F2, severity **high**: "subject of change is the producer agent's own harness or source code" is not currently a predicate derivable from `gate-decision`. The descriptor has no subject, proposer, changed-path, harness/source marker, or upstream proposal attribution field: `profiles/agent-assurance/gate-decision-kind.toml:47-60`, `profiles/agent-assurance/gate-decision-kind.toml:81-123`. The proposal must require a chain-verifiable self-modification marker or subject reference, not runtime memory.

Finding C1-F3, severity **medium**: provider-attribution fields should not become unconditional required fields for every `gate-decision`, because non-self-modification gates are explicitly unaffected. Per versioning policy, adding required fields or tightening validation is a major change: `SPEC.md:482-489`. The safer shape is additive optional fields plus a hard invariant: when the chain marks the gate as self-modification, proposer/decider attribution fields are required and mechanically verified.

IJB note: new descriptor blocks must follow §10 mapping: required fields and hard invariants are `constraint/structural` at `SPEC.md:618-627`; ontology vocabularies are `constraint` with structural/policy typing at `SPEC.md:597-617`. Instance provider/model-family values are observed attributes unless implemented as closed/extensible vocabularies.

## P01-C2 (the scope justification)

Classification: **complete with implementation notes**.

Finding C2-F1, severity **medium**: the posture is coherent only if "solo" means one developer, not one provider. Current tier prose says solo is "One developer" with "self-sign overrides" and "local log" at `profiles/agent-assurance/tiers/README.md:25-31`; solo permits AI self-sign overrides and exactly one gate-decision signer at `profiles/agent-assurance/tiers/solo.toml:29-35` and `profiles/agent-assurance/tiers/solo.toml:53-59`. A solo user can still conform if they use an external different provider/family for self-modification gates, but the tier README should say that explicitly.

Finding C2-F2, severity **low**: rationale should live in profile docs, not core SPEC. Recommended placement: `profiles/agent-assurance/overview.md` under "When to use the profile" after `profiles/agent-assurance/overview.md:53-68`, plus `profiles/agent-assurance/tiers/README.md` near the ladder at `profiles/agent-assurance/tiers/README.md:12-31`. The normative mechanics belong in `gate-decision-kind.toml`.

Audience harm, severity **medium**: single-provider, air-gapped, procurement-constrained, and regulated deployments lose "full assurance" for self-modification. The harm is real, but for self-modifying agent harness/source changes the assurance gain outweighs it because the current project policy already treats initiator self-approval as invalid evidence: `CONTRIBUTING.md:56-68`.

## P01-C3 (the agent-federator role)

Classification: **complete with wording risk**.

Finding C3-F1, severity **low**: no terminology collision in the spec/profile/core surface. Executed `grep -rni 'federator' SPEC.md core profiles; printf 'status=%s\n' "$?"`; output was `status=1` with no matches. The exact repo-wide grep now returns matches only because this review bundle/prompt/raw findings already contain the proposal text.

Finding C3-F2, severity **low**: "role" is the right framing. `adapter-contract` is for a pure function converting raw tool output into IJB assertions and explicitly does not specify execution: `profiles/agent-assurance/adapter-contract-kind.toml:21-31`. The federator's routing and provider-selection duties are runtime orchestration, not an adapter contract. Attestation emission could be implemented through an adapter, but the role itself only partially fits that kind.

Finding C3-F3, severity **low**: naming "agent-federator" can imply a central broker. The proposal mitigates this by saying the federator is one implementation shape and multiple implementations are expected. Stronger topology-neutral wording: "The runtime MUST record proposer/decider provider attribution and route self-modification gate decisions to an independently attributed provider/family; implementations may be centralized, peer-to-peer, or otherwise distributed."

## No new defects

No contradiction with current `SPEC.md §5` hard invariants. §5 covers existing implementation DAG, traceability, and review-readiness invariants and delegates machine-readable contracts to descriptors: `SPEC.md:341-383`.

No JSON Schema dependency introduced. Existing policy says no separate JSON Schema layer is shipped or planned: `SPEC.md:493-537`.

No VAP-specific runtime name is proposed; the bundle explicitly keeps VAP-specific names out of scope at `docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal/review_bundle.toml:53-59`.

No kind/example drift exists at proposal stage because no files are edited. Future implementation must update `profiles/agent-assurance/gate-decision-kind.toml:160-163` and `examples/minimal-gate-decision.toml:17-30` together if fields are added.

## Process checks

Active-user migration/behavior-change guidance: **missing but implied**. The proposal says single-provider deployments cannot achieve full assurance, but implementation should add migration guidance for current profile users in `profiles/agent-assurance/overview.md` and `profiles/agent-assurance/tiers/README.md`.

No historical dated spec retconned without link/correction note: **pass**. The proposal is forward-looking; I found no retcon claim in the proposal text.

Claimed tests actually run: **pass with scope correction**. `git rev-parse HEAD` returned `8a63abbc430ef18b39d6449786f511b88f614ab7`. Scoped collision check `grep -rni 'federator' SPEC.md core profiles` returned no matches with status `1`. Repo-wide grep returns status `0` now because the proposal review files themselves contain the word.

## Terminal verdict

`concrete_unresolvable_blocker`

Rationale: approval cannot be based on intent or "should be fixed" language under `tools/review-request-dag.toml:77-94`. The proposal text must change before implementation to define a single provider/model-family predicate and require a chain-verifiable self-modification/proposer/decider attribution surface. Current `gate-decision` bytes do not carry enough data to verify the proposed MUST mechanically.
