# Agent Assurance Profile

**`framework_profile = "agent-assurance"`**

An optional extension to core DAG-TOML that adds stronger governance,
threat modelling, and release gating. Use the Agent Assurance Profile
when the work being done warrants:

- A **machine-checkable spec contract** that the implementation is held
  to.
- A **threat model** for the change itself (not just the system under
  change).
- **Smoke validation** results that the change does not regress agreed
  behaviour.
- A **rollback plan** with explicit, observable triggers.

> **Codename note.** This profile was previously circulated under the
> internal codename **AGDF** (Agent-Driven Development Framework). Files
> in the wild may carry `framework_profile = "AGDF"`; treat that value
> as an alias for `"agent-assurance"`.

---

## What the profile adds

| `template_kind` | Adds | Defined in |
|---|---|---|
| `spec-contract` | Machine-checkable contract the implementation must satisfy | [spec-contract-kind.toml](spec-contract-kind.toml) |
| `threat-model` | Risk analysis of the change itself (see IJB stance below) | [threat-model-kind.toml](threat-model-kind.toml) |
| `smoke-validation` | Recorded smoke run with pass/fail decision | [smoke-validation-kind.toml](smoke-validation-kind.toml) |
| `rollback-plan` | Pre-declared rollback triggers and procedure | [rollback-plan-kind.toml](rollback-plan-kind.toml) |

The profile's entity inventory and attribute vocabularies are
formalised in
[`ontology.toml`](ontology.toml) — the machine-readable companion to
the core ontology at [`../../core/ontology.md`](../../core/ontology.md).
It carries its own `ontology_version` that tracks the Agent Assurance
Profile's vocabulary independently of the core ontology version.

The profile also constrains some core fields:

- **`requirement_kind`** SHOULD draw from the core set plus
  `performance`, `correctness`, `operational` (already in the core
  extensible set).
- **`test_kind`** MAY add domain-specific values (e.g. `benchmark`,
  `property`, `robustness`).
- The Agent Assurance Profile defines a fixed vocabulary for
  **`trigger_kind`** in rollback plans; see
  [rollback-plan-kind.toml](rollback-plan-kind.toml).

---

## When to use the profile

Adopt the profile when **any** of the following hold:

- The change touches a system with regulated outputs (financial,
  medical, safety, compliance).
- The change is part of a release train coordinated across multiple
  repositories.
- The reviewing organisation requires explicit risk acceptance for
  agent-authored changes.
- You need a fleet-wide control plane to reduce many per-repo signals
  into a single release-readiness decision.

If none of these hold, **core DAG-TOML is enough.** Adding the profile
without a corresponding policy environment costs ceremony without
returning evidence.

---

## Scope and posture

The Agent Assurance Profile is positioned for **multi-provider
operating environments**. The load-bearing case is self-modification:
when the artifact under change IS the producer agent's own harness
or source code, the gate-decision adjudicating that change MUST be
issued by a model whose `provider_id` AND `model_family_id` BOTH
differ from the proposing agent's (gate-decision invariant `INV06`).
This conjunctive cross-provider requirement is enforced regardless
of deployment tier; the solo tier's otherwise-permissive self-sign
rule explicitly does NOT relax it (see `tiers/solo.toml` contracts
C02 and C05).

The reason is structural, not commercial: same-model-family review
inherits the training-data and reasoning biases that produced the
failure under review. No amount of process discipline within a single
provider substitutes for genuinely independent review across providers.

**Audience impact.** Deployments that cannot reach a second
provider — air-gapped environments, single-vendor procurement
contracts, regulated stacks with one approved model, sealed
appliances — **cannot achieve full assurance** under this profile
for self-modification gates. Those deployments can still adopt the
profile for ordinary gates (`subject_class` absent or
`"downstream-change"`); self-modification gates will fail INV06
under conformance validation. Operators have three coherent
options: (1) accept partial-assurance status for self-modification,
(2) obtain a second-provider review path (e.g., a separately
contracted human reviewer recorded under `provider_id = "human"`
with a non-overlapping `model_family_id`), or (3) declare the
agent-assurance profile out of scope and use core DAG-TOML alone
for self-modifying systems.

**Migration note for existing profile users.** Pre-INV06 gate-decision
instances do NOT carry `subject_class` or provider/family attribution
fields. Those instances remain valid (INV06 only triggers when
`subject_class = "self-modification"`). New self-modification gates
SHOULD set `subject_class` explicitly and supply the four attribution
fields. Existing tier files (notably `solo.toml`) carved out
self-modification gates from their self-sign permissions as part of
the INV06 introduction; review your tier adoption to confirm the
new contract surface matches your operational reality.

---

## How it slots in

A repository using the Agent Assurance Profile typically ships, for
each release:

```
docs/planning/
├── 01_spec.md
├── 02_DESIGN.md
├── 03_IMPLEMENTATION_PLAN.md
├── 05_TEST_PLAN.md
├── implementation_dag.toml          # core
├── traceability.toml                # core
├── review_readiness.toml            # core (readiness-gate)
├── contract_declaration.toml        # core
├── evidence_matrix.toml             # core
├── SPEC_CONTRACT.toml               # profile
├── threat_model.toml                # profile
├── SMOKE_RESULT.toml                # profile
└── rollback_plan.toml               # profile
```

Each profile artifact sets `framework_profile = "agent-assurance"` in
its `[meta]` table.

---

## Provenance scope

DAG-TOML files describe **intent, evidence, and review readiness**.
They do not issue identities, sign artifacts, or run rollbacks. Those
are runtime concerns belonging to whichever execution and observability
stack you pair this profile with.

A full worked example (four prose documents plus eight DAG-TOML files
for a Rust performance milestone) is published with the upstream
tooling repository, not in this spec repo. It is mentioned here for
context only.

---

## IJB stance for `threat-model`

The `threat-model` artifact's purpose label is "Risk analysis of the
change itself". That phrase describes what the kind *does*; it is not
an in-data abstraction that violates the IJB framework's reality
check (see spec.md §10.5).

Concretely, every field in a threat-model instance reduces to one of
the six IJB primitives:

- `[[threats]]` entries are `thing/instance` (concrete `THREAT:`
  things).
- `likelihood`, `impact`, `residual_risk` are `observed/instance`
  attribute values drawn from closed `constraint/structural`
  vocabularies declared in the profile ontology.
- `mitigated_by` entries are `path/instance` references to `TEST:`
  things.
- Free-text `detection` and `mitigation` are `observed/instance`
  authored facts about the threat (see spec.md §10.3 for the
  free-text deviation policy).

The IJB-forbidden phrase "risk posture" does not appear as a
field name, value, kind label, or conforming-instance concept — only
in this section, in the matching SPEC §10.5 stance, and in the
`threat-model-kind.toml` note, all of which discuss the phrase's
forbidden status as the topic. "Risk analysis" is kind-purpose
metadata, not substrate.
