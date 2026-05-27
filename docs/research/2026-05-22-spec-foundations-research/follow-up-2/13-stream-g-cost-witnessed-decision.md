# Stream G — Cost-Witnessed Decision (added 2026-05-22)

The third named frontier primitive, peer to **Provable Intent** (Stream B)
and **Structural Governance** (Stream A + abstraction-class type safety,
Stream F). Where Provable Intent asks *what did the producer mean to do?*
and Structural Governance asks *what is this artifact allowed to do?*,
Cost-Witnessed Decision asks the third question the spec has been quietly
assuming an answer to:

> **What did it cost to decide?** And which kind of *deciding entity*
> incurred that cost — a deterministic check, a single LLM, a consensus
> run, a human reviewer, a notarised audit?

Today the spec's gate-decision and evidence-matrix kinds record *that* a
gate fired and *what* evidence was cited. They do not record the
**price** of the decision or **what class of decider** paid it. That
gap is load-bearing for separation-of-duty validation, for auditor
threat-modelling, and for the multi-implementation interop story.
Stream G surfaces it as a named research stream.

---

## Question

**At the SPEC layer**, what is the smallest declarative shape that
captures the cost of a costed action — be it an LLM call, a CI
evidence run, a human review, a notarisation, a transparency-log
write — such that:

1. A gate-decision can cite *which* cost records witnessed the
   decision, and an auditor can see *what kind of entity* paid for it.
2. An evidence-matrix entry can cite *which* cost records were paid to
   produce each piece of evidence — distinguishing a deterministic
   check from an LLM consensus run *as a structural property of the
   matrix*, not as implementer flavour.
3. The shape is **closed enough** that two independent runtimes
   produce interoperable cost records, and **open enough** that the
   spec does not become a billing dialect.

The stream's deliverable is a **kind-descriptor sketch** for a new
`cost-record` (or similar abstractly-named) `template_kind` — not a
ledger format, not a billing schema, not a unit-of-account
specification.

---

## Why this is the third frontier primitive

Three earlier dossier threads point at this gap; Stream G is the
consolidation:

