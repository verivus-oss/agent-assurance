# Review — reword the overbroad "all business reality" primitive claim (2026-05-31)

You are a **fresh-context independent reviewer** under `tools/review-request-dag.toml
[policy.*]`. Verify against bytes; do **not** accept the initiator's summary as evidence.
File:line + severity for every finding.

## Why this change exists

A multi-model adversarial review of a BWW (Bunge-Wand-Weber) usability analysis of IJB
converged (3-0, after a round-2 rebuttal) on one — and only one — actionable spec critique:
the literal sentence **"All business reality can be described using six primitives"**
(`foundations/ijb/primitives.md:7`, `foundations/ijb/README.md:14`) is **overbroad on its
face**. Read in isolation it invites a *modeling-grammar* reading (a claim to represent all
business/social phenomena incl. intent, causality, obligations), which the rest of the IJB
corpus explicitly disclaims — IJB is a projection/observation substrate that "refuses to
abstract" (`faq.md:13-15`), "projects facts into space without interpretation" (`faq.md:7`),
is "queried, never drawn" (`primitives.md:139`), and lists Non-Goals incl. intent/causality/
interpretation and full FCO-IM metaconcepts (`canonical-assertion-grammar.md:15-19`). The
reword scopes the claim to projectable/observed facts so the sentence matches the rest of
the corpus. (Full research trail: `docs/research/2026-05-31-ijb-six-primitive-usability.md`,
"ROUND-2 RESOLUTION".)

## The change under review (uncommitted working-tree diff)

Two files, scoping prose only — no primitive added/removed/renamed:

**`foundations/ijb/primitives.md:7`**
- OLD: `All business reality can be described using six primitives. These are never visual artifacts themselves - they are facts that get projected into spatial representations.`
- NEW: `All business reality that IJB projects — what exists and what was observed — can be described using six primitives. These are never visual artifacts themselves; they are facts that get projected into spatial representations. IJB describes facts, not intent, causality, interpretation, or hypothetical futures (see the canonical grammar's Non-Goals).`

**`foundations/ijb/README.md:14`**
- OLD: `All business reality can be described using six primitives:`
- NEW: `All business reality that IJB projects — the observable facts about what exists, how it moves, and what was witnessed — can be described using six primitives:`

Inspect the actual diff: `git diff -- foundations/ijb/primitives.md foundations/ijb/README.md`.

## What to verify (each needs file:line + a verdict)

1. **Accuracy / does it actually fix the overbreadth?** Does the new wording scope the claim
   to IJB's declared territory (projectable, observed facts) without misstating what IJB
   does? Cross-check the scoping against `faq.md:5-15,:66-84`, `core-specification.md:9-15`,
   `canonical-assertion-grammar.md:15-19`.
2. **Over-correction?** Does it weaken the claim too far or add hedging that dulls the
   plain-spoken, anti-abstraction brand (`why-this-matters.md`, `faq.md:13-15`)? The brand is
   load-bearing — the cure must not be worse than the disease.
3. **Accuracy of the new bounding clause** in primitives.md: are intent/causality/
   interpretation/hypothetical-futures genuinely disclaimed by the bytes it points to
   (`canonical-assertion-grammar.md:15-19`; `faq.md:66-84`)? Is the parenthetical
   cross-reference to "the canonical grammar's Non-Goals" correct and resolvable?
3a. The em-dash/semicolon punctuation change vs the original `" - "` hyphen style — is it an
   improvement or undesirable stylistic drift for this file?
4. **Parallelism & completeness.** primitives.md and README.md should stay consistent. Are
   there OTHER occurrences of the same overbroad claim that this change leaves stale? Grep
   the repo (e.g. `core-specification.md`, `getting-started.md`, `faq.md`) for "all business
   reality" / equivalent and report any missed sites.
5. **No semantic/normative change.** Confirm this touches only `foundations/ijb` prose, adds
   no primitive, changes no grammar/ontology/validator behavior, and no closure_root/sha
   (these are non-normative docs). Confirm nothing in the change reproduces a `*-kind.toml`
   forbidden-phrase issue (n/a here, but confirm).

## Required output (write to `raw_findings/<your-model>.md` and return it)

1. Per-item verdict (1–5 above) with file:line evidence.
2. Findings list: `file:line | severity (blocker/major/minor) | issue`.
3. **Terminal recommendation** — exactly one of:
   - `approve` (the reword is accurate, scoped, brand-consistent, complete),
   - `approve_with_revisions` (give the **exact replacement text** you'd ship instead),
   - `reject` (a concrete reason the reword should not land).
4. The single highest-leverage reason for your call, one sentence.

Decide on inspected bytes. If you'd phrase it better, supply the verbatim wording — don't
just gesture at it.
