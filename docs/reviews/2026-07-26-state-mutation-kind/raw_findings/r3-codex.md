# Round 3, Codex: NOT APPROVED

Final verdict message, reproduced as received. Em dashes normalized to commas
per the repo writing convention; nothing else altered. Full session transcript
345 KB (gateway job `091b633f-e50d-486d-9ff0-029ad78ceb29`, correlation
`1dd81a20-cd87-4850-b619-b7aaef3c2554`).

Codex reached the SAME blocker as Grok independently, and pushed it one step
further by using an array of tables carrying real proof material rather than a
bare scalar. That variant is the one the repo now ships as a fixture.

---

Not approved.

I built both primaries from this worktree: `cargo build --release` and
`go build -o /tmp/dagtoml-validate-go .`.

The committed positives and mutation negatives behaved as expected, and the
CI-shaped Python closure sweep passed at 90 files. Timestamp edge tests also
agreed across Python, Rust, and Go.

Finding: Go's RKC02 check only rejects `execution_proof` when it is a table.
RKC02 forbids a mutation-claim from carrying proof material
(`profiles/com.verivus.runtime/mutation-claim-kind.toml:160`), but Go checks
`tableOf(doc, "execution_proof")` only
(`tools/dagtoml-validate-go/main.go:3945`). `tableOf` returns false for arrays,
strings, integers, and booleans (`tools/dagtoml-validate-go/main.go:63`).

I reproduced this by adding a root key to `examples/minimal-mutation-claim.toml`:

```toml
execution_proof = [{ scheme = "provider-receipt", finality_basis = "provider-acknowledged", proof_sha256 = "...", binds_sha256 = "...", proof_locator = "https://proof.example/receipt" }]
```

Python and Rust reject it under RKC02. Go passes both explicit
`mutation-kinds` mode and auto mode. Closure validation still passes, so this
is not masked by the closure layer.

**BLOCKER: RKC02-NON-TABLE-PROOF-BYPASS at
`tools/dagtoml-validate-go/main.go:3945`.**

Earlier in the same session, on the non-table variant of the REQUIRED tables:

> I also checked the proof-shaped array variant, not just a scalar. A
> `mutation-claim` with `execution_proof = [{ ... }]` remains closure-valid and
> passes Go in both explicit `mutation-kinds` mode and auto mode, while Python
> and Rust reject it under RKC02.

And on `state-mutation` with a non-table `execution_proof` (int, array, bool,
string): all three implementations FAIL, so accept/reject parity holds there
and only the diagnostic is wrong.
