# Decision review — IJB primitive #1: `referent` vs `party` (2026-05-31)

You are a **fresh-context, independent reviewer**. Your job is to adjudicate which
name the first IJB primitive ("the thing an assertion is about") should take:
`referent` or `party`. This is a SPEC-level decision about a foundational
primitive, dispatched under `tools/review-request-dag.toml [policy.*]`.

**Verify everything against bytes. Do NOT accept the initiator's summary as
evidence.** Every finding needs `file:line` + severity. Use sqry semantic search
first, literal grep only to confirm exact tokens.

## Repositories

- **Upstream code/spec (the ground truth):**
  `/srv/repos/external/verivus-oss/agent-assurance/`
- **Decision corpus (the deliberation + both adoption drafts):**
  `/srv/repos/external/kasselman/ijb-primitive-naming-review/`

## The two proposals (read both in full)

- **`party`** — standing recommendation:
  `/srv/repos/external/kasselman/ijb-primitive-naming-review/06-drafts-for-party.md`
- **`referent`** — challenger:
  `/srv/repos/external/kasselman/ijb-primitive-naming-review/07-drafts-for-referent.md`

Prior deliberation for context (verify claims, don't trust): files `00`–`05` in
the corpus. Note files `04`/`05` reasoned partly from memory of upstream paths;
re-confirm any path/line they cite.

## What is already eliminated (do not relitigate)

`thing` (dehumanizing), `subject` (GDPR "data subject" term-of-art collision +
internal overload), `entity` (`[[entities]]` saturation), `matter`
(`matter=Priya-Nair` ≈ "she is a problem"; "in the matter of" proceedings idiom),
`principal` (agency/identity/security overload + implies importance).

## Mandatory verifications (each needs file:line evidence)

1. **Official meaning of primitive #1.** Read `foundations/ijb/primitives.md` §1
   and the replay templates in `foundations/ijb/canonical-assertion-grammar.md`.
   Confirm/refute that #1 is currently the **existence** primitive ("objects that
   exist"). Decide whether naming it `referent` ("the thing referred to") is a
   tolerable reframe or a category error of the same shape that sank `matter`.
   The `referent` draft leans on WordNet sense 2 ("the first term in a
   proposition; the term to which other terms relate") to argue the reframe
   coincides with existence-anchoring — assess that argument.

2. **Internal collision.** Re-run whole-word scans. Initiator reports `referent`
   0 / `referents` 0, but the `reference` family is saturated (`reference` ~757,
   `references` ~376, `referenced` ~113, incl. `--check-references-exist` and
   "dereference referenced assertion IDs" in the grammar). Decide whether
   `referent` would be **confused-by-proximity** with that family in code, prose,
   and conversation. This is the strongest argument against `referent` — weigh it
   honestly. For `party`: confirm the ~102/43 hits are ordinary English with no
   schema role (check `profiles/agent-assurance/tiers/enterprise.toml` and the
   `third-party` uses).

3. **Legal / regulatory risk.** Confirm neither is a GDPR-style hard blocker.
   Assess relative audit-misinterpretation exposure: `party` (GDPR "third party",
   SCCs "the Parties", NIST "relying party") vs `referent` (semiotics term, no
   legal term-of-art). Cite the actual loaded surfaces.

4. **Brand / tone.** IJB is explicitly plain-spoken, anti-abstraction (confirm
   from `foundations/ijb/` brand text + `why-this-matters.md`). `referent` is a
   semiotics term of art whose dominant modern sense is academic — the same
   failure mode that helped kill `subject`. `party` is plain business English with
   participation baggage. Decide how decisive this axis is.

5. **Replay & ergonomics.** Both drafts adopt the same softening (drop the noun:
   "X exists within Scope Y"), which makes human-facing replay identical. Confirm
   that, and judge the candidates where they actually differ: keys, types, error
   classes (`NoSuchReferentError` vs `NoSuchPartyError`), TOML sections
   (`[[referents]]` vs `[[parties]]`), and the existence-vs-reference reframe.

6. **Directional ambiguity (referent-specific).** M-W defines `referent` as "one
   that refers **or** is referred to." The draft fixes IJB to the passive sense
   only (SPEC §10.6). Judge whether a primitive whose dictionary gloss is
   "X or its converse" is a precision liability in a precision-first framework.

## Process checks (report on each)

- Confirm the `referent` collision scan by re-running it yourself (don't trust the
  number).
- Confirm files `04`/`05` upstream citations still resolve at today's HEAD, or
  note drift.
- Run the standard slopscan discipline on both drafts' factual claims
  (`tools/README.md#standard-slopscan`): no hallucinated file paths, no invented
  legal/lexical facts.

## Required output (persist as `raw_findings/<your-model>.md`)

Structured, in this order:

1. **Per-axis verdict** (1–6 above): for each, state `referent` | `party` | tie,
   with file:line evidence and a one-line justification.
2. **Findings list**: each with `file:line`, severity (blocker / major / minor),
   and which candidate it counts against.
3. **Terminal recommendation** — exactly one of:
   - `adopt_referent` (with the concrete reasons `party`'s drawbacks outweigh the
     brand-tone cost),
   - `adopt_party` (with the concrete reason `referent`'s cost is disqualifying),
   - `concrete_unresolvable_blocker` (a fact that blocks *both*, stated with
     evidence).
4. **The decisive factor**, in one sentence: the single highest-leverage reason
   for your recommendation.

Decide on inspected bytes, not on either draft's framing. If a draft overstates
its own case, say so with the contradicting bytes.
