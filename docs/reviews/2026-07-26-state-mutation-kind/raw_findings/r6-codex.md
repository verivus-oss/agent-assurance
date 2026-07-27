# Round 6, Codex: NOT APPROVED

Final verdict message, reproduced as received. Em dashes normalized to commas
per the repo writing convention. Gateway job
`c5b71f32-cb76-450b-bb12-f874bb0792b4`, correlation `adacg-r6-codex-b`,
595 KB transcript, 6m59s. Provider session `019fa342-b360-7f33-889c-9f51ae2c0031`.

**Codex's blocker is correct and the initiator reproduced it.** This is the
second consecutive round in which Codex named a real defect.

## Blocker

`301a322` left false count headers in the three reference SQL seeds.
`reference/database/postgres/seed.sql:10-11` claims "Counts (verified against
ontology files; matches MANIFEST.toml)" and then "21 template kinds", but the
actual seed data and the manifest both contain 23. Line 26 claims 48 attribute
vocabularies against an actual 50. The same stale values remain in the SQLite
and DuckDB headers.

Reproduction, executed by Codex and re-executed by the initiator:

```
$ python3 validators/check_attribute_values.py --repo-root . --quiet
count-mirror gate: OK

$ python3 -c '... derive_seed_counts(...) ...'
postgres {'kind_descriptor': 23, ..., 'attribute_vocabulary': 50, ...}
sqlite   {'kind_descriptor': 23, ..., 'attribute_vocabulary': 50, ...}
duckdb   {'kind_descriptor': 23, ..., 'attribute_vocabulary': 50, ...}

$ rg -n '21 template|48 attribute|21 kind_descriptor' reference/database/*/seed.sql
postgres/seed.sql:11:  * 21 template kinds
postgres/seed.sql:26:  * 48 attribute vocabularies
sqlite/seed.sql:10:    21 template kinds
duckdb/seed.sql:8:    21 kind_descriptor
duckdb/seed.sql:9:    48 attribute_vocabulary
```

Codex's characterisation: "a green-but-false reference surface, and the headers
explicitly claim they are verified or CI-gated. `check_attribute_values.py` does
not parse those headers."

The initiator adds two details. First, the residue is wider than the two
headline numbers: `postgres/seed.sql:31` still says `kind_descriptor (20 rows)`
and `:161` says `attribute_vocabulary (46 rows)`, with the same pair at
`sqlite:20` / `sqlite:118` and `duckdb:107`. Second, `301a322`'s own commit
message says it fixed "the two engine seeds whose declared counts I had already
bumped while their rows still said 21", so the author fixed the data rows and
left the prose that describes them, which is exactly the residue Codex found.

## Other checks Codex executed

Exact-head scratch clone at `2d5809e`, fresh Rust and Go primary builds, 45-case
conformance pass, 12-sidecar discrimination pass, provenance / closure / RKC02
checks on both mutation-claim negatives, RDF verification at 1476 triples,
manifest drift, provenance containment, pin-resolution guards, safe-tools, Ruff
0.15.15, and CI-run status queries.

**Codex installed golangci-lint itself.** Its first attempt failed with
`golangci-lint: command not found`, so it ran
`GOBIN=/tmp/r6-codex/.review-bin go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.12.2`
and then linted all four Go modules: `0 issues` each. It is the only round-6
reviewer that ran the linter (Grok reported it as not installed and skipped it).

Codex also executed the allowlist regression independently: restoring Go's old
`tableOf` behaviour made `array-proof` pass and left `table-proof` rejected, so
the `ALLOWED_COLLISIONS` exemption is earned. That is the third independent
reproduction of that result this round, alongside Grok, Devin, Mistral and the
initiator.

Read rather than executed: SPEC 12.8.1, the profile pin list, the workflow
guards, and the count-gate code.
