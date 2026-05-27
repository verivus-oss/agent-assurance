# Frequently Asked Questions

## Conceptual Questions

### Q: Is this a modeling framework?

No. This is a projection framework.

Modeling implies interpretation and abstraction. This framework projects facts into space without interpretation.

### Q: How is this different from enterprise architecture frameworks?

Enterprise architecture frameworks (TOGAF, Zachman, etc.) create abstraction layers and meta-models.

This framework has six primitives and refuses to abstract. It projects reality as described, not as interpreted.

### Q: Can I use this with existing notation systems?

Only if the notation system maps directly to the six primitives without introducing concepts.

Most notation systems (UML, BPMN, ArchiMate) introduce domain concepts and implied semantics. Those do not fit this framework.

### Q: What about industry-specific models?

No. Industry-specific models introduce domain concepts.

This framework works across all domains precisely because it refuses domain-specific abstraction.

### Q: Is this just a graph database?

The descriptive layer could be stored in a graph database, but the framework is not about storage.

It is about maintaining separation between facts and their spatial projection.

### Q: How does this relate to digital twins?

Digital twins typically try to create a "mirror" of reality that can be simulated.

This framework makes no claims about simulation. It only projects observed facts into navigable space.

## Practical Questions

### Q: Where do I start?

1. Read docs/getting-started.md
2. Pick one real scenario from your environment
3. Describe it using only the six primitives
4. Project one single path across scopes over time

Do not try to visualize your entire organization on day one.

### Q: What tools should I use?

The framework is tool-agnostic. The six primitives are independent of visualization technology.

Start with written descriptions. Technology choices come later.

### Q: How do I handle systems I don't have visibility into?

You show absence.

If you cannot observe what happens inside a system, that system appears as a thing with paths entering and exiting, but no internal traversal.

Absence of observation is information.

### Q: How do I model uncertainty?

You do not model it. You show what was observed and when.

If something was observed inconsistently, the observations show that inconsistency.

### Q: What about future state or planned changes?

The framework describes what exists and what was observed.

Future plans exist as things (documents, decisions, commitments) with their own observations.

Do not project hypothetical futures. Project facts about plans.

### Q: How do I show strategy?

You do not show strategy. You show what exists, how it moves, and what was observed.

If strategic decisions result in observable changes, those changes appear when observed.

### Q: Can I use this for planning?

The framework shows you what exists now and what existed in the past based on observation.

Planning happens by examining current reality and deciding what to change. The framework helps by making current reality explicit.

## Technical Questions

### Q: How do I handle scale?

Distance determines detail level.

Zoom out: fewer objects visible, paths simplified, scopes emphasized
Zoom in: more objects visible, paths detailed, observations prominent

The description contains all facts. The projection shows what fits at current distance.

### Q: What about performance with large datasets?

The descriptive layer is queryable. You do not load everything into visualization.

The projection queries for facts relevant to current view, time range, and focus.

### Q: How do I version this?

The description can be versioned like any factual dataset.

Each projection is deterministic from the description, so you version the description, not the visualizations.

### Q: Can multiple people edit the description simultaneously?

That is a technical implementation question outside the framework scope.

The framework requires that everyone projects from the same facts. How you manage collaborative fact-editing is an implementation detail.

## Philosophical Questions

### Q: Isn't "just facts" impossible? Doesn't observation require interpretation?

Observation does require framing, but there is a difference between:

"System response time exceeded 5 seconds at 09:23" (observed)

and

"System is too slow due to poor architecture" (interpreted)

The framework captures the former, not the latter.

### Q: Don't different people see different realities?

Different people care about different parts of reality.

The framework lets them view the same facts from different distances and with different emphasis, but the facts do not change.

### Q: What about subjective experience?

Subjective experience can be observed if someone reports it.

"User reported confusion with interface" is an observable thing (the report) with observable time and scope.

"Interface is confusing" is interpretation and does not belong.

### Q: Isn't this just positivism?

This framework makes no epistemological claims about ultimate truth.

It simply maintains that:
1. Organizations can agree on what was observed
2. Disagreements should be about facts, not interpretations
3. Visualizations should not introduce concepts beyond what was described

### Q: What about emergent properties?

Emergent properties appear as observations.

"Traffic pattern changed after deployment" is observable.

"System exhibits complex adaptive behavior" is interpretation unless you can point to the specific observations that demonstrate it.

## Objections

### Q: This seems too rigid. Can't we add just one more concept?

No.

Every previous business visualization framework failed because "just one more concept" became hundreds of concepts.

The six primitives are complete. Adding more collapses the framework.

### Q: This seems limiting. How do I express X?

If you cannot express X using the six primitives, either:
1. X is interpretation, not fact
2. You have not yet found the right factual grounding

Most concepts that feel "unexpressible" are interpretation that should not be visualized.

### Q: My industry is different. This won't work for us.

Every industry says this.

Then they try to describe one scenario using the six primitives and discover they can.

The primitives are domain-independent by design.

### Q: This removes all the useful context and meaning.

Context appears as scopes. Meaning emerges from relationships between facts.

What this removes is interpretation masquerading as visualization.

### Q: Our executives need simplified views.

Executives get simplified views by increasing distance, not by removing facts.

When you remove facts, you create lies-by-omission. When you increase distance, you show the same reality with less detail.

### Q: This is just academic. It won't work in real organizations.

The framework exists precisely because traditional approaches fail in real organizations.

Multiple contradictory diagrams, endless alignment meetings, slides becoming source of truth—these are the real-world failures this framework prevents.

## Misconceptions

### Misconception: "This is a new diagramming notation"

No. This is a framework for projecting facts into space without introducing notation-specific concepts.

### Misconception: "This replaces architecture documentation"

No. This complements factual documentation by making it navigable in space.

### Misconception: "This is a data visualization tool"

Data visualization typically finds patterns in data. This framework projects organizational reality into space.

Some of that reality is data, but much is not.

### Misconception: "This is for technical people only"

The framework is for anyone who needs to understand organizational reality without translation errors.

Technical people, executives, operators, auditors—all can view the same projection.

### Misconception: "This eliminates the need for judgment"

This framework makes facts explicit so judgment can be applied to reality instead of to competing interpretations.

Judgment is still required. But now it operates on facts, not on persuasive diagrams.

## Questions This Framework Cannot Answer

### "Why did this happen?"

The framework shows what happened and when. Causality requires controlled experiments.

You can observe correlation. You cannot visualize causation without experimental evidence.

### "What should we do?"

The framework shows what exists and what was observed. Decisions about action require judgment.

It can make current reality explicit, but it cannot prescribe action.

### "What will happen if...?"

The framework does not simulate or predict. It projects observed reality.

Scenario planning happens outside the framework, though you can describe scenarios as things with their own observations.

### "Is this good or bad?"

The framework does not evaluate. It projects.

"Response time exceeded 5 seconds" is observable. "5 seconds is unacceptable" is judgment.

### "How do we optimize this?"

Optimization requires objectives and constraints. The framework can show current constraints and observed behavior, but optimization decisions are separate.

## Final Question

### Q: If I still don't understand, what should I do?

1. Read docs/why-this-matters.md to understand the problem this solves
2. Read docs/core-specification.md to understand the mapping
3. Read docs/getting-started.md and try describing one scenario
4. Try to project that scenario without introducing concepts
5. Check if someone can point at your projection and name the primitives

If you still cannot make it work, you may be trying to visualize interpretation instead of facts.

The framework is simple, but it is not easy. It requires discipline to avoid the collapse back into traditional diagramming.
