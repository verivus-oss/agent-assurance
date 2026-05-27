# Example 02: Incident Response Traversal

A single path following an observed system degradation through detection, escalation, and resolution.

## The Scenario

A database performance issue is observed, triggers automated detection, propagates through dependent services, and moves through incident response procedures.

This example demonstrates:
- Path crossing technical and organizational scopes
- Observable propagation through dependent systems
- Time-sensitive constraint violations (SLO breaches, escalation delays)
- State changes tracked through observations
- Multiple simultaneous paths (technical remediation + organizational communication)

---

## Part 1: Factual Description

### Things That Exist

```
DB-Primary-US-East-1A        # Primary database instance
DB-Replica-US-East-1B        # Read replica database instance
API-Gateway-Fleet            # API service (6 instances)
Web-Frontend-Fleet           # Frontend service (12 instances)
Monitoring-System            # Datadog monitoring platform
PagerDuty-Service            # Incident routing system
Incident-5847                # Incident record in system
Slack-Channel-Incidents      # #incidents Slack channel
StatusPage-External          # Public status page (status.company.com)
DB-Query-Log-Extract         # Exported query log (15MB file)
Remediation-Script-v2        # Script: kill-long-queries.sh
Deploy-Pipeline-Job-8821     # CI/CD pipeline execution
Postmortem-Doc-Draft         # Google doc for postmortem

Alex Kim                     # On-call SRE (primary)
Jordan Lee                   # On-call SRE (secondary)
Casey Martinez               # Engineering Manager
Database-Team-Rotation       # Group of 4 DBAs
Customer-Support-Team        # Group of 8 support agents
External-Customer-Requests   # Aggregate of 247 incoming requests
```

### Scopes Where Things Exist

```
Production Environment       # All production systems
US-East-1A                  # AWS availability zone
US-East-1B                  # AWS availability zone
Database Layer              # Technical architecture layer
Application Layer           # Technical architecture layer
User-Facing Layer           # Technical architecture layer

SRE Team                    # Organizational scope
Database Team               # Organizational scope
Engineering Management      # Organizational scope
Customer Support            # Organizational scope

Internal Systems            # Network scope
Public Internet             # Network scope

Business Hours              # Temporal scope (Mon-Fri 9am-6pm EST)
After Hours                 # Temporal scope
Critical Incident Mode      # Special operational scope (declared at T+47min)

Observed-Degraded-State     # System state scope (DB performance)
Observed-Normal-State       # System state scope (before and after)
```

### Paths That Connect Things

```
Path 1: Detection → Alert
  Monitoring-System observes DB-Primary-US-East-1A metrics
  Alert moves from Monitoring-System → PagerDuty-Service
  Page moves from PagerDuty-Service → Alex Kim

Path 2: Triage → Escalation
  Acknowledgment moves from Alex Kim → PagerDuty-Service
  Investigation query moves from Alex Kim → DB-Primary-US-East-1A
  DB-Query-Log-Extract moves from DB-Primary-US-East-1A → Alex Kim
  Escalation moves from Alex Kim → Jordan Lee
  Escalation moves from Alex Kim → Database-Team-Rotation
  War room notification moves from Alex Kim → Slack-Channel-Incidents

Path 3: Propagation (Technical)
  Load moves from DB-Primary-US-East-1A → DB-Replica-US-East-1B
  Slow responses move from DB-Primary-US-East-1A → API-Gateway-Fleet
  Timeout errors move from API-Gateway-Fleet → Web-Frontend-Fleet
  Failed requests move from Web-Frontend-Fleet → External-Customer-Requests
  Error rate metrics move from Web-Frontend-Fleet → Monitoring-System

Path 4: Communication (Organizational)
  Status update moves from Alex Kim → Slack-Channel-Incidents
  Customer notification moves from Casey Martinez → Customer-Support-Team
  Public status moves from Casey Martinez → StatusPage-External

Path 5: Remediation → Resolution
  Remediation-Script-v2 moves from Database-Team-Rotation → DB-Primary-US-East-1A
  Kill commands move from Remediation-Script-v2 → long-running queries (18 terminated)
  Recovery observation moves from DB-Primary-US-East-1A → Monitoring-System
  All-clear moves from Jordan Lee → PagerDuty-Service
  Resolution notification moves from Jordan Lee → Slack-Channel-Incidents
  Status update moves from Casey Martinez → StatusPage-External

Path 6: Follow-up
  Postmortem-Doc-Draft moves from Jordan Lee → Engineering Management
  (Future path: doc review, not yet observed)
```

