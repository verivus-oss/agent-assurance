# SPEC §13 retrofit — scoping plan (2026-05-25)

**Status**: proposal, pending independent multi-LLM review at
`docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan/`.

**Author / Initiator**: claude-opus-4-7 (excluded from reviewer set).

**Closes** (when implementation lands): the explicit follow-up
called out in `spec.md:1478-1486` and `CHANGELOG.md` for the
§13 abstraction-class + capability-envelope work that landed for
only one kind (`cost-record`) in `27c1020` / `7328dfd`.

## 1. Goal

Retrofit the 18 blessed `*-kind.toml` descriptors that do not yet
declare `[kind.abstraction_class]` + `[kind.capability_envelope]`,
in scope-limited phases, so that every conforming kind in the
public spec participates in §13's class + envelope contract and
its closure-root cascade-break property.

## 2. Non-goals (deferred)

- **Wire-format CBOR encoding** (SPEC §13.5): RUNTIME-SPEC, separate
  document.
- **Attenuation calculus** (SPEC §13.5): separate executable
  specification.
- **Enforcement backend** (seccomp+landlock, Capsicum, sandbox-exec,
  Wasmtime): RUNTIME-SPEC.
- **`runtime-observation-attestation` kind** (SPEC §13.5): separate
  follow-up; not declared here.
- **Per-instance envelope narrowing**: instances of any retrofitted
  kind MAY narrow the envelope further (§13.4); this plan addresses
  only the kind-descriptor declaration.

## 3. Current state

Verified via
`python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml`:
> `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).`

Inventory of all 19 blessed kind descriptors and their §13 status
at HEAD (`6b2d451`):

| # | Kind descriptor | §13 today |
|---|---|---|
| 1 | `core/contract-declaration-kind.toml` | (none) |
| 2 | `core/evidence-matrix-kind.toml` | (none) |
| 3 | `core/implementation-dag-kind.toml` | (none) |
| 4 | `core/profile-descriptor-kind.toml` | (none) |
| 5 | `core/readiness-gate-kind.toml` | (none) |
| 6 | `core/traceability-kind.toml` | (none) |
| 7 | `profiles/agent-assurance/adapter-contract-kind.toml` | (none) |
| 8 | `profiles/agent-assurance/adapter-registry-binding-kind.toml` | (none) |
| 9 | `profiles/agent-assurance/assertion-bundle-kind.toml` | (none) |
| 10 | `profiles/agent-assurance/assertion-log-record-kind.toml` | (none) |
| 11 | `profiles/agent-assurance/gate-decision-kind.toml` | (none) |
| 12 | `profiles/agent-assurance/rollback-plan-kind.toml` | (none) |
| 13 | `profiles/agent-assurance/smoke-validation-kind.toml` | (none) |
| 14 | `profiles/agent-assurance/spec-contract-kind.toml` | (none) |
| 15 | `profiles/agent-assurance/threat-model-kind.toml` | (none) |
| 16 | `profiles/cost/cost-record-kind.toml` | **✓ §13** (reference) |
| 17 | `profiles/disclosure/disclosure-attestation-kind.toml` | (none) |
| 18 | `profiles/disclosure/redaction-manifest-kind.toml` | (none) |
| 19 | `profiles/disclosure/selective-disclosure-proof-kind.toml` | (none) |

## 4. Reference shape (cost-record, lines 282–327)

The canonical example landed in `27c1020`. Exact shape at HEAD:

```toml
[kind.abstraction_class]
id          = "observation-record.v1"
description = "Read-only observation artefact: declares hashed citations to prior actions + closed-vocabulary categorical dimensions + integer quantities. No I/O outside the canonical-form text serialisation; no networking; no process spawn."
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"

[kind.capability_envelope]
spec_version = "0.1.0"
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"

[kind.capability_envelope.cpu_bounds]
max_cpu_ms      = 100
max_cpu_percent = 5

[kind.capability_envelope.memory_bounds]
max_bytes = 1048576  # 1 MB

[kind.capability_envelope.filesystem] denied = true
[kind.capability_envelope.sockets]    denied = true
[kind.capability_envelope.http]       denied = true
[kind.capability_envelope.clocks]
  wall_clock_allowed      = false
  monotonic_clock_allowed = false
  precision_cap_ms        = 0
[kind.capability_envelope.random]
  entropy_source = "none"
[kind.capability_envelope.environment]  denied = true
[kind.capability_envelope.process_spawn] denied = true
[kind.capability_envelope.ipc]           denied = true
[kind.capability_envelope.crypto_keys]   denied = true
```

All nine domains explicitly present (per §13.9 missing = denied
fail-closed), all denied / zeroed. This is the **Family A** shape.

## 5. Envelope semantics — interpretation choice

§13.4 says the envelope bounds "an instance MAY require at
runtime". Two readings are possible for kinds whose instances
*describe future actions* (e.g. `implementation-dag` describes
units to be executed, `smoke-validation` records the result of
a smoke run that already executed):

- **Reading R1 (narrow)**: envelope bounds processing the
  TOML document itself. Every kind descriptor is text; parsing
  is pure-data work. Envelope = Family A for all 19 kinds.
- **Reading R2 (wide)**: envelope bounds the actions the
  instance describes. `implementation-dag` envelope would
  cover the units; `smoke-validation` envelope would cover
  the smoke run; etc.

The **cost-record precedent** at HEAD follows **R1**: cost-record
declares observed costs (an action already happened) and uses
Family A. R2 would require cost-record to declare an envelope
covering "anything a costed action might require", which is
both unbounded and useless.

**This plan adopts R1.** Rationale:

- The descriptor is a structural rule about admissibility of
  instances, not a forward-looking permission grant for runtime
  actions (which is §13.5's RUNTIME-SPEC layer).
- R2 would force every kind to declare maximal envelopes, which
  defeats the failure-mode-bounding intent of §13.
- §13.4's "cascade-break on widening" still bites under R1:
  any kind that adds a per-instance executable surface (e.g.
  inline script field) widens parse requirements and breaks
  closure_root.

**Family B / C exceptions**: none under R1. Earlier draft proposed
a Family C envelope for `selective-disclosure-proof` (random +
crypto_keys grants), but round-1 review caught two defects: (a)
the descriptor's own prose at
`profiles/disclosure/selective-disclosure-proof-kind.toml:61`
delegates cryptographic verification to RUNTIME-SPEC, so the
descriptor parse itself needs no crypto capabilities; (b) the
proposed field names (`entropy_source = "system"`, `sign = false`,
`verify = true`) are not in the validator's accepted vocabularies
(`validators/validate_abstraction_class.py:182` accepts only
`os | deterministic_seed | none`; line 214 accepts only
`read_keys | use_keys | generate_allowed`). Selective-disclosure-proof
is therefore Family A like every other kind at HEAD; cryptographic
work is RUNTIME-SPEC and lies outside the descriptor's envelope.

For `adapter-contract`, the descriptor declares an interface, but
the spec author may intend the envelope to bound what the
declared adapter may demand at runtime (R2 leakage). Under R1
this is still Family A. Reviewers may challenge in the Phase 3
review if R2 is the canonical intent for adapter-contract
specifically.

This plan classifies every kind as Family A under R1 by default.

## 6. Proposed abstraction-class taxonomy

Producer-attested taxonomy (Verivus / DAG-TOML). A class id is a
producer-attested **label** for the artefact's role; it is shared
across kinds that share that role at a coarse level. The class id
is NOT a byte-level structural-shape contract — each kind's
own `[[kind.required_fields]]`, `[[kind.required_sections]]`, and
`[[kind.hard_invariants]]` remain the structural rule, and each
kind's `[kind.abstraction_class].description` field MUST reflect
that kind's specific shape (cost-record's existing description at
`profiles/cost/cost-record-kind.toml:282-286` is the right shape
for cost-record only; each retrofitted kind needs its own
kind-specific description).

