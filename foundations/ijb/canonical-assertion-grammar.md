# SPEC: Canonical assertion grammar

Slug: 20260420-canonical-assertion-grammar

## Summary
Define a tight, machine-usable assertion syntax for IJB so structure, instances, observations, constraints, and replay can share one canonical substrate.

## Goals
- Make IJB assertions parseable without inference.
- Keep syntax aligned with the six primitives.
- Support Option 2: concrete instances, explicit identity, explicit observation metadata, explicit constraints.
- Preserve replay into plain language.
- Make structural-to-instance links explicit.

## Non-Goals
- Create a new visualization notation.
- Replace the six primitives.
- Encode intent, causality, or interpretation.
- Model full FCO-IM metaconcepts.

## Requirements

### Syntax shape
- One assertion per line.
- Every assertion has globally unique assertion ID.
- Every referenceable `id=` value shares one global namespace across primitive kinds.
- Every primitive uses fixed field order.
- References are by identifier only.
- Reference matching is character-for-character. Hyphen and underscore are distinct characters and no normalization occurs.
- Timestamps use RFC3339 UTC form: `YYYY-MM-DDTHH:MM:SSZ`.
- Free text is allowed only inside quoted `rule=` values.
- Replay must dereference referenced assertion IDs before rendering plain language.

### Canonical line form
```text
<assertion-id> = <primitive-call>
```

Example:
```text
A-thing-request-9001 = thing(id=Access-Request-9001,class=instance,instance_of=Access-Request,type=request,identity=request_id)
```

### ABNF
```abnf
assertion = assertion-id SP "=" SP primitive-call

assertion-id = "A-" ref

primitive-call = thing-call / scope-call / path-call / constraint-call / time-call / observed-call

thing-call = "thing(" (thing-struct / thing-inst) ")"
thing-struct = "id=" ref "," "class=structural" "," "type=" token "," "identity=" token
thing-inst = "id=" ref "," "class=instance" "," "instance_of=" ref "," "type=" token "," "identity=" token

scope-call = "scope(" (scope-def / scope-use) ")"
scope-def = "id=" ref "," "class=structural" "," "type=" token
scope-use = "thing=" ref "," "within=" ref

path-call = "path(" (path-struct / path-inst) ")"
path-struct = "id=" ref "," "class=structural" "," "from=" ref "," "to=" ref "," "within=" ref "," "moves=" token
path-inst = "id=" ref "," "class=instance" "," "instance_of=" ref "," "from=" ref "," "to=" ref "," "within=" ref "," "moves=" token

constraint-call = "constraint(" "id=" ref "," "type=" constraint-type "," "target=" ref "," "within=" ref "," "rule=" quoted-string ")"

time-call = "time(" "id=" ref "," "event=" assertion-id "," "at=" timestamp ")"

observed-call = "observed(" "id=" ref "," "asserts=" assertion-id "," "by=" ref "," "time=" assertion-id "," "within=" ref ")"

constraint-type = "structural" / "policy" / "observed"

ref = id-start *id-char
token = id-start *id-char
id-start = ALPHA / DIGIT
id-char = ALPHA / DIGIT / "-" / "_"

quoted-string = DQUOTE *qchar DQUOTE
qchar = %x20-21 / %x23-5B / %x5D-7E

timestamp = date "T" time-of-day "Z"
date = 4DIGIT "-" 2DIGIT "-" 2DIGIT
time-of-day = 2DIGIT ":" 2DIGIT ":" 2DIGIT
```

### Primitive meaning
- `thing(...class=structural...)`: declares a structural Thing and states identity method.
- `thing(...class=instance...)`: declares an instance Thing, states `instance_of`, and states identity method.
- `scope(id=...)`: declares a structural Scope.
- `scope(thing=...,within=...)`: places a Thing within a Scope.
- `path(...class=structural...)`: declares a structural Path.
- `path(...class=instance...)`: declares an instance Path and states `instance_of`.
- `constraint(...)`: declares a Constraint with explicit type, target, scope, and rule text.
- `time(...)`: binds a timestamp to an event-bearing assertion. Valid targets are instance `path(...)` assertions or `observed(...)` assertions. `thing(...)` assertions are state facts and are not valid `event=` targets.
- `observed(...)`: records that another assertion was observed at a time in a scope.
- `by=` names the recorder or observing source for the observation. It is not required to equal `from` or `to` on the asserted path.

