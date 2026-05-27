# Example 01: Purchase Approval Traversal

A single path following one purchase request across organizational scopes over time.

## The Scenario

A purchase request for software licenses moves through an organization's approval process.

This example demonstrates:
- One path crossing multiple scopes
- Observable delays against constraints
- Multiple views of the same facts
- No interpretation, no causality, only observation

---

## Part 1: Factual Description

### Things That Exist

```
PR-2847           # Purchase request document
Sarah Chen        # Employee who created request
Mike Rodriguez    # Department manager
Lisa Park         # Finance approver
Procurement-API   # System that processes requests
Finance-System    # System that tracks budget
Slack-Thread-947  # Communication thread
Email-Chain-4821  # Email communications
Budget-Line-D400  # Budget allocation
```

### Scopes Where Things Exist

```
Engineering Department    # Organizational scope
Management Layer         # Organizational scope
Finance Department       # Organizational scope
Internal Network        # Technical scope
SaaS Vendor Portal      # External scope
Business Hours          # Temporal scope (Mon-Fri 9am-5pm)
After Hours             # Temporal scope
US-East Region          # Geographic scope
```

### Paths That Connect Things

```
Path 1: Creation → Submission
  PR-2847 moves from Sarah Chen → Procurement-API

Path 2: Submission → Manager Review
  PR-2847 moves from Procurement-API → Mike Rodriguez
  Notification moves from Procurement-API → Slack-Thread-947

Path 3: Manager Review → Finance Review
  PR-2847 moves from Mike Rodriguez → Lisa Park
  Query moves from Mike Rodriguez → Sarah Chen (via Email-Chain-4821)
  Response moves from Sarah Chen → Mike Rodriguez (via Email-Chain-4821)
  Approval moves from Mike Rodriguez → Procurement-API

Path 4: Finance Review → Completion
  Budget check moves from Finance-System → Procurement-API
  PR-2847 moves from Lisa Park → Procurement-API
  Notification moves from Procurement-API → Sarah Chen
```

### Observations Made

```
2024-11-18T14:23:00Z - Sarah Chen created PR-2847
2024-11-18T14:24:00Z - PR-2847 submitted to Procurement-API
2024-11-18T14:24:30Z - Notification posted to Slack-Thread-947
2024-11-18T14:25:00Z - PR-2847 routed to Mike Rodriguez
2024-11-19T10:15:00Z - Mike Rodriguez opened PR-2847
2024-11-19T10:47:00Z - Mike Rodriguez sent query via Email-Chain-4821
2024-11-19T15:22:00Z - Sarah Chen responded via Email-Chain-4821
2024-11-20T09:05:00Z - Mike Rodriguez approved PR-2847
2024-11-20T09:06:00Z - PR-2847 routed to Lisa Park
2024-11-20T09:06:30Z - Budget check executed against Budget-Line-D400
2024-11-20T09:07:00Z - Budget check completed (sufficient funds)
2024-11-21T11:30:00Z - Lisa Park opened PR-2847
2024-11-21T14:45:00Z - Lisa Park approved PR-2847
2024-11-21T14:46:00Z - Notification sent to Sarah Chen
2024-11-21T14:46:00Z - PR-2847 marked complete
```

### Constraints That Apply

```
Constraint 1: PR-2847 cannot proceed to Finance without Manager approval
  Type: Sequential dependency
  Scope: Procurement-API

Constraint 2: Manager review expected within 4 business hours
  Type: Time expectation
  Scope: Engineering Department
  Observed: 19.8 hours elapsed (constraint violated)

Constraint 3: Finance approval requires Budget-Line-D400 to show sufficient funds
  Type: Budget availability
  Scope: Finance-System

Constraint 4: Finance review expected within 8 business hours
  Type: Time expectation
  Scope: Finance Department
  Observed: 29.6 hours elapsed (constraint violated)

Constraint 5: Approvals can only happen during Business Hours scope
  Type: Temporal restriction
  Scope: All approval paths

Constraint 6: PR-2847 requires justification text >50 characters
  Type: Data validation
  Scope: Procurement-API
  Observed: Satisfied (247 characters provided)
```

### Time Ordering

