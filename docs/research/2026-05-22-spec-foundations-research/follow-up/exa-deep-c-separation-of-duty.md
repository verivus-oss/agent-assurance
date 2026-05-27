# Exa Deep Researcher — Stream C — Separation-of-duty gate validation

Model: `exa-research`. Cost: $1.67. Searches: 93. Pages crawled: ~240.
Research ID: `r_01ks6k9p13ym0bfj9x0ytbb1rd` (2026-05-22).

---

## Survey — evaluated mechanisms

For each: (a) threats mitigated, (b) costs/trust assumptions, (c) composability with cryptographic attestation, (d) gate-gaming resilience.

### 1) ISO audit / audit-separation principles (ISO 9001, ISO/IEC 17021, ISO 19011)

- (a) auditor independence and impartiality reduce conflict-of-interest, biased findings and subjective self-validation; risk-based audit planning increases chance of discovering deliberate or accidental control bypasses
- (b) procedural overhead (independent teams, rotation, impartiality committees, evidence collection); assumes auditors will act ethically and competently
- (c) audit records, independence declarations and findings can be digitally signed and timestamped to provide tamper-evident evidence — ISO procedures map naturally to crypto-attestation-based evidence chains
- (d) reduces opportunities to game gates but remains vulnerable to collusion, selective evidence or timing manipulations unless logs and attestations are tamper-evident

### 2) Two-party control / "two-man rule" (procedural dual control)

- (a) prevents unilateral malicious/erroneous approvals; eliminates single-person capability to flip critical switches
- (b) increased latency, personnel overhead, need for synchronized presence/authorization; assumes two actors are independent and not colluding; human factors (rubber-stamping) remain an operational risk
- (c) dual approvals map to dual cryptographic signatures or multi-key approval records to produce tamper-evident proof of two-party consent
- (d) strong against single-agent gaming but fails if both parties collude, if one impersonates the other, or if procedural controls are weak

### 3) Threshold signatures (FROST, BLS, Shamir, m-of-n schemes)

- (a) distributes signing authority so no single key-holder can sign; defends against key compromise and single-point signing fraud while enabling availability despite some offline parties
- (b) setup and distributed key generation complexity (DKG or trusted dealer), communication and protocol rounds, assumption that fewer than threshold participants are corrupted; potential coordinator attack vectors require secure protocol variants
- (c) yields a single compact signature that cryptographically attests that >m parties approved; easily embedded in attestation records
- (d) much stronger than 1-of-1 signatures; vulnerable when adversary controls or coerces threshold participants or when protocol setup is subverted

### 4) Multi-party computation (MPC) for verification

- (a) allows mutually-distrusting parties to compute verification/validation checks without revealing private inputs; reduces data-leakage and prevents a single party from falsifying validation data
- (b) cryptographic and communication overhead, latency, adversary-model assumptions (honest majority vs. malicious); setup complexity
- (c) MPC outputs can include cryptographic proofs or be paired with attestations proving the protocol executed correctly; ZKPs can be used to attest properties of private inputs
- (d) reduces single-party gaming; collusion across MPC parties or incorrect implementation allow gaming

### 5) Trusted third-party witnesses & transparency logs (notaries, CT, Rekor, SCITT)

- (a) append-only public logs deter undetected modification, provide public visibility of attestations or releases, and enable third-party monitoring
- (b) requires parties to submit attestations/log entries; shifts partial trust to log operators and monitoring agents; monitoring infrastructure required
- (c) logs store signed attestations and provide inclusion/consistency proofs; highly composable as external immutable witness
- (d) very effective vs. hiding or retroactive editing; depends on independent monitors—if nobody monitors logs, attackers can exploit detection delays

### 6) Reproducible builds (rb-tools, Bazel RBE, Tekton Chains, deterministic build practices)

- (a) prevents supply-chain/build-time insertion of backdoors by enabling independent parties to rebuild and confirm binaries match source; detects tampering between source and final artifact
- (b) engineering effort to remove non-determinism, pin toolchains/deps, establish hermetic build environments
- (c) reproducible outputs can be hashed and signed (Tekton Chains/Tekton attestations) to create verifiable provenance chains
- (d) robust against stealthy binary substitution; vulnerable if the build environment or tooling itself is compromised or if only the original producer performs verification

### 7) Capability-based isolation (OCaps, WASI, capability VMs)

- (a) minimizes blast radius, prevents confused-deputy abuses, and enforces least privilege in runtime and CI environments — reducing avenues for producers to corrupt validator-observable surfaces
- (b) requires redesign for capability granularity, hardware/monitoring support (e.g., CHERI), and rigorous capability management
- (c) capabilities and their issuance can be attested (signed capability grants) enabling verifiable checks that producers cannot write to validator-readable surfaces
- (d) high when capabilities are tightly scoped and enforced; leaks or overly broad capabilities permit gaming

