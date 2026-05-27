# Exa Deep Researcher report — IJB primitives prior art

Model: `exa-research-pro`. Cost: $1.16. Searches: 36. Pages crawled: ~95.
Research ID: `r_01ks6fpjaqrsh8e4dz6y7tkx8j` (2026-05-21).

Prompt: comparison of a six-primitive ontology (thing/scope/path/observed/
constraint/time) against BFO, DOLCE, SUMO, UFO, Bunge-Wand-Weber, FCO-IM,
NIAM, ORM, situation calculus, event calculus, ArchiMate, ARIS, REA, W3C PROV,
TOVE, Enterprise Ontology (Uschold), Cyc upper ontology.

---

## Six-primitive meta-ontology (design summary)

- Primitives (as-proposed): thing, scope, path, observed, constraint, time.
- Class markers: structural vs instance; attribute-vocabulary marker:
  structural | policy | observed.

Immediate reading of these primitives for the analysis below:

- **thing**: intended as the primary entity/individual category (objects,
  resources, records) used for structural modeling.
- **scope**: a context or bounding construct (could be used for grouping,
  namespace, role-like scoping).
- **path**: intended to represent movement, sequence, or process-like
  trajectories.
- **observed**: intended to capture measured or recorded facts/events/
  observations.
- **constraint**: first-class object representing integrity rules, policies,
  obligations, or structural constraints.
- **time**: temporal primitive.

## Comparison with established frameworks

For each framework: (a) primitives; (b) documented category-error warnings;
(c) which warnings transfer if the six-primitive system conflates "thing"
with "observed" and treats "constraint" as first-class; (d) canonical
reference.

### 1) Basic Formal Ontology (BFO)

