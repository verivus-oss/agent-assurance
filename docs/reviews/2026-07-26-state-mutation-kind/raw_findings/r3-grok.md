# Round 3, Grok: NOT APPROVED

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention; nothing else altered.

**Range:** `origin/main` (`f9a37cf`) .. `HEAD` (`a7efe37`); fix under review `d333d52`
**Built from this worktree:** Rust release binary; Go `/tmp/dagtoml-validate-go`
**Method:** read R1/R2 request plus eight verdicts; read `Field`/`fieldOf` and
RKC02 paths; differential-tested blank/typed/non-table/calendar fixtures across
py/rs/go; re-ran the Python closure sweep as CI invokes it

## Priority 1: the R2 fix class

### Claimed R2 blocker: fixed, verified by execution

| Fixture | py | rs | go |
|---|---|---|---|
| `scheme = ""`, `finality_basis = ""` | fail vocab | fail vocab | fail vocab |
| `scheme = 1`, `finality_basis = 2`, `proof_locator = 3` | fail | fail | fail |
| shipped `state-mutation-blank-scheme.toml` | 1 | 1 | 1 |
| shipped `state-mutation-wrong-typed-proof.toml` | 1 | 1 | 1 |

Vocabulary membership no longer has an empty-string or wrong-type escape on the
primaries. Whitespace-only scheme and finality also fail all three.

### What the fix closed, and the nearest open neighbour

`Field` / `fieldOf` close the SCALAR three-way collapse (absent / blank /
wrong-typed string fields). They do NOT close the same collapse one structural
level up: table-shaped sections still go through `as_table` / `tableOf`, which
return "not a table" for both absent and present-but-not-a-table.

For REQUIRED tables on `state-mutation` (`[mutation]`, `[execution_proof]`),
that still rejects everywhere, though the message claims "missing" even when
the key is present as `1`, `[]`, `true`, or a string. Accept/reject parity
holds; the diagnostic is dishonest.

For FORBIDDEN presence on `mutation-claim` (RKC02), the same collapse is an
accept path on Go only.

### BLOCKER: Go RKC02 treats non-table `execution_proof` as absent

Starting from the valid minimal claim, insert at document root:

```toml
execution_proof = 1
```

| Implementation | Mode | Result |
|---|---|---|
| Python | kind | FAIL RKC02 |
| Rust | `--mode mutation-kinds` and auto | FAIL RKC02 |
| Go | `--mode mutation-kinds` and auto | PASS |

Same split for `execution_proof = "hollow"`, `= []`, `= true`. An empty
`[execution_proof]` table is rejected by all three, since Go only sees tables.

Cause: `tools/dagtoml-validate-go/main.go:3945` calls
`tableOf(doc, "execution_proof")`, and `tableOf` (`main.go:63-69`) is false for
any non-map value, so RKC02 never fires. Contrast Rust
`tools/dagtoml-validate-rs/src/main.rs:3994` (`.is_some()`) and Python
`validators/validate_state_mutation.py:277` (`in doc`), which reject any
presence.

This is the next member of the R2 class: round 2 closed "present scalar that
looks empty"; this is "present key that looks like no table". RKC02 is the
claim/proof seam. A primary-only Go consumer accepts a claim that still carries
the proof field name under a non-table value.

Remaining `str_field` / `stringOf` on `provenance.source_sha256` still collapse
absent and wrong-typed, but the catch-all fails closed (all three reject empty
and integer). That reasoning holds.

## Priority 2: calendar validity

Hand-rolled month/day/leap/hour/minute/second checks agree across all three on
25 cases, including `0000-01-01`, month and day `00`, month `13` and `99`,
Apr 31, Feb 29 in 1900 (reject), 2000 (accept), 2100 (reject), 2024 (accept),
second `60` (accept) and `61` (reject), hour `24`, minute `60`, 1 and 9
fractional digits (accept), 10 (reject), and a Unicode year digit (reject).

No overflow or panic path found: year is four ASCII digits into `u32` / `int`
over a fixed 4-byte window.

Leap-second policy: unconditional `second <= 60` matches a permissive reading
of RFC3339 5.6 and keeps the three aligned. It does accept leap seconds at
instants where none was declared. For a bound freshness claim that is a
deliberate over-accept. Prefer keeping it unless the SPEC wants IERS-table
awareness, which would reintroduce versioned external data into the byte
contract. Not a blocker.

## Priority 3: SPEC 12.8.2 additions (`spec.md:1298-1315`)

| Bullet | Verdict |
|---|---|
| Non-string bound field is an error; MUST NOT coerce or treat as absent | Correct, implementable, matches the RKM04 skip-unless-all-strings guard |
| Field paths frozen to the 12.8.1 grammar | Correct; closes label-boundary ambiguity |
| No Unicode normalization | **Right call** |

Gemini's "must mandate a normalization form" is the wrong trade for a byte
commitment. Normalization depends on a Unicode version; a bound tuple must
recompute from document bytes alone. NFC versus NFD producing different digests
is intentional and stated.

"Constrain the field's grammar so only one encoding is representable" works for
closed tokens (`operation`, the scheme vocabularies: ASCII token classes
already force a single encoding). For free-form `target_id` URIs it only works
if the grammar forbids non-ASCII codepoints or requires a single escaped form,
for example rejecting raw non-ASCII and requiring percent-encoding. Feasible
but harsh; the SPEC's escape hatch is honest about the cost.

## Priority 4: classes this board keeps missing

New class exercised this round: presence checks implemented only through typed
table accessors. That hides present-but-wrong-typed keys on FORBIDDEN fields
(RKC02), while the same pattern on REQUIRED fields only corrupts diagnostics.
Rounds 1 and 2 hammered scalar fields and never asked what happens when the
table itself is the wrong TOML type.

Other underexamined classes, not blockers today:

1. Enumerated CI exclude lists versus generic discovery. Primaries skip
   `conformance/cases/*/invalid` generically; the Python closure sweep still
   lists explicit `--exclude` paths (`validate.yml:383-386`). Adding
   `conformance/cases/<new-kind>/invalid` without updating them can turn the
   sweep red again. Residual Codex-class hazard.
2. Compiled versus ontology-loaded vocabularies. Drift is possible without a CI
   lock that diffs them.
3. Cross-layer accept when one mode is green.

CI claim re-run: the closure sweep as CI invokes it PASSED at 90 files. Shipped
positives pass py/rs/go under `--mode mutation-kinds`; the round-2 negatives
fail all three.

## Verdict: NOT APPROVED

**Named blocker: MUTATION-CLAIM-RKC02-TYPE-BYPASS.** Go enforces RKC02 only
when `execution_proof` is a table (`tools/dagtoml-validate-go/main.go:3945` via
`tableOf` at `main.go:63-69`). A `mutation-claim` with root-level
`execution_proof = 1` (or string, array, bool) is accepted by the Go primary in
both auto and `--mode mutation-kinds`, and rejected by Python
(`validators/validate_state_mutation.py:277`) and Rust
(`tools/dagtoml-validate-rs/src/main.rs:3994`).

Same class as R2's empty and wrong-typed scheme bypass: a typed accessor
collapses "absent" and "present but wrong shape" into one skip path. R2 closed
that for proof scalars; it remains open for the claim's forbidden proof key.