### 8) in-toto layouts (multi-party supply-chain workflow attestations)

- (a) enforces that only authorized functionaries perform each supply-chain step and produces signed link metadata proving who did what, preventing step-skipping or unauthorized operations
- (b) authoring and maintaining layouts and key management; assumes specified functionaries are honest (but deviations are detected)
- (c) native — in-toto is an attestation format that links step metadata via signatures, suitable for bundling into transparency logs (Rekor) and SLSA provenance
- (d) strong at detecting skipped or forged steps; collusion among functionaries or compromised layout keys remain risks

### 9) Governance Gauntlet dual-rubric pattern

- (a) provides a standing adversarial rubric (parallel integrity-check) in governance to catch optimization-for-payoff behavior and incentive-driven gate gaming
- (b) administrative/analysis overhead to run parallel rubrics and maintain metric calibration; assumes rubrics are sufficiently orthogonal to detect gaming
- (c) governance outputs and checks can be attested; combining technical attestations with dual rubrics strengthens detectability of gaming
- (d) explicitly designed to make gaming harder by requiring an auditee to satisfy two independent criteria simultaneously

### 10) Stackelberg auditor-auditee games; Robust ML Auditing using prior knowledge

- (a) formal models that anticipate strategic auditor-evasion and design audit policies that reduce incentives for auditees to game tests; prior-knowledge-based audits reduce the ability of auditees to craft outputs that only look good under the audit's public tests
- (b) requires auditable prior knowledge and sophisticated audit-design capability; depends on behavioral assumptions about auditee rationality
- (c) game-theoretic audit outcomes can be coupled with cryptographic attestations of audit execution and evidence to prevent post-hoc manipulation
- (d) directly addresses strategic gaming by modeling it and prescribing audit policies that increase auditee cost of gaming

### 11) Attestable audits with TEEs

- (a) runs audit code and models in hardware-isolated environments producing attestations that the audit actually ran as declared, preventing auditee tampering during evaluation
- (b) TEE overhead, dependency on hardware vendor attestation roots, and potential side-channel risks; prototype costs show non-trivial CPU/GPU overheads
- (c) TEEs provide hardware-backed attestation primitives — ideal building block for proof-of-execution attestations
- (d) powerful for preventing runtime manipulation; remains sensitive to TEE implementation vulnerabilities and supply-chain of TEE firmware

### 12) Mandatory Access Control (Bell-LaPadula, Biba)

- (a) BLP preserves confidentiality by restricting flows; Biba enforces integrity constraints — both prevent unauthorized data flows that could enable gaming of validation channels
- (b) label management, strict policy enforcement that can reduce flexibility and require administrative effort
- (c) system states and policy enforcement logs can be attested; MAC reduces reliance on human assertions about data flows
- (d) strong technical control of flows reduces covert channel attacks, though covert channels and insider misuse remain concerns

### 13) Banking SoD: maker/checker, ICFR under SOX §404, COBIT

- (a) prevents fraud and reporting errors by segregating transaction initiation and approval, and by enforcing internal controls and tested processes
- (b) significant governance, documentation and auditing cost; assumes audit independence and integrity of control design and testing
- (c) digital signatures and cryptographic logs strengthen evidence for ICFR control operation and external attestations
- (d) strong when controls are enforced and monitored; collusion or control overrides can subvert controls

## Threat-model table (quick reference)

| Mechanism | Threats mitigated | Primary cost / trust assumption | Composable w/ crypto attestation? | Survives gate-gaming? |
|---|---|---|---|---|
| ISO audit separation | Biased/self audits, conflict-of-interest | Procedural overhead; trust in auditors | Yes — signed audit evidence | Partially — collusion & selective evidence remain risks |
| Two-party control | Unilateral sabotage/unauthorized actions | Latency, personnel coordination | Yes — dual signatures | Good vs single actor; fails under collusion |
| Threshold signatures | Key compromise, unilateral signing | Setup complexity, communication rounds | Native — single verifiable joint sig | High if threshold not compromised; collusion remains threat |
| MPC verification | Data leakage, biased inputs | Crypto/comm overhead; honest-majority assumptions | Yes — protocol proofs, ZKPs | Strong if parties honest; collusion reduces effectiveness |
| Transparency logs/witnesses | Hidden attestations, retroactive edits | Monitoring & submission overhead | Yes — inclusion/consistency proofs | Strong if monitored; weak if unmonitored |
| Reproducible builds | Binary-source mismatch/backdoors | Build engineering overhead | Yes — signed deterministic artifacts | Strong; fails if build tooling compromised |
| Capability isolation | Privilege escalation, confused deputy | Design/management complexity | Yes — signed capability grants | Strong when enforced; weak on leaks |
| in-toto | Step substitution, skipped checks | Layout & key mgmt overhead | Native — signed link metadata | Strong; collusion of functionaries can subvert |
| Governance Gauntlet | Incentive-driven manipulation | Rubric design & maintenance cost | Yes if checks are attested | Strong — detects optimizations-for-audit when rubrics orthogonal |
| Stackelberg / prior-knowledge audits | Strategic audit evasion | Prior knowledge & modeling cost | Yes when attested | Targets gaming by design; depends on priors |
| TEEs (attestable audits) | Runtime tampering, audit manipulation | Hardware trust & TCB attack surface | Native — remote attestation | Very strong vs runtime gaming; TEE vulns remain |
| MAC (BLP/Biba) | Unauthorized flows, integrity breaches | Policy labeling burden | Yes — attest enforcement logs | Strong technical control; covert channels exist |
| Banking SoD / SOX | Fraud, misreporting | Compliance, audit cost | Yes — crypto logs strengthen ICFR | Strong when properly monitored; collusion/overrides risk |