```
Timeline:
  T+0:00:00  (Mon 14:23) - Request created
  T+0:00:60  (Mon 14:24) - Request submitted, notification sent
  T+0:02:00  (Mon 14:25) - Routed to manager

  [19.8 hour gap - includes after-hours and overnight]

  T+19:52:00 (Tue 10:15) - Manager opened request
  T+20:24:00 (Tue 10:47) - Manager sent clarification query

  [4.6 hour gap]

  T+24:59:00 (Tue 15:22) - Employee responded

  [17.7 hour gap - includes after-hours and overnight]

  T+42:42:00 (Wed 09:05) - Manager approved
  T+42:43:00 (Wed 09:06) - Routed to finance, budget check started
  T+42:44:00 (Wed 09:07) - Budget check completed

  [26.4 hour gap - includes after-hours and overnight]

  T+69:07:00 (Thu 11:30) - Finance opened request
  T+72:22:00 (Thu 14:45) - Finance approved
  T+72:23:00 (Thu 14:46) - Request completed, notification sent

Total elapsed: 72 hours 23 minutes (3 days, 23 minutes)
Business hours elapsed: ~18 hours
```

---

## Part 2: Spatial Projection Mapping

### Things → Objects in Space

Each thing becomes an object:

```
PR-2847           → Document object (cube)
Sarah Chen        → Person object (sphere)
Mike Rodriguez    → Person object (sphere)
Lisa Park         → Person object (sphere)
Procurement-API   → System object (rectangular volume)
Finance-System    → System object (rectangular volume)
Slack-Thread-947  → Communication object (flat surface with text)
Email-Chain-4821  → Communication object (flat surface with text)
Budget-Line-D400  → Data object (small cube)
```

Visual form indicates existence only, not importance.

### Scopes → Spatial Grouping

Scopes become planes and layers:

```
Engineering Department    → Blue-tinted vertical plane (left side)
Management Layer         → Yellow horizontal band crossing both departments
Finance Department       → Green-tinted vertical plane (right side)
Internal Network        → Solid platform (base layer)
SaaS Vendor Portal      → Translucent platform (elevated, separate)
Business Hours          → Lit environment
After Hours             → Dimmed environment with time indicator
```

Objects appear in multiple scopes without duplication:
- Mike Rodriguez appears in both Engineering and Management scopes
- PR-2847 traverses multiple scopes but remains the same object

### Paths → Routed Connections

Paths become directed flows:

```
Creation → Submission
  Line from Sarah Chen → Procurement-API
  Color: Blue (active during T+0 to T+1min)

Submission → Manager Review
  Line from Procurement-API → Mike Rodriguez
  Line from Procurement-API → Slack-Thread-947 (branched)
  Color: Blue (active during T+1min to T+2min)

Manager Review → Finance Review
  Line from Mike Rodriguez → Email-Chain-4821 → Sarah Chen
  Line from Sarah Chen → Email-Chain-4821 → Mike Rodriguez
  Line from Mike Rodriguez → Procurement-API
  Line from Procurement-API → Lisa Park
  Color: Orange (active during T+20h to T+43h)

Finance Review → Completion
  Line from Finance-System → Procurement-API (budget check)
  Line from Lisa Park → Procurement-API
  Line from Procurement-API → Sarah Chen
  Color: Green (active during T+43h to T+72h)
```

All paths are directional. Nothing moves along a path unless observed moving.

### Observed → Overlays

Observations become visual overlays:

```
Timestamps → Floating markers at each path segment activation
  "Mon 14:23" appears when PR-2847 created
  "Tue 10:15" appears when Mike Rodriguez opens request
  etc.

Delays → Color shift on paths
  Manager review path: Orange glow (constraint violated)
  Finance review path: Orange glow (constraint violated)

Gaps → Darkened path segments during after-hours
  Visible from Mon 17:00 to Tue 09:00
  Visible from Tue 17:00 to Wed 09:00
  Visible from Wed 17:00 to Thu 09:00

Activity → Pulsing highlight
  When Sarah Chen creates PR-2847: object pulses
  When Mike Rodriguez opens email: Email-Chain-4821 pulses
  When budget check runs: Budget-Line-D400 pulses
```

Observations change appearance, not the things themselves.

### Constraints → Affordances and Limits

Constraints become visible restrictions:

```
Sequential Dependency (Manager approval required)
  Path from Procurement-API to Lisa Park is grayed/dashed until Mike Rodriguez approves
  Once approved, path becomes solid and traversable

Time Expectations (4hr manager, 8hr finance)
  Clock indicators appear on paths
  As time exceeds expectation, indicator shifts from green → yellow → orange

Budget Requirement
  Gate icon appears at Finance-System → Procurement-API path
  Gate opens only after budget check completes

Business Hours Restriction
  During After Hours scope: all approval paths show "inactive" state
  During Business Hours scope: approval paths show "active" state

Data Validation
  Small checkmark badge appears on PR-2847 after validation passes
```