### Observations Made

```
2024-12-05T02:37:15Z - DB-Primary-US-East-1A query latency p95: 45ms (baseline)
2024-12-05T02:37:45Z - DB-Primary-US-East-1A query latency p95: 1,250ms (degraded)
2024-12-05T02:38:00Z - DB-Replica-US-East-1B query latency p95: 890ms (degraded)
2024-12-05T02:38:15Z - API-Gateway-Fleet error rate: 0.2% → 12.4%
2024-12-05T02:38:30Z - Web-Frontend-Fleet error rate: 0.1% → 8.7%
2024-12-05T02:39:00Z - Monitoring-System creates alert: "DB latency critical"
2024-12-05T02:39:15Z - PagerDuty-Service pages Alex Kim (page sent)
2024-12-05T02:41:30Z - Alex Kim acknowledges page
2024-12-05T02:42:00Z - Alex Kim creates Incident-5847
2024-12-05T02:43:15Z - Alex Kim exports DB-Query-Log-Extract
2024-12-05T02:45:00Z - Alex Kim posts initial assessment to Slack-Channel-Incidents
2024-12-05T02:47:30Z - Alex Kim escalates to Jordan Lee
2024-12-05T02:47:45Z - Alex Kim escalates to Database-Team-Rotation
2024-12-05T02:49:00Z - Casey Martinez posts to Slack-Channel-Incidents (joining war room)
2024-12-05T02:51:00Z - Casey Martinez notifies Customer-Support-Team
2024-12-05T02:53:00Z - Casey Martinez updates StatusPage-External: "Investigating"
2024-12-05T02:56:30Z - Database-Team-Rotation identifies 18 long-running queries
2024-12-05T02:58:00Z - Database-Team-Rotation executes Remediation-Script-v2
2024-12-05T02:58:15Z - 18 queries terminated
2024-12-05T02:59:00Z - DB-Primary-US-East-1A query latency p95: 520ms (improving)
2024-12-05T03:01:00Z - DB-Primary-US-East-1A query latency p95: 62ms (recovered)
2024-12-05T03:01:30Z - API-Gateway-Fleet error rate: 2.1% (recovering)
2024-12-05T03:03:00Z - API-Gateway-Fleet error rate: 0.3% (baseline)
2024-12-05T03:03:15Z - Web-Frontend-Fleet error rate: 0.2% (baseline)
2024-12-05T03:05:00Z - Jordan Lee posts resolution to Slack-Channel-Incidents
2024-12-05T03:06:00Z - Jordan Lee marks Incident-5847 resolved
2024-12-05T03:08:00Z - Casey Martinez updates StatusPage-External: "Resolved"
2024-12-05T03:10:00Z - Jordan Lee closes PagerDuty incident
2024-12-05T09:15:00Z - Jordan Lee creates Postmortem-Doc-Draft
```

### Constraints That Apply

```
Constraint 1: Page acknowledgment expected within 5 minutes
  Type: SLO expectation
  Scope: PagerDuty-Service → Alex Kim
  Threshold: 5 minutes
  Observed: 2.25 minutes
  Status: Satisfied

Constraint 2: Initial triage assessment expected within 10 minutes of page
  Type: Incident response procedure
  Scope: Alex Kim → Incident-5847
  Threshold: 10 minutes
  Observed: 5.75 minutes (from page to Slack post)
  Status: Satisfied

Constraint 3: Database query latency SLO p95 < 200ms
  Type: Service level objective
  Scope: DB-Primary-US-East-1A
  Threshold: 200ms
  Observed: Up to 1,250ms for 23.75 minutes
  Status: Violated (duration: 23.75 minutes)

Constraint 4: API error rate SLO < 1.0%
  Type: Service level objective
  Scope: API-Gateway-Fleet
  Threshold: 1.0%
  Observed: Up to 12.4% for 24.75 minutes
  Status: Violated (duration: 24.75 minutes)

Constraint 5: Public status update expected within 15 minutes of user-facing impact
  Type: Communication policy
  Scope: StatusPage-External
  Threshold: 15 minutes from user-facing error spike
  Observed: 14.5 minutes (from Web-Frontend errors at T+0:53 to status post at T+15:15)
  Status: Satisfied

Constraint 6: Escalation to Database Team if not resolved in 10 minutes
  Type: Incident runbook procedure
  Scope: Alex Kim → Database-Team-Rotation
  Threshold: 10 minutes from triage start
  Observed: 5.75 minutes (escalated at T+10:15 from incident creation at T+4:30)
  Status: Satisfied

Constraint 7: Postmortem required for incidents > 15 minutes user impact
  Type: Engineering policy
  Scope: Incident-5847
  Threshold: 15 minutes user-facing impact
  Observed: 24.75 minutes user-facing impact
  Status: Required (postmortem draft created at T+6h37m)

Constraint 8: Only Database-Team-Rotation can execute write operations on production DB
  Type: Access control policy
  Scope: DB-Primary-US-East-1A
  Observed: Remediation-Script-v2 executed by Database-Team-Rotation
  Status: Satisfied
```

