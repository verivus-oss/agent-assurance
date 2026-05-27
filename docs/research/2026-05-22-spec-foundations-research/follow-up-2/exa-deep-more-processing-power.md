# Exa Deep Researcher — "more processing power" thesis

Model: `exa-research-pro`. Cost: $2.23. Searches: 73. Pages crawled: ~183.
Research ID: `r_01ks6nprxecw3tpm25axv9xc31` (2026-05-22).

Researches the historical lineage of cognitive-task automation creating
new problem frontiers; grounds the user's thesis with primary sources
from Engelbart, Hamming, Brooks, Backus, Dijkstra, Brynjolfsson/McAfee,
Sutton, Karpathy, and 2021–2026 AI-for-science milestones.

---

## Thesis

Each wave of cognitive-task automation raises the effective floor of competence (making routine and formerly time-consuming work cheap and reliable) and thereby shifts attention and resources toward problems previously considered intractable. As routine generation becomes cheap, the bottleneck becomes trustworthy validation and governance; therefore trust infrastructure that appears over-engineered at the floor is in fact the load-bearing primitive for the new frontier (autonomous regulatory compliance, machine-witnessed legal proceedings, attested scientific reproducibility at scale).

## 1. Historical lineage: how successive automation waves raised the floor and moved the frontier

### 1.1 Pre/post calculator (1960s–1980s)

What changed in practice: slide rules and mechanical calculators performed approximations, logarithmic and trigonometric interpolation, and basic arithmetic; handheld scientific electronic calculators (notably the HP-35 in 1972) made those operations fast, portable, and far more precise, removing much manual numerical drudgery from engineering practice and enabling real-time field and office computation rather than laborious table lookup and hand interpolation. Petroski emphasizes how tools change what designers routinely do and hence what they can attempt; design tools (pencils, calculators) shape the problems engineers will take on.

What engineers stopped/started doing: engineers stopped relying on slide-rule approximation heuristics and lengthy manual table interpolations; they began doing more iterative numerical exploration, more parametric sensitivity studies, and more exploratory design calculations at the desk and on site—activities that were previously deferred to batch mainframe runs or avoided entirely.

Problem classes made tractable: repeated, higher-precision engineering calculations facilitated advances in nuclear engineering (safety computations, shielding), aerospace (trajectory and aerodynamic optimization), and large civil projects (iterative structural analysis and load modeling).

Sources: [TNMOC](https://www.tnmoc.org/slide-rules-calculators), [Medium HP-35 article](https://medium.com/@vplevris/the-calculator-that-killed-the-slide-rule-b66667ffb2ed), [Petroski review (NYT)](https://www.nytimes.com/1990/01/22/books/books-of-the-times-engineering-a-perfect-pencil-and-thoreau-s-part-in-it.html).

### 1.2 Pre/post compiler (1950s–1970s)

Key primary sources: Grace Hopper's compiler work (A-0, FLOW-MATIC, and COBOL lineage) and the FORTRAN Automatic Coding System (Backus et al., 1957) show the first steps of lifting programmers from machine language to mathematical and domain-oriented notation. Compilers abstracted away machine opcodes, letting more people express problems in higher-level terms and iteratively refine algorithms instead of coding machine instructions by hand. By enabling higher-level expression and modularity, compilers made practical the development of operating systems, database engines, and networking stacks—system classes whose conceptual complexity is high but whose accidental cost (machine coding) had been a limiting factor. Influential paradigms (Dijkstra's "Go To Statement Considered Harmful" and the broader structured programming movement) were possible because languages and compilers made structured constructs available and analyzable. Brooks' analysis later emphasized that compilers cut accidental complexity but not essential complexity—the floor was raised enough to enable new classes of systems.

