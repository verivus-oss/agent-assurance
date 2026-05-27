# Spec foundations research — 2026-05-22

External, independent research on guidance and challenges for the DAG-TOML /
IJB / Agent Assurance specification design. Five parallel streams, each with
unrestricted access to Exa (web search and deep research):

- Claude with Exa (the agent driving this dossier)
- Exa Deep Researcher (`exa-research-pro` model)
- OpenAI Codex with Exa
- Google Gemini with Exa
- xAI Grok with Exa

All three CLI agents (Codex, Gemini, Grok) were briefed identically with the
same context block and the same six research questions; they did not see each
other's output. Codex and Grok needed config adjustments before they could run
(Gemini and Grok had no Exa MCP registered locally; that was added via
`gemini mcp add -s user exa …` and `grok mcp add exa --command …`).

## Files in this folder

- `README.md` — this file, plus the consolidated synthesis (below)
- `01-exa-deep-researcher.md` — Exa `exa-research-pro` report on IJB primitives
  prior art, with 49 citations
- `02-codex-with-exa.md` — Codex independent report
- `03-gemini-with-exa.md` — Gemini independent report
- `04-grok-with-exa.md` — Grok independent report
- `05-claude-exa-searches.md` — Key URLs and findings from Claude's own Exa
  searches that fed into the synthesis
- `06-user-design-directives.md` — Design statements from the user's response
  to the synthesis (changes which recommendations apply)
- `07-followup-research-streams.md` — Open research questions launched in
  follow-up (kind-descriptor drift solutions, legal-grade one-shot attestation,
  separation-of-duty validation, alternative format selection / new format
  design)
- `08-follow-up-synthesis.md` — Cross-comparison of follow-up Stream A/B/C/D
  results (Codex + Gemini + Grok + Exa Deep Researcher); converged designs
  per stream and recommended build order
- `follow-up/codex-streams-a-b-c-d.md` — Codex follow-up raw report
- `follow-up/gemini-streams-a-b-c-d.md` — Gemini follow-up raw report
- `follow-up/grok-streams-a-b-c-d.md` — Grok follow-up raw report
- `follow-up/exa-deep-a-kind-descriptor-drift.md` — Exa deep report on
  Stream A
- `follow-up/exa-deep-b-legal-grade-attestation.md` — Exa deep report
  (exa-research-pro) on Stream B
- `follow-up/exa-deep-c-separation-of-duty.md` — Exa deep report on
  Stream C
- `follow-up/exa-deep-d-format-selection.md` — Exa deep report on Stream D
- `prompts/` — every prompt sent during the dossier's preparation, for
  research reproducibility. See `prompts/README.md` for the
  prompt→response cross-reference.
- `raw/` — operational state (job manifest, failed-attempt logs); records
  *how* the research ran, not what it produced.

## Consolidated synthesis

### 1. The six IJB primitives — where the design sits and where it bleeds

**Strongly convergent verdict across all four sources:** the six-primitive set
`thing | scope | path | observed | constraint | time` has no clean precedent
and risks several documented category errors.

| Primitive   | What collapses inside it                                                | What the prior art warns                                                                                                                                                                                          |
|-------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **thing**   | artifacts, agents, plans, requirements, files, institutional objects    | BFO's continuant/occurrent and dependent/independent distinctions disappear; PROV's Entity vs Agent split lost                                                                                                    |
| **path**    | graph edge, process, event, derivation chain, file path                 | DOLCE perdurant / BFO occurrent / Situation Calculus fluent / Event Calculus event — collapsing them reintroduces the **frame problem** and **qualification problem**                                             |
| **observed**| epistemic facts, measurements, evidence                                 | PROV-O models observation as a *relation* (Activity generates Entity at Time), not a primitive — making it primitive loses provenance fidelity                                                                    |
| **constraint** | structural integrity, policy, regulatory obligation, validation rule | ArchiMate explicitly separates motivation/constraint from structural elements; REA, ORM/FCO-IM attach constraints to fact types — single bucket is ontologically promiscuous                                      |
| **scope**   | context, namespace, role, authorization boundary                        | UFO insists roles are anti-rigid and relators can bear properties — encoding roles as scopes loses temporal role lifecycle and the ability to attach attributes to relationships                                 |
| (missing)   | "quality" / "qua entity" — DOLCE/UFO first-class                        | Attributes like `valid`, `complete`, `redacted` have no clean home; they get forced onto things (overloading) or observations (confusing observational metadata with domain attributes)                          |

Foundational-ontology interchange experiments (SUGOI, mapping between
DOLCE/BFO/GFO) achieve only 2–82% equivalence (~36% avg). The implication: a
six-primitive engineering taxonomy cannot honestly claim *philosophical* status
without explicit collapse-and-extension tables to BFO/DOLCE/UFO.

**Strong recommendation (4/4 agreement):** retire any claim of being an "upper
ontology." Frame IJB as a **disciplined annotation scheme** with published
mapping tables to BFO/DOLCE/UFO/PROV that explicitly call out the collapses.
Define each primitive with **forbidden uses and category-error examples**, not
just positive examples.

### 2. TOML-only spec design — risks (and user's resolution)

**Original finding.** Cargo, pyproject, Taplo all teach the same lesson: TOML
is a strong human-authored config surface and a risky normative-graph-spec
surface. TOML weaknesses that bite DAG-TOML:

- No `null`, no `$ref`, no native schema, no imports, no identity system
- Deeply nested arrays-of-tables become unreadable; users copy-paste → drift
- Downstream tools' tolerated subsets vary (Taplo vs `tomllib` vs `toml-rs`)
- TOML 1.x discipline is good but does not constrain semantic drift

The structural concern: if the Python validators are the *only* enforcement
layer, those validators **are** the spec, with all their accidental quirks
(Hyrum's Law). The classic remedies are a schema sidecar (rejected by user —
JSON has insurmountable problems for this context) or multiple independent
implementations (W3C "two implementations" rule, IETF "running code").

**User's resolution (binding on the spec):** primary validators in *safe Rust*,
*safe Go*, and *safe C*; other languages are ports. Multiple independent
primary implementations replace the schema-sidecar remedy. This is a coherent
answer to the Hyrum's-Law concern — independent implementations expose
accidental dependencies before they harden.

Remaining work: declare validator behavior, canonical normalization, and
conformance fixtures as **normative** in `spec.md §9`. Without that, ports will
diverge from primaries.

### 3. Kind-descriptor / self-describing-schema drift

All four sources flagged the same drift mechanism: prose, descriptors,
validators, and examples diverge over time. Prior art (JSON-LD contexts,
SHACL, OpenAPI components, ProtoBuf `FileDescriptor`, CUE definitions, Dhall
types) all report this. CUE is the cleanest example because values and schemas
live in the same lattice — no separate descriptor to drift.

**User direction:** survey existing solutions AND propose something new fit
for this context. Launched as follow-up research stream — see
`07-followup-research-streams.md`.

### 4. Agent assurance — three documented failure modes

#### (a) Provenance paradox

The 2026 "Mini Shai-Hulud" / TanStack npm worm shipped with **valid SLSA L3
provenance** — the build pipeline was correctly attested; the compromise
happened inside the trusted runner after OIDC token theft. SLSA proves
*pipeline*, not *intent* or *content*. This applies directly to
`assertion-bundle` / `disclosure-attestation` — *signed* does not mean *safe*.

#### (b) Evidence fatigue

Stacked attestations (build provenance + SBOM + VEX + assertion bundle + gate
decision) produce so much signed material that downstream policy engines stop
evaluating substance. G7 AI-SBOM guidance already acknowledges
autonomy/decision-making as unsolved.

#### (c) Gate gaming

If the **same agent** generates the work, evidence, assertions, and pass/fail
rationale, the gate is unverifiable. Recent research formalizes this as a
Stackelberg game between auditor and auditee and shows that any noise-aware
static auditor design has a "cover regime" where coverage and granularity
cannot both be closed.

**User direction:** problems (a) and (b) require a new design — *one-shot,
immutable, legal-grade attestations* where the consumer checks only the last
artifact and any upstream change breaks the downstream sha. Trust shifts to
the producer of the signing process, not the consumer. Problem (c) is its own
research-and-validation stream: the agent who performs work cannot validate
its own work; validation must be mechanically separated and auditable in an
ISO-9001-like sense. Both launched as follow-up research streams — see
`07-followup-research-streams.md`.

### 5. Spec-design failure modes (recorded, return later)

Convergent points to revisit:

- **Hyrum's Law** as the dominant risk against any single-implementation spec
- **OWL/RDF over-expressivity trap.** OWL 2 had to introduce restricted
  profiles (EL/QL/RL) — lesson: if `*-kind.toml` can express things validators
  cannot check, the spec has failed in slow motion
- **Two-implementations / running-code traditions** as the only honest test of
  implementability (user's safe-Rust+safe-Go+safe-C plan addresses this)
- **Noy 2004:** ontology evolution has dimensions (instance preservation,
  query preservation, consequence preservation) the spec doesn't currently
  distinguish

### 6. DAG traceability invariants — fragility + format question

- `blocks` should be **derived** from `depends_on` and mechanically checked,
  not independently authored
- "Exactly one producer per ART" is clean for build artifacts and *wrong* for
  assurance evidence with multiple contributors/reviewers/signers
- `critical_path` is decorative if edge weights mix duration + risk +
  confidence + review burden. CPM assumes deterministic durations and
  unlimited resources — false for agentic execution. Critical Chain (CCPM) or
  PERT-style probabilistic models fit better.
- **One global DAG is an anti-pattern.** `depends_on` (scheduling), `verifies`
  (test→requirement), `derives_from` (artifact provenance), `supports`
  (evidence→claim), and `implements` (adapter→contract) are *different graphs
  with different acyclicity rules*. Bazel learned this; separate query
  primitives, separate cycle semantics.
- **Iteration is not a cycle.** Model iteration as **versioned nodes**, not
  edges back in time.

**User direction:** is there *any* format/mechanism/standard better suited?
Should we create something new? Brittleness is a feature, not a bug; trust is
the currency. Launched as follow-up research stream — see
`07-followup-research-streams.md`.

## Top risks (where all four sources agreed)

1. Single-implementation lock-in (Hyrum's Law) — *addressed by user's
   multi-language-primary plan*
2. Six-primitive ontology category errors — most acute around `path` (event
   collapse), `observed` (epistemic vs ontological), `constraint` (structural
   vs policy)
3. Provenance theatre — signed-but-empty attestations à la SLSA + TanStack
4. Gate gaming — same agent producing both work and assertion
5. Kind-descriptor / prose drift
6. TOML strain at graph scale — no `$ref`, no cross-file identity
7. `critical_path` false confidence with non-commensurable weights
8. No published threat model for the spec itself