### Time Ordering

```
Timeline (Total incident duration: 32 minutes 45 seconds, war room active)

T+0:00      (02:37:15) - Baseline: DB latency 45ms, all systems normal
T+0:30      (02:37:45) - DB latency spikes to 1,250ms [degradation begins]
T+0:45      (02:38:00) - Replica latency degrades
T+1:00      (02:38:15) - API error rate spikes to 12.4%
T+1:15      (02:38:30) - Frontend error rate spikes to 8.7%
T+1:45      (02:39:00) - Monitoring alert triggers
T+2:00      (02:39:15) - PagerDuty pages Alex Kim
T+4:15      (02:41:30) - Alex Kim acknowledges (2.25min response)
T+4:45      (02:42:00) - Incident-5847 created
T+6:00      (02:43:15) - Query log exported
T+7:45      (02:45:00) - Initial war room post (triage complete)
T+10:15     (02:47:30) - Jordan Lee escalated
T+10:30     (02:47:45) - Database Team escalated
T+11:45     (02:49:00) - Engineering Manager joins war room
T+13:45     (02:51:00) - Customer Support notified
T+15:45     (02:53:00) - Public status page updated [within 15min constraint]
T+19:15     (02:56:30) - Root queries identified (18 long-running queries found)
T+20:45     (02:58:00) - Remediation script executed
T+21:00     (02:58:15) - Queries terminated [remediation action]
T+21:45     (02:59:00) - DB latency improving (520ms)
T+23:45     (03:01:00) - DB latency recovered (62ms) [degradation ends]
T+24:15     (03:01:30) - API error rate improving
T+25:45     (03:03:00) - API error rate baseline
T+26:00     (03:03:15) - Frontend error rate baseline
T+27:45     (03:05:00) - Resolution announced in Slack
T+28:45     (03:06:00) - Incident-5847 marked resolved
T+30:45     (03:08:00) - Status page updated: Resolved
T+32:45     (03:10:00) - PagerDuty incident closed [war room ends]

[6 hour 5 minute gap]

T+6:37:45   (09:15:00) - Postmortem draft created (next business day morning)

Key metrics:
- Detection lag: 1m45s (from degradation start to alert)
- Response time: 2m15s (from alert to acknowledgment)
- Time to resolution: 23m45s (from degradation start to recovery)
- User-facing impact: 24m45s (from frontend errors to recovery)
- War room duration: 32m45s (from incident creation to closure)
- SLO violation duration: 23m45s (DB latency), 24m45s (API errors)
```

---

## Part 2: Spatial Projection Mapping

### Things → Objects in Space

Each thing becomes an object:

```
DB-Primary-US-East-1A        → Database object (large cylinder, pulsing)
DB-Replica-US-East-1B        → Database object (medium cylinder)
API-Gateway-Fleet            → Service cluster (6 small cubes in formation)
Web-Frontend-Fleet           → Service cluster (12 small cubes in formation)
Monitoring-System            → Monitoring platform (wireframe sphere)
PagerDuty-Service            → Alert routing system (small pyramid)
Incident-5847                → Incident record (glowing red cube when active)
Slack-Channel-Incidents      → Communication space (flat message board)
StatusPage-External          → Public interface (outward-facing panel)
DB-Query-Log-Extract         → Data artifact (small file icon)
Remediation-Script-v2        → Executable artifact (script icon)
Deploy-Pipeline-Job-8821     → Automation object (pipeline segment)
Postmortem-Doc-Draft         → Document object (page icon)

Alex Kim                     → Person object (sphere, blue)
Jordan Lee                   → Person object (sphere, green)
Casey Martinez               → Person object (sphere, yellow)
Database-Team-Rotation       → Group object (cluster of 4 small spheres)
Customer-Support-Team        → Group object (cluster of 8 small spheres)
External-Customer-Requests   → Aggregate object (cloud of 247 small points)
```

