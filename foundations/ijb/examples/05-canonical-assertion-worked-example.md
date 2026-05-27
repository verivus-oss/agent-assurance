# Example 05: Canonical Assertion Worked Example

A small end-to-end example showing how one IJB traversal is recorded in canonical assertion grammar, replayed into plain language, and projected into space.

## The Scenario

An employee requests badge access to a lab. Manager approval is required before the security system grants access.

This example demonstrates:
- Canonical machine-usable assertions
- Structural vs instance separation
- Explicit identity
- Explicit observation metadata
- Replay into plain language
- Projection without new concepts

---

## Part 1: Canonical Assertions

### Structural declarations

```text
A-scope-engineering = scope(id=Engineering,class=structural,type=org)
A-scope-security = scope(id=Security,class=structural,type=org)

A-thing-access-request = thing(id=Access-Request,class=structural,type=request,identity=request_id)
A-thing-employee = thing(id=Employee,class=structural,type=person,identity=employee_id)
A-thing-manager = thing(id=Manager,class=structural,type=person,identity=employee_id)
A-thing-security-system = thing(id=Security-System,class=structural,type=system,identity=system_id)

A-path-submit-request = path(id=submit_access_request,class=structural,from=Employee,to=Access-Request,within=Engineering,moves=request)
A-path-manager-approval = path(id=manager_approval,class=structural,from=Access-Request,to=Manager,within=Engineering,moves=request)
A-path-grant-badge-access = path(id=grant_badge_access,class=structural,from=Security-System,to=Employee,within=Security,moves=permission)

A-constraint-grant-after-approval = constraint(id=grant_after_approval,type=policy,target=grant_badge_access,within=Security,rule="grant requires manager approval")
```

### Instance declarations

```text
A-thing-request-9001 = thing(id=Access-Request-9001,class=instance,instance_of=Access-Request,type=request,identity=request_id)
A-thing-alice = thing(id=Alice-Kim,class=instance,instance_of=Employee,type=person,identity=employee_id)
A-thing-bob = thing(id=Bob-Gray,class=instance,instance_of=Manager,type=person,identity=employee_id)
A-thing-security-system-1 = thing(id=Security-System-1,class=instance,instance_of=Security-System,type=system,identity=system_id)

A-scope-request-engineering = scope(thing=Access-Request-9001,within=Engineering)
A-scope-alice-engineering = scope(thing=Alice-Kim,within=Engineering)
A-scope-bob-engineering = scope(thing=Bob-Gray,within=Engineering)
A-scope-security-system-security = scope(thing=Security-System-1,within=Security)

A-path-submit-request-9001 = path(id=submit_access_request_9001,class=instance,instance_of=submit_access_request,from=Alice-Kim,to=Access-Request-9001,within=Engineering,moves=request)
A-path-manager-approval-9001 = path(id=manager_approval_9001,class=instance,instance_of=manager_approval,from=Access-Request-9001,to=Bob-Gray,within=Engineering,moves=request)
A-path-grant-badge-access-9001 = path(id=grant_badge_access_9001,class=instance,instance_of=grant_badge_access,from=Security-System-1,to=Alice-Kim,within=Security,moves=permission)
```

### Time and observation

```text
A-time-request-submitted-9001 = time(id=T-request_submitted_9001,event=A-path-submit-request-9001,at=2026-04-20T09:00:00Z)
A-observed-request-submitted-9001 = observed(id=OBS-request_submitted_9001,asserts=A-path-submit-request-9001,by=Alice-Kim,time=A-time-request-submitted-9001,within=Engineering)

A-time-manager-approval-9001 = time(id=T-manager_approval_9001,event=A-path-manager-approval-9001,at=2026-04-20T09:05:00Z)
A-observed-manager-approval-9001 = observed(id=OBS-manager_approval_9001,asserts=A-path-manager-approval-9001,by=Bob-Gray,time=A-time-manager-approval-9001,within=Engineering)

A-time-badge-granted-9001 = time(id=T-badge_granted_9001,event=A-path-grant-badge-access-9001,at=2026-04-20T09:07:00Z)
A-observed-badge-granted-9001 = observed(id=OBS-badge_granted_9001,asserts=A-path-grant-badge-access-9001,by=Security-System-1,time=A-time-badge-granted-9001,within=Security)
```

### Moves vocabulary

```text
request
permission
```

---

## Part 2: Replay Into Plain Language

### Structural replay

