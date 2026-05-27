# Follow-up wave 2 — consolidated synthesis

Cross-comparison of four independent sources on the cognitive-automation
lineage question, three on the HW/SW/cognition layering question, plus
the extracted Grok share conversation. Raw reports in
[`./`](./).

## The "more processing power" thesis (Codex + Gemini + Exa Deep Researcher)

Three independent sources converge on the same argument, with the same
six-section structure and the same primary-source citations:

### Pattern across four automation waves

| Wave | Floor automated | Frontier opened | What did NOT change |
|---|---|---|---|
| Calculator (1972, HP-35) | Slide-rule arithmetic, table interpolation | Iterative numerical exploration, sensitivity studies, real-time engineering, nuclear/aerospace at scale | Estimation, dimensional reasoning, suspicion of exact-looking numbers |
| Compiler (FORTRAN 1957) | Machine-code instruction scheduling, register management | Operating systems, networks, databases; later distributed systems | Conceptual integrity, modularity, machine sympathy |
| Search engine (Google 1998) | Retrieval, document location | Synthesis, source quality, defensible-view construction from too many documents | Judgment, taste, information literacy, ranking transparency awareness |
| LLM (2020s) | Routine drafting, summarization, boilerplate code, candidate code | AI4Science (AlphaFold, GNoME, GraphCast, FunSearch, AlphaProof, fusion control), formal verification, multi-agent assurance, autonomous compliance, machine-witnessed proceedings | Specification, verification, provenance, orchestration, liability, trust |

### Strategic claims (universal agreement across the three sources)

**A. The work doesn't disappear; the frontier moves.** Hamming: tools redefine which problems are worth attacking. Engelbart's H-LAM/T: capability belongs to the whole system. Brooks: tools reduce accidental complexity but expose essential complexity. The "automation makes us idle" claim is empirically wrong across all four waves; Jevons paradox of computation is the right model.

**B. Trust infrastructure is the load-bearing primitive of the LLM wave.** When output is cheap, scarcity disappears and verification becomes the bottleneck. Permissive parsing is not kindness — it's an ambiguity amplifier. Silent acceptance scales the wrong way. Strict canonical TOML, content-hashed kind descriptors, multi-language safe validators, golden-master fixtures are "a way to make meaning brittle on purpose."

**C. The "too complex / too brittle / too hard" objection is a category error.** It applies floor economics (minimize friction, tolerate ambiguity) to a frontier system where the cost of silent acceptance is unbounded. The correct reference class for DAG-TOML / Agent Assurance is not `serde` parsing a developer preference file — it is qualified electronic signatures, evidence preservation, supply-chain provenance, and court-admissible accountability.

**D. Investment in the floor pays for itself at the frontier.** Codex: "Calculators made nuclear engineering tractable; compilers made the internet possible; search made global open-source review tractable; LLMs are making frontier scientific reproducibility tractable IF AND ONLY IF the trust infrastructure exists to validate AI output at scale." Exa Deep adds operational specifics: RegTech/Reg-AI platforms (DXC, Infosys, Accure) already demonstrate codification of regulations into machine-actionable forms with audit trails; the trust primitives we are building plug directly into this category.

### Convergent rebuttals to "this is overkill"

- **"Too complex"** — compared to a config parser, yes; compared to legal infrastructure for high-stakes machine claims, no. Reference class = qualified signatures, not `serde`.
- **"Too brittle"** — *good*. At the frontier, dominant failure mode is silent acceptance of something that should have been rejected. Brittleness is how process trust propagates. A brittle validator is hostile to ambiguity, not to developers.
- **"Hard to maintain"** — so are compilers, TLS stacks, operating systems, build systems. Maintainability answer is small canonical profiles, golden fixtures, independent implementations, conformance suites, boring cryptographic envelopes.
- **"Won't pay for itself"** — applies floor economics to a frontier system. Payoff is not a safer config file; payoff is autonomous work crossing institutional, legal, scientific, and regulatory boundaries without every recipient reconstructing trust from scratch.

## HW/SW/cognition layering (Grok + Exa Deep Researcher, plus convergent inputs from Codex/Gemini)

Both sources validate the user's intuition that the optimal ratio is
**layer-dependent and shifts with cost curves**. The converged table:

| Layer | Primary substrate today | Where HW acceleration helps | Where cognition fits | How inference-decline shifts the ratio |
|---|---|---|---|---|
| **Canonicalization & crypto** (canonical CBOR/DER, SHA-256, signatures) | ASIC/HSM (Intel QAT, Marvell NitroX, AWS Nitro) | FPGA for upgradeable acceleration (esp. PQC migration) | Meta-validation only | Doesn't change — determinism-critical |
| **Validator / parser** (safe Rust/Go/C) | Safe-language CPU code (simdjson tier) | FPGA at line-rate frontiers (PipeJSON; hXDP for NIC-integrated) | LLM-driven fuzzing, schema recovery, anomaly detection | Cognition tools expand; deterministic core unchanged |
| **Schema / kind-descriptor** (content-hashed ASTs) | CPU + SSD | FPGA bulk-hashing at scale | **Hybrid — primary cognition use case for descriptor synthesis & migration** | Cognition share grows fastest here |
| **Attestation / signing ceremony** | HSM/TPM/QSCD + TEE (SGX/TDX/SEV-SNP/CCA) | FPGA HSMs for upgradeable algorithms | Policy interpretation only | HW root remains; cognition runs *inside* attested boundaries |
| **Audit / verification** | CPU re-builders, transparency logs | FPGA for Merkle/ZKP/heavy crypto | Anomaly detection, evidence correlation | More AI-assisted audit; deterministic anchors unchanged |
| **Reasoning / policy** | GPU/CPU/TPU/LPU inference | Specialized inference silicon (Groq, Cerebras, SambaNova, Tenstorrent, Etched Sohu) | **Primary** — LLMs within attested boundaries | This is where the biggest economic shift happens (10×/100×/1000× makes always-on LLM gates economical) |
| **Authoring** | Human + LLM-assisted | Inference silicon reduces latency, enables local/offline | **Primary cognition** | Tools explode; human judgment stays central |

### Inference cost curve shifts (Grok, with Exa Deep verification)

From arXiv 2511.23455 (Gundlach et al., MIT FutureTech/Epoch, Nov 2025): ~5–10×/year on Pareto frontier price-performance for frontier models; ~3×/year algorithmic after hardware adjustment; benchmarking cost rising due to larger models. a16z "LLMflation" report (Sep 2025): intelligence cost down >10×/year for three years.

- **10× decline** = ~1 year at current rates
- **100×** = ~2–3 years
- **1000×** = stretches further, slows as models grow and energy/physical limits bind

Skepticism worth carrying forward: open-model trends lag closed; energy (not just $ per token) and memory-bandwidth walls appear in surveys; TPU history shows only stable workloads migrate fully.

### Historical precedent that grounds the layering

Both sources cite the same migration pattern, traceable to Hennessy & Patterson's 2019 Turing lecture "A New Golden Age for Computer Architecture":

- Signal processing → DSPs (1980s) once algorithms stabilized
- Graphics → GPUs (1990s–2000s) for parallel fixed-function then GPGPU
- Training → TPUs (2010s) for dense matmul at datacenter scale
- Inference → ASICs/LPUs (2020s) for transformer serving