- **[`08-follow-up-synthesis.md` Stream C](../08-follow-up-synthesis.md#stream-c--separation-of-duty-validation-converged-design):**
  the converged separation-of-duty pattern requires that "Proof" be
  produced by an entity distinct from the producer, and identifies four
  candidate mechanisms (reproducible re-build, TEE re-execution, MPC
  aggregate, threshold signer). An auditor confronted with a `gate-decision`
  document today **cannot tell** which mechanism was used — and the four
  mechanisms have radically different cost profiles, threat surfaces, and
  defensible-against-what guarantees. The cost shape *is* the signal.
- **[`follow-up-2/11-overkill-rebuttal-and-frontier-problems.md`](./11-overkill-rebuttal-and-frontier-problems.md):**
  "if implementation is automated, attention shifts to governance of
  generated artifacts." If the *cost* of generating an artifact is the
  variable the producer optimises against — and post-2026 every producer
  does — then a governance spec that ignores cost is a spec that ignores
  the actual incentive surface. The compiler analogue is exact: early
  compilers were judged on bytes-per-instruction (a cost metric); modern
  ones report compile-time, memory-peak, codegen-size, and binary-size
  *as load-bearing observable properties* of the build artifact.
- **The VAP-vs-spec sub-agent finding** (see Stream F prep notes): the
  internal product implementation has a load-bearing cost-accounting
  module that the public spec has no slot for. The current
  patch — "leave it to the runtime" — produces a vendor-incompatible
  extension surface for anyone who ships an Agent Assurance runtime,
  because every vendor invents their own cost record shape. Without
  naming the shape at the SPEC layer, fragmentation is the default
  outcome.

The argument generalises: **cost is a structural property of
agent-driven systems, not implementer flavour.** Every action in an
autonomous-agent system has measurable cost. "Routing work to the
cheapest competent model" is a decision the spec's evidence-matrix
and gate-decision kinds implicitly assume but never document.
Brittleness-as-feature says: *if the spec is implicitly assuming a
thing, the spec must explicitly model the thing — or the assumption
becomes the seam an attacker exploits.*

In particular, for **auditor threat modelling**:

- A gate decided by a deterministic SHA-256 comparison defends
  against one class of threats (silent bit-flip, supply-chain
  substitution).
- A gate decided by a single LLM call defends against a different
  class (semantic policy violation under attacker-controlled prose),
  with a different failure mode (prompt injection, hallucinated
  pass).
- A gate decided by a three-model consensus run defends against the
  second-class threats *and* model-specific failure modes, at higher
  cost.
- A gate decided by a human reviewer defends against a fourth class
  (novel-category threats the rule set never anticipated) at much
  higher cost.

These are not equivalent. An auditor reading a gate-decision *must*
be able to see which of these four classes paid for the verdict.

This is why Cost-Witnessed Decision is a peer of Provable Intent and
Structural Governance — not a subordinate of either. Provable Intent
says *what* was meant; Structural Governance says *what shape* the
work must hold; Cost-Witnessed Decision says *what kind of work was
spent to certify it.* All three must be observable at the artifact
layer, or the artifact is undergoverned.

---

## Constraints

- **No VAP-specific names.** This is a public-spec deliverable. The
  cost-record kind must be nameable independently of any private
  product line; others must be free to build their own conforming
  implementations. Names like `ledger`, `vault`, `meter`, `ijb`-suffixed
  variants, etc., are out of bounds at the SPEC layer.
- **No currency, billing, vendor pricing, or model SKUs.** Spec
  records the *shape* of a cost record and how it cross-references
  other kinds. Conversion rates, contract terms, fiat values, and
  vendor-specific identifiers (e.g. specific model IDs at specific
  providers) are runtime / control-plane territory.
- **No per-unit rates or formulas in the canonical form.** A
  cost-record carries a **declared quantity in a closed-set dimension
  category** (token-equivalent, compute-time-seconds, storage-bytes,
  bandwidth-bytes, human-review-time-seconds, energy-joules-equivalent,
  evidence-run-count) and an optional **producer-attested unit label**.
  No formulas. No `eval`. No computed fields.
- **No JSON Schema sidecar.** Per `06-user-design-directives.md` and
  the `feedback_no_json_schema` ethos: cost-record validation lives in
  the `*-kind.toml` descriptor and the IJB-tagged ontology entries,
  enforced by the safe-Rust / safe-Go / safe-C validators (per Stream
  D / Stream E).
- **No Turing-complete primitives in canonical form.** Cost records
  are declarative data. Where aggregation is needed, it happens in
  the runtime — a downstream `cost-rollup` artifact (out of scope
  here) MAY summarise many records, but the canonical cost-record is
  not itself an evaluator.
- **The cost-record is not itself a signed attestation.** Stream B's
  attestation can *witness* a cost-record (sign over its content
  hash), but the record alone is not legally binding. Producers MAY
  ship cost-records inside an assertion bundle; consumers treat
  unwitnessed cost-records as declared posture, not as proof.
- **Placement in the profile structure.** Two viable homes:
  - **Option A — extend the Agent Assurance Profile.** Add
    `cost-record` to the existing nine kinds. Pro: lowest friction;
    cost is a peer of `gate-decision` and `assertion-log-record`,
    and the cross-reference shape is local. Con: the profile is
    already large; adding a tenth kind raises the "kitchen-sink
    profile" objection.
  - **Option B — new minimal `cost` profile under `profiles/cost/`.**
    A standalone profile with one or two kinds (`cost-record`,
    eventually `cost-rollup`), separately versioned, declared via
    `framework_profile = "cost"`, composable with `agent-assurance`
    by virtue of the namespace partition in SPEC §2.5.
    Pro: keeps Agent Assurance focused; opt-in by adopters who want
    auditor-grade cost signals without the rest of Agent Assurance.
    Con: requires the multi-profile composition story (which the
    spec already nominally supports via `extends`, but has no
    worked example yet).

  **Preliminary verdict:** Option B. Cost-Witnessed Decision is
  conceptually peer to (not subordinate of) Agent Assurance — a
  disclosure-bundle profile, a smoke-validation profile, and a
  rollback-plan profile all benefit from costed gates. The minimal
  `cost` profile becomes the first worked example of
  multi-profile composition. **Final decision deferred to the
  research wave.**

---

## Survey targets (for the actual research wave)

The goal of the survey is **not** to adopt any one of these
verbatim — none of them target an agent-assurance / autonomous-
infrastructure context — but to learn what dimension categories
existing systems treat as load-bearing, how they cross-reference
costs to the artifacts that incurred them, and where the seams
are.

- **FinOps Foundation principles and Framework v2.** What the
  Framework declares as a "unit of accounting" and how cost
  allocation maps onto resource hierarchies. Treat as the
  closest organisational analogue; not a schema source.
- **CNCF FOCUS spec (FinOps Open Cost & Usage Specification).**
  Currently the most ambitious attempt at a cross-vendor schema
  for cloud cost / usage telemetry. Survey its dimension
  enumeration, its canonical-record shape, and what it does *not*
  cover (agent runtime cost, evidence runs, human review).
- **OpenCost (CNCF, ex-Kubecost).** The reference open
  implementation of FOCUS-adjacent accounting on Kubernetes. Of
  particular interest: how it attributes shared / overhead costs
  back to namespaces — the analogue is attributing shared
  evidence-run costs back to specific gate decisions.
- **Hyperscaler Cost Explorer APIs (AWS Cost Explorer, GCP
  Billing, Azure Cost Management).** Less for adoption (vendor-
  specific); more to understand the dimensions each treats as
  primitive. Note especially "tags" / "labels" — the join key
  between cost records and the artifacts they cover. The Stream
  G analogue is the citing-kind reference.
- **MLOps cost telemetry surfaces (Weights & Biases run logs,
  MLflow metric logging, OpenLLMetry / OpenInference traces).**
  How model-call cost is currently emitted (tokens, latency,
  dollars-equivalent, model identifier). Of interest: the
  emerging convention of treating tokens-in / tokens-out /
  latency / cost as a triple-quad on every model call.
- **OpenTelemetry metrics and semantic conventions for
  generative AI.** The W3C-adjacent attempt at standardising the
  triple-quad above. Note the spec-vs-runtime boundary:
  OpenTelemetry is wire telemetry, not a signed durable record.
- **eBPF-based attribution stacks (Kepler for energy,
  Pixie / Parca for compute).** For the energy and compute-time
  dimensions. Note these are observation engines; the cost-record
  is the durable summary produced from their output.
- **Carbon-aware accounting (Cloud Carbon Footprint, Boavizta,
  Software Carbon Intensity / SCI ISO/IEC 21031).** For the
  energy-joules-equivalent dimension. Important: ISO/IEC 21031
  is a measurement methodology, not a record format; what we
  borrow is the closed-set of dimensions, not the math.
- **OpenChain / SPDX SBOM cost extensions (emerging).** If
  the SBOM-adjacent cost-of-supply story has begun to coalesce,
  surface what dimensions they treat as primitive.
- **Academic: differential-privacy budget accounting.** The
  cleanest existing example of *accounting a non-monetary
  scarce resource against a security-critical decision*. The
  cost-record / gate-decision pairing is closely analogous to
  the privacy-budget / query pairing.
- **Academic: PoLR-style proofs of resource use in TEEs.** For
  the witness-the-runtime-actually-spent-this case (energy-of-
  execution, cycles-of-compute) at the boundary where a TEE
  attests its own compute consumption. Relevant if Stream B's
  attestation envelope needs to witness cost-records produced
  inside a TEE.

The survey wave **MUST stay neutral** on which to adopt. The
deliverable is a comparison matrix, not a vote.

---

## Argument to ground or rebut

The research wave should treat these as specific testable claims:

1. **Closed dimension set is sufficient.** The seven categories
   below cover the practical surface of agent-driven costs at the
   SPEC layer:
   - `token_equivalent` — work measured in tokenisable units (LLM
     calls, prompt-templated reasoning, embedding lookups)
   - `compute_time_seconds` — wall-clock or CPU-second consumption
     of deterministic compute (CI runs, validator passes,
     re-builds)
   - `storage_bytes` — durable storage retained as a consequence
     of the action (log writes, evidence retention)
   - `bandwidth_bytes` — data egress / transport consumed
   - `human_review_time_seconds` — wall-clock time of a named
     human reviewer's engagement
   - `energy_equivalent` — energy in a producer-declared
     equivalent unit (joules, kWh, etc.) — *unit choice is
     producer-attested, not spec-fixed*
   - `evidence_run_count` — discrete count of evidence runs
     incurred (smoke-validation invocations, threat-model
     replays, separation-of-duty re-derivations)

   **Claim to ground or rebut:** these seven cover ≥95% of the
   actual costed actions in a working Agent Assurance runtime.
   Anything more granular (e.g. "tokens in" vs "tokens out") is
   producer-declared at the unit label, not a new dimension.

2. **Producer-attested units, not spec-fixed units.** The dimension
   category is closed; the *unit label* inside the category is
   free-form, producer-attested, and not normalised at the SPEC
   layer. This honours the "trust as currency, brittleness as
   feature" ethos — comparing across producers requires an
   explicit conversion artefact, not silent unit coercion.
3. **Cost records are not transitive.** A `gate-decision` cites the
   cost-records that were paid *to reach this decision*. It does
   NOT cite the cost-records of every upstream evidence-matrix
   entry that was paid earlier. Transitive aggregation is a
   runtime concern (a `cost-rollup` summary, out of SPEC scope).
4. **Decider-class is a structural property of the record.** Each
   cost-record declares the *class* of entity that incurred it, drawn
   from a closed set: `deterministic_check | llm_single |
   llm_consensus | human_reviewer | tee_attested_compute |
   notarisation | transparency_log_write | other`. Auditors read
   `decider_class` to know what threat surface the decision
   defends against. The `other` slot is **deliberately included** —
   the spec must allow a producer to declare a costed action that
   doesn't fit the closed set, paying for it with a more
   suspicious treatment by downstream auditors. Brittleness over
   completeness.
5. **Cost-records are observation, not policy.** A cost-record
   declares *what was spent*; it does NOT declare *what was
   allowed*. A separate kind (out of scope here, a candidate for
   Stream G+1) would declare cost *policy* — caps, allowances,
   approval thresholds. Mixing observation and policy in one
   record is a design failure (the same trap JSON Schema falls
   into when it mixes type and constraint).
6. **The gate-decision cross-reference is by citation, not by
   embedding.** The gate-decision file's existing
   `[[decision.cited_bundles]]` shape extends naturally; a new
   `[[decision.cited_costs]]` array references cost-records by
   their content hash. Cost-records are independent artefacts;
   gate-decisions cite them. This mirrors the existing
   assertion-bundle citation pattern.

---

## Expected deliverables

The research wave should produce:

1. **Per-source survey** of each target above: what dimensions
   each treats as primitive; how each cross-references costs to
   the artifact that incurred them; what each treats as policy
   vs observation.
2. **Comparison matrix** along the axes:
   - Dimension enumeration (closed? open? hierarchical?)
   - Unit handling (fixed? declared? convertible?)
   - Cross-reference shape (tag? id? content-hash?)
   - Decider-class signal (present? absent? inferred?)
   - Policy / observation separation (present? collapsed?)
   - Spec / runtime boundary (where does the schema stop?)
   - Multi-implementation parity (one runtime? cross-vendor?)
3. **Verdict** on whether any existing schema can be adopted as-is
   for the SPEC-layer `cost-record` kind. (Predicted answer: no —
   they all assume currency, vendor SKUs, or transitive
   aggregation. The expected outcome is "adopt the closed-set
   dimensions from FOCUS / OpenTelemetry / SCI, ignore the
   runtime layers".)
4. **Concrete kind-descriptor sketch** — the `cost-record-kind.toml`
   file, IJB-tagged, with required-fields, hard-invariants, and an
   example pointer. Plus the ontology-entry deltas (new attribute
   vocabularies for `cost_dimension_category` and
   `decider_class`).
5. **Cross-reference design** — how `gate-decision`,
   `evidence-matrix`, and `assertion-bundle` cite cost-records.
   The change to existing kinds is **minimal and additive only**:
   an optional `cited_costs = [...]` array on each. (This stream
   does NOT propose modifying the existing kinds in the same
   change; that is a separate downstream proposal once the
   `cost-record` kind has been adopted.)
6. **Placement verdict** — Option A (extend Agent Assurance) or
   Option B (new `cost` profile). With justification.
7. **Threat model** focused on cost-record gaming: under-reporting
   incentives, the "deterministic-check that's actually an LLM
   call" mislabelling threat, the "human review of zero seconds"
   anti-pattern, the cross-producer unit-coercion threat.

---

## Preliminary sketch — the `cost-record` kind

This is illustrative, not normative. The actual research wave
ratifies, modifies, or replaces it.

### Required fields

| Field | Role |
|---|---|
| `[meta].template_kind` | MUST equal `"cost-record"` |
| `[meta].framework_profile` | `"cost"` (Option B) or `"agent-assurance"` (Option A) |
| `[record].action_id` | Citation string identifying the costed action (e.g. `EVMTX:smoke-run-2026-05-22-001`). Free-form prefixed slug. |
| `[record].incurred_at` | RFC 3339 timestamp. |
| `[record].citing_kind` | One of: `gate-decision | evidence-matrix | assertion-bundle | smoke-validation | threat-model | rollback-plan | other`. Identifies the kind whose execution paid this cost. |
| `[record].citing_ref` | Free-form citation string into the citing artefact (e.g. document hash + section pointer). |
| `[[record.dimensions]]` | Array of declared cost dimensions (see below). |
| `[record].decider_class` | One of: `deterministic_check | llm_single | llm_consensus | human_reviewer | tee_attested_compute | notarisation | transparency_log_write | other`. |
| `[record].producer_id` | Citation string referencing the producing entity (key id, service account, agent id). |
| `[record].hash_algorithm` | E.g. `"sha256"`. |
| `[record].canonical_form` | E.g. `"rfc8785-jcs"` — declared so a witnessing attestation can re-derive the canonical bytes. |

### Cost dimensions array shape

```toml
[[record.dimensions]]
category    = "token_equivalent"   # closed set; see ontology
quantity    = 12450                 # non-negative integer
unit_label  = "tokens.openai-style" # producer-attested free-form
note        = ""                    # optional, free-form
```

The category is drawn from the closed `cost_dimension_category`
vocabulary; the unit label is free-form, producer-attested, and
**not normalised at the SPEC layer**. Two records with the same
category and different unit labels are *not* directly
comparable — by design. Comparability is a runtime concern,
established via a separately-attested conversion artefact.

### Example

```toml
[meta]
schema_version    = "1.0.0"
template_kind     = "cost-record"
framework_profile = "cost"
title             = "Cost record for smoke-validation run 2026-05-22-001"
created           = "2026-05-22"

[record]
action_id        = "EVMTX:smoke-run-2026-05-22-001"
incurred_at      = "2026-05-22T14:32:11Z"
citing_kind      = "smoke-validation"
citing_ref       = "sha256:1234...64hex#section.checks[3]"
decider_class    = "llm_consensus"
producer_id      = "did:agent-assurance:runtime:ci-worker-12"
hash_algorithm   = "sha256"
canonical_form   = "rfc8785-jcs"

[[record.dimensions]]
category    = "token_equivalent"
quantity    = 12450
unit_label  = "tokens.consensus-3way"
note        = "sum across three independent model invocations"

[[record.dimensions]]
category    = "compute_time_seconds"
quantity    = 47
unit_label  = "wall-clock-seconds"

[[record.dimensions]]
category    = "evidence_run_count"
quantity    = 3
unit_label  = "consensus-rounds"
```

### Hard invariants (planned)

1. `[record].action_id` MUST be a non-empty string.
2. `[record].incurred_at` MUST be a valid RFC 3339 timestamp.
3. `[record].decider_class` MUST be drawn from the closed
   `decider_class` vocabulary.
4. `[record].citing_kind` MUST be drawn from the closed
   `cost_citing_kind` vocabulary.
5. Every `[[record.dimensions]].category` MUST be drawn from the
   closed `cost_dimension_category` vocabulary.
6. Every `[[record.dimensions]].quantity` MUST be a non-negative
   integer (real-valued quantities are expressed by choosing a
   finer-grained unit label — e.g. `compute_time_milliseconds`
   instead of `compute_time_seconds`, declared in the unit label
   not the category). This honours canonical-form determinism
   (no floats per Stream D's CDT consensus).
7. SPEC-layer validation MUST NOT compare quantities across
   records, MUST NOT verify any signature, and MUST NOT
   aggregate. Cross-record arithmetic is RUNTIME-SPEC.

### Cross-reference shape

The cost-record is a flat, self-contained artefact. It cites
upward (the artefact whose execution paid the cost); it is cited
downward (by gate-decisions and evidence-matrix entries that name
it).

- **`gate-decision`** would gain an OPTIONAL
  `[[decision.cited_costs]]` array, each entry holding a content-
  hash citation to a cost-record. This change is proposed by a
  separate downstream task, not by Stream G itself.
- **`evidence-matrix`** would gain an OPTIONAL `cited_costs`
  field per matrix entry — same shape, same content-hash
  citation. Also a separate downstream task.
- **`assertion-bundle`** MAY bundle cost-records alongside
  observations; the bundle's hash then witnesses the cost-records
  through the existing assertion-log-record chain. Producers MAY
  carry cost-records *outside* a bundle; consumers treat
  unbundled records as declared posture, not as proof.

### What stays out of the cost-record

- **Currency, rate, conversion** — runtime / control plane.
- **Vendor SKUs, model identifiers** — runtime, expressible inside
  the producer-attested `unit_label` if the producer chooses.
- **Allowances, caps, policy** — a separate (future) kind,
  candidate for a successor stream.
- **Aggregation across records** — runtime concern; a future
  `cost-rollup` artefact summarises, the canonical record does
  not.
- **Signatures** — Stream B's attestation witnesses the
  cost-record by hash; the cost-record itself carries no
  signature field.

### Relationship to provenance

A cost-record carries provenance metadata (`producer_id`,
`incurred_at`, `action_id`) — *who* paid the cost *when* for
*what action*. This is structural; it is not a signed attestation.
Stream B's one-shot attestation envelope MAY witness a cost-record
by signing over its content hash, at which point downstream
consumers treat the record as legally provable; until then it is
**declared posture only**.

This mirrors the assertion-bundle / assertion-log-record / Stream-B-
attestation layering pattern: the artefact is independent of the
signature; the signature is a separate, brittle, propagating
witness over an existing content hash.

---

## Cross-references

- **Stream A — Kind-descriptor drift.** The `cost-record-kind.toml`
  descriptor obeys the same KDLL / KindLock content-hashed lockstep
  as every other descriptor. The closed vocabularies for
  `cost_dimension_category`, `decider_class`, and `cost_citing_kind`
  are ontology entries with the standard IJB tags. Drift between
  descriptor prose and validator behaviour fails CI in the same way.
- **Stream B — Legal-grade one-shot attestation.** Cost-records are
  *witnessed by* Stream B attestations; they are not themselves
  attestations. A signed cost-record is a cost-record whose content
  hash is the subject of an OSIA / QES-anchored statement. The
  brittleness propagation rule applies: if the upstream
  evidence-matrix entry the cost-record cites is invalidated, the
  attestation that witnessed the cost-record breaks visibly.
- **Stream C — Separation-of-duty validation.** This is the
  load-bearing intersection. `decider_class` is the structural
  property an auditor reads to answer: *did the entity that paid
  the cost belong to the same control domain as the entity it
  validated?* A `decider_class = "llm_consensus"` cost-record paid
  by the same agent that produced the artefact is a separation-of-
  duty violation, regardless of how many models voted.
- **Stream D — Canonical DAG-TOML (CDT).** Cost-records are
  canonical-form text artefacts under CDT: integer-only quantities,
  closed-set categorical fields, sorted keys, no floats, no eval,
  no computed totals. The cost-record is one of the simplest
  possible CDT artefacts and serves as a good early CDT
  conformance fixture.
- **Stream E — HW/SW/cognition layering.** Cost-records are
  produced at multiple layers — TEE-attested compute records the
  energy/cycles spent in hardware-attested boundaries; software
  validators record CI run cost; the cognition layer records
  LLM-call cost. The `decider_class` enum is the layer-discriminator
  visible to auditors. A future open question: should
  `decider_class` decompose further into hardware / software /
  cognition primitives, or stay coarse?
- **Stream F — Capability envelopes (abstraction-class type
  safety).** Cost-records are observations, not policy. Capability
  envelopes are policy. The intersection: *budgeted capability
  envelopes* — where an abstraction class declares not just "this
  is a compression library" but "this compression library may
  consume at most N token-equivalent units per invocation." The
  budget side is the future cost-policy kind; the envelope side is
  Stream F. The two will eventually compose; not in this stream.
- **`06-user-design-directives.md` ethos.** Trust as currency
  (cost-records make the cost of trust explicit). Brittleness as
  feature (closed dimension sets reject silent reinterpretation;
  producer-attested unit labels refuse silent coercion). Process-
  trust over artifact-trust (cost-records are observations of the
  process, not properties of the artefact). Producer-side
  responsibility (the producer attests cost; the consumer reads
  the last record only).
- **`follow-up-2/11-overkill-rebuttal-and-frontier-problems.md`.**
  The three named frontier primitives: Provable Intent
  (Stream B), Structural Governance (Stream A + Stream F),
  Cost-Witnessed Decision (this stream). Each is a peer; none
  is subordinate. The spec is undergoverned without all three.

---

## Open questions deferred to the research wave

1. Closed-set verdict: are the seven dimension categories
   sufficient? Should `human_review_time_seconds` decompose? Should
   `energy_equivalent` decompose into compute-energy vs storage-
   energy? Open to grounding or rebuttal.
2. Should `decider_class` carry a secondary `decider_root_of_trust`
   slot — e.g. for `tee_attested_compute`, *which* TEE vendor —
   or is that runtime concern?
3. Placement verdict (Option A vs Option B). Recommendation here
   is B, but the wave should test the implications: can a
   downstream profile depend on `cost` *and* `agent-assurance`
   simultaneously via the namespacing partition? The spec
   nominally allows this; no worked example exists.
4. Naming: `cost-record` is the working name. Alternatives worth
   surveying: `decision-cost`, `costed-action`, `cost-witness`.
   The wave should pick one and justify.
5. Granularity: one cost-record per costed action vs one
   cost-record per gate-decision (aggregating its constituent
   actions). Recommendation: one per costed action; the gate-
   decision cites many. The wave should ratify or rebut.
6. Is there a `cost_root_algorithm` analogue to the
   `evidence_root_algorithm` on gate-decision? I.e., should a
   gate-decision carry a hash-of-all-cited-cost-records to
   simplify witnessing? Likely yes; defer to the wave.

---

## Why this stream now

The frontier-problem framing in
`follow-up-2/11-overkill-rebuttal-and-frontier-problems.md` named
two of three primitives. The third — Cost-Witnessed Decision — has
been load-bearing in the dossier without being named:

- Stream C's separation-of-duty mechanisms differ in cost by
  orders of magnitude; without naming cost, the spec can't
  distinguish them.
- The VAP comparative review surfaced a runtime-side cost module
  with no spec slot.
- The post-2026 cost decline curve in Stream E shifts the optimal
  ratio between deterministic, LLM, and human deciders at every
  layer — the spec must let auditors observe which ratio was used.

Naming the gap **before** vendors fragment the extension surface
is the cheap moment. Naming it after is the expensive moment. The
spec ethos — process-trust, brittleness as feature — points to
naming now.
