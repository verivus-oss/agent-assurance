# Follow-up research streams (open as of 2026-05-22)

Launched after the user's design directives in
[`06-user-design-directives.md`](./06-user-design-directives.md). All four
streams are independent of each other and will be researched in parallel via
Exa + delegated agents (Codex, Gemini, Grok).

## Stream A — Kind-descriptor / self-describing-schema drift

**Question.** What mechanisms keep prose-and-machine-form aligned in long-
lived specs, beyond what JSON-LD/SHACL/CUE/Dhall/clayers offer? Survey
existing options AND propose a novel approach that fits a TOML-only,
multi-implementation, trust-as-currency, brittleness-as-feature world.

**Constraints.**

- No JSON Schema sidecar.
- Compatible with three primary safe-language validators (Rust, Go, C).
- Drift must surface as a *visible failure* — silent acceptance is wrong.

**Expected deliverables.**

- Annotated survey of existing drift-mitigation mechanisms (content
  hashing, bidirectional generation, schema-as-data, AST-level
  fingerprinting, executable specifications, golden-master testing,
  property-based contracts).
- A proposed novel mechanism, with explicit failure modes and example
  walk-throughs.

## Stream B — Legal-grade one-shot immutable attestation

**Question.** How do you build attestations that are:

- bound to a single sha256-hashed artifact, single-use
- legally provable (intent + ability to withdraw/age signatures)
- one-shot — no upgrades, no version inheritance
- propagating — any upstream change *intentionally* breaks downstream
  signatures, signalling re-verification
- built on current cryptographic stacks (no novel crypto)
- producer-side responsibility (consumer only checks the last artifact)

**Survey targets.**

- in-toto, SLSA v1.2 provenance, Sigstore/Fulcio/Rekor, RATS/RFC 9334,
  Entity Attestation Token (RFC 9711), COSE, SCITT, C2PA, qualified
  electronic signatures (eIDAS), DSSE, Witness Statements (RFC 9162 CT
  log), age (FiloSottile), Sequoia-PGP, MTV2 SCITT, OpenSSF Scorecard,
  RFC 6962/9162 transparency, age-based key aging, time-stamping
  authorities (RFC 3161, TSP).

**Failure modes to avoid.**

- Provenance paradox (TanStack worm with valid SLSA L3 attestation)
- Evidence fatigue (stacked attestations no one evaluates)
- Verifier root-of-trust shift (over-attestation shifts the attack surface
  to the verifier)
- Legal non-repudiation gaps (key compromise, post-dating, intent proof)

**Expected deliverables.**

- Annotated landscape of existing solutions; per-solution gap analysis.
- Proposed design (or design family) — what new components are needed and
  what existing primitives compose to fill the gap.
- Threat model.

## Stream C — Separation-of-duty gate validation

**Question.** How do you mechanically enforce that the agent (human,
program, LLM) who performs work cannot also validate its own work? What
patterns produce the "intent → action → proof → audit" cycle in an
ISO-9001-like sense?

**Survey targets.**

- ISO 9001 audit-separation requirements, ISO/IEC 17021 (audit-body
  competence), ISO 19011 (auditing management systems).
- Two-party control / "two-man rule" (NSA/DoD heritage, FIPS 140-3 dual
  control, banking key ceremonies).
- Threshold signatures (FROST, BLS, Shamir-style ceremonies).
- Multi-party computation (MPC) for verification.
- Trusted third-party witnesses (notaries, transparency logs).
- Witness-based attestations (in-toto layouts, SCITT receipts).
- Reproducible builds (rb-tools, Bazel remote execution + reproducibility).
- Capability-based isolation (sandboxes that prevent the producer from
  writing to verifier-readable surfaces).