- Scope Engineering exists.
- Scope Security exists.
- Structural Thing Access-Request exists.
- Structural Thing Employee exists.
- Structural Thing Manager exists.
- Structural Thing Security-System exists.
- Structural Path submit_access_request connects Employee to Access-Request within Scope Engineering.
- Structural Path manager_approval connects Access-Request to Manager within Scope Engineering.
- Structural Path grant_badge_access connects Security-System to Employee within Scope Security.
- Constraint grant_after_approval restricts grant_badge_access within Scope Security.

### Instance replay

- Thing Access-Request-9001 exists as instance of Access-Request.
- Thing Alice-Kim exists as instance of Employee.
- Thing Bob-Gray exists as instance of Manager.
- Thing Security-System-1 exists as instance of Security-System.
- Thing Access-Request-9001 exists within Scope Engineering.
- Thing Alice-Kim exists within Scope Engineering.
- Thing Bob-Gray exists within Scope Engineering.
- Thing Security-System-1 exists within Scope Security.
- Path submit_access_request_9001 connects Alice-Kim to Access-Request-9001 within Scope Engineering.
- Path manager_approval_9001 connects Access-Request-9001 to Bob-Gray within Scope Engineering.
- Path grant_badge_access_9001 connects Security-System-1 to Alice-Kim within Scope Security.

### Observation replay

- Path submit_access_request_9001 occurred at Time 2026-04-20T09:00:00Z.
- Observation OBS-request_submitted_9001 records that Path submit_access_request_9001 occurred at Time 2026-04-20T09:00:00Z by Alice-Kim within Scope Engineering.
- Path manager_approval_9001 occurred at Time 2026-04-20T09:05:00Z.
- Observation OBS-manager_approval_9001 records that Path manager_approval_9001 occurred at Time 2026-04-20T09:05:00Z by Bob-Gray within Scope Engineering.
- Path grant_badge_access_9001 occurred at Time 2026-04-20T09:07:00Z.
- Observation OBS-badge_granted_9001 records that Path grant_badge_access_9001 occurred at Time 2026-04-20T09:07:00Z by Security-System-1 within Scope Security.

---

## Part 3: Validation Checks

### Structure vs observation

- Structure exists before observation.
- The path `submit_access_request_9001` is structural instance data.
- The path `grant_badge_access_9001` is structural instance data.
- The observation `OBS-badge_granted_9001` records that the path was observed.
- Observation does not create the path.

### Constraint check

- Constraint: `grant_after_approval`
- Target: `grant_badge_access`
- Scope: `Security`
- Rule: `grant requires manager approval`

Observed order:
1. Request submission observed at `2026-04-20T09:00:00Z`.
2. Manager approval observed at `2026-04-20T09:05:00Z`.
3. Badge grant observed at `2026-04-20T09:07:00Z`.

Result:
- Observed sequence satisfies the constraint.

### Identity check

- `Access-Request-9001` is identified by `request_id`.
- `Alice-Kim` is identified by `employee_id`.
- `Bob-Gray` is identified by `employee_id`.
- `Security-System-1` is identified by `system_id`.

---

## Part 4: Projection Mapping

### Things

- `Access-Request-9001` becomes document object.
- `Alice-Kim` becomes person object.
- `Bob-Gray` becomes person object.
- `Security-System-1` becomes system object.

### Scopes

- `Engineering` becomes one spatial plane.
- `Security` becomes a second spatial plane.

### Paths

- `submit_access_request_9001` becomes directed connection from employee to request in Engineering.
- `manager_approval_9001` becomes directed connection from request to manager in Engineering.
- `grant_badge_access_9001` becomes directed connection from security system to employee in Security.

### Observed

- `OBS-request_submitted_9001` becomes timestamp overlay at request submission.
- `OBS-manager_approval_9001` becomes timestamp overlay on manager approval path.
- `OBS-badge_granted_9001` becomes timestamp overlay on badge grant path.

### Constraints

- `grant_after_approval` becomes gated visibility or blocked traversal on badge grant path until manager approval is observed.

### Time

- `T-request_submitted_9001`, `T-manager_approval_9001`, and `T-badge_granted_9001` order the traversal.
- Scrubbing time reveals request, review, then badge grant in sequence.

---

## Part 5: Reality Check

- Every line is one parseable assertion.
- Every visual element traces back to one or more assertions.
- No new concept was introduced beyond the six primitives.
- A domain reviewer can challenge the exact recorded statements, not a diagram summary.
