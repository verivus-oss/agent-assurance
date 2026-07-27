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

Current corpus: `api-snapshot` (2 valid, 6 invalid) covering the SPEC
12.8/12.8.1 profile-pinned closure stream: the four-record positive, the
witness-strip stale-root rejection (contract C02 of the
closure-record-form promotion), a missing required pinned record, and a
malformed pinned digest. The runner also executes the Python closure
validator (`validate_closure_root.py`) on EVERY fixture of every kind,
so closure parity is exercised on all three implementations, not only
via the rs/go auto modes; the Python verdict is the combination of the
kind validator and the closure step. Invalid cases are excluded from
the repo-wide positive closure sweep (they are asserted-negative here).

Also: `implementation-dag` (3 valid, 18 invalid) covering
required fields, status/tier vocabularies, self-dependencies, unknown
references, the `blocks`/`depends_on` inverse invariant, dependency
cycles, single-producer artifacts, consumed-but-never-produced
artifacts, artifact id prefixes, unresolved placeholders in file claims, layer ordering, `meta.total_units`
coherence, and the recomputed `[computed]` claims (entry points,
max_parallel, critical-path sum, and critical-path-is-longest-path).

And: `state-mutation` (3 valid, 9 invalid) and `mutation-claim` (1
valid, 2 invalid). Every case here is a regression from the design review
of those kinds, and every invalid one carries an
`error_contains` sidecar, because the whole point of that review was
that exit-code agreement is not enough: a defect was found where all
three implementations rejected and two reported the wrong reason.

The invalid cases cover the RKM02 hollow proof, RKM04 unbound proof,
RKM03 inlined payload, blank and wrong-typed vocabulary tokens, an
impossible calendar date, a Unicode-digit timestamp, a required pin
deleted, a malformed kind selector, and RKC02 in both TOML shapes a
proof can take (a table and an array of tables, which is the shape that
bypassed one primary entirely).

The three `state-mutation/valid/` cases include two **regression
guards** that are easy to mistake for oversights. SPEC §12 ratifies two
escapes from conformance scope: a non-spec-reserved `template_kind`
string, and no `template_kind` at all. Both are asserted here as
MUST-ACCEPT, because rejecting them has been proposed and declined: doing so
would break behaviour the spec guarantees. Only a
`template_kind` that is present and is *not a string* is malformed
(SPEC §2.3), and that is `invalid/malformed-kind-selector.toml`.

Wanted next: corpora for `traceability`, `review-readiness`,
`kind-descriptor`, and `profile-descriptor`.

## Adding a kind

`PY_VALIDATORS` in `runner.py` maps a case directory to its Python
reference validator. A directory with no entry is a hard failure rather
than a silent skip, which is correct, but it means **adding a case
directory without registering it turns CI red**. That happened once:
`conformance/cases/state-mutation/` was added in one commit and
registered several commits later. If the runner reports "no Python
reference validator registered", that is the fix.

The complementary hazard is now gone. The repo-wide positive closure
sweep used to enumerate `conformance/cases/<kind>/invalid` exclusions by
hand and went red twice for want of a new line;
`validate_closure_root.py` now derives that skip from the path shape,
matching what the Rust and Go discovery paths always did.