## Mechanical-pattern proposals (intent → action → proof → audit)

### Rules and rationales

- **Mandatory distinctness**: the Proof and Audit steps MUST be performed by entities cryptographically distinct from the Producer that performed Action. Reason: producer-controlled proof generation or self-audit creates an obvious self-validation vulnerability; an independent proof-generator and auditor create separation-of-duty that is auditable and tamper-evident.
- **Minimal distinctness set**: at minimum, (Proof) must be generated by an entity with a separate key/root of trust from the Producer; (Audit) must use evidence that cannot be rewritten by the Producer after Action occurs (append-only log or attestation). This supports consumer verification of final artifacts while preserving producer responsibility.
- **Human-originated intent declarations** should be bound cryptographically (signed intent manifests) and logged so auditors verify intent vs. action mismatches.

### Which steps MUST be done by distinct entities

- **Intent**: may be produced by the actor (human or agent) that initiated the workflow but MUST be signed with a key distinct from any high-privilege deployment or build key. If intent originates from an agent, that agent's intent signature must be distinct from the agent/process that later performs Action.
- **Action**: done by the Producer (builder, trainer, deployer). The Producer must not have the only signing key for Proof or Audit artifacts.
- **Proof**: MUST be produced by a validator that cannot be influenced to change after the Action (e.g., independent builder/reproducer, separate signing key in a different trust domain, TEE-based verifier, MPC-based aggregator, or threshold signer that excludes the producer).
- **Audit**: MUST be performed by an independent auditor or auditor-service whose root of attestation (key, TEE endorsement, or threshold share set) is distinct from the Producer's root; audit findings and their attestations must be published to an append-only transparency log (Rekor/Trillian/SCITT) for public verifiability.

### Cryptographic enforcement techniques for "distinct entity"

- **Separate cryptographic identities and roots-of-trust**: issue distinct long-lived key material for Producer, Proof-Validator, and Auditor; bind keys to organizational or hardware roots (HSM/TEE key attestation) and require that Proof and Audit signatures verify against different trust anchors than the Producer's operational keys.
- **Threshold signing that excludes Producer**: use m-of-n threshold keys where the Producer lacks a signing share; require that the Proof and/or Audit signatures come from a key whose shares are controlled by independent stakeholders.
- **Attested TEEs for Proof**: run the validator's reproduction or verification in a TEE that can produce remote attestation binding the code, inputs, and outputs — attestation signed by TEE root and published to a transparency log.
- **Append-only witness logs**: make Proof and Audit attestations referenced by inclusion proofs in public transparency logs so Producers cannot retroactively modify records.
- **in-toto/integrated provenance**: place layout-signed steps and link metadata into the attestation chain so consumer verification can validate end-to-end provenance.
- **Reproducible-builder cross-check**: require at least one independent re-builder (distinct key/identity) to replicate Action and publish matching artifact hash signed by the re-builder.

### Handling the auditor-as-agent and gate-gaming by auditor-agents

- Treat auditors that are agents as potentially strategic actors. Apply Stackelberg-game-informed audit policy design: auditors should commit publicly to audit policies and sampling strategies (commitment limits auditee optimization against unknown tests) and publish policy commitments and attestation of execution.
- Use dual-rubric (Governance Gauntlet) checks: pair the primary audit with an orthogonal secondary rubric (e.g., black-box behavior test + supply-chain attestation review) so an auditor-agent cannot simultaneously optimize both without significant cost.
- Force auditor transparency: auditor-agents must produce attested execution records (TEE attestations, signed logs) and publish them to transparency logs so third-party monitors can detect selective omission or manipulation.
- Randomized and private test vectors: where possible, auditors should use partially-private or randomized test inputs (seeded by auditable RNG sources) or prior-knowledge based tests that are hard for producers to overfit to.
- Cross-auditor redundancy: require multiple, independently-operated auditor-agents to attest to the same event; combine attestations using threshold or MPC schemes so no single auditor-agent can unilaterally satisfy audit obligations.

