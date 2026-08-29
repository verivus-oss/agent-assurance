---
id: ISS-003
title: `dagtoml-duckdb` + `dagtoml-duckdb-go` carry hardcoded `EXPECTED_COUNTS` arrays that duplicate MANIFEST
status: open
severity: low
opened: 2026-05-23
opened_in_commit: 9996826
classification: maintenance hygiene / mirror-pattern rot
---

> **Commit citations in this issue predate the repository.** This repository's
> root commit is `eccdcab` (2026-05-27). The commits cited below were made
> against the pre-mint tree and cannot be resolved here, so the claims that
> rest on them cannot be checked against the code they name. The citations are
> kept because they are the record as written. They are enumerated with reasons
> in [`validators/unresolvable-commit-citations.toml`](../../validators/unresolvable-commit-citations.toml)
> and gated by `validators/check_commit_citations.py`, which fails on any new
> unresolvable citation.

## Symptom

Two files in `tools/` carry hand-maintained constant arrays that
mirror `reference/database/MANIFEST.toml [verification.duckdb].expected_seed_counts`:

- `tools/dagtoml-duckdb/src/main.rs:21-27`:
  ```rust
  const EXPECTED_COUNTS: &[(&str, i64)] = &[
      ("kind_descriptor", 20),
      ("entity_kind_descriptor", 27),
      ("relation_descriptor", 31),
      ("attribute_vocabulary", 41),
      ("attribute_value_allowed", 106),
  ];
  ```
- `tools/dagtoml-duckdb-go/main.go:36-45`:
  ```go
  var expectedCounts = []struct {
      table string
      want  int64
  }{
      {"kind_descriptor", 20},
      {"entity_kind_descriptor", 27},
      {"relation_descriptor", 31},
      {"attribute_vocabulary", 41},
      {"attribute_value_allowed", 106},
  }
  ```

Both arrays are identical numeric snapshots of one MANIFEST row.
They are now gated by `validators/check_attribute_values.py`
(commit `9996826`) — drift here will fail CI. But the cure for the
symptom does not address the disease: the mirror still exists; the
gate just makes it noisy when it drifts.

Historical context: before `9996826`, both arrays were stale
relative to MANIFEST on every single field (19/26/30/37/81 vs
MANIFEST's then-current 16/24/31/33/79; both wrong vs the actual
seed 20/27/31/41/106). The drift had survived the disclosure
commit AND the cost commit without being noticed by any
reviewer — the Opus consultant surfaced it during the
methodology investigation.

## Why it matters

The whole point of the §12 closure-root rule and the
methodology-convergence session is that brittleness propagates.
A hand-maintained mirror in a Rust file AND a Go file AND a
MANIFEST table AND the actual seed.sql files is four places
where the same number lives. Three of those places agree only
because a CI gate forces them to. The fourth (the seed itself)
is the truth; the others are documentation.

The current CI gate is sufficient for correctness, but it is
not sufficient for ergonomics: every PR that touches MANIFEST's
verification block has to also touch two source files. New
contributors will:

- Edit MANIFEST.
- Push.
- CI fails on the Rust hardcode.
- Edit Rust.
- Push.
- CI fails on the Go hardcode.
- Edit Go.
- Push.
- CI green.

Each cycle is a minute lost; multiplied across the project's
expected ontology evolution (every new profile, every new kind),
this is real friction the project doesn't need to ship. The
brittleness-as-feature principle says invalidations propagate
visibly, but it does not say the same number must be typed in
three places.

## Safeguard (what would prevent recurrence)

The safeguard is already in place: `check_attribute_values.py`
gates drift across all three sites. Nothing further is needed
to prevent the symptom (stale hardcodes shipping). What's
needed is to remove the duplication so the gate becomes a
no-op for these specific surfaces, not a recurring tax.

If the hardcodes are eliminated (resolution below), the gate
entries for `rust.EXPECTED_COUNTS.*` and `go.expectedCounts.*`
in `check_attribute_values.py` can be deleted: there's nothing
to check against once the values are read at runtime.