Thirteen class ids for 19 kinds; 5 ids are shared across multiple
kinds with related but not identical structural rules.

| Class id | Role at the artefact level (NOT a byte-level shape) | Kinds (count) |
|---|---|---|
| `observation-record.v1` | Read-only observation of a past state, action, or outcome; each kind declares its own structural shape. | 5: cost-record (existing), evidence-matrix, gate-decision, assertion-log-record, redaction-manifest |
| `relation-ledger.v1` | Graph of named relations across identifier sets. | 1: traceability |
| `policy-declaration.v1` | Declares contracts / gates / policies that consumers MUST enforce; each kind declares its own constraint shape. | 3: readiness-gate, contract-declaration, spec-contract |
| `procedure-declaration.v1` | Declares a procedure (triggers + actions) executed by a runtime. | 1: rollback-plan |
| `plan-decomposition.v1` | Declares a plan: units → outputs, with DAG ordering. | 1: implementation-dag |
| `validation-record.v1` | Records the outcome of a validation procedure that already ran. | 1: smoke-validation |
| `assertion-set.v1` | Sealed ordered set of canonical assertions with provenance. | 1: assertion-bundle |
| `interface-contract.v1` | Declares a pure-function adapter interface and its runtime policies. | 1: adapter-contract |
| `binding-declaration.v1` | Resolves a reference to an adapter (file, https, oci, ipfs). | 1: adapter-registry-binding |
| `extension-declaration.v1` | Declares a profile: name, namespace, ontology, contained kinds. | 1: profile-descriptor |
| `threat-declaration.v1` | Risk analysis of a change: threats + mitigations. | 1: threat-model |
| `attestation-record.v1` | Signed posture statement about disclosure of subjects. | 1: disclosure-attestation |
| `cryptographic-proof.v1` | Verifiable commitment / proof artefact (SPEC-layer shape only; cryptographic verification is RUNTIME-SPEC). | 1: selective-disclosure-proof |

(13 class ids total; the cost-record-shared one means 12 NEW class
ids if cost-record is counted as already-declared.)

**Per-kind `description` field rule**: when a kind declares
`[kind.abstraction_class].id = "<shared-id>"`, the
`description` field MUST be kind-specific (not the class-level
role text above). Example: `evidence-matrix` declares the
`observation-record.v1` id but its description names the
claims-evidence-matrix structure declared in its own
`[[kind.required_sections]]`. Cost-record's existing
description at HEAD (`profiles/cost/cost-record-kind.toml:282-286`)
is the shape Phase 1+2 retrofits should follow.

## 7. Per-kind proposal

| # | Kind | Proposed class id | Envelope family | Variance from cost-record shape |
|---|---|---|---|---|
| 1 | `contract-declaration` | `policy-declaration.v1` | A | none |
| 2 | `evidence-matrix` | `observation-record.v1` | A | none |
| 3 | `implementation-dag` | `plan-decomposition.v1` | A | none (R1) |
| 4 | `profile-descriptor` | `extension-declaration.v1` | A | none |
| 5 | `readiness-gate` | `policy-declaration.v1` | A | none |
| 6 | `traceability` | `relation-ledger.v1` | A | none |
| 7 | `adapter-contract` | `interface-contract.v1` | A | none (R1; reviewers challenge if R2 intended) |
| 8 | `adapter-registry-binding` | `binding-declaration.v1` | A | none |
| 9 | `assertion-bundle` | `assertion-set.v1` | A | none |
| 10 | `assertion-log-record` | `observation-record.v1` | A | none |
| 11 | `gate-decision` | `observation-record.v1` | A | none |
| 12 | `rollback-plan` | `procedure-declaration.v1` | A | none (R1) |
| 13 | `smoke-validation` | `validation-record.v1` | A | none |
| 14 | `spec-contract` | `policy-declaration.v1` | A | none |
| 15 | `threat-model` | `threat-declaration.v1` | A | none |
| 16 | `disclosure-attestation` | `attestation-record.v1` | A | none |
| 17 | `redaction-manifest` | `observation-record.v1` | A | none |
| 18 | `selective-disclosure-proof` | `cryptographic-proof.v1` | A | none — SPEC-layer parse is shape-only per `selective-disclosure-proof-kind.toml:61`; all cryptographic work is RUNTIME-SPEC and lies outside the descriptor's envelope |

