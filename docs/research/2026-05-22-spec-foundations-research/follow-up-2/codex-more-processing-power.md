# Codex (gpt-5.5) — "more processing power" thesis

Run via `llm-gateway` with Exa MCP, sandbox read-only. ~17KB stdout, 38
Exa searches across the four cognitive-automation waves and 2023–2026
AI-for-science milestones.

---

## 1. Historical Lineage

The pattern is not "automation ends work." It is "automation removes a bottleneck and makes the next bottleneck visible."

Before electronic calculators, engineers did arithmetic as a craft. Slide rules, logarithmic tables, mechanical calculators, Marchant and Friden desktop machines, and later electromechanical calculators were part of engineering discipline. They did not merely compute; they trained estimation, dimensional reasoning, scale awareness, and error suspicion. The HP-35 did not invent numerical engineering, and it would be wrong to claim it "made nuclear engineering possible" by itself. Large programs already used mainframes and specialist computation. But the HP-35 changed the personal economics of calculation: transcendental functions, ten-digit precision, exponent handling, and portability moved from desks, departments, and tables into an engineer's hand. What was discarded was much clerical calculation and slide-rule manipulation. What carried forward was sanity checking: orders of magnitude, units, approximation, and suspicion of exact-looking numbers.

FORTRAN repeated the same pattern in programming. Backus's team explicitly framed FORTRAN as a way to reduce the cost of preparing scientific problems for the IBM 704. The opposition was not irrational: early programmers feared that compiled code would be slow, opaque, and untrustworthy compared with hand-tuned assembly. Backus's answer was an optimizing compiler. The result did not eliminate programming; it shifted programming from instruction scheduling and register trivia toward algorithms, data structures, portability, and eventually software engineering. Dijkstra's attack on `goto` was a second-order consequence: once higher-level languages made larger programs possible, control-flow intelligibility became a central problem.

Search engines did the same for research. Google did not abolish libraries, expertise, or librarianship. It made access radically cheaper and broader, especially across uncontrolled hypertext. But it did not solve source quality, synthesis, judgment, or ranking transparency. It raised the floor of retrieval and moved the scarce work to evaluation.

LLMs are now doing this to routine cognitive production. Karpathy's Software 2.0 and Software 3.0 framing is useful because it describes a shift in what is "programmed": from explicit code, to data-trained weights, to natural-language/context-driven model behavior. Again, the work does not vanish. The frontier moves to specification, verification, provenance, orchestration, liability, and trust.

**Sources:**