Visual form indicates existence and type, not severity or blame.

### Scopes → Spatial Grouping

Scopes become planes, layers, and fields:

```
Production Environment       → Red-tinted volume (entire scene)
US-East-1A                  → Left vertical plane
US-East-1B                  → Right vertical plane (10 units offset)

Database Layer              → Bottom horizontal plane (z=0)
Application Layer           → Middle horizontal plane (z=5)
User-Facing Layer           → Top horizontal plane (z=10)

SRE Team                    → Blue circular field around Alex Kim, Jordan Lee
Database Team               → Purple circular field around Database-Team-Rotation
Engineering Management      → Yellow circular field around Casey Martinez
Customer Support            → Green circular field around Customer-Support-Team

Internal Systems            → Solid platform (opaque)
Public Internet             → Translucent platform (elevated, separate from internal)

After Hours                 → Dimmed lighting (nighttime timestamp indicators)
Critical Incident Mode      → Red pulsing boundary appears at T+10:15

Observed-Degraded-State     → Red heat overlay on affected systems
Observed-Normal-State       → Normal color (no overlay)
```

Objects appear in multiple scopes:
- DB-Primary exists in Production, US-East-1A, Database Layer, Internal Systems
- StatusPage-External exists in Public Internet (visible to external customers)

### Paths → Routed Connections

Paths become directed flows with timing:

```
Detection → Alert (T+1:45 to T+4:15)
  Monitoring-System → PagerDuty-Service: Yellow data flow
  PagerDuty-Service → Alex Kim: Pulsing red alert line

Triage → Escalation (T+4:15 to T+10:30)
  Alex Kim → DB-Primary-US-East-1A: Blue query line
  DB-Primary-US-East-1A → Alex Kim: Blue data return line (log file)
  Alex Kim → Slack-Channel-Incidents: White communication line
  Alex Kim → Jordan Lee: Orange escalation line
  Alex Kim → Database-Team-Rotation: Orange escalation line

Propagation - Technical (T+0:30 to T+25:45)
  DB-Primary-US-East-1A → DB-Replica-US-East-1B: Red stress line (load transfer)
  DB-Primary-US-East-1A → API-Gateway-Fleet: Red slow-response line (thickens over time)
  API-Gateway-Fleet → Web-Frontend-Fleet: Red timeout line
  Web-Frontend-Fleet → External-Customer-Requests: Red failed-request lines (247 individual)
  Web-Frontend-Fleet → Monitoring-System: Yellow error metric line

Communication - Organizational (T+11:45 to T+32:45)
  Casey Martinez → Customer-Support-Team: White info line
  Casey Martinez → StatusPage-External: White status line

Remediation → Resolution (T+19:15 to T+32:45)
  Database-Team-Rotation → DB-Primary-US-East-1A: Green remediation line
  Remediation-Script-v2 → long-running queries: Green termination actions (18 individual)
  DB-Primary-US-East-1A → Monitoring-System: Green recovery metric line
  Jordan Lee → Slack-Channel-Incidents: Green resolution announcement

Follow-up (T+6:37:45)
  Jordan Lee → Postmortem-Doc-Draft: White creation action
```

Lines are directional and time-activated. Thickness indicates volume or intensity.

### Observed → Overlays

Observations become visual overlays:

```
Metrics → Real-time graphs
  DB-Primary-US-East-1A: Latency graph overlay (45ms → 1,250ms → 62ms)
  API-Gateway-Fleet: Error rate graph (0.2% → 12.4% → 0.3%)
  Web-Frontend-Fleet: Error rate graph (0.1% → 8.7% → 0.2%)

State Changes → Color shifts
  T+0:30: DB-Primary-US-East-1A shifts from green → red
  T+23:45: DB-Primary-US-East-1A shifts from red → yellow → green

Human Actions → Action markers
  T+4:15: "Acknowledged" badge appears on Alex Kim
  T+7:45: "Triaging" badge appears on Alex Kim
  T+10:15: "Escalated" badge appears on Alex Kim
  T+19:15: "Identified" badge appears on Database-Team-Rotation
  T+20:45: "Executing Fix" badge appears on Database-Team-Rotation

Timestamps → Floating time indicators
  Each observation gets timestamp label
  Critical events get larger, pulsing timestamps

SLO Violations → Red boundary pulse
  Database Layer shows red pulse from T+0:30 to T+23:45
  Application Layer shows red pulse from T+1:00 to T+25:45

Activity Heat → Intensity overlay
  Slack-Channel-Incidents glows brighter with message frequency
  War room participants have heat halos during active investigation
```

