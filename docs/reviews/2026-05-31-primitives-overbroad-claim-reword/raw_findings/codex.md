# Codex Review

## Per-Item Verdicts

1. Accuracy / overbreadth: pass for the edited bytes. `foundations/ijb/primitives.md:7` now scopes the claim to "business reality that IJB projects" and immediately limits that to "what exists and what was observed"; that matches `foundations/ijb/faq.md:7-15`, which says IJB is a projection framework that projects facts without interpretation and refuses abstraction. `foundations/ijb/README.md:10,14,23` likewise frames the system as factual descriptions rendered as navigable space, and the new line 14 scopes the claim to observable facts rather than all business/social phenomena.

2. Over-correction: pass. The new wording keeps the plain, strong claim that the six primitives cover IJB's projected business facts. It does not add weak hedging like "some" or "many." That is consistent with the anti-abstraction posture in `foundations/ijb/faq.md:13-15` and `foundations/ijb/why-this-matters.md:57-64`.

3. Bounding clause accuracy: pass. `foundations/ijb/primitives.md:7` says IJB does not describe "intent, causality, interpretation, or hypothetical futures." Intent, causality, and interpretation are expressly excluded by `foundations/ijb/canonical-assertion-grammar.md:15-19`; future-state projection is excluded by `foundations/ijb/faq.md:72-79`, and prediction/simulation is excluded by `foundations/ijb/faq.md:252-256`. The parenthetical "the canonical grammar's Non-Goals" is resolvable because the exact heading exists at `foundations/ijb/canonical-assertion-grammar.md:15`.

3a. Punctuation: pass. The em dash and semicolon in `foundations/ijb/primitives.md:7` improve readability over the original ASCII hyphen separator. This is prose, not grammar; `foundations/ijb/canonical-assertion-grammar.md:126-129` keeps the grammar ASCII, but does not impose ASCII-only prose on these Markdown files.

4. Parallelism & completeness: fail with one required revision. The two edited files are internally consistent: `foundations/ijb/primitives.md:7` and `foundations/ijb/README.md:14` both scope the claim to IJB-projected / observable facts. Exact grep no longer finds the old sentence outside review/research history. However, repo-wide grep found a stale equivalent in `docs/architecture.md:175-178`: "IJB is the framework that says every business reality reduces to exactly six primitives..." That repeats the same overbroad modeling-grammar claim in public architecture prose.

5. No semantic / normative change: pass for the inspected diff. `git diff -- foundations/ijb/primitives.md foundations/ijb/README.md` shows one prose-line replacement in each file only. `git status --short -- foundations/ijb/primitives.md foundations/ijb/README.md` shows only those two `foundations/ijb` Markdown files modified, and `git diff --numstat` reports `1 1` for each. No primitive, grammar, ontology, validator, closure_root, SHA, or `*-kind.toml` file is changed; the forbidden-phrase issue for kind descriptors is not applicable.

## Findings

- `docs/architecture.md:175` | major | A stale equivalent overbroad claim remains: "every business reality reduces to exactly six primitives." This leaves the same modeling-grammar invitation in public architecture prose even though the two IJB files were scoped correctly.

## Terminal Recommendation

approve_with_revisions

Exact additional replacement to ship in `docs/architecture.md:175-178`:

```markdown
DAG-TOML sits on top of the IJB ("It's Just Business") substrate. IJB
is the framework that says every projectable business fact in its scope
is expressed through six primitives — `thing`, `scope`, `path`,
`observed`, `constraint`, `time` — and forbids any other categorisation
at the substrate level.
```

The edited `foundations/ijb/primitives.md:7` and `foundations/ijb/README.md:14` wording can land unchanged once that stale architecture sentence is scoped too.

Highest-leverage reason: the requested reword fixes the two named bytes, but leaving `docs/architecture.md:175-178` unchanged preserves the same overbroad claim in another reader-facing spec explainer.