### Composing with consumer-verifies-final-artifact requirement

- **Producer responsibility**: producers supply (a) final artifact, (b) provenance bundle (in-toto or Tekton/TLS-signed provenance), (c) Proof attestations (independent re-builder signature or TEE attestation), and (d) Audit attestations (independent auditor signatures plus transparency-log inclusion proof). Consumers verify only final artifact + bundled attestations: verifying final artifact integrity and provenance chain is sufficient to trust validation without fetching upstream evidence.
- **Minimal verification for consumers**: (1) check artifact hash matches signed Producer attestation, (2) verify at least one independent Proof attestation (re-builder/TEE) signed by a trust anchor separate from Producer, (3) verify inclusion of Audit attestation in transparency log with valid auditor key or threshold signature. This balances producer responsibility with consumer simplicity.

## Practical pattern cookbook (component-level recommendations)

- **Build pipeline**: require hermetic, reproducible builds; sign provenance using Tekton Chains/in-toto layouts; publish to Rekor-like log and produce a reproducibility attestation signed by an independent reproducibility-runner or threshold-key.
- **Model training & dataset gates**: log dataset hashes and training hyperparameters in provenance; require independent validator to re-run a reproducibility check on held-out seeds in a TEE producing an attestation linking inputs→weights→hash.
- **Authorization & approval**: use threshold signatures or two-party dual-signatures for release approvals where release signing key is a threshold key controlled by separate roles; ensure Producer lacks a full share.
- **Runtime capability enforcement**: run validators in capability-limited sandboxes (WASI or capability VMs) so the Producer cannot write to validator-observable surfaces; attest capability policies and enforcement logs.
- **Logs & transparency**: always publish Proof and Audit attestations (signed) into an append-only log with inclusion proofs consumers can fetch or rely on for offline verification.

## Auditable evidence taxonomy (what must be signed/published)

- Signed intent manifest (signed by originator, distinct key) — binds declared purpose & policy.
- Action artifact + producer signature (signed by Producer's production key).
- Independent Proof attestation(s): re-builder signature, MPC aggregate proof, or TEE attestation (signed by validator's distinct key/root).
- Audit attestation(s): independent auditor signature(s) or threshold-signed statement; inclusion-proof in transparency log.
- All attestations include timestamps and nonces to limit replay/rollback attacks.

## Operational notes and trade-offs

- **Trade-offs**: stronger separation (distinct keys, independent re-builders, TEEs, MPC) increases cost and latency but yields materially higher resistance to self-validation and gate gaming; threshold-signature and transparency-log patterns mitigate collusion and retroactive tampering while keeping verification efficient for consumers.
- **Trust distribution**: the design goal is to move from trusting single producers (opaque self-attestation) toward a composable trust model: local producer keys + independent validator keys + public transparency logs + hardware/threshold roots.

## Key citations (selected)

- Attestable Audits (arXiv 2506.23706) — https://arxiv.org/html/2506.23706v1
- CAP-VMs (OSDI 2022) — https://www.usenix.org/system/files/osdi22-sartakov.pdf
- Robust ML Auditing using Prior Knowledge — https://proceedings.mlr.press/v267/garcia-bourree25a.html
- Strategic Auditee Gaming — https://arxiv.org/html/2605.06340v1
- Reproducible Builds — https://reproducible-builds.org
- Trillian transparency log — https://transparency.dev
- ISO 19011 — https://synersia.org/wp-content/uploads/2021/02/ISO-19011-2018-Pedoman-Audit-Sistem-Manajemen-EN.pdf
- Sigstore Rekor — https://docs.sigstore.dev/logging/overview
- in-toto spec — https://github.com/in-toto/docs/blob/master/in-toto-spec.md
- FROST (NIST threshold cryptography) — https://csrc.nist.gov/csrc/media/Projects/threshold-cryptography/documents/TCall-1/FROST-PW01.pdf
- Governance Gauntlet (SSRN) — https://papers.ssrn.com/sol3/Delivery.cfm/6625918.pdf
- NIST two-person control glossary — https://csrc.nist.gov/glossary/term/two_person_control
- SOX 404 — https://www.cbh.com/insights/articles/sox-404
- Bell–LaPadula — https://en.wikipedia.org/wiki/Bell–LaPadula_model