Observations change appearance, not what things are.

### Constraints → Affordances and Limits

Constraints become visible restrictions and gates:

```
Page Acknowledgment (5min expectation)
  Timer appears on PagerDuty → Alex Kim path
  Starts green, turns yellow at 3min, would turn red at 5min
  Stopped at 2.25min (green, satisfied)

Triage Assessment (10min expectation)
  Timer appears on Alex Kim
  Satisfied at 5.75min

Database Latency SLO (p95 < 200ms)
  Threshold line visible on DB-Primary latency graph
  Graph line turns red when exceeding threshold
  Duration counter: 23.75 minutes in violation

API Error Rate SLO (< 1.0%)
  Threshold line visible on API error rate graph
  Graph line turns red when exceeding threshold
  Duration counter: 24.75 minutes in violation

Status Update Policy (15min from user impact)
  Countdown timer appears on StatusPage-External
  Satisfied at 14.5min (green)

Escalation Procedure (10min to DB team)
  Branching gate appears on Alex Kim's action space
  Gate triggers automatically, path to Database-Team-Rotation activates at T+10:15

Access Control (DB write operations)
  Lock icon on DB-Primary-US-East-1A
  Only unlocks for Database-Team-Rotation
  Remediation-Script path can only originate from authorized team
```

Constraints restrict actions and indicate threshold breaches.

### Time → The Moving Dimension

Time controls everything:

```
T=0 (02:37:15)
  - All systems normal (green)
  - Baseline metrics displayed

T=0:30 (02:37:45)
  - DB-Primary-US-East-1A shifts to red
  - Latency spike visible on graph
  - Heat overlay begins

T=1:45 (02:39:00)
  - Alert path activates (yellow)
  - Monitoring-System → PagerDuty-Service line appears

T=2:00 (02:39:15)
  - PagerDuty → Alex Kim path activates (red, pulsing)
  - Timer starts for acknowledgment constraint

T=4:15 (02:41:30)
  - Alex Kim action marker appears
  - Acknowledgment timer stops (green, 2.25min)
  - Alex Kim → DB-Primary query path activates

T=10:15 (02:47:30)
  - Escalation paths branch out (orange)
  - Critical Incident Mode scope appears (red boundary)
  - More participants enter scene

T=20:45 (02:58:00)
  - Remediation path activates (green)
  - Script execution visible

T=21:00 (02:58:15)
  - 18 termination actions flash
  - DB-Primary begins color shift red → yellow

T=23:45 (03:01:00)
  - DB-Primary returns to green
  - SLO violation overlay fades
  - Recovery metrics rise

T=32:45 (03:10:00)
  - Incident-5847 stops glowing (closed)
  - War room boundary fades
  - All paths become historical (gray)

T=6:37:45 (09:15:00)
  - Postmortem-Doc-Draft appears
  - New path from Jordan Lee activates briefly
```

Scrubbing time backward shows the incident "unresolving" - metrics degrading, people unjoining, alerts unsending.

Freezing at T=15:00 shows the war room at peak activity with systems still degraded.

---

## Part 3: Multiple Views of Same Facts

### View 1: On-Call Engineer (Alex Kim) Perspective

**Emphasis:**
- PagerDuty alert path (immediate attention)
- DB-Primary-US-East-1A metrics and state
- Available diagnostic tools (query logs)
- Escalation paths and timing
- Runbook constraint indicators

**De-emphasis:**
- Downstream service details (API/Frontend internals)
- Customer communication flow
- Management organizational scope
- External customer request volume

**Focus:**
What's broken? What data do I need? When do I escalate?

**Distance:**
Close - zoomed in on DB-Primary, monitoring graphs, and escalation triggers

**Key Observations:**
- Alert at T+2:00
- Latency spike visible immediately
- Escalation constraint triggers at T+10:15
- Can see exactly when Database Team took action

### View 2: Incident Commander (Casey Martinez) Perspective

**Emphasis:**
- All organizational communication paths
- StatusPage-External state and timing
- Customer-Support-Team awareness
- SLO violation durations and impact
- War room participant activity
- Resolution timeline