## 8. Phasing

Phased by risk. Each phase = one PR, dispatched to multi-LLM
review per `tools/review-request-dag.toml [policy.*]`.

**Phase 1 — observation records** (5 kinds, all `observation-record.v1`):
- `evidence-matrix`, `gate-decision`, `assertion-log-record`,
  `redaction-manifest` (+ `cost-record` as already-done reference).
- All Family A; insertion of the canonical envelope block plus
  a kind-specific `[kind.abstraction_class].description` field
  per §6's Per-kind description field rule.
- Risk: lowest. The descriptor file's bytes change (its SHA-256
  flips), but its declared root-level `closure_root` value remains
  the empty-closure sentinel because the descriptors cite no
  upstream evidence (§9).

**Phase 2 — declarations** (8 kinds):
- `traceability`, `readiness-gate`, `contract-declaration`,
  `spec-contract`, `threat-model`, `profile-descriptor`,
  `implementation-dag`, `adapter-registry-binding`,
  `disclosure-attestation`.
- All Family A; class ids vary per Section 6 taxonomy.
- Risk: low.

**Phase 3 — procedure-bearing and special** (5 kinds):
- `rollback-plan`, `smoke-validation`, `assertion-bundle`,
  `adapter-contract`, `selective-disclosure-proof`.
- All Family A under R1.
- Risk: medium. Reviewers may push back on R1 vs R2 for the
  procedure-bearing kinds (especially `adapter-contract`, where
  the spec author may intend R2). Plan: ship R1 baseline; if a
  reviewer files a concrete-evidence blocker for R2 on a specific
  kind, revisit that kind in a separate PR.

## 9. Per-kind verification commands

After each retrofit commit (single kind or batch within a phase),
the following MUST be green locally before review dispatch:

```sh
# 1. Abstraction-class validator
python3 validators/validate_abstraction_class.py \
  --repo-root . \
  core/*-kind.toml \
  profiles/agent-assurance/*-kind.toml \
  profiles/disclosure/*-kind.toml \
  profiles/cost/*-kind.toml

# 2. IJB conformance (every kind descriptor)
for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml \
         profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
  python3 validators/validate_ijb_conformance.py "$f"
done

# 3. Kind descriptor structural validation
for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml \
         profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
  python3 validators/validate_kind_descriptor.py "$f" \
    --repo-root . --check-references-exist
done

# 4. §12 closure-root gate
python3 validators/validate_closure_root.py --discover .
```

**§12 closure_root expectation**: the canonical empty-closure
sentinel (`sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`)
**persists** across the retrofit. Per `spec.md §12.1` and `§12.11`,
the `closure_root` field covers upstream-evidence citations only —
not the descriptor's own internal content. Kind descriptors at HEAD
cite no upstream evidence (no `[provenance]` table, no fields
carrying the `cites_upstream` ontology mapping, no `[[evidence_*]]`
rows), so they qualify for the empty sentinel both before and after
the retrofit. The cost-record example at HEAD (the only kind
currently declaring §13) confirms this: it carries the empty
sentinel at `profiles/cost/cost-record-kind.toml:15` even after
declaring `[kind.abstraction_class]` + `[kind.capability_envelope]`.
Reviewers should verify empirically that the §12 validator still
exits 0 after each retrofit and that `grep -n closure_root` shows
the empty sentinel on every retrofitted descriptor.

