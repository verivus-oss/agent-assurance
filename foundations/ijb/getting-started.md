# Getting Started with It's Just Business

A practical guide to applying the framework without collapsing back into diagrams.

## Step 0: Check Your Mindset

Before you begin, internalize this:

**You are not visualizing the business. You are projecting a description into space.**

If you think you are creating a model, stop. You are creating a projection of facts.

## Step 1: Describe Before You Visualize

Do NOT open a drawing tool first. Do NOT sketch architecture diagrams.

Start with the six primitives as facts:

### Capture Things
List what exists. Nothing more.

```
# Things that exist:
- Customer Service System
- Order Database
- Support Agent (Sarah)
- Support Agent (Mike)
- Ticket #4521
- Customer (Acme Corp)
```

### Capture Scopes
List contexts where things exist.

```
# Scopes:
- Internal systems
- External access
- US region
- EU region
- Production environment
- Development environment
```

### Capture Paths
List what connects things and what moves along them.

```
# Paths:
- Ticket routes from Customer → Support Agent
- Data flows from Customer Service System → Order Database
- Escalations route from Support Agent → Engineering Team
```

### Capture Observed
List what was actually witnessed.

```
# Observed:
- Ticket #4521 created at 2024-01-15T09:23:00Z
- Ticket #4521 assigned to Sarah at 2024-01-15T09:25:00Z
- Ticket #4521 escalated at 2024-01-15T11:47:00Z
- Expected assignment time: < 5 minutes (constraint)
- Actual assignment time: 2 minutes (observed)
- Expected escalation time: < 30 minutes (constraint)
- Actual escalation time: 2 hours 22 minutes (observed late)
```

### Capture Constraints
List what restricts movement.

```
# Constraints:
- Only verified agents can access Customer Service System
- Escalations require manager approval during business hours
- EU customer data cannot route through US systems
- Maximum 50 active tickets per agent
```

### Capture Time
Establish when things happened and in what order.

```
# Timeline:
09:23 - Ticket created
09:25 - Assigned to Sarah
09:30 - Sarah begins work
11:15 - Sarah requests escalation
11:47 - Manager approves escalation
11:47 - Ticket escalated to Engineering
```

## Step 2: Verify Factual Grounding

Before projecting anything into space, answer these questions:

1. **Can you point to where each fact was observed?**
   - If you wrote "System is overloaded", where was that observed?
   - If you cannot point to a log, metric, or human observation, remove it.

2. **Did you introduce any concepts beyond the six primitives?**
   - If you wrote "strategic alignment" or "organizational culture", remove it.
   - Only things, scopes, paths, observed, constraints, and time.

3. **Did you make assumptions about causality?**
   - If you wrote "System overload caused by insufficient capacity", remove the "caused by".
   - You can write: "System overload observed" and "Capacity constraint exists" but not causality.

4. **Is time explicit?**
   - Every observation should have a timestamp.
   - Every path should have traversal timing.

## Step 3: Choose Your First Projection

Do NOT try to visualize everything at once.

Start with a single path traversal:

**"Follow one path across scopes over time."**

Example:
- Path: Ticket #4521 from creation → assignment → escalation
- Scopes: Customer space → Internal system → Support team → Engineering team
- Time: 09:23 → 09:25 → 11:47

## Step 4: Map Primitives to Space

Now, and only now, consider spatial representation.

### Things → Objects
- Ticket #4521 → object
- Support Agent Sarah → object
- Customer Service System → object

### Scopes → Spatial Grouping
- Customer space → one plane
- Internal system → another plane
- Support team → layer or color field
- Engineering team → separate layer or color field

### Paths → Routed Connections
- Creation to assignment → routed line with direction
- Assignment to escalation → another routed line

### Observed → Overlays
- Assignment at 09:25 → timestamp marker
- Escalation at 11:47 → timestamp marker
- Delay (expected < 30min, actual 2h 22min) → delayed highlight

### Constraints → Affordances
- Manager approval required → gate on escalation path
- Verified agent only → conditional access to system

### Time → Dimension
- Scrub from 09:23 → 11:47
- Path appears as time progresses
- Delay becomes visible when comparing expected vs actual

## Step 5: Reality Check

Point at your visualization and ask: "What is that?"

If the answer is:
- "A ticket" → Good (thing)
- "The support team scope" → Good (scope)
- "The escalation path" → Good (path)
- "The observed delay" → Good (observed)
- "The approval constraint" → Good (constraint)
- "The timestamp" → Good (time)

If the answer is:
- "Organizational dysfunction" → Failed
- "Poor strategic alignment" → Failed
- "Team culture problem" → Failed

If you failed, go back to Step 1. You introduced interpretation.

## Step 6: Test Multiple Views

The same description should support multiple projections:

**Support Manager View:**
- Emphasize: paths, constraints, observed delays
- De-emphasize: technical system details
- Focus: bottlenecks and constraint violations

**Engineer View:**
- Emphasize: systems, technical paths, scope boundaries
- De-emphasize: individual agent assignments
- Focus: system behavior and integration points

**Executive View:**
- Emphasize: scopes, major paths, aggregate observations
- De-emphasize: individual transactions
- Focus: capacity and throughput patterns

All three views show the same facts. None introduce new concepts. Distance and emphasis change, facts do not.

## Common Mistakes

### Mistake 1: Starting with a diagram
Starting with boxes and arrows introduces bias before facts are established.

**Fix:** Write the description first. Always.

### Mistake 2: Abstracting too early
Creating meta-concepts like "service layer" or "business logic" before describing what actually exists.

**Fix:** Name actual things, not categories.

### Mistake 3: Implying causality
Drawing an arrow and calling it "causes" or "impacts" without observed evidence.

**Fix:** Arrows only represent paths where something moves. Causality requires controlled observation.

### Mistake 4: Decorative elements
Adding boxes, colors, or shapes that don't map to primitives.

**Fix:** Every visual element must answer: which primitive is this?

### Mistake 5: Time as afterthought
Building a static view and then trying to animate it.

**Fix:** Time is fundamental. If you cannot scrub time, rebuild from primitives.

## What Success Looks Like

You know this is working when:

1. **Multiple roles agree on what exists**
   - Even if they care about different parts

2. **Absence is informative**
   - "We don't observe performance in EU region" is visible

3. **Disagreements are about facts, not interpretation**
   - "Was escalation approved at 11:15 or 11:47?" not "Is this strategic?"

4. **Changes propagate automatically**
   - Update the description, all projections update

5. **No translation needed**
   - Engineer and executive discuss the same view at different distances

## Next Actions

1. Pick one real scenario from your environment
2. Describe it using only the six primitives
3. Verify every fact is observed
4. Project one single path across scopes over time
5. Test if someone else can understand it by pointing at primitives

Do not try to visualize your entire organization. Do not try to model your strategy. Do not try to explain your architecture.

Just describe one factual traversal and see if you can project it without introducing concepts.

That is the test.