**De-emphasis:**
- Technical diagnostic details (query logs, script internals)
- Database layer technical architecture
- Individual query termination actions
- Monitoring system internals

**Focus:**
Who knows what? What are we telling customers? Are we meeting communication policies?

**Distance:**
Medium - seeing organizational scopes, communication paths, and high-level system state

**Key Observations:**
- User-facing impact from T+1:15
- Status update at T+15:45 (within 15min constraint)
- Customer Support notified at T+13:45
- Resolution at T+32:45
- All communication constraints satisfied

### View 3: Database Team Perspective

**Emphasis:**
- DB-Primary-US-East-1A and DB-Replica-US-East-1B detailed state
- Query log analysis
- Remediation-Script-v2 execution
- 18 individual query terminations
- Recovery metrics (latency normalization)
- Access control constraints

**De-emphasis:**
- Upstream paging and alert routing
- External customer experience
- Organizational communication overhead
- Management involvement

**Focus:**
What's the technical root cause? What actions fix it? Did it work?

**Distance:**
Very close - zoomed in on database layer with detailed metrics

**Key Observations:**
- 18 long-running queries identified at T+19:15
- Remediation script executed at T+20:45
- Latency recovery observed at T+23:45
- Access control constraint satisfied (only DB team executed writes)

### View 4: Post-Incident Review Perspective

**Emphasis:**
- Complete timeline (all 32m45s)
- All constraint satisfaction/violations
- Detection lag (1m45s)
- Response times (2m15s acknowledgment, 5m45s triage)
- SLO violation durations (23m45s DB, 24m45s API)
- Gaps and delays
- Parallel paths (technical + organizational)

**De-emphasis:**
- Real-time urgency indicators
- Individual message contents
- Participant stress levels
- Moment-to-moment state changes

**Focus:**
What was the timeline? Where were delays? Were procedures followed? What violated SLOs?

**Distance:**
Far - seeing entire incident arc from degradation to postmortem

**Key Observations:**
- Total user impact: 24m45s
- All response constraints satisfied (ack, triage, escalation, status update)
- Two SLO violations (DB latency, API errors)
- Postmortem required (>15min user impact)
- Remediation took 3m from identification to recovery

---

## Part 4: Reality Check

### Test 1: Point and Name

Point at any element and name its primitive:

| Point at | Answer | Primitive |
|----------|--------|-----------|
| DB-Primary-US-East-1A | A database instance | Thing |
| Red-tinted volume | Production environment | Scope |
| Line from Monitoring to PagerDuty | Alert routing path | Path |
| "02:39:15" timestamp | Observation of when page was sent | Observed |
| Latency spike to 1,250ms | Observation of degraded performance | Observed |
| Timer on acknowledgment path | 5-minute response expectation constraint | Constraint |
| Red pulse on DB latency SLO | Constraint violation observation | Observed + Constraint |
| Timeline scrubber | Time dimension | Time |
| Red heat overlay | Observed degraded state scope | Scope (state-based) |
| Lock icon on DB writes | Access control constraint | Constraint |

All answers are primitives. ✓

### Test 2: No New Concepts

Concepts NOT introduced:
- "System instability"
- "Architecture fragility"
- "Insufficient capacity planning"
- "Team coordination excellence"
- "Root cause: X caused Y"
- "Incident severity level"

Only facts:
- DB latency increased
- Errors propagated to dependent services
- Alerts triggered
- People responded
- Remediation executed
- Metrics returned to baseline
- Constraints violated or satisfied

✓

### Test 3: Multiple Roles See Same Facts

On-call engineer sees: DB latency spiked at T+0:30, resolved at T+23:45
Incident commander sees: DB latency spiked at T+0:30, resolved at T+23:45
Database team sees: DB latency spiked at T+0:30, resolved at T+23:45
Post-incident reviewer sees: DB latency spiked at T+0:30, resolved at T+23:45

They emphasize different aspects and operate at different distances, but the facts are identical. ✓

### Test 4: Causality Not Implied

What we DO NOT say:
- "Long-running queries caused the latency spike"
- "Database degradation caused API errors"
- "Insufficient monitoring led to delayed detection"