Constraints restrict movement, not existence.

### Time → The Moving Dimension

Time controls everything:

```
T=0 (Mon 14:23)
  - Sarah Chen and PR-2847 appear
  - Path to Procurement-API activates

T=1min (Mon 14:24)
  - PR-2847 moves along path to Procurement-API
  - Paths to Mike Rodriguez and Slack-Thread-947 activate
  - Timestamp marker appears

T=20h (Tue 10:15)
  - Mike Rodriguez interacts with PR-2847
  - Time constraint indicator shifts to orange (exceeded 4hr expectation)

T=43h (Wed 09:06)
  - PR-2847 crosses from Management to Finance scope
  - Budget check path activates
  - New time constraint begins for finance review

T=72h (Thu 14:46)
  - PR-2847 reaches completion
  - All paths become historical (shift to gray)
  - Final timestamp marker appears
```

Scrubbing time backward/forward shows paths appearing and disappearing.

Freezing time at T=20h shows the request waiting at Mike Rodriguez with orange delay indicator.

---

## Part 3: Multiple Views of Same Facts

### View 1: Process Manager Perspective

**Emphasis:**
- Time constraints (zoomed in on delay indicators)
- Path traversal timing
- Where things wait

**De-emphasis:**
- Individual system details
- Communication content
- Budget calculation specifics

**Focus:**
Where are the bottlenecks? The two orange-glowing path segments immediately visible.

**Distance:**
Medium - can see individual approval steps but not message contents

### View 2: Sarah Chen (Requester) Perspective

**Emphasis:**
- PR-2847 location and state
- Notifications received
- Current blocker (who has the request now?)

**De-emphasis:**
- Other requests in the system
- Budget system internals
- Management layer abstractions

**Focus:**
Where is my request? What's the next step?

**Distance:**
Close - following one object (PR-2847) through its journey

### View 3: Finance Audit Perspective

**Emphasis:**
- Budget check execution
- Approval timestamps
- Constraint satisfaction
- Cross-scope traversal (internal → external)

**De-emphasis:**
- Communication style and content
- Individual employee identities
- Department cultural context

**Focus:**
Was policy followed? Were constraints satisfied? What was the timeline?

**Distance:**
Far - seeing the complete traversal with emphasis on compliance checkpoints

### View 4: System Architecture Perspective

**Emphasis:**
- System objects (Procurement-API, Finance-System)
- API calls and data flows
- Technical scope boundaries
- System-to-system paths

**De-emphasis:**
- Human decision-making steps
- Organizational scopes
- Business hour constraints

**Focus:**
How do systems interact? Where are integration points?

**Distance:**
Medium - focused on technical layer, organizational context dimmed

---

## Part 4: Reality Check

### Test 1: Point and Name

Point at any element and name its primitive:

| Point at | Answer | Primitive |
|----------|--------|-----------|
| PR-2847 | A purchase request | Thing |
| Blue vertical plane | Engineering Department | Scope |
| Line from Sarah to API | Submission path | Path |
| "Tue 10:15" marker | Observation of when manager opened request | Observed |
| Orange glow on path | Observed delay exceeding time constraint | Observed + Constraint |
| Grayed-out line to Lisa | Sequential dependency constraint | Constraint |
| Timeline scrubber | Time dimension | Time |

All answers are primitives. ✓

### Test 2: No New Concepts

Concepts NOT introduced:
- "Organizational dysfunction"
- "Poor communication culture"
- "Strategic misalignment"
- "Process inefficiency"
- "Approval bottleneck pattern"

Only facts:
- Request existed
- Request moved along paths
- Delays were observed
- Constraints existed
- Time elapsed

✓

### Test 3: Multiple Roles See Same Facts

Process Manager sees: PR-2847 took 72 hours with delays at manager and finance review
Sarah Chen sees: PR-2847 took 72 hours with delays at manager and finance review
Finance Auditor sees: PR-2847 took 72 hours with delays at manager and finance review

They emphasize different aspects, but the facts are identical. ✓

### Test 4: Causality Not Implied

What we DO NOT say:
- "Manager delay caused finance delay"
- "Lack of urgency resulted in violations"
- "Poor prioritization led to slow approval"

