# DAG-TOML Conformance Corpus

A shared semantic test corpus that every validator implementation (Rust
primary, Go primary, Python reference) must agree on. The TOML *parser*
conformance suites in the Makefile prove the implementations read TOML
identically; this corpus proves they enforce the same **DAG-TOML
semantics** — the layer where independent implementations actually
drift.

## Layout

```
conformance/
  runner.py                 # cross-implementation runner (stdlib only)
  known-divergences.toml    # tolerated drift — a baseline, not a green light
  cases/
    <kind>/                 # one directory per template kind
      valid/*.toml          # must be ACCEPTED by every implementation
      invalid/*.toml        # must be REJECTED by every implementation
      invalid/*.expected.toml  # optional sidecar: error_contains substrings
```

Each invalid fixture mutates exactly one aspect of a known-good
document, so a failure isolates one semantic rule. The optional
`<name>.expected.toml` sidecar pins the error *category* via substrings
that every implementation's output must contain (the implementations
deliberately share error phrasing).

## Running

```sh
make dagtoml-conformance
# or directly:
python3 conformance/runner.py \
  --rs tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs \
  --go /path/to/dagtoml-validate-go
```

Exit 0 means every implementation agreed on every fixture (modulo
entries in `known-divergences.toml`, which are printed as warnings).
Exit 1 is a cross-implementation disagreement: either fix the lagging
validator or, if the drift is accepted for now, add a documented entry
to `known-divergences.toml` with the reason and the code location.

## The contract for known divergences

Identical to `TOML_CONFORMANCE_SKIPS` in the Makefile: each entry is a
*currently-known-tolerated* gap, not permission. Revisit every entry
when any validator changes. If a run newly agrees on a listed case,
delete the entry. If a run newly disagrees on an unlisted case, treat
it as a regression in the validator, not a candidate for this file.

## Adding cases

1. Start from `examples/minimal-implementation-dag.toml` (or the
   minimal example for the kind under test).
2. Mutate one thing. Name the file after the rule it violates.
3. Add an `error_contains` sidecar with the stable error substring.
4. Run `make dagtoml-conformance`. All three implementations must
   reject it; if one does not, you have found real drift — fix it or
   document it.

## Coverage

Current corpus: `implementation-dag` (2 valid, 18 invalid) covering
required fields, status/tier vocabularies, self-dependencies, unknown
references, the `blocks`/`depends_on` inverse invariant, dependency
cycles, single-producer artifacts, consumed-but-never-produced
artifacts, artifact id prefixes, unresolved placeholders in file claims, layer ordering, `meta.total_units`
coherence, and the recomputed `[computed]` claims (entry points,
max_parallel, critical-path sum, and critical-path-is-longest-path).

Wanted next: corpora for `traceability`, `review-readiness`,
`kind-descriptor`, and `profile-descriptor`.
