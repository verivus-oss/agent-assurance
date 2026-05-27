# User design directives (2026-05-22, post-synthesis)

After receiving the consolidated synthesis, the user issued a set of design
statements that change which research-stream recommendations apply and which
are off the table. They are recorded here verbatim in spirit (paraphrased
where compressed) so subsequent work has a single anchor.

## Ethos

- **Trust is the currency.** This is a security/legal-grade system, not a
  convenience tool.
- **Brittleness is a feature, not a bug.** Invalidations must propagate;
  attempts to paper over a broken upstream signature must surface as a
  visible failure.
- **Process-trust, not artifact-trust.** Supply-chain attacks compromise the
  artifact while leaving the artifact's surface valid. The defence is to
  shift trust to the process that produced the artifact, not the artifact
  itself.
- **Responsibility lives with the producer, not the consumer.** A consumer
  should only have to verify the last artifact and make provenance possible
  for the next one.

## Off the table

- **JSON Schema as a remedy.** JSON has insurmountable problems for this
  context. Do not propose JSON Schema sidecars. (Implication: any schema
  sidecar must be in a format that already aligns with the rest of the
  ethos.)

## Mandated by the user

### Validator language strategy (replaces the "JSON Schema sidecar" remedy)

- Primary, normative implementations in:
  - safe Rust
  - safe Go
  - safe C
- Every other implementation is a port.
- (Implication: validator behavior, canonical normalization, and conformance
  fixtures must be normative in `spec.md §9` — the ports have to match
  *something* concrete.)

### Provenance / attestation requirements

- Consumer checks only the *last* artifact, makes provenance possible for
  the next.
- Established via *minimum* a SHA-256 hash of the source.
- Attested provenance is **one-shot, immutable**:
  - no upgrades to a signed artifact
  - no application to previous versions
  - any change requires a new attestation tied to the new sha
- Authentication / authorization built on current cryptographic stacks (no
  novel crypto).
- Legally provable:
  - intent to sign (must be more than "the key was used")
  - ability to withdraw authority / invalidate a signature (key aging,
    revocation, time-bounding)
- Any upstream attestation update *intentionally* breaks the downstream
  sha — this is the signal mechanism for "something changed; recheck".
- This is a mandatory requirement for anyone who can ship an artifact.
- The problem space exists; **no existing solution covers all of it**.
  This is "creating something new" — research stream open.

### Gate validation (separation of duty)

- An agent (human, program, LLM, …) cannot validate its own work.
- Mechanical check pattern:
  1. **Show** what we intend to do
  2. **Do** it
  3. **Prove** that we did it
  4. **Audit** at the end — auditable in an ISO-9001-like sense
- The proof must not depend on the agent who created the work.
- Separate research and validation stream.

### Other open research questions

- **Kind-descriptor / self-describing-schema drift.** Survey solution
  options *and* create something new. (Drift mitigation under the
  trust/brittleness ethos — content-hashed prose-to-validator binding may
  apply, but the design has to come from the ethos, not from JSON-LD/SHACL
  pattern transplants.)