What we DO say:
- "Manager review observed at T+20h, exceeding 4h constraint"
- "Finance review observed at T+69h, exceeding 8h constraint from T+43h"
- "Total elapsed time: 72h23m"

We show correlation of timing. We do not claim causation. ✓

### Test 5: Can Traverse

Starting at Sarah Chen at T=0, can we follow the path?

1. Sarah Chen → PR-2847 (creates)
2. PR-2847 → Procurement-API (submits)
3. Procurement-API → Mike Rodriguez (routes)
4. Mike Rodriguez → Email-Chain-4821 (queries)
5. Email-Chain-4821 → Sarah Chen (delivers)
6. Sarah Chen → Email-Chain-4821 (responds)
7. Email-Chain-4821 → Mike Rodriguez (delivers)
8. Mike Rodriguez → Procurement-API (approves)
9. Procurement-API → Lisa Park (routes)
10. Finance-System → Procurement-API (validates budget)
11. Lisa Park → Procurement-API (approves)
12. Procurement-API → Sarah Chen (notifies)

Every step is observable. Every path has something moving along it. ✓

---

## Part 5: What This Example Demonstrates

### It Shows

1. **Facts without interpretation**
   - Times, routes, durations, constraint states

2. **Absence as information**
   - The gaps between observations are visible
   - After-hours periods appear as darkened timeline

3. **Constraints as explicit**
   - Sequential dependencies visible as gated paths
   - Time expectations visible as constraint indicators

4. **Multiple views without translation**
   - Same facts, different emphasis
   - No conflicting "truths"

### It Does Not Show

1. **Why delays occurred**
   - Manager might have been unavailable, busy, forgot, or deprioritized
   - We do not know, so we do not show

2. **Whether this is "good" or "bad"**
   - 72 hours might be acceptable or unacceptable
   - That judgment is external to the projection

3. **What "should" happen**
   - The ideal process is not shown
   - Only what was observed

4. **Organizational culture or politics**
   - Interpretation of why things move slowly
   - Who has power, who is avoiding work, etc.

---

## Part 6: Implementation Notes

### Data Structure (Conceptual)

```json
{
  "things": [
    {"id": "pr-2847", "type": "document", "created": "2024-11-18T14:23:00Z"},
    {"id": "sarah-chen", "type": "person"},
    {"id": "mike-rodriguez", "type": "person"},
    // ... more things
  ],
  "scopes": [
    {"id": "engineering", "type": "organizational"},
    {"id": "finance", "type": "organizational"},
    {"id": "business-hours", "type": "temporal", "pattern": "Mon-Fri 09:00-17:00"},
    // ... more scopes
  ],
  "paths": [
    {
      "id": "path-1",
      "from": "sarah-chen",
      "to": "procurement-api",
      "via": null,
      "observed_start": "2024-11-18T14:23:00Z",
      "observed_complete": "2024-11-18T14:24:00Z"
    },
    // ... more paths
  ],
  "observations": [
    {
      "timestamp": "2024-11-18T14:23:00Z",
      "thing": "pr-2847",
      "event": "created",
      "scope": "engineering"
    },
    // ... more observations
  ],
  "constraints": [
    {
      "id": "manager-review-time",
      "type": "time-expectation",
      "applies_to": "path-2",
      "threshold": "4h",
      "observed_duration": "19.8h",
      "satisfied": false
    },
    // ... more constraints
  ]
}
```

This structure contains only facts. The projection queries this structure and renders it spatially.

### Projection Parameters

```yaml
view_config:
  camera_position: [0, 5, 10]  # Position in 3D space
  focus: ["pr-2847"]           # What to emphasize
  time_range: ["2024-11-18T14:00:00Z", "2024-11-21T15:00:00Z"]
  visible_scopes: ["engineering", "finance", "management"]
  visible_things: null  # null = all things in view
  emphasis:
    - type: "constraint-violations"
      intensity: 1.0
    - type: "path-timing"
      intensity: 0.7
```

Different view configurations query the same data structure but render different spatial projections.

---

## Conclusion

This example demonstrates one path traversing organizational scopes over time using only the six primitives.

It introduces no concepts beyond Things, Scopes, Paths, Observed, Constraints, and Time.

Someone can point at any element and name its primitive.

Multiple roles can view the same facts from different distances.

This is how you prevent collapse back into diagrams.