Sources: [Backus et al. FORTRAN paper (1957)](https://archive.computerhistory.org/resources/text/Fortran/102663113.05.01.acc.pdf), [Yale biography of Grace Hopper](https://president.yale.edu/biography-grace-murray-hopper), [Dijkstra (1968)](https://homepages.cwi.nl/~storm/teaching/reader/Dijkstra68.pdf), [Brooks "No Silver Bullet"](https://www.cs.unc.edu/techreports/86-020.pdf).

### 1.3 Pre/post search engine (1990s–2010s)

Search engines made massive information retrieval practical; the friction of physically locating journals, books, or curated indexes disappeared for many tasks. The productivity gains were not automatic—the J-curve dynamic and need for complementary organizational changes appear in productivity research. What did not change: synthesis, sense-making, and evaluation of quality remained human bottlenecks even as retrieval became cheap. Retrieval reduced the cost of finding data but increased the volume and diversity of things to be synthesized, making integration and provenance verification the new hard tasks. The shifted frontier: real-time, global literature synthesis, large-scale open-data curation, collaborative knowledge engineering, and platformized marketplaces of information became tractable once retrieval barriers fell.

Sources: [Edge.org on Lanier "local-global flip"](https://www.edge.org/conversation/jaron_lanier-the-local-global-flip-or-the-lanier-effect), [Brynjolfsson productivity J-Curve (NBER)](https://www.nber.org/papers/w28254).

### 1.4 Pre/post Large Language Models (2020s)

Karpathy's "Software 2.0" framing (models trained on data rather than hand-coded features) and Sutton's "The Bitter Lesson" argue that general methods that scale with compute tend to outperform domain-specific hand-engineering over time. LLMs make advanced language tasks—summarization, translation, extraction, drafting and initial coding—cheap and available to a broad class of users, turning previously expert bottlenecks into routine outputs that can be produced at scale. The limiting task becomes verification, provenance, and attestation of model outputs.

Sources: [Karpathy Software 2.0](https://karpathy.github.io/software-2/), [Sutton The Bitter Lesson](http://www.incompleteideas.net/IncIdeas/BitterLesson.html), [Brookings: impact of language models](https://www.brookings.edu/articles/exploring-the-impact-of-language-models).

### 1.5 Engelbart, Hamming, Brooks, Brynjolfsson — theoretical anchors

- Engelbart's augmentation thesis: the H-LAM/T model argues that augmenting human intellect with interactive artifacts and trained methods produces superior problem-solving capacity compared with pure automation that substitutes for humans. His 1968 Mother-of-All-Demos implemented interactive augmentation (mouse, hypertext, collaborative editing) that made new collaborative problem classes tractable. [Engelbart AHI 1962](https://dougengelbart.org/library/AHI-Framework).
- Hamming on tools reframing first-rate problems: tools redefine what counts as a first-rate problem by changing feasibility boundaries—new tools make previously unreachable problems worthwhile and solvable. [Hamming "You and Your Research" transcript](https://www.cs.virginia.edu/~robins/YouAndYourResearch.html).
- Brooks on essential vs accidental complexity: tools shift the balance by lowering accidental costs, which in turn makes tackling larger essential problems feasible—but they do not eliminate essential complexity. [Brooks "No Silver Bullet"](https://www.cs.unc.edu/techreports/86-020.pdf).
- Brynjolfsson & McAfee on the J-curve: general-purpose technologies produce slow initial productivity uptake until complementary capital and organizational changes are in place. [NBER J-Curve paper](https://www.nber.org/papers/w28254).

### 1.6 Jevons paradox of computation

Efficiency enabling more total activity: per-unit efficiency gains (more FLOPs per watt, better PUE in data centers) correlate with greater total computational demand, not less—more efficient compute encourages larger models, more experiments, and more automated pipelines.

Source: [Sharma, "The Jevons Paradox in Cloud Computing"](https://arxiv.org/html/2411.11540v1).

## 2. AI-for-Science (2021–2026): concrete milestones that illustrate a moved frontier

- **AlphaFold (2021):** AlphaFold2 demonstrated that deep learning could predict single-protein 3D structures at near-experimental accuracy, and DeepMind's AlphaFold Protein Structure Database made hundreds of millions of predicted structures available. [Nature: AlphaFold paper (2021)](https://www.nature.com/articles/s41586-021-03819-2), [DeepMind AlphaFold five-year impact blog](https://deepmind.google/blog/alphafold-five-years-of-impact).
- **AlphaFold 3 (2024):** extended capabilities for complexes, ligands, and interactions—further reducing experimental burdens and enabling higher-throughput computational chemistry. [Review of AlphaFold 3 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11292590).
- **AlphaProof / AlphaGeometry (2024):** systems that combine learning and symbolic/formal machinery to achieve human-level performance on hard mathematical contest problems and to generate formalizable, checkable proofs. [DeepMind blog on IMO-level results](https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level).
- **FunSearch (2023–2024):** LLM-driven program search that produces interpretable, human-readable algorithms and mathematical constructions, enabling discovery of new proofs and algorithms. [DeepMind FunSearch blog](https://deepmind.google/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models).
- **GraphCast / GenCast (2023):** graph-neural-network and generative models that produce weather forecasts faster and in some regimes more accurately than traditional NWP. [DeepMind GraphCast blog](https://deepmind.google/blog/graphcast-ai-model-for-faster-and-more-accurate-global-weather-forecasting).
- **Materials discovery at scale (GNoME / Materials Project, 2023):** deep learning models that propose millions of candidate crystal structures and rapidly triage plausible materials. [DeepMind materials discovery blog](https://deepmind.google/blog/millions-of-new-materials-discovered-with-deep-learning), [Nature materials discovery paper](https://www.nature.com/articles/s41586-023-06735-9).
- **Fusion plasma control (DeepMind / EPFL, 2022):** learned controllers using reinforcement learning successfully stabilized plasma in tokamaks. [DeepMind fusion control blog](https://deepmind.google/blog/accelerating-fusion-science-through-learned-plasma-control).
- **AI-assisted formal verification (2023–2026):** integration of LLMs and theorem provers (Lean, Coq) has enabled substantial reductions in manual proof effort. [Lean project](https://lean-lang.org).
- **Multi-agent orchestration (2025–2026):** emergent multi-agent orchestration systems coordinate modular AI agents to execute complex workflows. [RTInsights analysis](https://www.rtinsights.com/if-2025-was-the-year-of-ai-agents-2026-will-be-the-year-of-multi-agent-systems).

## 3. Strategic claims

### A. Each cognitive-automation wave raises the floor; the frontier moves—work does not disappear

Across calculators → compilers → search → LLMs → AI-for-science, routine generation costs fall and human attention migrates to higher complexity tasks (design exploration, systems integration, synthesis, validation). Hamming and Engelbart both argue that new tools redefine which problems are worth attacking; Brooks clarifies that tools reduce accidental complexity but leave essential complexity to be addressed.

### B. Trust infrastructure is the load-bearing primitive of the current wave

As generation gets cheap, verification and provenance at scale become the binding constraints. When an LLM or multi-agent pipeline can produce thousands or millions of candidate artifacts or experimental plans, the central question is "can we trust and verify these outputs?" The answer requires attestation, auditable provenance, human-machine separation-of-duty, and producer accountability.

Examples in practice: RegTech/Reg-AI platforms (DXC Regulatory AI Engine, Infosys Autonomous Compliance Officer, ComplianceAI by Accure) demonstrate codification of regulations into machine-actionable forms and auditable trails. [DXC Regulatory AI Engine](https://dxc.com/content/dam/dxc/projects/dxc-com/us/pdfs/about-us/partner-ecosystem/aws/DXC%20Regulatory%20AI%20Engine.pdf), [Infosys Autonomous Compliance Officer](https://www.infosys.com/iki/techcompass/agentic-ai-autonomous-compliance-officer.html).

Brittleness as a surfaced safety signal: rather than hiding brittleness, modern trust infrastructure exposes brittleness through telemetry, anomaly detection, tamper-evident time-stamping, and multi-party attestations so that failures become observable events with provenance for post-mortem and prevention. [IETF Verifiable AI Provenance draft (VAP)](https://datatracker.ietf.org/doc/html/draft-kamimura-vap-framework-00.html).

### C. The complaint "too complex / too brittle / too hard to maintain" is a category error

Floor economics optimizes for minimal friction and acceptable ambiguity; frontier systems require high assurance. On the floor, friction is a cost to be minimized; at the frontier, the cost of silent acceptance (undetected errors, fraud, irreproducible science, regulatory violations) can be unbounded.

Legal analogue: courts and practitioners treat machine evidence as credibility-dependent conveyances rather than mere physical artifacts—complexity here requires authentication, design disclosure, and attested provenance rather than rejection for being complex. [Yale Law Journal, "Machine Testimony"](https://yalelawjournal.org/article/machine-testimony). Machine-witnessed proceedings and tamper-evident evidence platforms show how legal admissibility is engineered through timestamps, human verification gates, and audit trails—not by "simplifying" the evidence away.

### D. Investment in the floor (rigorous trust primitives) pays for itself at the frontier

Historical precedents: calculators, compilers, search engines required foundational investments that looked like overhead to contemporaries (training, standards, tooling), yet those investments enabled nuclear and aerospace engineering, modern OSs and networks, and global synthesis work, respectively. The same lever applies today.

Concrete trust primitives and paths to frontier utility:

- Cryptographic provenance and tamper-evident logging: VAP and related SCITT/RATS approaches.
- Autonomous compliance engines: Reg-AI vendors demonstrate codification of textual regulations.
- Machine-witnessed legal artifacts: court-admissible transcription with word-level timestamps; secure digital evidence platforms.
- Scientific reproducibility platforms: Code Ocean's Compute Capsules, RO-Crate provenance packaging, MLflow model registries.

## 4. Practical anatomy of the trust primitives

- **Provenance, attestation, and completeness:** machine-readable provenance (RO-Crate, MLflow lineage) plus cryptographic anchoring (RFC3161 time stamping, hash anchoring) and supply-chain transparency.
- **Separation-of-duty and multi-party attestations:** signed, ordered logs; multi-sig attestations; notarized human-review gates.
- **Brittleness surfacing and telemetry:** instrument models and agents to emit structured failure signals.
- **Legal and regulatory alignment:** notarization, certified human verification, immutable audit trails.
- **Scientific reproducibility and experiment pipeline design:** package code, data, environment, metadata, and provenance into capsules or crates; connect model outputs to registered, versioned experiments; combine with formal verification (Lean/Coq) where applicable.

## 5. Closing substantive note

The archival and contemporary record—from the calculator's dissolution of tedious arithmetic, through compilers that unlocked systems software, to search that collapsed retrieval friction and LLMs that collapse routine authoring—shows a consistent mechanism: lowering the cost of routine cognitive labor reallocates human attention to harder problems and shifts the bottleneck to verification, governance, and synthesis. In the current wave, trust infrastructure (cryptographic provenance, multi-party attestations, legal-grade logging, lineage and reproducibility frameworks) is not optional hygiene; it is the load-bearing architecture that transforms cheap machine generation into legally and scientifically usable knowledge.

**Substantive operational takeaway:** build trust infrastructure as first-class plumbing—cryptographic provenance, deterministic logs, multi-party attestations, and reproducible experiment packaging—and the outputs of LLMs and multi-agent scientific pipelines cease to be speculative drafts and instead become auditable, legally and scientifically actionable artifacts that shift the frontier in predictable, measurable ways.

## Citation cluster (selected primary sources)

- Engelbart "Augmenting Human Intellect" (1962): <https://dougengelbart.org/library/AHI-Framework>
- Hamming "You and Your Research": <https://www.cs.virginia.edu/~robins/YouAndYourResearch.html>
- Brooks "No Silver Bullet": <https://www.cs.unc.edu/techreports/86-020.pdf>
- Backus FORTRAN paper (1957): <https://archive.computerhistory.org/resources/text/Fortran/102663113.05.01.acc.pdf>
- Dijkstra "Go To Considered Harmful": <https://homepages.cwi.nl/~storm/teaching/reader/Dijkstra68.pdf>
- Karpathy Software 2.0: <https://karpathy.github.io/software-2/>
- Sutton "The Bitter Lesson": <http://www.incompleteideas.net/IncIdeas/BitterLesson.html>
- Brynjolfsson J-curve: <https://www.nber.org/papers/w28254>
- AlphaFold (2021): <https://www.nature.com/articles/s41586-021-03819-2>
- DeepMind materials discovery: <https://www.nature.com/articles/s41586-023-06735-9>
- Yale Law Journal "Machine Testimony": <https://yalelawjournal.org/article/machine-testimony>
- IETF Verifiable AI Provenance (VAP) draft: <https://datatracker.ietf.org/doc/html/draft-kamimura-vap-framework-00.html>
- RO-Crate provenance: <https://www.researchobject.org/ro-crate/specification/1.1/provenance.html>
- MLflow Model Registry: <https://mlflow.org/docs/latest/ml/model-registry>
- Code Ocean: <https://codeocean.com/product>
- Jevons paradox in cloud computing: <https://arxiv.org/html/2411.11540v1>