What *does* change post-retrofit is the descriptor file's SHA-256
(it has new bytes). Per SPEC §13.4, this propagates as a
cascade-break to downstream INSTANCE documents that cite the
descriptor — but the descriptor's own declared `closure_root`
value stays at the sentinel. (`spec.md §13.4` arguably reads as
the descriptor's own closure_root flipping; whether that is a
SPEC defect against `§12.1` is out of scope for this plan and is
filed as a separate issue candidate — see Section 11.)

## 10. Reversibility per phase

Each phase is one PR. To revert, `git revert <phase-sha>` restores
the descriptors to pre-§13 state; downstream consumers that started
relying on the class+envelope contract would lose the structural
rule but no normative breakage at the schema-version level (the
retrofit is `additive` per `spec.md:1478-1486`).

## 11. Out of scope

The following are NOT addressed by this plan and remain follow-ups:

- §13.4 cascade-break property is structural (declared); CI does
  not test cascade propagation across instances downstream of a
  retrofitted kind. Instances do not yet exist for most kinds in
  the public examples; testing cascade on real producer corpora
  is RUNTIME-SPEC work.
- Per-kind `[kind.abstraction_class].description` fields. Each
  retrofitted kind will need its own description; this plan does
  not pre-draft them. The cost-record description at
  `profiles/cost/cost-record-kind.toml:282-286` is the canonical
  shape (kind-specific, ties back to the kind's own
  `[[kind.required_fields]]`).
- The `[[checklist_coverage_satisfied.pairs]]`-style addition is
  cost-record-specific; not needed for other kinds.
- **SPEC §13.4 vs §12.1 internal tension**: §13.4 reads as
  asserting that the descriptor's own `closure_root` flips on
  §13-block changes, but §12.1 / §12.11 say a descriptor citing
  no upstream evidence stays at the empty-closure sentinel. This
  is either a SPEC defect in §13.4 or an implicit forward-looking
  assumption that future descriptors will cite upstream evidence.
  Filed as **ISS-005 candidate**; out of scope for this retrofit
  plan but worth a separate issue if not already documented.

## 12. Open questions for reviewers

1. Does Section 5's R1 reading match the spec author's intent at
   `spec.md:1308-1326`? Cite the exact bytes that confirm or
   refute.
2. Is the taxonomy in Section 6 structurally sound at the
   **producer-attested role** level (which is what §6 now claims,
   per the round-1 review correction)? Cite kind-descriptor bytes
   that confirm or refute. Note: §6 no longer claims the kinds
   sharing a class id have byte-identical structural rules — only
   that they share an artefact-level role and each kind keeps its
   own per-kind description.
3. For `adapter-contract`, is R1 (Family A — bound the descriptor
   parse) correct, or should the envelope cover the adapter's
   own runtime requirements? Cite `[[kind.required_fields]]` or
   the adapter-contract worked example.
4. Is the phasing in Section 8 right? Should Phase 3 be split
   further? Should `adapter-contract` land separately given its
   R1/R2 ambiguity?

## 13. Revision history

| Date | Commit | Change |
|---|---|---|
| 2026-05-25 | `c88f7ea` | Initial plan landed |
| 2026-05-25 | (this commit) | Three round-1 blockers from `docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan/raw_findings/codex.md` addressed: (a) selective-disclosure-proof reclassified Family A; cryptographic-proof.v1 class id retained; (b) `observation-record.v1` description reframed as producer-attested artefact-level role; per-kind description field rule added; (c) §9 internal contradiction on `closure_root` removed — sentinel-persists statement is now the single truth. Round-1 SDP question dropped from §12 (now answered). New §11 out-of-scope item added for the SPEC §13.4 vs §12.1 tension flagged by codex Q6 and gemini U07-F2. |
