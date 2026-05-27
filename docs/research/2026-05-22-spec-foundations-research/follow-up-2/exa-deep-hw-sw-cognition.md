# Exa Deep Researcher — HW/SW/cognition layering

Model: `exa-research`. Cost: $0.85. Searches: 48. Pages crawled: ~121.
Research ID: `r_01ks6ntbafxnm45dtfwxw1qjxe` (2026-05-22).

Researches the per-layer HW/SW/cognition ratio for a security/legal-grade
trust stack and the strategic implications of inference-cost decline
and FPGA emergence. Validates or pushes back on the user's per-layer
claims and proposes concrete spec choices that keep all three doors
open at every layer.

---

## Canonicalization & cryptographic primitives (deterministic CBOR, ASN.1 DER, SHA-256, signatures)

**(a) Who/what performs this today.** Fixed cryptographic primitives and canonical encodings are implemented across ASICs, FPGAs, HSMs and general-purpose CPUs depending on deployment: high-volume hash/signature work is often on ASICs and HSMs; cloud providers and appliances use dedicated accelerators (Intel QAT, Marvell/Cavium NitroX, AWS Nitro) and FPGA prototypes for PQC experiments; CPUs run software reference stacks for flexibility/portability. [Intel QAT security policy](https://csrc.nist.gov/CSRC/media/projects/cryptographic-module-validation-program/documents/security-policies/140sp5032.pdf), [AWS PQC migration slides](https://na.eventscloud.com/file_uploads/ab427273097016082635f809ed6aa0a0_Day1-1300-AWSAcloudcentricapproachtoPQCmigrationCampagna.pdf), [Marvell NITROX III](https://www.marvell.com/products/security-solutions/nitrox-iii.html), [NIST PQC FPGA implementations](https://csrc.nist.gov/csrc/media/Events/2022/fourth-pqc-standardization-conference/documents/papers/high-performance-hardware-implementations-pqc2022.pdf).

**(b) Determinism vs flexibility.** Canonicalization and cryptographic primitives demand maximal determinism: any non-deterministic serialization will break hashes and signatures. The only practical flexibility is limited, explicit, versioned changes (new canonical rules) rather than tolerance of multiple encodings. [CBOR determinism discussion](https://cborbook.com/part_2/determinism.html).

**(c) What HW acceleration buys.** Performance (Intel QAT/Marvell NitroX/AWS Nitro), security boundary (HSMs/TPMs/secure elements with tamper resistance), upgradeability (FPGAs combine hardware acceleration with reconfigurability—useful during PQC migration). [TPM library spec](https://trustedcomputinggroup.org/resource/tpm-library-specification).

**(d) How inference-cost decline shifts the ratio.** Falling inference costs do not change that canonical cryptographic functions are best executed in hardened hardware where determinism and tamper resistance matter. Cheaper inference enables richer tooling around canonicalization (AI-assisted verification, anomaly detection) but the primitive compute remains hardware-anchored.

**Verdict:** User intuition validated. Determinism-critical canonical and crypto layers strongly trend to hardware; FPGAs attractive when algorithm evolution (e.g., PQC) requires field reprogrammability.

## Validator / parser layer (safe Rust/Go/C parsers consuming canonical bytes)

**(a) Today.** CPUs with optimized libraries (simdjson demonstrates CPU SIMD strategies for line-rate JSON parsing). When throughput becomes binding, FPGA parsers (PipeJSON and follow-ons) show multiple-x speedups over top CPU parsers. [simdjson GitHub](https://github.com/simdjson/simdjson), [PipeJSON ACM paper](https://dl.acm.org/doi/fullHtml/10.1145/3533737.3535094), [Hyperscan paper](https://www.usenix.org/system/files/nsdi19-wang-xiang.pdf).

**(b) Determinism vs flexibility.** Validators must be deterministic with respect to canonical bytes they consume: parsing must reject non-canonical variants in trust contexts to avoid signature mismatch, but the parser implementation can retain flexibility in error reporting, recovery paths, and extensible schema support. Safe languages (Rust/Go/C with safety subsets) are the standard for secure parser implementations.

**(c) What FPGA acceleration buys.** Throughput/latency headroom; attack surface narrowing (pushing fastest, simplest validation checks into hardware reduces the trusted codebase running in the OS).

**(d) Inference-cost decline.** As inference gets cheaper, cognitive tooling (LLM-based validators, schema inference helpers, anomaly detectors) augment parser testing, fuzzing, and schema repair, improving developer productivity and safety; however, the parser's core deterministic acceptance rules remain software or hardware implementations depending on throughput.

**Verdict:** Largely validated. Software (safe Rust/Go/C) is the correct baseline for validator parsers; FPGA is the correct frontier when throughput, latency or power become binding.

## Schema / kind-descriptor layer (content-hashed ASTs, golden-master fixtures)

**(a) Today.** CPUs perform schema management, content hashing, AST canonicalization and golden-master validation; HSMs may host signing of golden masters. [C2PA spec](https://spec.c2pa.org/specifications/specifications/1.0/specs/C2PA_Specification.html).

**(b) Determinism vs flexibility.** Determinism required for content hashes and AST canonical forms; flexibility required for controlled schema evolution. Well-designed descriptor systems explicitly version canonicalizers rather than rely on ad-hoc permissiveness.

**(c) What FPGA acceleration could buy.** Speed up bulk hashing, pattern matching, and large fixture reconciliation in high-throughput pipelines (build farms, CI at hyperscaler scale). [FPGA SHA-3 architectures](https://pmc.ncbi.nlm.nih.gov/articles/PMC9031777), [FPGA accel for DBs/queries](https://dl.acm.org/doi/full/10.1145/3674843).

**(d) Inference-cost decline.** Cheaper inference empowers richer LLM-driven schema evolution tooling (automatic migration suggestions, semantic diffing of ASTs). Hard integrity guarantees (content hashes, canonical AST serialization) remain deterministic.

**Verdict:** Mixed. Deterministic integrity operations should remain hardware/low-level software, but the schema/kind descriptor layer is also a natural locus for cognition. Layer becomes hybrid.

## Attestation / signing ceremony (HSM, TPM, FIDO2, eIDAS QSCD)

**(a) Today.** TPMs, HSMs, certified secure elements (FIDO2 authenticators, QSCD for eIDAS), and TEE-backed attesters (Intel SGX/TDX, AMD SEV-SNP, ARM CCA). [TPM library spec](https://trustedcomputinggroup.org/resource/tpm-library-specification), [Intel TDX overview](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html), [AMD SEV info](https://www.amd.com/en/developer/sev.html), [Arm CCA docs](https://developer.arm.com/documentation/den0125/400/Arm-CCA-Extensions), [FIDO Device Onboard](https://fidoalliance.org/wp-content/uploads/2022/12/FIDO-Device-Onboard-The-Device-Key-White-Paper.pdf).

**(b) Determinism vs flexibility.** Attestation ceremonies require determinism for cryptographic assertions and provenance. Flexibility required in policy (what measurements are acceptable) and occasionally in programmable HSMs.

**(c) What HW acceleration buys.** HSMs and secure elements already use dedicated silicon/firmware to provide tamper resistance and efficient signing; FPGA-based HSMs combine reconfigurability with hardware isolation for fast migration during standards transitions (e.g., PQC). TEEs (SGX/TDX, SEV-SNP, ARM CCA) provide attestable execution boundaries.

**(d) Inference-cost decline.** Cheaper LLM inference enables richer cognitive verification of attestation statements but does not erode the need for hardware roots of trust. Cognition improves attestation interpretation and policy checks, but signing ceremonies and key custody remain hardware-centric.

**Verdict:** Validated with nuance. Attestation/signing stays hardware-anchored; cognition augments validation and policy decisions that act on attestation statements but must execute within hardware-attested boundaries.

## Audit / verification (re-builders, threshold signing, transparency logs)

**(a) Today.** CPU/GPU clusters for heavy verification tasks, HSMs for signing, distributed software systems for transparency logs (e.g., Certificate Transparency) and re-builders (reproducible builds). Threshold signing systems combine HSMs or distributed key-share software running on TEEs. [Certificate Transparency primer](https://www.sectigo.com/knowledge-base/detail/Understanding-Certificate-Transparency-CT-Logs-and-Precertificates).

**(b) Determinism vs flexibility.** Determinism for reproducibility and accountability; flexible tooling (anomaly detection, probabilistic evidence linking) for triage. Deterministic crypto primitives and reproducible build pipelines remain the bedrock.

**(c) What FPGA could buy.** Speed cryptographic verification, log ingestion, Merkle tree computations, ZKP precomputation; enable real-time log monitoring at scale. [ZKP and FPGA research](https://arxiv.org/html/2510.26576v2).

**(d) Inference-cost decline.** AI-assisted audit activities (anomaly detection over logs, natural language evidence correlation) but verifiable artifacts (signed rebuild outputs, Merkle roots) remain deterministic. Threshold signing still centers on HSMs/TEE or distributed MPC hardware.

**Verdict:** Validated. Audit/verification is determinism-critical and moves toward specialized hardware when the algorithm is fixed and scale demands it.

## Reasoning / policy (LLM-driven gate decisions, policy synthesis)

**(a) Today.** LLMs and model ensembles running on GPU/CPU clusters or specialized inference silicon (Groq LPU, Cerebras WSE, SambaNova RDU, Tenstorrent, Etched Sohu) for latency/throughput advantages, with humans in the loop for governance. [Groq LPU explainer](https://groq.com/blog/the-groq-lpu-explained), [Cerebras architecture](https://www.cerebras.ai/blog/announcing-the-cerebras-architecture-for-extreme-scale-ai), [SambaNova RDU](https://sambanova.ai/products/rdu-ai-chips), [Tenstorrent QuietBox](https://tenstorrent.com/en/newsroom/these-ai-workstations-look-like-pcs-but-pack-a-stronger-punch), [Etched Sohu](https://www.linkedin.com/pulse/etcheds-sohu-chip-company-betting-big-ai-asic-anshuman-jha-bjsdc).

**(b) Determinism vs flexibility.** This layer prefers flexibility because policy rules, threat models, and context change. Deterministic enforcement only at enforcement points. **Architecture should separate "reasoning" (probabilistic/adaptive, LLMs) from "authority" (deterministic gates implemented in auditable code/hardware).**

**(c) What specialized silicon buys.** Drastically reduces cost/latency of running larger models in production, enabling real-time, higher-quality cognition at scale. FPGAs offer reconfigurable acceleration that can embed parts of the inference pipeline for latency-sensitive policy gates.

**(d) Inference-cost decline.** Rapid inference cost decline (a16z "LLMflation", EpochAI analyses) makes running sophisticated LLMs for policy synthesis and gate decisions economically feasible, shifting workloads from occasional batch analysis to always-on inference pipelines. [a16z LLMflation](https://a16z.com/llmflation-llm-inference-cost), [EpochAI cost analysis](https://epoch.ai/gradient-updates/how-persistent-is-the-inference-cost-burden).

**Verdict:** Validated. Policy/reasoning belongs primarily to cognition (LLMs/humans) but must be executed/validated within hardware-attested boundaries for high-assurance deployments.

## Authoring (humans + LLM assistants writing descriptors, threat models)

**(a) Today.** Human-led with heavy LLM assistance for drafts, threat scenario enumeration, automated checklisting.

**(b) Determinism vs flexibility.** Authoring benefits from maximal flexibility: outputs are creative and contextual and should remain probabilistic and human-guided. Determinism only for output formats intended for machine consumption.

**(c) What FPGA could buy.** Modest direct value—authoring is highly interactive cognitive work. FPGA/ASIC acceleration primarily benefits this layer indirectly by reducing inference latency.

**(d) Inference-cost decline.** Tooling becomes more capable: continuous LLM assistants, auto-generated threat matrices, interactive golden-master synthesis. Human cognition remains central.

**Verdict:** Validated. Authoring remains cognition-centric; cheaper inference improves tooling and productivity rather than replacing human judgement.

## Per-layer optimal HW/SW/cognition split (summary)

| Layer | HW | SW | Cognition |
|---|---|---|---|
| Canonicalization & crypto | **Primary (ASIC/HSM)**, FPGA for upgrade | Orchestration | Meta-validation only |
| Validator/parser | FPGA for throughput frontier | **Baseline (safe Rust/Go/C)** | Schema recovery, fuzzing, testing |
| Schema/descriptors | Hashing/signature offload at scale | Management | **Descriptor generation, migration** |
| Attestation/signing | **Primary (HSM/TPM/secure-element + TEE)** | Policy code in enclaves | Policy interpretation |
| Audit/verification | FPGA for ZKP/Merkle/heavy crypto | Deterministic verification anchored here | Anomaly detection, evidence correlation |
| Reasoning/policy | Specialized inference silicon | Deterministic enforcers must be HW-attested | **Primary (LLMs)** |
| Authoring | Inference silicon reduces latency | Workflow integration | **Primary (humans + LLM)** |

## Strategic implication for the SPEC

A trust-infrastructure spec written today must preserve **orthogonality** between representation, validation, attestation and cognition so implementers may choose HW, SW or cognitive implementations as cost/performance/assurance tradeoffs change. The spec must:

(a) mandate determinism where security requires it,
(b) standardize verifiable attestation interfaces,
(c) favor small, auditable validators,
(d) avoid vendor lock-in for inference engines or hardware,
(e) enable pluggable attestable execution contexts.

### Spec choices that KEEP the door open

- **Canonical deterministic on-the-wire formats:** require deterministic CBOR/DER-style canonicalization for all signed artifacts (strict rules for numeric normalization, map ordering, length forms). Ensures hardware/ASIC/FPGA implementations can be substituted without ambiguity.
- **No Turing-complete macros in canonical descriptors:** use limited DSLs or ASTs that are simple to re-implement in hardware or small safe runtimes (content-hashed ASTs with canonical serialization).
- **Verifiable, minimal validator spec:** define the validator as a small, auditable state machine (accept/reject with deterministic diagnostics) and publish a formal test corpus (golden-master fixtures) and content-hashed ASTs so both software and hardware vendors can prove conformance.
- **Pluggable attestation API and attester abstraction:** define an attester abstraction that accepts hardware roots (TPM/HSM/TEE signatures) and a canonical statement format for attestation quotes; do not mandate a specific root.
- **Signed fixture transparency logs + Merkle proofs:** require artifacts be logged in tamper-evident transparency logs with canonical Merkle root representations.
- **Schema/version metadata for forward compatibility:** mandate explicit version and upgrade paths for canonicalizers; canonicalizers must be content-addressed.
- **No mandatory single-vendor inference runtime:** allow LLM outputs anywhere in the stack but require any cognitive decision used to modify authoritative state be accompanied by a canonicalized signed claim, provenance metadata, and an attestation claim that the inference executed in an accredited environment.
- **No mandatory remote includes/eval:** disallow specifications that require fetching executable code or model weights from a remote authority at runtime.
- **Specify minimal, auditable serialization for policy decisions:** require that policy gating results be expressible as canonical signed decision objects (e.g., `decision = {policy_id, inputs_hash, model_hash, model_signature, decision, proof}`).

### Choices that CLOSE the door (do not do these)

- Mandatory JSON permissiveness (no canonicalization)
- Mandating a single vendor's inference runtime, model, or remote evaluator
- Embedding Turing-complete evaluators in the canonical chain
- Required dynamic, unbounded server-side includes at validation time
- Required opaque attestations without standardized quote format or provenance

## Implementation guidance (spec language examples)

- "All signed artifacts MUST be serialized using the SpecCanonicalCBOR v1 encoder. Implementations MUST reject signatures computed over non-canonical encodings."
- "Validator implementations MUST pass the ValidatorTestSuite; test vectors are content-addressed fixtures hashed with SHA-256 and published in the spec's test log."
- "Any policy decision that affects an authoritative artifact MUST be emitted as DecisionRecord = {policy_id, inputs_hash, model_id, model_hash, model_signature(optional), decision, timestamp, attester_quote(optional)}; DecisionRecords are signed and loggable."
- "Attesters MAY present TPM, HSM, or TEE quotes in the standardized AttestationStatement format v1; verifiers declare acceptance policies as a policy manifest."

## Final substantive point

A robust trust-infrastructure spec should explicitly separate determinism-critical primitives (serialization, hashing, signing, attestation anchors) from flexible cognition (schema synthesis, policy generation, human authoring) and standardize the interfaces between them: **canonical bytes + small validators + attestable execution + signed decision records + transparency logging**. Those design choices preserve the ability to implement any layer in hardware (ASIC/FPGA/HSM), in safe software (Rust/Go/C), or as cognition (LLMs/reasoning engines) as economics and threat models evolve, while preventing opaque rules that would lock the ecosystem into a single vendor or execution model.
