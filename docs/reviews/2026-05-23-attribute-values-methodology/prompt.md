# Methodology convergence — what does `MANIFEST.toml [counts].attribute_values` mean and how do we measure it?

You are one of two independent agents being asked to propose a
measurement protocol. This is NOT a code review, NOT an approval
gate, and NOT a verdict. This is a **methodology consultation**:
two prior reviewers produced two different numbers for the same
field, and we need to converge on a single, defensible
measurement protocol before deciding what value to put in the
file.

This is a fresh / clean-context session. You have no prior memory
of this artefact. Do not assume any prior reasoning is correct.
Examine the symptoms below from scratch.

## The symptoms

`reference/database/MANIFEST.toml` in the repo at
`/srv/repos/external/verivus-oss/agent-assurance` contains a
`[counts]` table that describes the size of the DAG-TOML ontology
the reference databases mirror. One of its fields is:

```toml
[counts]
template_kinds         = 20
entity_kinds           = 27
relation_predicates    = 31
attribute_vocabularies = 41
attribute_values       = ???
```

The first four fields are checked by
`validators/check_manifest_drift.sh`. The fifth — `attribute_values`
— is **not** checked by that script. It has historically been
maintained by hand, and it has drifted.

Two independent reviewers were recently asked to verify the field
against ontology reality. They produced two different numbers:

- **Reviewer A:** 170. Computed by walking every
  `[[attribute_vocabularies]]` block across all four ontology
  files (`core/ontology.toml`, `profiles/agent-assurance/ontology.toml`,
  `profiles/disclosure/ontology.toml`, `profiles/cost/ontology.toml`)
  and summing `len(values)` regardless of whether the vocabulary is
  marked `extensible = true` or `extensible = false`.

- **Reviewer B:** 99. Computed the same way but **only** for
  vocabularies with `extensible = false` (i.e. closed sets).

The MANIFEST comment for the field as it stood at one point read:

> `# union across all closed-and-extensible-vocabulary allowed values`

That phrasing is ambiguous. "Closed-and-extensible" could be read
as:
1. "Closed-AND-extensible" = both kinds, i.e. ALL values across
   ALL vocabularies → Reviewer A's 170.
2. "Closed (and extensible)" as a single category description, with
   "and extensible" qualifying that closed vocabularies may
   gain extensions over time → Reviewer B's 99.

Three additional complications worth knowing about:

- The per-engine SQL seed files
  (`reference/database/{postgres,sqlite,duckdb}/seed.sql`) have
  divergent row counts in their `attribute_value_allowed` tables:
  postgres has ~63, sqlite has ~106, duckdb's count differs again.
  None of these match either 170 or 99.
- One of the closed vocabularies is `cost_citing_kind`, whose
  *values* are themselves DAG-TOML `template_kind` slugs
  (e.g. `"gate-decision"`, `"smoke-validation"`). So under
  interpretation 1, those values would be double-counted against
  the `template_kinds = 20` field's content.
- Some entries (e.g. `requirement_kind`) are marked
  `extensible = true` but ship with a starter value list. Under
  interpretation 2, those values are ignored entirely from the
  count; under interpretation 1, the starter list contributes
  but a downstream profile that adds a new requirement_kind also
  contributes — meaning interpretation 1's number is
  *not stable across profile compositions*.

## What we need from you

Propose, in writing, a measurement protocol that resolves the
disagreement. Specifically:

### 1. Measure definition

What should `[counts].attribute_values` represent, semantically?
Pick **one** of:

- (A) Total count of values across every `[[attribute_vocabularies]]`
  block in every loaded ontology, closed or extensible, including
  starter lists for extensible vocabularies.
- (B) Total count of values across vocabularies with
  `extensible = false` only.
- (C) Some other interpretation you propose — name it precisely.
- (D) Delete the field entirely (with rationale) — argue that
  `attribute_values` is meaningless without a tighter definition
  and the seed-file row counts are the real source of truth.

State which of (A)-(D) you recommend and **why** in two sentences.
If your reasoning depends on the consumer of this field (which
runtime artefact relies on it being accurate), name the consumer.

### 2. Data acquisition method

Spell out the **exact mechanical recipe** to compute your chosen
measure. Be precise enough that a junior implementer could
follow it without judgement calls. State:

- Which files are read (paths).
- Which TOML sections are inspected.
- Which fields within those sections.
- What aggregation is applied.
- How profile composition is handled (does the count depend on
  which profiles are present? what's the canonical profile set?).

### 3. Validation tooling

What tool computes and validates this number? Pick **one**:

- (i) Extend `validators/check_manifest_drift.sh` to compute and
  enforce the value. Specify exactly which `awk` / `grep` /
  `python` invocations would do the job.
- (ii) Write a small Python validator
  (`validators/check_attribute_values.py` or similar) that the
  drift script invokes.
- (iii) Compute the value at MANIFEST-generation time (one-shot,
  manual) and add a CI gate that re-derives and compares.
- (iv) Compute on-demand only; do not gate in CI; document the
  recipe in the MANIFEST comment.

State which of (i)-(iv) you recommend and **why** in two sentences.
If you recommend (i) or (ii), provide the actual command or script
body inline.

### 4. Independent computation under your protocol

Execute your own recommended protocol against the current repo
state at HEAD (`99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc`). Show:

- The exact command(s) you ran.
- The verbatim output.
- The number you got.
- Whether `reference/database/MANIFEST.toml` `[counts].attribute_values`
  matches your number at HEAD (currently it claims 170).

### 5. Other-reviewer reconciliation

The other agent dispatched in parallel with you is being asked
the same question with the same prompt. Your protocols will be
compared. To reduce talk-past disagreements:

- State the **most defensible interpretation you considered but
  rejected**, and the one specific reason you rejected it.
- State what would change your mind. (E.g. "If interpretation B
  is required by an existing downstream consumer at file:line X,
  I would switch to B.")
- State any **decision the spec maintainer needs to make** that
  your protocol leaves open.

## Output structure (mandatory)

Produce a single document with **exactly these five sections**, in
order, headed by their numbers above. Do not output anything
outside this structure. Be specific: file paths, line numbers,
exact commands, exact numbers.

Begin.