- Recent academic work on Stackelberg-game auditing
  ([arXiv 2605.06340](https://arxiv.org/html/2605.06340)).
- "Governance Gauntlet" dual-rubric pattern
  ([Zenodo 19689504](https://zenodo.org/records/19689504)).

**Expected deliverables.**

- Pattern catalogue: which separation-of-duty mechanisms apply to which
  parts of the work-prove-audit cycle.
- Proposed mechanical patterns for the spec — what verification steps
  *must* be performed by an entity distinct from the producer; what
  cryptographic / procedural mechanisms make this enforceable.
- Threat model focused on gate gaming.

## Stream E — HW/SW/cognition layering (added 2026-05-22, Turn 5 addendum)

**Question.** As inference costs decline and FPGA / specialized-inference
silicon emerges, how should the trust stack divide labor across
HARDWARE (FPGA, ASIC, custom silicon), SOFTWARE (safe Rust/Go/C), and
INTELLIGENCE/COGNITION (LLMs and reasoning engines) at each layer?

**Layers under consideration.**

1. Canonicalization & cryptographic primitives (deterministic CBOR,
   ASN.1 DER, SHA-256, signatures).
2. Validator / parser layer (safe Rust/Go/C parsers consuming canonical
   bytes).
3. Schema / kind-descriptor layer (content-hashed ASTs, golden-master
   fixtures).
4. Attestation / signing-ceremony layer (HSM, TPM, FIDO2, eIDAS QSCD).
5. Audit / verification layer (re-builders, threshold signing,
   transparency logs).
6. Reasoning / policy layer (LLM-driven gate decisions, policy
   synthesis).
7. Authoring layer (humans + LLM assistants writing descriptors, threat
   models, policies).

**Argument to ground or rebut.**

- The optimal ratio of HW/SW/cognition is layer-dependent and shifts as
  cost curves move.
- Determinism-critical layers tend toward hardware over time.
- Policy/reasoning layers tend toward cognition (LLMs) within
  hardware-attested boundaries.
- Validator/parser layers are software-first at the floor; FPGA at the
  frontier when throughput becomes load-bearing.
- Authoring layer remains cognition-primary; tooling shifts as
  inference gets cheap.

**Strategic implication for the spec.** What spec choices KEEP all three
doors open at every layer? What choices CLOSE them?

**Expected deliverables.**

- Per-layer HW/SW/cognition ratio recommendations (today, 2026).
- Projections as inference cost declines 10×, 100×, 1000×.
- What FPGA acceleration buys at each layer.
- Historical precedent from DSP→GPU→TPU→inference-ASIC migration.
- A specific list of spec choices that keep all three doors open, and a
  list of choices that would close them.

---

## Stream D — Alternative formats / new-format design (brittleness as feature)

**Question.** Is there *any* format/mechanism/standard better suited than
TOML for a trust-as-currency, brittleness-as-feature, multi-implementation
spec? Should we create something new?

**Survey targets (existing).**

- TOML (current), JSON, YAML (rejected — Norway problem), CBOR, ASN.1,
  CDDL, S-expressions, EDN, KDL, RON, NestedText, capnproto, FlatBuffers,
  Dhall, CUE, KCL, Jsonnet, Pkl, Nickel, Starlark, Lean/Coq tactics for
  config, deterministic Turing-incomplete config DSLs.
- Canonical-form requirements (JCS RFC 8785, COSE canonicalisation,
  RFC 8949 deterministic CBOR).
- Configuration as code vs. configuration as data debate.

**Evaluation axes.**

1. Human readable / editable
2. Deterministic canonical form (for stable hashing)
3. Cryptographic provenance (one-to-one mapping between text and hash)
4. Trust by process, not artifact (does the format facilitate
   producer-side responsibility?)
5. **Brittleness as feature** — does the format reject ambiguity, silent
   type coercion, optional fields with defaults that hide intent?
6. Multi-language safe parsing (Rust, Go, C primary)
7. No remote includes / no eval / Turing-incomplete
8. Schema mechanism that does not require a separate JSON Schema

**Expected deliverables.**

- Comparison matrix across the axes above.
- Verdict on whether an existing format fits, with concrete trade-off
  analysis.
- If "no" — sketch of what a new format would look like (design goals,
  syntax sketch, canonicalisation algorithm, comparison to nearest
  existing format).

---

## Stream G — Cost-Witnessed Decision (added 2026-05-22, Turn 7+)

**Question.** What is the smallest SPEC-layer declarative shape for a
cost record — one entry per costed action (an LLM call, a CI evidence
run, a human review, a notarisation, a transparency-log write) — such
that gate-decisions and evidence-matrix entries can cite *which* cost
records witnessed them, and an auditor can read off *what class of
deciding entity* paid for each verdict (deterministic check, single
LLM, LLM consensus, human reviewer, TEE-attested compute, notarisation,
transparency-log write)?

This is the **third named frontier primitive**, peer to Provable
Intent (Stream B) and Structural Governance (Stream A + Stream F).
Earlier research treated cost as implementer flavour; the dossier
now shows it is a structural property of agent-driven systems. See
[`follow-up-2/13-stream-g-cost-witnessed-decision.md`](./follow-up-2/13-stream-g-cost-witnessed-decision.md)
for the full stream-shape document.

**Argument to ground.**

- Every action in an autonomous-agent system has measurable cost
  (tokens, CPU-seconds, evidence runs, human review time, energy,
  storage retention). "Route work to the cheapest competent
  decider" is a decision the spec's gate-decision and
  evidence-matrix kinds implicitly assume but never document.
- Gate-decisions today carry a pass / fail / inconclusive verdict
  with no signal as to *what class of decider* produced it. A gate
  decided by a deterministic SHA-256 comparison defends against a
  different threat surface than a gate decided by a single LLM,
  which differs again from a three-model consensus, which differs
  from a human reviewer. Auditors today cannot read this distinction
  off a `gate-decision` file. For separation-of-duty validation
  (Stream C), that gap is load-bearing.
- Without naming cost at the SPEC layer, every vendor builds an
  incompatible per-vendor extension. Naming the shape **before**
  fragmentation is the cheap moment.

**Constraints.**

- No vendor pricing, currency, billing, model SKUs, or per-unit
  conversion rates at the canonical layer.
- No formulas, no `eval`, no aggregation in the canonical form —
  cost records are declarative data. Aggregation is a runtime
  concern (a future `cost-rollup` artefact, out of scope here).
- No JSON Schema sidecar. The shape lives in a new `*-kind.toml`
  descriptor.
- Cost records are observation, not policy — they declare *what was
  spent*, not *what was allowed*. Cost-policy is a separate (future)
  kind.
- A cost record is not itself a signed attestation. Stream B's
  attestation envelope MAY witness a cost-record by signing its
  content hash; the record alone is declared posture only.
- The new kind belongs in either the Agent Assurance Profile (Option
  A) or a new minimal `cost` profile under `profiles/cost/` (Option
  B). Preliminary verdict: B. Final verdict pending the wave.

**Survey targets.**

- FinOps Foundation Framework v2 (organisational analogue, not
  schema source).
- CNCF FOCUS spec (FinOps Open Cost & Usage Specification) — closest
  existing cross-vendor cost schema; survey its dimension
  enumeration and what it does NOT cover (agent runtime, evidence
  runs, human review).
- OpenCost (CNCF, ex-Kubecost) — shared-cost attribution patterns
  analogous to attributing shared evidence-run cost back to gate
  decisions.
- Hyperscaler Cost Explorer APIs (AWS, GCP, Azure) — for primitive
  dimensions and the cost-to-artefact join key pattern.
- MLOps cost telemetry surfaces (Weights & Biases, MLflow,
  OpenLLMetry, OpenInference traces).
- OpenTelemetry semantic conventions for generative AI.
- Energy / carbon stacks: Kepler, Cloud Carbon Footprint, Boavizta,
  Software Carbon Intensity (ISO/IEC 21031).
- eBPF compute attribution (Pixie / Parca).
- Differential-privacy budget accounting (the cleanest existing
  analogue of accounting a non-monetary scarce resource against a
  security-critical decision).
- PoLR-style proofs of resource use inside TEEs.

**Claims to ground or rebut.**

1. The seven dimension categories — `token_equivalent`,
   `compute_time_seconds`, `storage_bytes`, `bandwidth_bytes`,
   `human_review_time_seconds`, `energy_equivalent`,
   `evidence_run_count` — cover ≥95% of practical agent-driven
   costed actions. Finer granularity is producer-attested via the
   `unit_label`, not new categories.
2. Producer-attested units, not spec-fixed units. Cross-producer
   comparability requires an explicit conversion artefact; silent
   coercion is rejected by design.
3. Cost records are not transitive. A gate-decision cites only the
   cost-records paid to reach *this* verdict; upstream costs roll
   up in a runtime-side `cost-rollup`, not in the canonical record.
4. `decider_class` is a structural, closed-set property. Auditors
   read it to know which threat surface the decision defends
   against.
5. Cost-record observation must not collude with cost-policy in one
   kind. Mixing the two is the JSON-Schema-shaped trap.

**Expected deliverables.**

- Per-source survey + comparison matrix along the axes: dimension
  enumeration, unit handling, cross-reference shape, decider-class
  signal, policy/observation separation, spec/runtime boundary,
  multi-implementation parity.
- Verdict on whether any existing schema can be adopted as-is for
  the SPEC-layer cost-record kind (predicted answer: no).
- Concrete `cost-record-kind.toml` sketch — required fields, hard
  invariants, IJB tags, example pointer; plus the ontology deltas
  for closed vocabularies (`cost_dimension_category`,
  `decider_class`, `cost_citing_kind`).
- Cross-reference design — how a `gate-decision` cites cost-records
  (`[[decision.cited_costs]]`), how an `evidence-matrix` entry
  cites cost-records, how an `assertion-bundle` may bundle them.
  Modifying the existing kinds is a separate downstream task; this
  stream proposes the new kind only.
- Placement verdict — Option A (extend Agent Assurance) vs Option B
  (new `cost` profile, first worked example of multi-profile
  composition).
- Threat model — under-reporting incentives, the "deterministic-
  check that's actually an LLM call" mislabelling threat, the
  "human review of zero seconds" anti-pattern, cross-producer unit
  coercion.

**Cross-references.** Stream A (descriptor lockstep applies to the
new kind), Stream B (attestation may witness a cost-record by
content hash), Stream C (load-bearing — `decider_class` answers the
separation-of-duty question Stream C poses), Stream D (canonical-
form integer-only quantities; no floats), Stream E (`decider_class`
is the HW/SW/cognition discriminator visible to auditors), Stream F
(cost-records are observation; capability envelopes are policy; the
future composition is "budgeted capability envelopes").