### Replay templates
- `thing(...class=structural...)` → `Structural Thing <id> exists.`
- `thing(...class=instance...)` → `Thing <id> exists as instance of <instance_of>.`
- `scope(id=...)` → `Scope <id> exists.`
- `scope(thing=...,within=...)` → `Thing <thing> exists within Scope <within>.`
- `path(...class=structural...)` → `Structural Path <id> connects <from> to <to> within Scope <within>.`
- `path(...class=instance...)` → `Path <id> connects <from> to <to> within Scope <within>.`
- `constraint(...)` → `Constraint <id> restricts <target> within Scope <within>.`
- `time(...)` → `<resolved event subject> occurred at Time <at>.`
  Contracted form allowed when target is a path: `Path <id> occurred at Time <at>.`
- `observed(...)` → `Observation <id> records that <resolved asserted subject> occurred at Time <at> by <by> within Scope <within>.`

### Validation rules
- Every `within=` reference must resolve to a declared scope.
- Every referenceable `id=` value must be globally unique across scopes, things, paths, constraints, times, and observations.
- Every `thing=` / `from=` / `to=` / `by=` / `target=` reference must resolve.
- Every reference must match its declaration character-for-character.
- Every `time=` reference in `observed(...)` must resolve to an existing `time(...)` assertion ID.
- Every instance `thing(...instance_of=...)` must point to a structural Thing.
- Every instance `path(...instance_of=...)` must point to a structural Path.
- Every `observed(asserts=...)` must point to an existing assertion.
- Every `time(event=...)` must point to an existing event-bearing assertion.
- No `time(event=...)` may target a `thing(...)` assertion.
- Every structural `path(...)` must have at least one instance `path(...)`.
- Every structural construct used in examples must have at least one instance.
- Observation never substitutes for structure.
- Every document using canonical assertions must define an allowed `moves=` vocabulary for that document.
- A structural Scope is considered instantiated when referenced by `scope(thing=...,within=...)`, `path(...within=...)`, `constraint(...within=...)`, or `observed(...within=...)`.

## Constraints
- Syntax is substrate only, never visualization.
- Grammar must stay ASCII.
- Grammar must stay append-only or versioned for breaking changes.
- New syntax forms require a spec update and worked example.

## Authority
- `01_SPEC__20260420-fco-im-integration.md` is authoritative for descriptive semantics.
- This spec is authoritative for canonical assertion encoding when canonical syntax is used.

## Examples
```text
A-scope-engineering = scope(id=Engineering,class=structural,type=org)
A-thing-employee = thing(id=Employee,class=structural,type=person,identity=employee_id)
A-thing-request = thing(id=Access-Request,class=structural,type=request,identity=request_id)
A-thing-manager = thing(id=Manager,class=structural,type=person,identity=employee_id)
A-thing-alice = thing(id=Alice,class=instance,instance_of=Employee,type=person,identity=employee_id)
A-thing-bob = thing(id=Bob,class=instance,instance_of=Manager,type=person,identity=employee_id)
A-thing-request-9001 = thing(id=Access-Request-9001,class=instance,instance_of=Access-Request,type=request,identity=request_id)
A-scope-alice-engineering = scope(thing=Alice,within=Engineering)
A-path-manager-approval = path(id=manager_approval,class=structural,from=Access-Request,to=Manager,within=Engineering,moves=request)
A-path-manager-approval-9001 = path(id=manager_approval_9001,class=instance,instance_of=manager_approval,from=Access-Request-9001,to=Bob,within=Engineering,moves=request)
A-time-manager-approval-9001 = time(id=T-manager_approval_9001,event=A-path-manager-approval-9001,at=2026-04-20T09:05:00Z)
A-observed-manager-approval-9001 = observed(id=OBS-manager_approval_9001,asserts=A-path-manager-approval-9001,by=Bob,time=A-time-manager-approval-9001,within=Engineering)
```

Moves vocabulary for this mini-example:
```text
request
```

## Open Questions
- None.

## Token Rules
- Single-sentence summary.
- Bullets over long narrative paragraphs.
- Direct verbs. No filler.
- Keep grammar stable and field order fixed.