- [IEEE/ETHW HP-35 milestone](https://ethw.org/Milestones:Development_of_the_HP-35,_the_First_Handheld_Scientific_Calculator,_1972)
- [HP Virtual Museum: HP-35](http://www.hp.com/hpinfo/abouthp/histnfacts/museum/personalsystems/0023/index.html)
- [Backus et al., FORTRAN paper, 1957](https://bitsavers.org/pdf/ibm/704/FORTRAN_paper_1957.pdf)
- [Dijkstra, "Go To Statement Considered Harmful"](https://www.cs.utexas.edu/~EWD/transcriptions/EWD02xx/EWD215.html)
- [Brin and Page, Google search paper](https://research.google/pubs/the-anatomy-of-a-large-scale-hypertextual-web-search-engine/)

## 2. What Did Not Change Across Waves

Across these waves, the durable skills are not clerical execution. They are synthesis, judgment, taste, and trust.

The slide-rule engineer's habit of estimating did not become obsolete when calculators arrived; it became more important because wrong answers became faster and more precise-looking. The assembly programmer's machine sympathy did not vanish with FORTRAN; it reappeared as performance engineering, compiler literacy, systems design, and debugging. The librarian's discernment did not vanish with Google; it became information literacy under ranking opacity, source abundance, and decontextualized documents. The programmer's craft does not vanish with LLMs; it moves to knowing what should exist, what evidence would prove it works, and where automation should be refused.

Engelbart's H-LAM/T framework is the unifying model: capability belongs to the whole system of human, language, artifacts, methodology, and training. New tools change that system, but they do not remove the need for trained judgment. Hamming's "important problem" test adds the frontier criterion: a problem matters when there is now a plausible attack. Cognitive automation creates plausible attacks on problems that were previously too expensive to even approach.

**Sources:**

- [Engelbart, "Augmenting Human Intellect"](https://www.dougengelbart.org/pubs/augment-3906.html)
- [Hamming, "You and Your Research"](https://www.cs.virginia.edu/~robins/YouAndYourResearch.html)
- [Brooks, "No Silver Bullet"](https://www.cs.unc.edu/techreports/86-020.pdf)
- [Bawden/Brophy, "Is Google enough?"](https://federatedsearchblog.com/_dbawden/bawden%20and%20brophy%20ap.pdf)
- [Sutton, "The Bitter Lesson"](http://www.incompleteideas.net/IncIdeas/BitterLesson.html)

## 3. The Frontier Shift

The calculator frontier was not "people no longer calculate." It was that numerical exploration became cheaper. Portable scientific calculators let engineers evaluate alternatives in the field, classroom, lab, and office without waiting for a shared machine, table, or specialist. This changed teaching as well: instructors could assign more realistic numerical problems once arithmetic ceased to dominate the exercise. The real frontier was model choice, sensitivity, tolerances, and interpretation.

The compiler frontier was larger. FORTRAN reduced the cost of expressing numerical procedures; ALGOL, structured programming, C, Pascal, Unix, and later managed languages made larger software systems imaginable. Once programming escaped machine code, the bottleneck became conceptual integrity, modularity, concurrency, operating systems, networking, distributed state, and failure handling. Brooks saw this clearly: past productivity gains removed accidental difficulty, leaving essential complexity exposed. Compilers did not make software easy; they made hard software worth attempting.

The search frontier was synthesis over abundance. Google made the web searchable at scale, and Google Scholar and discovery systems made old and cross-disciplinary work more findable. But the new problem was not finding "a document." It was constructing a defensible view from too many documents: provenance, citation context, methodological quality, incentives, and hidden ranking mechanisms.

The LLM frontier is now cheap production of plausible cognitive artifacts: code, summaries, specs, tests, legal drafts, plans, diagrams, and candidate proofs. Jevons applies: cheaper cognitive execution will not reduce total cognitive work. It will increase the number of attempts. More code will be written; more contracts drafted; more experiments proposed; more models trained; more scientific hypotheses screened. The limiting factor becomes the scarce complement: verification.

This is why the "overkill" reaction is historically weak. Every wave makes the old bottleneck look trivial in retrospect and makes the next bottleneck look excessive at first. Structured programming looked fussy until large programs made unstructured flow intolerable. Type systems, CI, reproducible builds, SLSA, and formal verification look excessive until the artifact volume crosses the point where trust-by-reading collapses.

**Sources:**

- [HP-35 design case study](https://literature.hpcalc.org/community/hp35-design-case-study.pdf)
- [IBM history of FORTRAN](https://www.ibm.com/history/fortran)
- [Brooks, "The Mythical Man-Month" excerpt](https://courses.cs.duke.edu/compsci408/spring25/readings/mythical_man_month.pdf)
- ["From Search to Discovery"](https://www.degruyterbrill.com/document/doi/10.1515/bfp-2015-0028/html)
- [Northeastern on Jevons paradox and AI](https://news.northeastern.edu/2025/02/07/jevons-paradox-ai-future/)

## 4. The Current Frontier, 2026

By 2026, the frontier is no longer whether AI can produce text or code. It is whether AI-assisted systems can produce reliable, auditable, externally checkable work in domains where mistakes matter.

AI-for-science is the clearest signal. AlphaFold 3 extended structure prediction across proteins, nucleic acids, ligands, ions, and modifications in a unified model. GNoME predicted millions of candidate crystal structures and expanded the set of stable materials candidates by an order of magnitude. GraphCast showed learned weather models competing with or outperforming operational systems on many medium-range targets while running much faster. FunSearch paired LLM generation with a systematic evaluator and produced new constructions for established mathematical problems. AlphaGeometry, AlphaProof, and then 2025 IMO gold-level systems show that sustained mathematical reasoning is moving from toy benchmarks to hard proof-like tasks.

But the deeper lesson is the architecture of these successes. The strongest systems do not rely on free-form generation alone. They bind generation to evaluators, simulators, proof assistants, DFT calculations, benchmarks, expert grading, or experimental loops. FunSearch is compelling precisely because it uses an evaluator to reject nonsense. Formal theorem-proving systems are compelling because Lean can check the proof. Materials systems are compelling when predictions flow into databases, DFT, autonomous labs, and physical synthesis. Weather models are compelling because forecast skill can be scored against held-out atmospheric data.

That is the template for agent assurance. LLMs put autonomous regulatory compliance, AI-assisted spec writing, proof-carrying code review, machine-witnessed proceedings, and reproducibility-at-scale within attack range. But none of these become legal-grade by being fluent. They become legal-grade only when generation is coupled to canonical inputs, reproducible validators, signed provenance, time, identity, authority, separation of duty, and durable evidence.

**Sources:**

- [AlphaFold 3, Nature 2024](https://link.springer.com/article/10.1038/s41586-024-07487-w)
- [GNoME materials discovery, Nature 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10700131/)
- [GraphCast, Science 2023](https://www.science.org/doi/10.1126/science.adi2336)
- [FunSearch, Nature 2023](https://pubmed.ncbi.nlm.nih.gov/38096900/)
- [Lean Copilot, ICML 2025](https://proceedings.mlr.press/v288/song25a.html)

## 5. Why Trust Infrastructure Is Load-Bearing

When output is expensive, organizations can rely on scarcity as a weak filter. When output is cheap, scarcity disappears and verification becomes the bottleneck. This is the shift that makes strict trust infrastructure rational.

A canonical TOML profile, content-hashed kind descriptors, multi-language safe validators, and golden-master conformance fixtures are not "just config parser ceremony." They are a way to make meaning brittle on purpose. In a high-volume agent system, permissive parsing is not kindness; it is an ambiguity amplifier. Silent acceptance scales the wrong way. If an agent emits a near-miss artifact, the system should fail loudly, early, and deterministically.

Legal-grade attestations answer a different problem: not "is this JSON shaped correctly?" but "who stood behind this statement, when, under what authority, with what intent, and against what exact bytes?" CMS/CAdES and COSE give signature containers. RFC 3161 gives proof-of-existence time. SCITT gives signed-statement transparency and auditability. FIDO2/QSCD-style mechanisms connect cryptographic events to human or organizational intent. FROST threshold signatures and separation-of-duty gates prevent one actor, key, or agent from laundering responsibility into a single unchecked approval.

Producer-side responsibility is the only scalable economic model here. At frontier volumes, consumers cannot re-derive every fact from scratch. Producers must emit artifacts with evidence attached: provenance, validation results, policy context, thresholds met, identities involved, and revocation paths. The consumer should verify mechanically, not investigate archaeologically.

**Sources:**

- [RFC 9943, SCITT architecture](https://www.rfc-editor.org/authors/rfc9943.html)
- [RFC 3161, Time-Stamp Protocol](https://www.rfc-editor.org/rfc/rfc3161)
- [RFC 9052, COSE](https://datatracker.ietf.org/doc/html/rfc9052)
- [ETSI CAdES EN 319 122-1](https://www.etsi.org/deliver/etsi_en/319100_319199/31912201/01.03.01_60/en_31912201v010301p.pdf)
- [RFC 9591, FROST](https://www.rfc-editor.org/rfc/rfc9591)

## 6. Pre-Emptive Rebuttals

**"This is too complex."** Compared with a config parser, yes. Compared with legal infrastructure for high-stakes machine-produced claims, no. The correct reference class is not `serde` parsing a developer preference file. It is qualified signatures, evidence preservation, supply-chain provenance, and court-admissible accountability.

**"This is too brittle."** Good. At the frontier, the dominant failure mode is silent acceptance of something that should have been rejected. Brittleness is how process trust propagates. A brittle validator is not hostile to developers; it is hostile to ambiguity.

**"This is hard to maintain."** So are compilers, TLS stacks, operating systems, and build systems. The maintainability answer is not looseness; it is small canonical profiles, golden fixtures, independent implementations, conformance suites, and boring cryptographic envelopes.

**"This will not pay for itself."** That objection applies floor economics to frontier systems. The payoff is not that a single config file is safer. The payoff is that autonomous work can cross institutional, legal, scientific, and regulatory boundaries without every recipient reconstructing trust from scratch.

**Sources:**

- [eIDAS Article 25](https://www.legislation.gov.uk/eur/2014/910/chapter/III/section/4/adopted/data.xht?view=snippet&wrap=true)
- [SLSA specification](https://slsa.dev/spec/v1.2/)
- [in-toto specification](https://github.com/in-toto/specification/blob/v1.0/in-toto-spec.md)
- [WebAuthn Level 3](https://w3c.github.io/webauthn/)
- [Brooks, "No Silver Bullet"](https://www.cs.unc.edu/techreports/86-020.pdf)

---

**Concise thesis**: every serious cognitive automation wave makes routine work cheaper and makes trust, judgment, and verification more valuable. Agent assurance is not overbuilt for the old world. It is sized for the world where plausible output is abundant and only defensible output matters.
