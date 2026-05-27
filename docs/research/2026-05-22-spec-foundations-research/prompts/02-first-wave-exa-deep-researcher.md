# First-wave Exa Deep Researcher prompt

Run via `mcp__exa__deep_researcher_start` with `model: exa-research-pro`.

Research ID: `r_01ks6fpjaqrsh8e4dz6y7tkx8j` (2026-05-21).
Cost: $1.16. Searches: 36. Pages crawled: ~95.

## Prompt (verbatim)

```
Research prior art and known challenges for a six-primitive meta-ontology used as the foundation of a software-engineering specification. The six primitives are: thing, scope, path, observed, constraint, time — paired with class markers (structural vs instance, and an attribute-vocabulary marker structural|policy|observed). Compare and contrast against established upper ontologies and modeling frameworks:

- BFO (Basic Formal Ontology), continuant vs occurrent distinction
- DOLCE, endurants/perdurants/qualities/abstracts
- SUMO
- UFO (Unified Foundational Ontology, Guizzardi)
- Bunge-Wand-Weber ontology for IS modeling
- FCO-IM / NIAM / ORM (fact-based modeling)
- Situation Calculus and Event Calculus
- ArchiMate (active/passive/behavior + motivation + strategy layers)
- ARIS (Architecture of Integrated Information Systems)
- REA (Resource-Event-Agent, McCarthy 1982; ISO 15944-4)
- W3C PROV (Entity / Activity / Agent)
- TOVE enterprise ontology, Enterprise Ontology (Uschold), Cyc upper ontology

For EACH framework: (a) what its primitive set is, (b) what category errors or modeling failures the framework warns about, (c) which of those warnings transfer to a six-primitive system that conflates "things" with "observed facts" and treats "constraints" as first-class objects, and (d) cite the canonical reference (paper, standard, W3C/ISO document).

Then identify the top failure modes specifically for THIS six-primitive design:
- collapsing process/event into "path" — does this lose the perdurant distinction BFO/DOLCE preserve?
- conflating policy constraints with structural constraints under a single "constraint" primitive
- making "observed" a primitive rather than a relation between thing and time — how does PROV-O handle this differently?
- absence of an explicit "role" or "relator" primitive (UFO) — what breaks when roles are encoded as scopes?
- absence of a "quality"/"qua entity" primitive — how do attributes like "valid", "complete", "redacted" attach?

Deliver: a structured report (~2500 words), with named citations and URLs to the canonical references.
```