Pattern requirements: (1) workload volume + predictability high enough for NRE amortization; (2) general methods still win long-term via scale (Sutton's Bitter Lesson), but narrow fixed sub-tasks flip to specialized silicon; (3) compiler/software co-design is mandatory; (4) splits emerge (training vs inference, e.g., TPU 8t/8i bifurcation in 2026 reports).

**For trust infrastructure specifically:** canonicalization/hash/sig and fixed validators are "Bitcoin-mining-like" (unchanging core algo) → strong ASIC/FPGA candidate once volume exists. Policy/reasoning resembles "knowledge-heavy AI" that the Bitter Lesson says loses to scaled compute + learning — but must run inside attested hardware.

### Strategic implication for the spec — what KEEPS the door open

Both sources independently produced near-identical lists. The intersection is binding:

1. **Deterministic canonical bytes** (canonical CBOR/DER, strict numeric normalization, sorted map keys, length-prefixed). Enables ASIC/FPGA substitution without ambiguity.
2. **No Turing-complete primitives in canonical chain.** Prevents hardware/ASIC implementation; expands trusted codebase size.
3. **Small auditable validator state machine.** Accept/reject with deterministic diagnostics; formal test corpus; content-hashed ASTs.
4. **Pluggable attester abstraction.** Accepts TPM/HSM/TEE quotes in standardized statement format; verifier policies as data (policy manifests).
5. **Signed fixture transparency logs + Merkle proofs.** Hardware and software verifiers can independently check inclusion.
6. **Versioned canonicalizers, content-addressed.** Hardware accelerators can implement exact versions.
7. **No mandatory single-vendor inference runtime.** LLM outputs are signed `DecisionRecord` objects with provenance metadata and (optional) attester quotes — vendor-agnostic.
8. **No remote includes / no runtime fetches for validation.** Preserves offline and FPGA/HSM-sealed operation.
9. **Minimal auditable serialization for policy decisions.** `DecisionRecord = {policy_id, inputs_hash, model_id, model_hash, model_signature(opt), decision, timestamp, attester_quote(opt)}`.

### Strategic implication — what CLOSES the door

- Mandatory JSON-permissive parsing
- Mandatory single-vendor inference runtime / model / remote evaluator
- Embedded Turing-complete evaluators in canonical chain
- Required dynamic server-side includes at validation time
- Required opaque vendor-proprietary attestations without standardized quote format

## The Grok share conversation (Secure .toml Hosting on Cloudflare)

Full conversation recovered at
[`grok-share-secure-toml-cloudflare-raw.md`](./grok-share-secure-toml-cloudflare-raw.md)
(83.5KB, headless-Chrome rendered). The conversation covers three
implementation paths for hosting `.toml` artifacts with security
properties:

1. **Cloudflare Pages** (public + HTTPS/CDN) — for non-sensitive
   artifacts.
2. **Private R2 bucket + Cloudflare Access (Zero Trust)** — recommended
   for sensitive configs. Zero-code path; SSO/email/WARP allowlists; full
   audit logs.
3. **R2 + authenticated Worker** — maximum flexibility (custom auth,
   API keys, JWT, rate limiting, logging).

Toward the end the conversation moves into refined "core insight" framing
where the user pushes back that the first framing only partially covers
the trust problem — "the issue is probably closer to achieving what is
called zero trust, sort of" — and Grok agrees ("Understood. Thank you
for the correction... my previous framing only captured part of it. The
deeper issue is more fundamental.").

This is highly relevant going forward: the spec needs to interoperate
with Zero Trust deployment patterns (Cloudflare Access, identity-aware
proxies, WARP-style policies) when its artifacts are hosted on
infrastructure outside the producer's direct control. That overlaps
with Stream B (legal-grade attestation) — the consumer's verification
should not depend on the host (Cloudflare/R2/etc.) being trustworthy,
only on the producer's signature and the host being available.

The Grok conversation's framing of zero-trust-for-config-artifacts is
worth incorporating into the design directives file (`06-`) as a
deployment-pattern guidance item.

## Build-order implication (no change)

The follow-up-2 research does not change the four-stream build order from
[`../08-follow-up-synthesis.md`](../08-follow-up-synthesis.md):

1. **D** — canonical TOML profile / new format
2. **A** — kind-descriptor lockstep
3. **C** — separation-of-duty gates
4. **B** — legal-grade attestation

What it *adds* is a parallel "implementation-substrate roadmap":

- Today's primaries: safe Rust + safe Go + safe C software validators
  (mandated by user). HSM/TPM/FIDO2 hardware for signing ceremonies.
  GPU/CPU LLMs for policy/authoring with attested boundaries.
- 2030 trajectory: FPGA personalities for canonicalization and
  high-throughput validation at scale. Specialized inference silicon
  (Groq/Cerebras/Etched/etc.) for policy decisions. The spec must keep
  this door open from day one.

## Cost summary for the full dossier

| Wave | Exa Deep cost | Topics |
|---|---:|---|
| First wave | $1.16 | IJB primitives prior art |
| Follow-up wave (Streams A/B/C/D) | $5.98 | Kind-descriptor drift, legal attestation, separation of duty, format selection |
| Third wave (follow-up-2) | $3.07 | Cognitive automation lineage + HW/SW/cognition layering |
| **Total Exa Deep** | **$10.21** | 13 research streams across three waves |

CLI calls (Codex/Gemini/Grok across three waves) billed separately under
their respective API accounts.
