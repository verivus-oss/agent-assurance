# Review Findings — 2026-05-31 primitives overbroad claim reword

**Reviewer**: grok (fresh-context independent per review-request-dag policy)
**Session**: 2026-05-31-primitives-overbroad-claim-reword
**Method**: Byte inspection only. Did not accept initiator summary or prior review conclusions as evidence. Ran `git diff`, read every cited ground-truth file in full relevant ranges, grepped for stale claims across repo excluding research/review dirs.

## Diff Inspected (verbatim)

```
diff --git a/foundations/ijb/README.md b/foundations/ijb/README.md
index d9350dc..e1221b5 100644
--- a/foundations/ijb/README.md
+++ b/foundations/ijb/README.md
@@ -11,7 +11,7 @@ This is not a modeling tool. This is not a diagramming system. This is a project

 ## The Six Primitives

-All business reality can be described using six primitives:
+All business reality that IJB projects — the observable facts about what exists, how it moves, and what was witnessed — can be described using six primitives:

 1. **Things** - Objects that exist
 2. **Scopes** - Contexts in which things exist
diff --git a/foundations/ijb/primitives.md b/foundations/ijb/primitives.md
index 776dd7b..29d18dc 100644
--- a/foundations/ijb/primitives.md
+++ b/foundations/ijb/primitives.md
@@ -4,7 +4,7 @@ Quick reference for the foundational elements of It's Just Business.

 ## Overview

-All business reality can be described using six primitives. These are never visual artifacts themselves - they are facts that get projected into spatial representations.
+All business reality that IJB projects — what exists and what was observed — can be described using six primitives. These are never visual artifacts themselves; they are facts that get projected into spatial representations. IJB describes facts, not intent, causality, interpretation, or hypothetical futures (see the canonical grammar's Non-Goals).

 ## The Primitives
```

## Ground-Truth Corpus Verified (exact ranges read)

