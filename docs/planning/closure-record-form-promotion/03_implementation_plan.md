# Implementation plan: profile-pinned closure record forms

Status: **planning, blocked on U02 (grammar freeze + operator STOP/GO)**
Created: 2026-07-12
Referenced by: [`implementation-dag.toml`](implementation-dag.toml) `[meta].decomposition`

This is the decomposition rationale behind
[`implementation-dag.toml`](implementation-dag.toml). The DAG is the
machine-checkable artifact; this is the human-readable "why."

## Shape of the DAG

```
            U01 design-pack + cross-LLM design review     (layer 0, tier 1)
             |
            U02 grammar-freeze go/no-go + compat sweep    (layer 1, tier 1)   <- HARD GATE
             |----------------|
            U03 spec text     U04 profile-descriptor INV07 (layer 2, tier 2)
             |----------------|
             |----------------+----------------|
            U05 python       U06 rust         U07 go       (layer 3, tier 2)
             |----------------+----------------|
            U08 profile pin + kind prose + fixtures        (layer 4, tier 2)  <- one atomic change
             |
            U09 conformance corpus + runner closure step   (layer 5, tier 3)
             |
            U10 cross-impl verify + implementation review  (layer 6, tier 3)
```

Critical path: U01 -> U02 -> U04 (the heaviest layer-2 unit: INV07 lands in
Python AND both primaries plus the kind descriptor) -> U06 (widest triad unit)
-> U08 -> U09 -> U10. This matches `[computed].critical_path` in the DAG.

## Why this decomposition

- **U01/U02 mirror the toml-1.1 migration's parity gate.** The grammar (record
  shape, presence semantics, INV06 constraints) must be frozen and reviewed
  BEFORE any of the three closure implementations is touched; a grammar change
  after one implementation lands is exactly the divergence the triad exists to
  prevent. U02 also runs the compatibility sweep: enumerate every conforming
  document in-repo and confirm the only closure-verdict changes are the
  enumerated com.verivus.runtime instances.
- **U03 and U04 are parallel after the freeze.** Spec text and the
  profile-descriptor validator do not depend on each other, but both encode
  the frozen grammar, so both sit behind U02.
- **U05/U06/U07 are the triad, in parallel, one unit each** (same pattern as
  toml-1.1 U03/U04/U05). Each implements §3.2/§3.4 of the design against the
  frozen grammar. None may merge before all three are ready to merge in the
  same stack: this is a PROCESS constraint (deliberately not encoded as
  mutual DAG edges, which would be a cycle); CI enforces it by cross-checking
  the three on shared fixtures in the stacked-PR run.
- **U08 is deliberately one atomic unit**: PROFILE.toml pinning, kind-descriptor
  prose/RKV01, example recompute, negative-fixture rewrite, CHANGELOG. The repo
  rule "move prose, descriptor, ontology, and example together" makes splitting
  it a violation; and pinning before U05-U07 merge would break CI (the
  validators would not understand the new PROFILE.toml section).
- **U09 after U08** because the corpus cases exercise the pinned profile.
  The runner change (explicit Python closure step for every kind) is folded in
  here because it is what makes C01 non-vacuous on the Python side.
- **U10 is the verification + review terminal**: full sweep (closure discover,
  kind validators, IJB, abstraction class, dagtoml conformance), evidence
  recorded, and the independent multi-LLM implementation review dispatched via
  `tools/review-request-dag.toml` before merge. Initiator does not approve.

## Commit/PR shape

Stacked per-unit bot PRs (same convention as the toml-1.1 migration:
authored by verivusOSS-releases), U03..U10 each one PR, merged only after the
U10 review evidence lands. U08's PR carries the atomic
profile+descriptor+example+CHANGELOG change.

## Explicitly out of scope

Runtime-repository sequencing and the public carve-out: planned in that
repository's own bundle, gated on this DAG's terminal output (design §5).