## Resolution steps (the actionable fix)

### Rust side (`tools/dagtoml-duckdb/src/main.rs`)

1. Add `toml` (or `toml_edit`) to the crate's dependencies if
   not already present.
2. Replace the `EXPECTED_COUNTS` const + its usage with a
   runtime read from `MANIFEST.toml`:
   ```rust
   // Read MANIFEST [verification.duckdb].expected_seed_counts at
   // startup. The hand-maintained const has been removed; see
   // docs/issues/2026-05-23-ISS-003-...
   let manifest: toml::Value = toml::from_str(
       &std::fs::read_to_string("reference/database/MANIFEST.toml")?,
   )?;
   let expected = manifest
       .get("verification")
       .and_then(|v| v.get("duckdb"))
       .and_then(|v| v.get("expected_seed_counts"))
       .and_then(|v| v.as_table())
       .ok_or_else(|| "MANIFEST missing [verification.duckdb].expected_seed_counts")?;
   // Use `expected.iter().map(|(k, v)| (k.as_str(), v.as_integer().unwrap()))`
   // where the original const was iterated.
   ```
3. Verify the binary still builds + passes `cargo test`.
4. Verify `cargo run --release -p dagtoml-duckdb -- verify` produces
   identical output before and after.

### Go side (`tools/dagtoml-duckdb-go/main.go`)

1. Add `github.com/BurntSushi/toml` (likely already present from
   the validate-go module) or `github.com/pelletier/go-toml/v2`.
2. Replace `expectedCounts` with a runtime decode:
   ```go
   type manifestRoot struct {
       Verification struct {
           Duckdb struct {
               ExpectedSeedCounts map[string]int64 `toml:"expected_seed_counts"`
           } `toml:"duckdb"`
       } `toml:"verification"`
   }
   var root manifestRoot
   if _, err := toml.DecodeFile("reference/database/MANIFEST.toml", &root); err != nil {
       return err
   }
   expected := root.Verification.Duckdb.ExpectedSeedCounts
   // Iterate as before.
   ```
3. `go build ./...` and `go test ./...` pass.
4. The binary's verify output should be byte-identical to the
   pre-change version.

### Gate cleanup

5. Once both tools read MANIFEST at runtime, delete the two
   blocks in `validators/check_attribute_values.py` that gate
   `rust.EXPECTED_COUNTS.*` and `go.expectedCounts.*` (lines
   parsing the Rust + Go source). The gate file shrinks; the
   remaining surfaces (MANIFEST internal consistency + MANIFEST
   vs seed truth + MANIFEST vs ontology) are still gated.

### Documentation

6. Update CHANGELOG with a one-line note that the dagtoml-duckdb
   tools now read MANIFEST at runtime.
7. Close this issue with `closed_by: <commit-sha>` and a closing
   note pointing at the new runtime-read sites in both tools.

## Acceptance criteria

- `tools/dagtoml-duckdb/src/main.rs` has no literal numeric
  constant array that mirrors `expected_seed_counts`. `grep -n
  '"kind_descriptor"' tools/dagtoml-duckdb/src/main.rs` returns
  zero hits.
- Same for `tools/dagtoml-duckdb-go/main.go`.
- `validators/check_attribute_values.py` no longer parses
  `EXPECTED_COUNTS` or `expectedCounts`; the file is shorter
  and the remaining surfaces still pass.
- A clean run of both tools (`cargo run -p dagtoml-duckdb -- verify`
  and `go run ./tools/dagtoml-duckdb-go verify` or equivalent)
  produces identical exit codes and output as the pre-change
  version against the same MANIFEST.

## Worked counter-example

If runtime-read had been the design from the start of the
dagtoml-duckdb tools' existence: the disclosure commit, the cost
commit, AND the full count-mirror cleanup commit would each have
required zero edits to either of these files. The drift the
Opus consultant flagged could not have existed.
