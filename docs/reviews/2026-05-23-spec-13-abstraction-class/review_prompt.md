# Independent spec-change review — SPEC §13 abstraction class + capability envelope

You are an independent reviewer dispatched per the workflow at
`tools/review-request-dag.toml`. Fresh / clean-context session. No
prior memory of this artefact.

## What you are reviewing

- **Repo:** `/srv/repos/external/verivus-oss/agent-assurance`.
- **Commit under review:** `27c10203d5b23a3750ee85f6fc50377234bc4303`
  (titled "SPEC §13: abstraction class + capability envelope").
- **Parent:** `3697066`.
- **What changed:** 13 files, +955 / -20. SPEC.md gains a new
  §13 (10 subsections); `core/ontology.toml` gains 2 new
  attribute vocabularies; new validator
  `validators/validate_abstraction_class.py`; one worked-example
  kind descriptor (`profiles/cost/cost-record-kind.toml`)
  declares the §13 primitive; reference DB + Rust/Go hardcodes
  + MANIFEST counts all synced via the count-mirror gate added
  earlier in the session.

Inspect:

```bash
git -C /srv/repos/external/verivus-oss/agent-assurance show 27c1020 --stat
git -C /srv/repos/external/verivus-oss/agent-assurance diff 3697066..27c1020
git -C /srv/repos/external/verivus-oss/agent-assurance log --oneline -5
```

## Inputs you have

Authoritative surfaces (open directly):

- **`SPEC.md` §13** — the new section. Subsections §13.1 (rule),
  §13.2 (`[kind.abstraction_class]`), §13.3
  (`[kind.capability_envelope]`), §13.4 (cascade-break property
  via §12 closure-root), §13.5 (out of scope), §13.6 (IJB
  conformance), §13.7 (closed-vocabulary participation), §13.8
  (worked example `data-transform.v1`), §13.9 (forbidden
  mechanisms), §13.10 (backwards-compatible introduction).
- **`core/ontology.toml`** — search for `capability_envelope.domain`
  and `abstraction_class.id_pattern`.
- **`validators/validate_abstraction_class.py`** — the dedicated
  reference validator. ~340 lines, stdlib-only.
- **`profiles/cost/cost-record-kind.toml`** — first kind to
  declare the §13 primitive: search for `[kind.abstraction_class]`
  and `[kind.capability_envelope]`.
- **`.github/workflows/validate.yml`** — search for the new step
  "Validate abstraction class + capability envelope (SPEC §13)".

Prior-art (treat as hypotheses to verify, not ground truth):

- `docs/research/2026-05-22-spec-foundations-research/follow-up-2/16-stream-F-synthesis-v2.md`
  — the canonical Stream F synthesis the commit derives from.
- `docs/research/2026-05-22-spec-foundations-research/follow-up-2/10-abstraction-class-thread.md`
  + `.../12-canonical-thread.md` — the user's
  abstraction-class-type-safety framing.

## Workflow rules (binding, from `tools/review-request-dag.toml`)

1. Verify against code and docs, not the initiator's summary.
2. sqry MCP first (mcp__sqry__*); literal grep/text only for
   exact confirmation.
3. Every finding requires file + line + severity (high/medium/low).
4. Forbidden approval bases: stated intent, plan-compliance,
   "should be fixed" language.
5. Terminal states: `UNCONDITIONAL APPROVAL` or
   `CONCRETE UNRESOLVABLE BLOCKERS`. No conditional approvals.
6. Persist your full review verbatim.

## Substantive questions you MUST answer

### Q1 — Closed-vocabulary completeness and IJB tags

The two new vocabularies in `core/ontology.toml`
(`capability_envelope.domain` and `abstraction_class.id_pattern`)
both carry `ijb_primitive = "constraint"` and
`ijb_constraint_type = "structural"`. Verify each block is
well-formed and exactly nine values for the domains, exactly one
pattern value for the id_pattern. Run
`python3 validators/validate_ijb_conformance.py core/ontology.toml`
and quote the exit + last line.

### Q2 — Validator enforces every declared rule from §13.2 + §13.3

§13.2 declares the id-pattern rule, the description-required rule,
and the IJB-tag rules for `[kind.abstraction_class]`. §13.3
declares the spec_version-required rule, the IJB-tag rules, the
cpu_bounds + memory_bounds required tables, the closed-set
domain rule, and the per-domain shape checks.

Construct negative-test TOML files for each rule individually and
verify `validators/validate_abstraction_class.py` rejects each.
For each: exact command + exit code + verbatim error message.

Specifically test:
(a) `abstraction_class.id = "bad-no-version"` (missing
    `.v<integer>` suffix)
(b) `abstraction_class.description = ""` (empty)
(c) `abstraction_class` missing `ijb_primitive` or wrong value
(d) `capability_envelope` missing `cpu_bounds`
(e) `capability_envelope` missing `memory_bounds`
(f) `capability_envelope.cpu_bounds.max_cpu_ms` is a float (1.5)
(g) `capability_envelope.<unknown_domain>` (e.g.
    `made_up_domain`)
(h) `capability_envelope.filesystem` missing `read_allowed`

### Q3 — Backwards compatibility

Every existing `*-kind.toml` descriptor that does NOT declare
the §13 blocks must still pass the validator (backwards-compat
per §13.10). Verify by running the validator across all 19
descriptors:

```bash
python3 validators/validate_abstraction_class.py --repo-root . \
  core/*-kind.toml \
  profiles/agent-assurance/*-kind.toml \
  profiles/disclosure/*-kind.toml \
  profiles/cost/*-kind.toml
```

Quote the exit code and the summary line. Expected:
`PASSED (19 file(s) checked; 1 declared a §13 block).` Verify
the 1 declared is the cost-record kind (the worked example).

### Q4 — Closed-domain vocabulary load — single source of truth

The validator loads the closed domain set from
`core/ontology.toml` at startup (see `_load_domains()`). Verify
this by tampering: temporarily add `"invented_domain"` to the
ontology's `capability_envelope.domain.values`, run the validator
with a §13 declaration that uses `invented_domain`, and confirm
the validator now ACCEPTS it. Then restore the ontology and
confirm the validator REJECTS it again. This is the
single-source-of-truth check.

### Q5 — Cost-record worked example structural soundness

Open `profiles/cost/cost-record-kind.toml` (the first kind to
declare §13). Verify:
- `abstraction_class.id = "observation-record.v1"` matches the
  pattern.
- All 9 capability domains are declared (none implicitly missing).
- 8 of 9 domains use `denied = true`; clocks uses an explicit
  all-false sub-table with `precision_cap_ms = 0`.
- The block parses and the validator approves.

### Q6 — SPEC §13.4 cascade-break property is structurally enforced

§13.4 claims: "Changing the abstraction class or the capability
envelope flips the descriptor's closure root, which flips every
downstream instance's closure root that cited it."

Verify mechanically: compute the SHA-256 of
`profiles/cost/cost-record-kind.toml` at HEAD. Perturb one field
in the §13 blocks (e.g. change `max_cpu_ms = 100` to 200).
Compute the new SHA-256. Confirm they differ. This is the
cascade-break property in its weakest form (file-hash propagation).

```bash
sha256sum profiles/cost/cost-record-kind.toml
# perturb in /tmp, do not modify the real file
sed 's/max_cpu_ms      = 100/max_cpu_ms      = 200/' profiles/cost/cost-record-kind.toml | sha256sum
```

Report both hashes and that they differ.

### Q7 — §13.5 scope-out is honest

§13.5 explicitly defers five surfaces to RUNTIME-SPEC or
follow-up: wire format (CDDL), attenuation calculus, signing
tier (CB-AdES vs COSE_Sign1), enforcement backend (seccomp et
al.), WASM static observability. Confirm the commit does NOT
introduce any of these (no CBOR encoder, no attenuation algorithm,
no CB-AdES schema, no seccomp emitter, no WASM Component Model
import-check). Use `git show 27c1020 --stat` + targeted grep.

### Q8 — Forbidden mechanisms list (§13.9) is structurally
complete

§13.9 enumerates four forbidden papering-over mechanisms. Are
they the right four, given §12.7 already enumerates four
forbidden mechanisms for the closure-root rule? Is there
overlap, or do the two sets address orthogonal failure modes?

### Q9 — Reference DB + count-mirror gate are clean after §13

Two new vocabularies should propagate to:
(a) `[counts].attribute_vocabularies` 41→43
(b) `[counts].attribute_values_declared` 170→180
(c) `[counts].attribute_values_closed` 99→109
(d) `expected_seed_counts.attribute_vocabulary` 41→43 (×3 engines)
(e) `expected_seed_counts.attribute_value_allowed` 106→116 (×3)
(f) `expected_footer_counts.attribute_vocabularies` 41→43
(g) `expected_triple_counts.schema` 1291→1329
(h) Rust + Go EXPECTED_COUNTS hardcodes updated

Run `bash validators/check_manifest_drift.sh` and confirm exit 0
with all 28 mirror surfaces green.

### Q10 — Validator structure mirrors validate_cost.py pattern

The validator follows the prior pattern from `validate_cost.py`:
load closed vocabularies from `core/ontology.toml` as single
source of truth, run structural checks, exit 1 on any violation
with a named diagnostic. Verify the FAILURES output is operator-
visible per the lessons learnt in the count-mirror cleanup
session (which had to be re-fixed in commit 208e453). Construct
a multi-violation negative test and confirm each violation is
listed verbatim.

## Output structure (mandatory)

1. **SESSION META** — reviewer + version, sandbox/approval
   posture, MCP servers, re-derived HEAD sha.
2. **PROCESS CONFIRMATIONS** — migration guidance (does §13.10
   tell existing kind descriptors how to opt in?), no
   retconning, tests-run-with-output. Each: confirmed /
   refuted / unverifiable with file:line evidence.
3. **ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS** — one
   subsection per question. Each: verdict, file:line evidence
   (verbatim quotes), exact commands + exit codes + verbatim
   fenced output where applicable.
4. **INDEPENDENT FINDINGS** — anything the 10 questions missed.
   id, severity, file:line, verbatim quote, problem, fix.
5. **TERMINAL VERDICT** — `UNCONDITIONAL APPROVAL — <one-line
   justification anchored to specific inspected evidence>` OR
   `CONCRETE UNRESOLVABLE BLOCKERS:` numbered list with
   file:line + evidence + unblocking action for each.

Be specific. The user reads this directly and acts on it.

Begin.