What we DO say:
- "At T+0:30, DB latency spiked to 1,250ms"
- "At T+1:00, API errors increased to 12.4%"
- "Detection lag: 1m45s from degradation start to alert"
- "At T+19:15, Database Team observed 18 long-running queries"
- "At T+20:45, Database Team executed script terminating 18 queries"
- "At T+23:45, DB latency returned to 62ms"

We show temporal correlation and sequence. We do not claim causation.

The Database Team's action correlates with recovery, but we do not assert it "caused" recovery without controlled experiment. ✓

### Test 5: Can Traverse

Starting at Monitoring-System at T=1:45, can we follow paths?

1. Monitoring-System observes DB-Primary metrics
2. Monitoring-System → PagerDuty-Service (alert)
3. PagerDuty-Service → Alex Kim (page)
4. Alex Kim → PagerDuty-Service (ack)
5. Alex Kim → DB-Primary-US-East-1A (query)
6. DB-Primary-US-East-1A → Alex Kim (log file)
7. Alex Kim → Slack-Channel-Incidents (post)
8. Alex Kim → Jordan Lee (escalate)
9. Alex Kim → Database-Team-Rotation (escalate)
10. Database-Team-Rotation → DB-Primary (analyze)
11. Database-Team-Rotation → DB-Primary (remediate)
12. DB-Primary → Monitoring-System (recovery metrics)
13. Jordan Lee → Slack-Channel-Incidents (resolution)
14. Jordan Lee → Postmortem-Doc-Draft (create)

Every step is observable. Every path has something moving along it. ✓

---

## Part 5: What This Example Demonstrates

### It Shows

1. **Technical and organizational paths simultaneously**
   - Remediation path (technical)
   - Communication path (organizational)
   - Both visible, neither privileged

2. **Propagation without implied causation**
   - DB degraded, then API errored, then Frontend errored
   - Temporal sequence observable
   - Causality not asserted

3. **Multiple simultaneous constraint types**
   - Response time constraints (SRE procedures)
   - Performance constraints (SLOs)
   - Communication constraints (status update policy)
   - Access control constraints (DB write permissions)

4. **State changes as observations**
   - Normal → Degraded → Recovering → Normal
   - Each state shift has timestamp

5. **Gap visibility**
   - 1m45s detection lag
   - After-hours context (2am incident)
   - 6h gap until postmortem draft

6. **Constraint satisfaction and violation**
   - Some constraints satisfied (response times, escalation, access control)
   - Some violated (DB SLO, API SLO)
   - Durations explicit

### It Does Not Show

1. **Why the queries were long-running**
   - Were they poorly optimized? Legitimate workload? External attack?
   - Not observed, not shown

2. **Whether response was "good" or "bad"**
   - 32m45s incident duration—acceptable?
   - 24m45s user impact—within tolerance?
   - Judgment is external

3. **Root cause**
   - We observed correlation (queries present, then terminated, then recovery)
   - Root cause requires controlled investigation
   - Not shown in spatial projection

4. **Team competence or blame**
   - Database Team executed remediation
   - We do not assert they are "heroes" or "responsible for the issue"
   - Actions are visible, interpretation is not

5. **Customer sentiment**
   - 247 failed requests observed
   - Customer frustration is not observable in system metrics
   - Not shown

---

## Part 6: Implementation Notes

### Data Structure (Conceptual)