- **Alternative formats.** Is there *any* other format / mechanism /
  standard better suited than TOML? Should we create something new? Note:
  brittleness is desirable here — formats that are forgiving (YAML's
  Norway-problem; JSON's silent type coercion) are actively wrong for this
  context.

## Recorded but deferred

- The "spec-design failure modes" set (Hyrum's law, schema bloat, ontology
  drift, OWL/RDF over-expressivity, two-implementations rule, ontology
  versioning dimensions) — return later.

## Addendum (Turn 5, 2026-05-22) — HW/SW/cognition layering

The user added an observation that modifies the implementation horizon:

> as inference costs decline and FPGA solutions emerge, I get the sense
> that a combination of hardware, software and 'intelligence/cognition'
> will be needed in various ratios at different layers or levels

This is a binding design observation, not a research question. It implies
that the spec must keep the door open for *all three* (hardware, software,
cognition) at every layer of the trust stack, with the ratio varying:

- **Determinism-critical layers** (canonicalization, hash, signature,
  reproducibility) tend toward hardware over time — algorithm is fixed,
  cost of variance is unbounded.
- **Validator / parser layers** are software-first (safe Rust/Go/C) at
  the floor, with FPGA acceleration available at the frontier when
  throughput becomes load-bearing.
- **Policy / reasoning layers** tend toward cognition (LLMs) because
  the rules change — but executed within hardware-attested boundaries.
- **Authoring layers** stay cognition-primary (humans + LLM assistants)
  for the foreseeable future.

**How to apply:** when shaping spec choices, ask "does this close the
door on any of HW/SW/cognition at any layer?" Specifically:

- **Keeps the door open**: deterministic canonical form (FPGA-friendly),
  no Turing-complete primitives in the canonical form, no `eval`, no
  remote includes, safe-language validators, hardware-rooted signing
  ceremonies.
- **Closes the door**: mandatory JSON Schema (silently coercive — fails
  FPGA determinism), mandatory remote contexts, mandatory single-vendor
  inference runtime, mandatory features that depend on a Turing-complete
  evaluator.

Research stream launched in [`07-followup-research-streams.md`](07-followup-research-streams.md)
(Stream E). Open question: when does each workload migrate down the
stack? The DSP→GPU→TPU→inference-ASIC pattern (Hennessy & Patterson,
"A New Golden Age for Computer Architecture") gives the closest
analogue.

## Addendum (Turn 6, 2026-05-22) — abstraction-class type safety

After reviewing the recovered Grok-share conversation about secure
.toml hosting on Cloudflare with zero-trust framing, the user named
the missing supply-chain-security primitive:

> A valid signature on a corrupted abstraction is useless. The
> downstream party needs a mechanism to say, "I expected a decimal
> sequence. You handed me a validly signed hex sequence. The contract
> is broken, and I am rejecting it."

**Architectural type safety, applied at the supply-chain layer.** When
we adopt an upstream dependency, we implicitly declare its class
("this is a compression library"). The class declaration must bind.
A compression library that opens outbound sockets has violated its
class, regardless of signature validity.

**How to apply:** Kind descriptors must declare both **structural
shape** (what the artifact looks like) AND **capability envelope**
(what the artifact is allowed to do). Validators must enforce both.
Class violations cascade-break downstream. The "process-trust over
artifact-trust" ethos becomes mechanically enforceable through class
declarations whose violation is observable.

**The user is not locked on TOML.** Capability envelopes are awkward
to express in TOML; formats with richer capability/type declarations
(WIT from the WASM Component Model, CDDL with capability extensions,
or a small purpose-built DSL) are now back on the table for Stream D.

Detailed thread + design implications saved in
[`follow-up-2/10-abstraction-class-thread.md`](follow-up-2/10-abstraction-class-thread.md)
*(pending — write next)*.

## Addendum (Turn 7, 2026-05-22) — the two frontier problems

The user articulated the spec's two load-bearing deliverables in
their sharpest form to date:

**Provable Intent.** Moving away from guessing what a traditional
line-by-line diff means, and moving toward mathematically validating
the semantic intent of a change. Maps onto **Stream B (legal-grade
one-shot attestation)**: the signing ceremony must capture intent,
not just bytes.

**Structural Governance.** Mapping and enforcing the actual logic
graph of a massive codebase, ensuring that boundaries and classes
are never silently violated. Maps onto **Stream A (kind descriptors)**:
descriptors declare class; validators enforce envelope; violations
cascade-break.

**The framing that anchors the spec's introduction:** "It is only
'too complex' if you are still trying to build a bicycle. If you
are building autonomous, self-generating infrastructure, provable
clarity is the minimum barrier to entry."

The lineage the user added strengthens the rebuttal to "overkill"
objections — compiler, garbage collector + borrow checker, Kubernetes.
Each was "overkill" at introduction; each became the floor that
unlocked the next frontier. Full text in
[`follow-up-2/11-overkill-rebuttal-and-frontier-problems.md`](follow-up-2/11-overkill-rebuttal-and-frontier-problems.md).