**(a)** BFO distinguishes continuants (entities that persist through time),
occurrents (processes/events that unfold in time), dependent entities
(qualities, roles), independent entities, and foundational mereological/
topological primitives that underpin part/whole and boundary relations
([Smith FOIS 1998](http://ontology.buffalo.edu/smith/articles/fois1998.pdf);
[BFO/PROV mapping](https://arxiv.org/abs/2408.03866)).

**(b)** BFO consistently warns against conflating continuants (endurants)
with occurrents (perdurants/processes) and against treating dependent
entities (qualities, roles) as independent things.

**(c)** If the six-primitive model collapses processes/events into a single
"path" primitive, it directly violates BFO's key insistence on the
continuant/occurrent distinction; category errors flagged by BFO (treating
processes as things or vice versa) will apply and lead to representational
confusion about persistence, identity over time, and mereological relations.
Treating roles/qualities as mere attributes inside "thing" or as arbitrary
scopes will reproduce BFO-type category errors about dependent entities.

**(d)** Smith et al., *Basic Concepts of Formal Ontology* (FOIS 1998).

### 2) DOLCE

**(a)** Top categories: endurants (things wholly present at times),
perdurants (events/processes extended in time), qualities (properties or
attributes that inhere in endurants/perdurants), abstracts; participation
relations connecting endurants and perdurants
([Masolo et al., WonderWeb D18 2003](http://www.loa.istc.cnr.it/old/Papers/D18.pdf);
[DOLCE overview](https://arxiv.org/pdf/2308.01597)).

**(b)** DOLCE is explicitly built to avoid confusions among endurants/
perdurants and between qualities and objects; omissions or conflations of
these distinctions are considered ontologically unstable.

**(c)** Collapsing events/processes into "path" removes the perdurant
category DOLCE preserves — leading to inability to model participation
relations and temporal parts correctly. Making "observed" a primitive
conflates observation reports (dependent, relational) with the underlying
endurant/perdurant distinctions. DOLCE's emphasis on qualities implies that
an absent explicit quality/qua-entity primitive in the six-primitive model
will force ad hoc attachment of attributes (e.g., `valid`, `redacted`) to
things or observations, producing category errors DOLCE warns against.

**(d)** Masolo et al., WonderWeb Deliverable D18 (2003); Borgo et al., DOLCE
overview.

### 3) SUMO (Suggested Upper Merged Ontology)

**(a)** Top categories: Entity, Physical, Object, Process, Abstract,
Quantity, Attribute, Relation, Set/Class; SUMO documentation and pitfall
guidance highlight formal distinctions among instances, classes, processes,
and attributes (implemented in SUO-KIF) ([Ontology Portal](https://www.ontologyportal.org);
[SUMO Pitfalls](https://ontologyportal.org/Pitfalls.html)).

**(b)** Warns explicitly about confusing instance-of with subclass-of,
confusing part-of with subclassing, modeling events incorrectly as relations
(instead of reified occurrents), and modeling roles as classes (roles change
over time).

**(c)** The six-primitive model's conflation of things and observed facts,
and lack of explicit reified relator/role primitives, increases risk of
SUMO-style errors: e.g., treating observations as classes or instances
improperly, failing to distinguish event instances from relations, and using
constraint objects where subclass/instance distinctions should be used.

**(d)** SUMO portal; Niles & Pease FOIS (SUMO background).

### 4) UFO (Unified Foundational Ontology, Guizzardi)

**(a)** Primitives include Kinds/subkinds (rigid types), Roles (anti-rigid
types), Relators (reified relations that mediate between entities),
Particularized properties (tropes/modes), Events (occurrents), part-whole
relations, and taxonomic structures; UFO organizes these into micro-theories
to support conceptual modeling (OntoUML)
([UFO Applied Ontology](https://philarchive.org/rec/PORUUF);
[UFO Story](https://inf.ufes.br/~gguizzardi/UFO-Story.pdf)).

**(b)** UFO explicitly warns that omitting relators and particularized
properties leads to severe modeling failures (roles and relators cannot be
shoehorned into simple attributes), and that confusing roles (anti-rigid)
with kinds (rigid) is a common anti-pattern.

**(c)** The six-primitive system's lack of a relator/role primitive and the
suggestion to use "scope" as a surrogate for role will replicate UFO
warnings: roles encoded as scope will lose essential semantics (anti-rigidity,
temporal dependence, ability to be the bearer of relationships), relators
(which can bear properties and mediate relationships) cannot be modelled
faithfully as mere scopes or attributes. Treating constraints as first-class
objects will also interact poorly with UFO's particularized properties:
constraints might be mistaken for relators or tropes, creating category
confusion.

**(d)** Guizzardi et al., "UFO: Unified Foundational Ontology"
(Applied Ontology 2022).

### 5) Bunge–Wand–Weber (BWW) ontology

**(a)** Based on Mario Bunge's ontology and adapted by Wand & Weber for IS
modeling: things (substantial entities), properties, states, events (changes
of state), classes/kinds, compositions/associations, and representational
categories that map reality to information system constructs
([Kiwelekar & Joshi metamodel](https://arxiv.org/abs/1004.3640)).

**(b)** Warns against conflating things with their representations
(schemas/attributes), confusing states with events, and misplacing properties
as independent things.

**(c)** Conflation of "thing" and "observed" directly reproduces BWW
warnings: mixing the real-world entity and the observation/measurement/record
leads to errors in state/event modeling, misassignment of properties, and
confusion between the represented domain and its information-system encoding.
Treating "constraint" as first-class without clarifying whether it belongs to
the representational layer (schema, integrity constraint) or the domain
layer (laws, business rules) risks the BWW-style category errors about
representations vs. ontological things.

**(d)** Kiwelekar & Joshi, "An Object-Oriented Metamodel for Bunge-Wand-Weber
Ontology" (arXiv:1004.3640).

### 6) Fact-based modeling family (FCO-IM / NIAM / ORM)

**(a)** Fact types (elementary facts), object types, roles (objects play
roles in fact types), value types, objectified fact types (reified facts),
uniqueness and other constraints specified explicitly on fact types; FCO-IM
emphasizes natural language fact expressions and explicit constraints
([FCO-IM overview](https://en.wikipedia.org/wiki/FCO-IM)).

**(b)** Failing to model elementary facts and constraints explicitly leads
to misunderstandings; constraints must be modeled where they belong (as
uniqueness, mandatory, subset, frequency, etc.) and factification avoids
category errors that come from prematurely turning facts into attributes or
entities.

**(c)** Fact-based modeling shows that making "constraint" a first-class
object can be consistent if constraints are attached in the fact space;
however, the danger is conflating constraint types (structural integrity vs
policy/authorization vs observed validation) when the six-primitive design
collapses attribute vocabulary markers into a single "constraint" category.
Additionally, replacing roles with "scope" will lose the role semantics and
lead to the same modeling anti-patterns these methodologies warn about.

**(d)** FCO-IM and ORM literature.

### 7) Situation Calculus

**(a)** Situations (histories of actions), actions, fluents (state
properties parameterized by situation), objects, and formal formulae
([McCarthy](http://www-formal.stanford.edu/jmc/sitcalc.pdf)).

**(b)** Classical warnings include the **frame problem** (how to represent
what does not change when an action occurs) and the **qualification
problem** (exhaustively listing preconditions).

**(c)** Collapsing events/processes into a "path" primitive will reintroduce
frame/qualification-style problems unless the model provides a robust
successor-state or inertia handling mechanism. If "observed" is made
primitive rather than a relation between thing and time (or situation), the
logic for what persists and how observations map to fluents/situations is
lost.

**(d)** McCarthy; Reiter's formalization.

### 8) Event Calculus

**(a)** Events, fluents (properties varying over time), time points, and
narratives (sequences of events used as input); originally Kowalski & Sergot
1986 and elaborated by Miller & Shanahan
([Kowalski & Sergot 1986](https://link.springer.com/article/10.1007/BF03037383)).

**(b)** Event Calculus literature highlights complexity in dealing with
high-frequency or concurrent events, the need for complete/partial narratives
(narrative completeness), and careful distinction of primitive vs derived
fluents.

**(c)** If "path" subsumes events and the model does not provide explicit
event reification and careful narrative treatment, concurrency and temporal
ordering problems will arise; making "observed" primitive (instead of
relation) reduces the ability to represent narratives cleanly and risks
losing the fluent/event separation Event Calculus preserves.

**(d)** Kowalski & Sergot, "A logic-based calculus of events" (1986).

### 9) ArchiMate (The Open Group)

**(a)** Active structure elements (actors, roles, components), behavior
elements (processes, functions), passive structure elements (data objects),
motivation elements (goal, requirement, constraint), strategy elements,
layered viewpoints
([ArchiMate 3.1 spec](https://www.opengroup.org/sites/default/files/docs/downloads/n190p_5.pdf)).

**(b)** Warns against misuse of layers (mixing business/application/
technology elements incorrectly), modeling behavior as a passive element,
and improper use of motivation elements (confusing policy/constraint vs
requirement).

**(c)** ArchiMate's explicit separation of motivation/constraint elements
from structural elements shows that merging structural constraints and
policy constraints into a single "constraint" primitive loses stakeholder
semantics and traceability. ArchiMate also treats roles explicitly;
encoding roles as "scope" would likely produce stakeholder/semantic misuse
warned in ArchiMate guidance.

**(d)** ArchiMate 3.1 specification.

### 10) ARIS (Architecture of Integrated Information Systems)

**(a)** Function, organization, data, product/service and process views;
primitives include function, event (control/event), organizational unit,
data object, connectors (AND/OR/XOR), process, and risk
([ARIS Method Manual](https://docs.aris.com/10.0.27.0/yaa-method-guide/en/Method-Manual.pdf)).

**(b)** Warns about confusing events and control flow, misuse of connectors,
overloading elements semantically (using event as activity), and mixing
views improperly which results in inconsistent models.

**(c)** If "path" is used as a catch-all for both process sequences and
events, ARIS-style confusions between event and activity/control flow will
arise; treating "observed" as primitive without distinguishing whether an
observation is an event, data object, or function output will create the
same mixing of views ARIS warns against.

**(d)** ARIS Method Manual.

### 11) REA (Resource-Event-Agent)

**(a)** Resources (economic resources), Events (economic events changing
resource stocks), Agents (actors), Duality (paired events reflecting
double-entry semantics), Stockflow (flows linking events and resources),
Commitments/participation relations; formalized in ISO 15944-4
([McCarthy 1982](https://www.valueflo.ws/linked-docs/REA-Ontology_ISO-15944-4--BillMcCarthy_20131107.pdf);
[ISO 15944-4](https://www.iso.org/standard/40348.html)).

**(b)** Stresses strict separation of commitments versus actual events,
correct classification of stockflows vs events, and adherence to duality;
misclassifying flows or conflating commitments and events produces incorrect
accounting semantics.

**(c)** Conflating "thing" (resource) with "observed" (recorded event/state)
undermines REA's separation of resources and the economic events that change
them. Treating constraints as first-class without clarifying whether they
are accounting rules, legal policies, or schema constraints will obfuscate
enforcement of duality and stockflow semantics.

**(d)** McCarthy, "The REA Accounting Model" (1982); ISO/IEC 15944-4.

### 12) W3C PROV (PROV-DM / PROV-O)

**(a)** Entity (things), Activity (occurrences over time), Agent (responsible
actors), and relations: Generation, Usage, Derivation, Attribution,
Association, Start/End, Invalidation; PROV stresses temporal constraints and
provenance graph structure
([PROV-Overview](https://www.w3.org/TR/prov-overview/),
[PROV-O](https://www.w3.org/TR/prov-o/),
[PROV-DM](https://www.w3.org/TR/prov-dm/)).

**(b)** Cautions against confusing Activity (process) with Entity (artifact),
warns about temporal ordering constraints (uses/generation must obey time
bounds), and calls out risks of circularity when modeling provenance of
provenance or using bundles incorrectly.

**(c)** Making "observed" a primitive instead of modeling it as a relation
(e.g., an Activity that generated an Entity at a Time, or a Usage relation)
contradicts PROV's relational approach; PROV's admonitions about Activity vs
Entity ambiguity and temporal constraints show that a primitive "observed"
will likely break provenance reasoning unless it is explicitly tied to
Activity/Entity/Agent/time relations. Treating "constraint" as a top-level
object must be carefully scoped: provenance constraints are typically
modeled as annotations or higher-order relations rather than conflated with
structural entities.

**(d)** W3C PROV-Overview, PROV-O, PROV-DM.

## Synthesis: top failure modes for the six-primitive design

### A. Collapsing process/event into "path" — loss of the perdurant distinction

BFO and DOLCE both make a hard ontological split between continuants
(things/endurants) and occurrents/perdurants (processes, events). Collapsing
those into a single "path" primitive eliminates the ontology's ability to
represent temporal parts, participation relations, and different identity
criteria for processes vs things, producing category errors such as treating
an event as an object with persistent identity. Situation Calculus and Event
Calculus both model events and states explicitly to handle frame/
qualification and narrative completeness; flattening events into "path" will
reintroduce frame/qualification difficulties unless the model supplies
equivalent successor-state or inertia axioms.

### B. Conflating policy constraints with structural constraints under a single "constraint" primitive

ArchiMate explicitly separates motivation (requirements, constraints,
principles) from structural elements and models constraints as motivation
artifacts with different semantics than integrity constraints on data or
type systems. REA and ORM/FCO-IM treat constraints as semantic facts
attached to fact types or transaction rules, not as autonomous domain
entities. If the six-primitive model treats every constraint (structural
uniqueness, integrity, regulatory policy, SLA, observed validation rule) as
a single kind of object, systems and tooling cannot distinguish enforcement
mechanism, scope, or lifecycle.

### C. Making "observed" a primitive rather than a relation

W3C PROV models provenance by relating Entities, Activities, Agents, and
time: observations are typically represented by an Activity (observation
process) that generated an Entity (observation artifact) at a time and may
be attributed to an Agent. Treating "observed" as a primitive collapses this
relational semantics and obscures provenance temporal constraints.
Consequences: loss of provenance fidelity (who observed what, when, under
what method); inability to encode uncertainty/quality metadata as derived
relations rather than atomic things.

### D. Absence of explicit "role" or "relator" primitive — encoding roles as scopes

UFO stresses the importance of relators (reified relationships) and roles as
ontological primitives with temporal/anti-rigid behavior; encoding roles as
a generic "scope" discards anti-rigidity, status dependencies, and the
capacity for relators to be subjects of relations and bear properties.
Consequences: loss of modeling ability to express role-dependent constraints,
to attach attributes to relations (e.g., terms of a contract as properties
of a relator), and to reason about role lifecycle.

### E. Absence of a "quality" / "qua entity" primitive

DOLCE's qualities (and UFO's particularized properties/tropes) are
first-class in their ontologies to represent attribute values and their
dependence on bearers; lacking such a primitive forces modelers to either
attach attributes to things (leading to overloading) or to attach them to
observations (confounding observational metadata with domain attributes).
Difficulty representing quality provenance (who declared validity),
time-varying attribute values, or redaction as an operation on an entity
with its own provenance metadata.

## Practical implications

- **Reasoners and validation tools:** Without explicit perdurant/endurant
  separation and relator/role primitives, automated reasoning (temporal
  reasoning, identity checking, provenance validation) will be error-prone.
  Situation/Event calculi, PROV, and UFO provide patterns necessary to
  support automated inference about change, provenance, and role lifecycle.

- **Semantic interoperability and reuse:** SUMO, DOLCE, and BFO warn that
  ontological promiscuity (creating undifferentiated primitives) reduces
  reuse and mapping to external ontologies; a six-primitive model that
  collapses important distinctions will be harder to interoperate with
  established domain ontologies.

- **Auditability and regulatory semantics:** REA/ISO and PROV emphasize
  precise modeling of economic events, commitments, and provenance;
  conflating resources with observations or treating constraints as opaque
  objects will undermine audit trails and legal interpretability required
  by accounting and compliance models.

## Concluding takeaway

The literature converges on a common theme: ontologies and modeling
frameworks succeed when they preserve minimal but critical ontological
distinctions (endurant vs perdurant; entity vs activity; relator/role vs
attribute; quality vs bearer; constraint type vs structural type) and when
constraints/observations are modeled with explicit relations and provenance
rather than as undifferentiated primitives.

The six-primitive design will encounter predictable and documented failure
modes unless it:

1. Separates perdurant/process semantics from structural things (adopt
   successional/state semantics or explicit event reification patterned on
   Situation/Event Calculi);
2. Distinguishes constraint subtypes (structural vs policy vs observed
   validation) and binds them to the appropriate modeling layer;
3. Models observations as relations (Activity/Generation/Usage or
   situation/fluents) to preserve provenance and temporal constraints;
4. Introduces explicit relator/role and quality primitives or a clear
   mapping to them so that role lifecycle, reified relationships, and
   attribute provenance are representable.