```json
{
  "things": [
    {
      "id": "db-primary-us-east-1a",
      "type": "database",
      "properties": {
        "instance_id": "i-0a1b2c3d4e5f6",
        "region": "us-east-1",
        "az": "us-east-1a"
      }
    },
    {
      "id": "incident-5847",
      "type": "incident-record",
      "created": "2024-12-05T02:42:00Z",
      "resolved": "2024-12-05T03:06:00Z"
    }
    // ... more things
  ],
  "scopes": [
    {
      "id": "production-environment",
      "type": "operational"
    },
    {
      "id": "degraded-state",
      "type": "system-state",
      "start": "2024-12-05T02:37:45Z",
      "end": "2024-12-05T03:01:00Z"
    }
    // ... more scopes
  ],
  "paths": [
    {
      "id": "alert-routing",
      "from": "monitoring-system",
      "to": "pagerduty-service",
      "traversal_observed": "2024-12-05T02:39:00Z",
      "content": "alert: DB latency critical"
    },
    {
      "id": "remediation-execution",
      "from": "database-team-rotation",
      "to": "db-primary-us-east-1a",
      "traversal_observed": "2024-12-05T02:58:00Z",
      "content": "script: kill-long-queries.sh"
    }
    // ... more paths
  ],
  "observations": [
    {
      "timestamp": "2024-12-05T02:37:45Z",
      "thing": "db-primary-us-east-1a",
      "metric": "query_latency_p95_ms",
      "value": 1250,
      "state": "degraded"
    },
    {
      "timestamp": "2024-12-05T02:41:30Z",
      "thing": "alex-kim",
      "action": "acknowledged_page",
      "target": "incident-5847"
    },
    {
      "timestamp": "2024-12-05T02:58:15Z",
      "thing": "remediation-script-v2",
      "action": "terminated_queries",
      "count": 18
    }
    // ... more observations (35+ total)
  ],
  "constraints": [
    {
      "id": "db-latency-slo",
      "type": "performance-threshold",
      "applies_to": "db-primary-us-east-1a",
      "metric": "query_latency_p95_ms",
      "threshold": 200,
      "violation_start": "2024-12-05T02:37:45Z",
      "violation_end": "2024-12-05T03:01:00Z",
      "duration_seconds": 1395,
      "satisfied": false
    },
    {
      "id": "page-ack-expectation",
      "type": "response-time",
      "applies_to": "alex-kim",
      "threshold_seconds": 300,
      "observed_seconds": 135,
      "satisfied": true
    }
    // ... more constraints
  ]
}
```

This structure contains only facts. No interpretation. No causality assertions.

### Projection Parameters

```yaml
view_config_oncall_engineer:
  camera_position: [5, 3, 8]
  focus: ["db-primary-us-east-1a", "alex-kim", "pagerduty-service"]
  time_range: ["2024-12-05T02:35:00Z", "2024-12-05T03:15:00Z"]
  visible_scopes: ["production-environment", "database-layer", "sre-team"]
  visible_things:
    - include: ["db-primary-us-east-1a", "monitoring-system", "alex-kim",
                "jordan-lee", "database-team-rotation", "incident-5847"]
    - exclude: ["customer-support-team", "statuspage-external"]
  emphasis:
    - type: "constraint-violations"
      intensity: 1.0
    - type: "diagnostic-paths"
      intensity: 0.9
    - type: "escalation-timing"
      intensity: 0.8
  deemphasis:
    - type: "organizational-communication"
      intensity: 0.2

view_config_incident_commander:
  camera_position: [0, 15, 20]
  focus: ["incident-5847", "slack-channel-incidents", "statuspage-external"]
  time_range: ["2024-12-05T02:35:00Z", "2024-12-05T03:15:00Z"]
  visible_scopes: ["production-environment", "sre-team", "engineering-management",
                   "customer-support", "public-internet"]
  visible_things: null  # all things visible at this distance
  emphasis:
    - type: "communication-paths"
      intensity: 1.0
    - type: "slo-violations"
      intensity: 0.9
    - type: "constraint-satisfaction"
      intensity: 0.8
  deemphasis:
    - type: "technical-diagnostics"
      intensity: 0.3

view_config_post_incident:
  camera_position: [0, 25, 40]
  focus: null  # entire incident timeline
  time_range: ["2024-12-05T02:30:00Z", "2024-12-05T09:30:00Z"]
  visible_scopes: "all"
  visible_things: "all"
  time_scrubber_visible: true
  emphasis:
    - type: "timeline-completeness"
      intensity: 1.0
    - type: "constraint-tracking"
      intensity: 1.0
    - type: "gap-visibility"
      intensity: 0.9
  deemphasis: []
  annotations:
    - show_durations: true
    - show_constraint_results: true
    - highlight_violations: true
```

Different view configurations query the same factual data but render at different distances with different emphasis.

---

## Conclusion

This example demonstrates incident response as a traversal through technical and organizational scopes using only the six primitives.

**Key demonstrations:**

1. **Dual paths**: Technical remediation and organizational communication as parallel observable paths
2. **Propagation**: Degradation moving through dependent systems without asserting causation
3. **Constraint diversity**: SLOs, response times, policies, access controls all visible
4. **State changes**: Normal → Degraded → Recovered as time-stamped observations
5. **Multiple views**: On-call, commander, specialist, and reviewer perspectives from same facts

**Maintains discipline:**

- No interpretation of why (unknown, not shown)
- No judgment of quality (external to framework)
- No root cause claims (correlation ≠ causation)
- No concepts beyond the six primitives
- Every element passes the point-and-name test

This is incident response projected as factual traversal, not explained as narrative.
