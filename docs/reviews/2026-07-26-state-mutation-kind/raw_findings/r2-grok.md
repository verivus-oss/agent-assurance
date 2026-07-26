# Round 2, Grok: NOT APPROVED

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention; nothing else altered.

**Range:** `origin/main` (`f9a37cf`) .. `HEAD` (`1459666`), branch `profile/state-mutation-kind`
**Built:** Rust release binary; Go from this tree (not the stale prebuilt)
**Method:** read R1 request + four verdicts; read `spec.md` 12.8.2 and the three
mutation validators; recomputed digests; reconstructed the Codex collision;
differential-tested ~40 crafted documents

## Priority 1: SPEC 12.8.2 Bound tuples (`spec.md:1268-1314`)

**Prehashing injectivity.** Reconstructed the R1 Codex collision on the OLD
inline form and confirmed it still collides:

- Doc A: `operation = "a\nmutation.performed_at b"`, `performed_at = "c"`
- Doc B: `operation = "a"`, `performed_at = "b\nmutation.performed_at c"`
- Old form: same `binds_sha256` (`sha256:30e03916...c733`)
- New form: different digests (`18498611...` vs `c63cf9e5...`)

For a fixed declared field set with stable dotted labels, field labels determine
sort order, values never enter the stream, and records are fixed-width after the
label. The only remaining collision class is a SHA-256 collision on two
different UTF-8 value byte strings. That is the right security trade.

Could not construct two distinct field-value maps sharing one prehashed
`binds_sha256`. NFC vs NFD `café` produce different binds (correct under "UTF-8
bytes of the value", not under Unicode equality).

**`when-present`.** Sound for a proof binding: optional members would let the
producer choose what the external artefact commits to. Cost is real but is a
profile design choice, not a defect in 12.8.2.

**Double commitment.** No circularity. The tuple is computed from the five
mutation fields only; `binds_sha256` is not a tuple member. Producer order is:
compute tuple, write proof, pin digests, root.

**Still underspecified:** timestamp normalization (equality is string, not
temporal); Unicode form (NOT specified, two producers with equivalent strings
and different codepoints get different binds); bound-tuple field-path charset
(12.8.1 pins require `^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$`, 12.8.2 only says
"dotted path", so a future profile using a path with space or newline could
reintroduce stream ambiguity at the LABEL boundary).

## Priority 2: the ports (decisive)

Positives and all six shipped negatives agree on exit code across py/rs/go.
Then adversarial differential testing found a real split.

**Blocker reproduction: empty vocabulary tokens.** Every RKM02 key present,
correct binds, URI locator, but `scheme = ""` and `finality_basis = ""`:

| Implementation | Result |
|---|---|
| Python | FAIL (not in closed vocabularies) |
| Rust `--mode mutation-kinds` | PASS |
| Go `--mode mutation-kinds` | PASS |
| Rust auto | PASS |
| Go auto | PASS |

Cause is the empty-string special case in both ports, absent in Python:
`main.rs:3974-3986` rejects unknown scheme only `if !scheme.is_empty()`;
`main.go:3920-3928` same; `validate_state_mutation.py:281-292` uses
`if scheme is not None and scheme not in schemes`, and the empty string is not
`None`.

Not a cosmetic parity nit. It reopens the hollow-proof class R1 named: a
primary-only consumer accepts a `state-mutation` whose proof has no typed scheme
and no typed finality. Closure also passes (pins only care about the two
digests). Same pattern for empty finality alone with a real scheme.

**What did agree:** bound-tuple byte identity on the minimal example
(`sha256:7a5604ab...fda87`, independently recomputed); Unicode target
`https://x.example/café` with correct binds passes all three; wrong types
(`operation = 1`, `mutation = "nope"`, integer auth digest) all fail; non-ASCII,
`+`, and long-URI bounds show no exit-code split.

**Stale prose.** `state-mutation-kind.toml:221` still says primaries "do not
implement RKM02" and "a port is not scheduled". The ports do implement these.

## Priority 3: `mutation-claim` and RKC02

Claim with `[execution_proof]` (including an empty table) fails all three. Claim
without proof passes. Rename-to-claim cannot carry a proof past RKC02;
rename-to-mutation without proof fails RKM02. `claim-record.v1` is a coherent
third class. Three-record claim closure is consistent. No blocker.

## Priority 4: R1 blockers re-checked

| R1 blocker | Verdict now |
|---|---|
| Non-injective bound tuple (Codex) | Fixed; original collision no longer collides |
| RKM03 via `proof_locator` (Codex) | Fixed for raw non-URI paste |
| `provenance.source_sha256` unenforced (Grok) | Fixed in all three |
| Hollow proof (Grok) | Fixed for absent keys; NOT fixed for empty-string scheme/finality on primaries |
| `provider-receipt` (Gemini, not accepted) | Retained with RKM06. Re-argued: at SPEC no scheme is verified, so removing the honest weak label pushes mislabeling toward `tee-quote`/`zk-receipt`. Do NOT name vocabulary retention itself as the blocker |

## Verdict: NOT APPROVED

**Named blocker.** Primary/Python divergence on empty
`execution_proof.scheme` and `execution_proof.finality_basis`: Rust and Go treat
`""` as "skip vocabulary and RKM06", Python rejects as not in the closed
vocabulary. A document with blank scheme and finality, otherwise complete and
correctly bound, passes both primaries in auto mode and fails the Python
reference.

Until both primaries reject empty (and any non-member) scheme/finality the same
way Python does, the claim of RKM02/RKM06 parity is false, and hollow proof
remains open for primary-only consumers.