- foundations/ijb/faq.md:1-100 (5-15 modeling vs projection; 66-84 uncertainty/future/strategy), 100-281 (123-134 observation vs interpretation; 240-267 "why"/"what should we do"/prediction/judgment/optimization)
- foundations/ijb/core-specification.md:1-50 (9-15 "You are not visualizing the business... The visualization is not the model"; 19-31, 45 "This layer is never drawn. It is queried.")
- foundations/ijb/canonical-assertion-grammar.md:1-50 (15-19 Non-Goals exactly: "Encode intent, causality, or interpretation." "Model full FCO-IM metaconcepts.")
- foundations/ijb/primitives.md:1-50 (new line 7), 120-153 (129-152 "This layer is queried, never drawn." + Reality Check rejecting "strategy/culture/alignment/risk posture")
- foundations/ijb/README.md:1-50 (new line 14 + 3-10, 23-49 "What Visualization Is Forbidden To Do": invent concepts, explain intent, suggest causality)
- foundations/ijb/why-this-matters.md:1-30 (17-30 projection vs interpretation/explanation/causality)
- Grep sweep (excluding docs/research/** and docs/reviews/**): no other instances of the unscoped "All business reality can be described using six primitives" or equivalent overbroad headline claim in any live normative file.

## Per-item verdicts

### 1. Accuracy / does it actually fix the overbreadth?
**Verdict: PASS**
- primitives.md:7 NEW: "All business reality that IJB projects — what exists and what was observed — can be described using six primitives." + explicit "IJB describes facts, not intent, causality, interpretation, or hypothetical futures (see the canonical grammar's Non-Goals)." Directly matches faq.md:7-9 ("This is a projection framework. ... projects facts into space without interpretation"), faq.md:13-15 ("refuses to abstract"), core-specification.md:9-15 ("You are not visualizing the business. ... projecting the same description into different spatial representations. The visualization is not the model."), and canonical-assertion-grammar.md:18.
- README.md:14 NEW: "All business reality that IJB projects — the observable facts about what exists, how it moves, and what was witnessed — can be described using six primitives:" is consistent with the primitives list that immediately follows and with core-specification.md:21-27 (the six primitives as non-visual facts).
- The reword eliminates the isolated modeling-grammar reading while preserving the completeness claim inside IJB's declared projection/observed-facts envelope. No overstatement of territory.

### 2. Over-correction? Brand impact?
**Verdict: PASS**
- No weakening or hedging. The claim remains direct and load-bearing: completeness for "what IJB projects." Phrasing ("what exists and what was observed", "observable facts") is plain-spoken and matches the anti-abstraction voice in why-this-matters.md:17-30 and faq.md:13-15 ("refuses to abstract. It projects reality as described, not as interpreted."). The added sentence in primitives.md:7 reinforces rather than dilutes the "Reality Check Question" at primitives.md:148-152. Cure is not worse than the disease.

### 3. Accuracy of the new bounding clause
**Verdict: PASS**
- primitives.md:7 "IJB describes facts, not intent, causality, interpretation, or hypothetical futures (see the canonical grammar's Non-Goals)" is byte-accurate:
  - "intent, causality, or interpretation" == canonical-assertion-grammar.md:18 verbatim.
  - "hypothetical futures" covered by faq.md:72-78 ("Do not project hypothetical futures. Project facts about plans."), faq.md:252-256 (no simulate or predict), and core-specification.md:45 ("This layer is never drawn. It is queried.").
- The parenthetical cross-reference is correct and resolvable (Non-Goals section at canonical-assertion-grammar.md:15-19). No dangling pointer.

### 3a. Em-dash/semicolon punctuation vs original hyphen style
**Verdict: PASS**
- OLD primitives.md:7 used ASCII " - " (space-hyphen-space). NEW uses em-dash " — " (U+2014) + semicolon before the added sentence.
- Em-dashes already present in the same directory (faq.md:208 "—these are the real-world failures", faq.md:230 "auditors—all can view"). Not stylistic drift; alignment with existing house style in foundations/ijb/. Semicolon correctly joins the two independent clauses and improves scannability. Net improvement for this file.

### 4. Parallelism & completeness. Other stale sites?
**Verdict: PASS**
- primitives.md:7 and README.md:14 are now parallel in structure (both lead with the scoped "All business reality that IJB projects — [observable/projectable facts] — can be described using six primitives").
- Minor phrasing variance exists ("what exists and what was observed" vs "the observable facts about what exists, how it moves, and what was witnessed") — both accurate to corpus and contextually appropriate (README leads into the numbered list that includes Paths/"how it moves"). Not a defect.
- Completeness: exhaustive grep found zero other instances of the overbroad unscoped claim in any file under foundations/ijb/, docs/ (except this review's own prompt/bundle which quote the OLD text for the record), or root-level docs. All other "six primitives" mentions are scoped ("using only the six primitives", "aligned with the six primitives", "never visual artifacts themselves"). Research docs correctly retain historical quotes of the original phrasing. No stale sites remain in live corpus.

### 5. No semantic/normative change.
**Verdict: PASS**
- Change touches exactly two prose sentences in two files: foundations/ijb/primitives.md:7 and foundations/ijb/README.md:14.
- Zero primitives added/removed/renamed.
- Zero impact on grammar (canonical-assertion-grammar.md), ontology files, validators/, *-kind.toml descriptors, examples/, or any machine-readable contract.
- No closure_root or sha changes (these are non-normative foundations prose per AGENTS.md and review_bundle.toml:40).
- No forbidden-phrase or kind-descriptor violations introduced (n/a to this change class).

---

## Findings list

| file:line | severity | issue |
|---|---|---|
| foundations/ijb/primitives.md:7 | NONE | Reword accurately and minimally scopes the claim to IJB's declared projection/observed-facts territory; bounding clause is byte-exact match to canonical-assertion-grammar.md:18 and faq.md:66-84 disclamations |
| foundations/ijb/README.md:14 | NONE | Reword consistent with primitives.md:7 and surrounding "What Visualization Is Forbidden To Do" (intent/causality) at README.md:44-48; no functional change |
| foundations/ijb/primitives.md:7 | minor | Qualifying phrase "what exists and what was observed" vs README.md:14 "what exists, how it moves, and what was witnessed" — trivial non-parallel wording choice between the two headline claims; both correct in context |
| foundations/ijb/primitives.md:7 | minor | Parenthetical "(see the canonical grammar's Non-Goals)" is a shorthand reference; the actual heading is "## Non-Goals" under the file's "SPEC: Canonical assertion grammar" title. Resolvable and already used in research trail; could be "see canonical-assertion-grammar.md Non-Goals" for stricter pointer hygiene |
| (repo-wide grep) | NONE | No other occurrences of the overbroad "All business reality can be described using six primitives" left in normative files |

---

## Terminal recommendation

**approve**

The reword eliminates the single face-value overbreadth ("All business reality can be described using six primitives") by scoping it to IJB's explicitly declared projection/observed-facts envelope, matches every byte in the required ground-truth corpus (faq.md:5-15/66-84, core-specification.md:9-15, canonical-assertion-grammar.md:15-19 Non-Goals), preserves the direct anti-abstraction brand voice, introduces only trivial non-semantic wording variance between the two files, and changes nothing normative or machine-readable.