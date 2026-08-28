# Changelog

All notable changes to the DAG-TOML specification and the Agent
Assurance Profile will be documented here.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **`conformance/coverage_audit.py`, a mutation-based coverage gate, plus a
  ratcheted baseline.** Every `errors.append(...)` in a profile kind-layer
  validator is a check. The audit disables each one in turn and asks whether any
  gate in the repository notices; one that nothing notices is a check nothing
  tests, even when the code is correct.

  It exists because reading does not find these. The first audit run found
  **25 unprotected checks out of 45** in a surface that had been inspected
  repeatedly, with only a handful located that way.

  The cause is one construction defect, not 25 oversights: the corpus was built
  by mutating a single field of a known-good document, so every fixture inherits
  correct values everywhere else and any check on a commonly-correct field is
  structurally invisible to the oracle.

  `conformance/coverage-baseline.toml` declares the tolerated number and CI fails
  when the real number exceeds it, so adding a check without a fixture that
  exercises it is now a build break. It is a ratchet: the number may only fall
  without a deliberate, reasoned edit. Same contract as `known-divergences.toml`
  and `TOML_CONFORMANCE_SKIPS`.

  One methodological note recorded because it nearly shipped: an earlier version
  of the audit reported 28 of 28 checks as covered. That uniformity was the tell.
  It counted "an `examples/negative` fixture is accepted by validator X" as
  detection, but several of those are closure-layer negatives that X never
  rejected, so the rule fired on a pre-existing condition. Detection is now
  measured against a baseline recorded before any mutation.

- **Two closed-vocabulary gaps closed**, chosen first because they are the checks
  a policy engine actually filters on. `witness-scheme-unknown.toml` covers a
  `witness.scheme` outside the closed vocabulary, which was unprotected because
  every fixture carried `tls-notary`. `finality-basis-unknown.toml` covers a
  `finality_basis` outside its vocabulary, which was unprotected for the same
  reason. Both are closure-valid, both are rejected by all three implementations,
  and each was verified to kill the mutant it was written for. Baseline ratcheted
  25 to 23.

- **An external CI assertion for discrimination coverage.**
  `conformance/discrimination.py` carries its own coverage self-check, and that
  check works: dropping a kind from `KINDS` fails it. But it is a SAME-FILE
  oracle. The same defeat path is reproducible: delete the
  self-check and the kind together, and the script exits 0 with nothing to say. A
  guard that lives in the file it guards can always be removed alongside the
  thing it guards.

  `.github/workflows/validate.yml` now asserts the coverage independently. It
  derives one side from the FILESYSTEM (which kinds ship `*.expected.toml`
  sidecars) and the other from the SOURCE DECLARATION (`KINDS` and
  `KIND_VALIDATOR`, read with `ast` and never imported or executed), then
  compares. It shares no code with `discrimination.py`, so neutralising or
  deleting that file's self-check does not disable it. Verified against both
  defeat paths: with the in-file guard neutralised and `api-snapshot` dropped,
  `discrimination.py` exits 0 while the CI assertion reports
  `FAIL: uncovered kinds: api-snapshot`; dropping a `KIND_VALIDATOR` mapping the
  same way reports `FAIL: unmapped`.

  This does not make the gate undeletable, and it is not claimed to. Removing the
  CI step is still possible, but it is a visible change to the workflow, which is
  the trust root and the thing review actually watches. The point is that the
  guard no longer sits inside its own subject.

- **`conformance/discrimination.py` coverage self-check.** The api-snapshot
  coverage fix was itself unprotected: reverting
  `KINDS` to drop `api-snapshot` was a MUTATION SURVIVOR, since the shipped suite
  still exited 0 and merely reported `14 sidecar(s) over 14 case(s)` instead of
  19 over 25. A coverage fix whose removal nothing detects is not a fix. The
  check now fails when a kind ships sidecars but is absent from `KINDS`, and when
  a `KINDS` entry has no `KIND_VALIDATOR` mapping.

  Writing that guard immediately found a second, pre-existing instance of the
  same gap, and chasing it down turned up something larger. `implementation-dag`
  ships 18 sidecars that had never been cross-checked, and the reason they could
  not discriminate was not sidecar quality: **17 of its 18 invalid fixtures were
  malformed.** Each carried `tier1_units = '[U01, U02]'`, a quoted STRING rather
  than an array, so the validator iterated its characters and every fixture
  emitted the same pile of unrelated complaints about `U`, `[` and `]`. The same
  17 were also missing their `[computed.max_parallel]` table. All 17 derive from
  one bad template.

  That violated the corpus's own contract, that each invalid fixture "mutates
  exactly one aspect of a known-good document, so a failure isolates one
  semantic rule". Nothing was silently passing: after removing the unrelated
  defect every fixture still fails for its own stated reason. The hazard was
  latent rather than live, and it is the same class as an earlier finding in
  this work, a fixture rejected for the wrong reason. Had cycle detection or
  layer ordering regressed, the fixture would still have failed on
  `tier1_units` and the regression would have been masked.

  Fixed rather than exempted: `tier1_units` repaired and a correct
  `[computed.max_parallel]` added across the 17, so 12 of 18 now emit exactly
  one error and the other six emit only genuine cascades of their single
  mutation. Four sidecars whose needles were too generic were rewritten with
  direction-specific discriminators. `implementation-dag` is now covered, and
  the check reports 37 sidecars over 43 cases, up from 19 over 25.

  An earlier revision of this change added an `UNCOVERED_KINDS` exemption for
  `implementation-dag` instead. That was wrong and is not what shipped: it
  defeated the new guard on its first firing and handed the next contributor a
  documented way to silence it. There is no exemption mechanism.

- **`conformance/parity_sweep.py`.** The kind-layer-against-kind-layer sweep that
  produced the zero-divergence figure now ships, so the number is reproducible
  instead of asserted. Looking for it in `runner.py` gives 52 cases, which is a
  different instrument measuring a different thing.

### Fixed

- **The documented pre-commit closure-root command failed on a clean tree.**
  `CONTRIBUTING.md` instructs contributors to run
  `validate_closure_root.py --discover .` before `git commit` and adds "do not
  commit if it is red"; `README.md` lists the same command under Local
  Validation. Both omitted `--exclude examples/negative`. The instruction was
  correct when written: CI ran the bare `--discover .` form too, until #56
  (`1016bd0`) made the `api-snapshot` closure negatives deliberately
  closure-invalid and added the flag to the workflow without adding it to
  either document. Since then the documented command has exited 1 on an
  unmodified tree, currently on five asserted-negative fixtures that the
  negative-agreement step proves invalid instead. A contributor following the
  instruction saw a red gate on a healthy repository, which is the fastest way
  to teach people to skip a gate. Both documents now carry the flag CI uses.

- **Four count surfaces in the reference-database and ontology prose had
  drifted from the ontology.** None of them is gated: `check_manifest_drift.sh`
  compares `MANIFEST.toml` to the ontology and passes, and prose that restates
  those numbers sits outside its reach. Corrected against the tree at
  `38cd729`:

  - `reference/database/README.md` claimed 15 template kinds (5 core + 9
    profile), 23 entity kinds, 30 relation predicates, and 29 attribute
    vocabularies, plus "the 14 kinds" in the JSONB design principle. Every one
    was wrong: the figures are 23 (6 core), 27, 31, and 50. The file also
    named only two of the five ontologies as its derivation source, which is
    where 29 rather than 50 came from.
  - `core/ontology.md` section 3 called its predicate tables "authoritative
    for `ontology_version = 1`" while listing 30 of the 31 `[[relations]]`
    blocks. The missing one was `cites_upstream`, the marker that binds a
    descriptor field into the SPEC section 12 `closure_root` digest. It is now
    documented in a new section 3.5, numbered after 3.4 rather than inserted
    after 3.2 so the section 3.3 anchors cited from three profile ontology
    files keep resolving.
  - `reference/database/graph/schema.cypher` carried header comments written
    to make its known seed gap legible; the comments had themselves gone stale
    twice while the data stood still. They stated 21 template kinds against
    the ontology's 23, "1 com.verivus.runtime" against three, and an
    `expected_node_counts` of 21/27/31 against MANIFEST's 23/27/31. The
    comments now name the eight absent template kinds and four absent entity
    kinds explicitly and defer every total to `MANIFEST.toml`.
  - `conformance/README.md` reported the corpus as `api-snapshot` 2 valid / 6
    invalid and `state-mutation` 3 / 9; the tree holds 2 / 18 and 3 / 13. The
    section is now a table with a re-derivation command beside it, and it
    records that six `api-snapshot` invalid cases still assert by exit code
    alone with no `error_contains` sidecar.

  Each corrected surface now states that `MANIFEST.toml` or the TOML ontology
  is the source of truth and that the prose is a restatement, so the next
  reader knows which side to believe.

- **ISS-002's figures were certifying a stale file as fixed.** The issue's
  acceptance criterion required "a clean Neo4j load of `schema.cypher` contains
  20 KindDescriptor nodes"; the ontology declared 23 by `38cd729`, so meeting
  the criterion as written would have left three kinds unseeded and closed the
  issue anyway. The criterion now binds to
  `MANIFEST.toml [verification.graph].expected_node_counts` at the closing
  commit rather than to a copied number, the missing-kind list is refreshed
  from five to eight, and the resolution steps tell the fixer to re-derive both
  lists from the tree instead of copying them out of the issue. Observations
  dated to commit `9996826` are kept as written and marked as such.

- `com.verivus.runtime` returns to `ontology_version = 1`. The two new
  vocabularies moved it to `2`, but `core/ontology.md` and `spec.md` section 8
  both hold both version pins frozen until the first public release, and
  `schema_version` is still `0.1.0`. Core and the other three profiles never
  moved, so one profile at `2` was drift rather than policy.

- **Go `--help` still omitted `mutation-kinds` and `api-snapshot`.** The earlier
  fix replaced the first matching occurrence, which was `parseMode`'s error
  string, so the `flag.StringVar` help text never changed while the CHANGELOG
  claimed both primaries listed the modes.

- **RKV03 hardening: `snapshot.witness.present` is now a required field.** An
  `api-snapshot` that omits `[snapshot.witness]` entirely is now MALFORMED rather
  than valid: the absence of a witness must be ASSERTED (`present = false`) and
  cannot be achieved by deletion. Implemented in all three implementations
  together, so the parity established for RKV01 to RKV03 holds.

  What this buys is bounded, and the descriptor says so rather than overclaiming:
  it does NOT stop a producer who re-roots the document from writing
  `present = false`, because nothing computed from inside a document can. What it
  removes is the shape in which a STRIPPED document and an honestly unwitnessed
  one are indistinguishable, so a downgrade becomes a positive statement inside
  the closed content that an auditor and a policy engine can both read.

  This is a breaking change at the kind layer for documents that carried no
  witness table. Six fixtures were updated to assert `present = false`, which
  leaves every closure root unchanged because `present` is not a pinned record.
  In particular `conformance/cases/api-snapshot/valid/unwitnessed-three-record.toml`
  keeps its frozen parity-matrix property: that row is about the three-record
  STREAM (`attestation_sha256` absent), not about the witness table's existence.
  `witness-stripped` is now the well-formed downgrade (`present = false` plus the
  attestation removed) against a stale four-record root, which is a stronger case
  than deletion because the producer does the downgrade correctly and the stale
  anchored root still fails to reproduce.

  New case `conformance/cases/api-snapshot/invalid/witness-absent.toml` pins the
  deletion vector itself. It is deliberately closure-VALID, so the kind layer is
  demonstrably the only thing rejecting it.

### Fixed

- **`conformance/discrimination.py` did not cover `api-snapshot`.** `KINDS` listed
  only the two mutation kinds and `collect_output` hardcoded
  `validate_state_mutation.py`, so every api-snapshot sidecar sat uncovered: the
  cross-product never ran over them and they could have blessed the wrong defect
  class with nothing noticing. That is the exact failure mode this file exists to
  catch, one level up. `KINDS` and a new `KIND_VALIDATOR` map now cover
  api-snapshot, taking the check from 14 sidecars over 14 cases to 19 over 25.
  All existing sidecars discriminate under the widened cross-product.

- **Full kind-layer parity across the validator triad.** `RKV01` (sub-part
  consistency), `RKV02` (no inlined secret or raw header value) and `RKV03`
  (the witness conditional) were implemented in `validators/validate_api_snapshot.py`
  ALONE. Both primaries carried only the shared meta/provenance/IJB/closure
  surface for an `api-snapshot`, so a primary-only consumer accepted an inlined
  `authorization` header, a witness claiming `present = true` with no attester,
  and a `descriptor_sha256` that did not match the capture the document cites.
  The CI negative-agreement gate did not see it: those fixtures were asserted
  against the Python reference only, so the negatives agreed and the corpus
  looked green. Both primaries now implement all three
  (`tools/dagtoml-validate-rs` `mod api_snapshot`,
  `tools/dagtoml-validate-go` `validateAPISnapshot`), reachable as
  `--mode api-snapshot` and via the `auto` dispatch, and every api-snapshot
  negative is now asserted against all three implementations.

  An empirical sweep over all 87 fixtures that have a reference validator now
  reports **zero** accept/reject divergences, comparing kind layer against kind
  layer. `enforced_by_primaries` in the kind descriptors was NOT a usable audit
  key for this: it is under-declared, marking only 24 of 97 declared invariants
  as primary-covered while the primaries in fact implement far more, so the
  parity claim is measured from behaviour rather than from declarations.

- **Four `conformance/cases/api-snapshot/invalid/` cases pinning the ported
  rules.** `inlined-secret-header`, `header-value-inlined`, `witness-incomplete`
  and `subpart-descriptor-mismatch`. Every one is deliberately closure-VALID and
  honestly re-rooted, so the closure layer stays silent and the kind layer is
  demonstrably the only thing rejecting them; each sidecar asserts that with
  `error_not_contains = ["pinned closure record"]`.

  `subpart-descriptor-mismatch` exists because
  `examples/negative/api-snapshot-bad-subpart-digest.toml` cannot serve as the
  cross-implementation gate for RKV01: it is deliberately double-defective (its
  `source_bytes` is wrong so it also fails the provenance-negative sweep), so an
  implementation that checked only `source_bytes` rejected it for the wrong
  reason and still looked green. The conformance case removes that escape.

### Fixed

- **A three-way divergence in the `state-mutation` URI value grammar.** The
  Python reference and both primaries disagreed on `mutation.target_id` and
  `execution_proof.proof_locator`, on two independent axes. LENGTH: the regex
  `{1,480}` counts CODE POINTS while `str::len()` and `len()` count BYTES, so a
  value of 241 two-byte characters (482 bytes) was accepted by the reference and
  rejected by both primaries. CONTROL CHARACTERS: `[^\s\x00-\x1f\x7f]`
  excludes C0 and DEL but not C1 (U+0080 to U+009F), so 31 of the 32 C1 code
  points were accepted by the reference and rejected by both primaries (U+0085
  agreed only because `\s` happens to cover NEL). `target_id` is a member of the
  RKM04 bound tuple, so the grammar the descriptor calls defence in depth was the
  one the three implementations disagreed on. The reference now uses a
  hand-rolled `is_uri_shaped` matching the primaries on both axes, and
  `conformance/cases/state-mutation/invalid/target-id-c1-control.toml` and
  `proof-locator-oversize-multibyte.toml` pin both.

  The primaries were the stricter side throughout, so no unsafe document could
  ship through CI; what was broken was the triad's own guarantee that no single
  implementation self-vouches.

- **Stale `--mode` help text in both primaries.** Neither usage string listed
  `mutation-kinds`, which both had implemented since the state-mutation kinds
  landed. Both now list it and `api-snapshot`.

- **`conformance/discrimination.py`, and `error_not_contains` in the runner.**
  The corpus asserted less than it appeared to: a sidecar
  that matches its own case is necessary and not sufficient, because a needle
  can also match a DIFFERENT case's output and would then bless the wrong
  defect class. `hollow-proof.expected.toml` asserted only `"RKM02"`, and the
  RKC02 diagnostic contains that string incidentally while naming the
  invariants a proved record must face. Swapping the sidecar onto
  `mutation-claim/invalid/array-proof` left the corpus green.

  Running the full cross-product showed four sidecars affected, not one:
  `unbound-proof`'s bare `"RKM04"` matched four other cases. The new check runs
  every sidecar against every other case in CI, with a whitelist for pairs that
  legitimately share a defect class and discriminate by verdict instead.

  `error_not_contains` exists because presence-only needles cannot separate a
  case from one whose output is a strict SUPERSET of its own, which is the
  relationship between `hollow-proof` and `required-pin-missing-proof`. The
  former now asserts the closure layer stayed silent.

- **An RKM06 conformance case.** The scheme-to-finality coherence invariant was
  enforced in all three implementations with no fixture at all.
  It is the mitigation that kept `provider-receipt` in the ontology after a
  proposal to remove it, so leaving it untested left that objection
  unanswered.

- **A shared conformance corpus for `state-mutation` and `mutation-claim`**,
  which was independently named as the thing that ends the review cycle
  rather than another pass of it. 15 new cases (4 valid, 11
  invalid) under `conformance/cases/`, driven through the Rust primary, the Go
  primary and the Python reference by the existing `conformance/runner.py`.

  Every invalid case carries an `error_contains` sidecar asserting the defect
  CLASS, not the exit code. That distinction is the point: a defect was found
  where all three implementations rejected the document and two reported
  the wrong reason, which an exit-code corpus would have passed. The mechanism
  was negative-controlled by planting an unmatchable substring and confirming
  the runner fails all three implementations on it.

  Cases are the accumulated regressions of the review: RKM02 hollow
  proof, RKM04 unbound proof, RKM03 inlined payload, blank and wrong-typed
  vocabulary tokens, an impossible calendar date, a Unicode-digit timestamp, a
  deleted required pin, a malformed kind selector, and RKC02 in both TOML
  shapes proof material can take. `mutation-claim` had no conformance cases at
  all before this, which is why its RKC02 bypass survived so long.

  Two `state-mutation/valid/` cases are regression guards rather than examples:
  SPEC §12 ratifies both a non-spec-reserved `template_kind` and no
  `template_kind` at all as escapes from conformance scope, and both are now
  asserted MUST-ACCEPT because rejecting them was proposed and declined.

### Fixed

- **CI was red on this branch for a second reason,** unnoticed for some time:
  `conformance/cases/state-mutation/` was added without a
  `PY_VALIDATORS` entry in `conformance/runner.py`, and an unregistered case
  directory is a hard failure there. Both mutation kinds are now registered.

- **The enumerated-exclusion hazard that caused it, twice.** The repo-wide
  positive closure sweep listed `conformance/cases/<kind>/invalid` exclusions
  by hand, so adding a kind turned the sweep red until someone remembered the
  line. `validate_closure_root.py` now derives that skip from the path shape,
  matching what the Rust and Go discovery paths always did, and the workflow's
  per-fixture negative assertions for these kinds are discovered by glob rather
  than listed. Verified by adding an unregistered invalid tree and confirming
  the sweep stays green.

- A pre-existing conformance case (`required-pin-missing-proof`) declared
  `source_bytes = 417` against a 416-byte capture, so it failed for two
  reasons at once and proved neither. Corpus cases must fail for exactly the
  reason they name.

- **A malformed kind selector silently dropped every pinned closure record.**
  SPEC 2.3 says `meta.template_kind` is a
  string. All three implementations read a present-but-NON-STRING value as
  ABSENT: pin resolution returned no pins and no error, degrading the document
  to the SPEC 12.8 one-record source-hash closure, while every kind validator
  dispatched on the same value and correctly concluded "not my kind". A
  document with `template_kind = 1`, a full `[mutation]` table, a hollow
  `[execution_proof]`, and an honest one-record root therefore passed closure,
  provenance and the kind layer in all three. This is the pin-free fall-through
  that all three functions' own docstrings say does not exist. It affects every
  kind, not only these two, and predates this branch.

  The fix is deliberately narrow. SPEC 12 ratifies TWO escapes from conformance
  scope, a non-spec-reserved `template_kind` string and no `template_kind` at
  all, and both remain legal and are now asserted as legal so a later change
  cannot quietly remove them. Only the malformed case, which is neither escape,
  is rejected.

- **`validate_state_mutation.py` crashed on a table-typed vocabulary value.**
  `scheme not in schemes` raises `TypeError` on
  an unhashable value, so a table-typed `scheme` or `finality_basis` aborted
  the validator with a traceback. It exited 1, so it failed closed, but a
  traceback is not a defect report and it hid which invariant fired. The
  primaries already reported these cleanly.

- **RKC02 could be bypassed in the Go primary by shape.** RKC02 forbids a
  `mutation-claim` from carrying `[execution_proof]`, and Go enforced it
  through its table accessor, which answers false both for an absent key and
  for a key holding a non-table. So a claim carrying
  `execution_proof = [{ scheme = "provider-receipt", ... }]`, a fully populated
  provider receipt in an array of tables, passed the Go primary in both auto
  and explicit mode while Python and Rust rejected it. The document is
  closure-valid, so nothing else caught it. An invariant that forbids a field
  must ask whether the field is PRESENT, not whether it is well-formed; Go now
  uses `hasKey`.

  This is an earlier defect one structural level up. That one closed
  absent-versus-blank-versus-wrong-typed for proof SCALARS; the same collapse
  survived in the typed TABLE accessors.

  The same class appears on the REQUIRED tables, where all three
  implementations still reject but report `mutation = 1` as a MISSING table.
  Not a bypass, but it contradicted the rule SPEC 12.8.2 had just gained, that
  a present-but-wrong-typed element MUST NOT be treated as absent. All three
  now distinguish the two cases at both table sites.

- **Reference-versus-primary divergences in the mutation kinds.** Three were
  reproduced, all now closed with regression
  fixtures asserted against all three implementations.

  Two shared one root cause: both primaries reached string fields through an
  accessor that answered identically for an absent key and for a key holding a
  non-string, then defaulted to `""` and skipped any check keyed on a non-empty
  value. So `scheme = ""` and `scheme = 1` each bypassed the
  closed `execution_proof_scheme` vocabulary, RKM06, and the RKM03 locator
  grammar, while the Python reference rejected them. That reopened the hollow
  proof from a new direction: such a document satisfies key presence, carries
  both pinned digests, is closure-valid, and declares no proving system at all.
  Both ports now distinguish absent from present-but-not-a-string and check
  vocabulary membership with no empty-string and no wrong-type escape.

  The third ran the other way: Python's `\d` matches Unicode decimal
  digits, so the REFERENCE accepted `٢026-07-26T10:15:00Z` while both ASCII
  primaries rejected it. RFC3339 is ASCII, so Python was fixed, not the
  primaries.

  Also fixed, found by the initiator rather than the board: every
  implementation checked the shape of `performed_at` and not its meaning, so
  `2026-99-26T10:15:00Z` validated everywhere. That field sits inside the RKM04
  bound tuple and carries the freshness claim, so an impossible instant was
  being bound into the proof. All three now check month, day (against the
  month, with the leap-year rule), hour, minute and second.

  A wrong-typed bound field also made both primaries compute the bound tuple
  over empty strings and report a mismatch against a tuple no producer wrote
  Accept/reject parity held, but the diagnostic buried the real
  defect; RKM04 is now skipped unless every bound field is a string, matching
  the reference.

- **CI was red on the mutation-kinds branch.** The repo-wide Python closure
  sweep enumerates its exclusions by directory and did not name
  `conformance/cases/state-mutation/invalid`, so a deliberately
  closure-invalid conformance fixture failed the positive sweep. The primaries'
  own discovery step already skipped `conformance/cases/*/invalid/`
  generically, against a verification claim that had gone stale in the very
  commit that introduced the fixture.

### Added

- **SPEC 12.8.2 additions.** The same class of gap was found independently in
  the new bound-tuple section. A declared field
  that is present but not a string is now explicitly a validation error that
  MUST NOT be coerced or read as absent. Field paths are frozen to the 12.8.1
  pinned-record grammar, since a path containing 0x20 or 0x0A would reintroduce
  at the label boundary the ambiguity prehashing removes at the value boundary.
  And Unicode normalization is resolved by requiring that NONE is applied:
  values hash as the exact UTF-8 bytes in the document, so canonically
  equivalent NFC and NFD values produce different tuple digests. Normalizing
  would make a verifier's recomputation depend on a Unicode version, and a
  bound tuple must be reproducible from bytes alone.

- **`mutation-claim` kind, and primary parity for both mutation kinds.** The
  companion kind is the honest home for a state change with no execution proof:
  identical `[mutation]` table so promotion to `state-mutation` is mechanical,
  three pinned closure records, abstraction class `claim-record.v1`, and RKC02
  forbidding `[execution_proof]` so the claim/proof split cannot be evaded in
  either direction. The Rust and Go primaries now implement RKM02, RKM03,
  RKM04, RKM06 and RKC02 (`--mode mutation-kinds`, plus auto dispatch), closing
  the Python-only enforcement boundary recorded when the kind first landed. The
  motivating case was a hollow proof: an `[execution_proof]` carrying only the
  two pinned digests is closure-valid, so a primary-only consumer previously
  accepted a state-mutation with no typed proof. All three implementations
  agree byte for byte on the SPEC 12.8.2 bound tuple.

- **`state-mutation` kind in the `com.verivus.runtime` profile (PROPOSAL,
  pending design review).** Records one irreversible state change an agent
  CAUSED, as distinct from `api-snapshot`, which records one interaction an
  agent OBSERVED. The execution proof is **mandatory**: the kind's name
  asserts execution, so a record that cannot carry a proof is not a
  state-mutation and must use an observation-shaped or intent-shaped kind
  instead (RKM02). New files:
  [`profiles/com.verivus.runtime/state-mutation-kind.toml`](profiles/com.verivus.runtime/state-mutation-kind.toml),
  [`validators/validate_state_mutation.py`](validators/validate_state_mutation.py),
  [`examples/minimal-state-mutation.toml`](examples/minimal-state-mutation.toml)
  plus its capture, and three negatives (`no-proof`, `unbound-proof`,
  `inlined-proof`). The profile ontology gains two closed vocabularies,
  `execution_proof_scheme` and `finality_basis`, bumping its
  `ontology_version` to 2.

  The structural point: the profile descriptor pins all five state-mutation
  closure records as `required`, in deliberate contrast to the api-snapshot
  witness pinned `when-present`. A witness may legitimately be absent, so an
  honestly re-rooted unwitnessed capture is valid. An execution proof may
  not, so deleting it removes two REQUIRED pins and fails the closure gate in
  all three implementations rather than yielding a smaller valid stream. The
  `no-proof` negative proves it. This is what makes a state-mutation
  impossible to downgrade silently by deletion.

  `RKM04` makes proof-to-mutation binding mechanical: `binds_sha256` must
  equal the digest of the canonical bound tuple recomputed from the
  document's own fields, so a real receipt pointed at a different mutation is
  rejected. Whether the proof ARTEFACT actually carries that value is
  RUNTIME-SPEC, and is the consuming verifier's central obligation.

### Changed

- **`skills/convert-md-to-dag/SKILL.md`: de-hardcoded the multi-LLM review
  gate, and re-captured the package provenance.** The "Multi-LLM Review
  Command" section prescribed a `llm review --models
  "claude-3.5-sonnet,gpt-4o,grok-3"` invocation. The model identifiers had
  gone stale, and pinning them in the skill is what made staleness
  inevitable. The section is now "Multi-LLM Review Gate" and states the
  required inputs, criteria, and reviewer count without naming models:
  resolve the available models from the gateway at review time and record
  the identifiers that produced each review in the evidence. Reviewers must
  check claims against the generated files rather than a summary.

  Editing the source Markdown invalidated the package that cites it, which
  is the §12 binding working as intended. All six generated TOML files had
  their `[provenance].source_sha256` and `source_bytes` re-captured
  (`3077` to `3533` bytes) and their `closure_root` recomputed, plus
  `[meta].source_hash` in `traceability.toml`. Verified with the Rust and
  Go primaries (`--mode auto` and `--mode provenance-binding`), the Python
  reference validators, IJB conformance, `taplo lint`, and the repo-wide
  closure-root gate (92 files).

- **Dependabot noise reduction and coverage fix.** Consolidated the seven
  per-directory `cargo`/`gomod` update entries (four cargo, three gomod)
  in [`.github/dependabot.yml`](.github/dependabot.yml) into one `cargo`
  and one `gomod` entry, each using the `directories:` list plus
  `group-by: dependency-name`, so a single upstream release (e.g. `serde`,
  `toml`) opens ONE pull request spanning every affected crate/module
  instead of one PR per dependency-and-directory. Also added the
  previously-unmonitored `tools/toml-test-decode-go` Go module (which
  carries real dependencies) to Dependabot coverage, and created the five
  repository labels the config references (`dependencies`, `python`,
  `rust`, `go`, `github-actions`), which previously did not exist so
  Dependabot could not apply them.

### Added

- **U10 review gate CLOSED: 3 of 3 unconditional external approvals
  (rounds 3-5).** Round 3 proved the new pin-resolution guard script's
  guard 4 vacuously true under mutation and it was corrected (the
  trailing-newline name is now the fixture's only defect;
  mutation-verified) with a fifth guard pinning the newline-closure_root
  parity verdict; round 4 confirmed every behavioural surface across all
  three reviewers (grok unconditional) leaving two documentation items;
  round 5 closed with codex and gemini unconditional at 57d1647. Full
  five-round evidence under
  `docs/reviews/2026-07-13-closure-record-form-promotion-impl/`. The
  stack is merge-eligible; merge remains gated on the code-owner PR
  approval.

- **U10 implementation-review round 2 fixes.** Round 2 verified all
  round-1 fixes and exposed two incomplete sweeps, both fixed across the
  triad with regressions: the remaining `$`-anchored name regexes in the
  Python profile-descriptor validator (a trailing-newline profile name
  was accepted where the primaries reject; now backslash-Z, with
  CLOSURE_ROOT_RE hardened the same way) and the kind-descriptor
  candidate enumeration in both primaries not following symlinked
  profile directories (descriptor discovery was fixed in round 1, the
  candidate path was not). The alternate-root regressions are now
  executable: `validators/check_pin_resolution_guards.sh` constructs the
  duplicate-name, symlinked-profile, symlinked-kind-candidate, and
  newline-name roots at run time and asserts three-way agreement, wired
  as a CI behavioural guard. Record counts pinned to refs; stale corpus
  and coverage numbers corrected.

- **U10 implementation-review fixes for the closure-record-form
  promotion.** The independent multi-LLM implementation review (evidence
  under `docs/reviews/2026-07-13-closure-record-form-promotion-impl/`)
  returned consensus approval with required fixes; all applied: Python's
  pinned-value and pin-field regexes re-anchored with backslash-Z (the $
  anchor accepted a trailing newline the primaries reject); duplicate
  profile-descriptor names now make all three validators refuse to
  validate anything (fail-closed; a duplicate could shadow pins and
  reopen the pin-free fall-through the frozen rule forbids); the Go
  primary follows symlinked profile directories like rs/py; the Python
  profile-descriptor validator merges only the file under validation
  into extends resolution, matching the primaries. Four conformance
  cases added (missing/unresolvable framework_profile, unwitnessed
  three-record positive, trailing-newline regression; corpus now 29
  cases, rs/go/py agree). Also recorded during the U05-U07 porting: the
  extends double-emission dedup fix (a2d6b92), proven by the persisted
  parity harness (`research/03-parity-harness.md`).

- **Cross-implementation verification record for the closure-record-form
  promotion (U10).** Full sweep recorded in
  `docs/planning/closure-record-form-promotion/research/02-verification-record.md`:
  closure discover 79/80 conforming files on a clean tree (pinned to the
  refs measured), 29-case conformance corpus with rs/go/py agreement, INV07 parity across all three profile-descriptor validators,
  every wired negative rejected, posture-flip demonstration (C05), and
  the C01-C06 contract evidence with recorded boundaries and file-list
  deviations. Merge remains gated on the independent multi-LLM
  implementation review per tools/review-request-dag.toml.

- **api-snapshot conformance corpus + Python closure step in the runner
  (U09 of the closure-record-form promotion).** New
  `conformance/cases/api-snapshot/` cases (four-record positive;
  witness-strip stale root; missing required pin; malformed pinned
  digest); `conformance/runner.py` registers the api-snapshot Python
  validator and now runs `validate_closure_root.py` on every fixture of
  every kind, making cross-implementation closure parity (contract C01)
  non-vacuous on the Python side. Corpus: 25 cases, rs/go/py agree on
  all. Invalid corpus cases are excluded from the positive closure sweep
  alongside `examples/negative/`.

- **com.verivus.runtime pins the api-snapshot closure records; witness
  stripping is now detectable at the closure root (U08 of the
  closure-record-form promotion).** `PROFILE.toml` pins
  `snapshot.request.descriptor_sha256` (required),
  `snapshot.response.body_sha256` (required), and
  `snapshot.witness.attestation_sha256` (when-present) per SPEC 12.8.1;
  the api-snapshot kind's CLOSURE LAYERING prose and RKV01 now describe the
  four-record stream, and RKV03 is amended (witness digest/identity fields
  MUST be absent at `present = false`, enforced by
  `validate_api_snapshot.py`; the primaries do not implement RKV03, an
  explicitly recorded boundary). The shipped example re-roots to the
  four-record value `sha256:013f3d34...`; the blessed negatives re-root to
  their pinned-stream values; `api-snapshot-bad-closure` inverts polarity
  (now blessed, carrying the stale source-only root); new negatives
  `api-snapshot-witness-stripped` (stale four-record root, rejected by all
  three closure implementations: contract C02) and
  `api-snapshot-witness-lingering-digest` (closure-valid, rejected by
  amended RKV03). The CI closure sweep now explicitly excludes
  `examples/negative/` (each exclusion is asserted to fail in the
  negative-agreement step), via the new `--exclude` option on
  `validate_closure_root.py --discover`.

- **Go primary consumes profile-pinned closure records (U07 of the
  closure-record-form promotion).** `tools/dagtoml-validate-go` mirrors U06:
  kind-keyed pin map from the discovered descriptor set (extends union,
  (field, presence) dedup), SPEC 12.8.1 record emission and pin resolution
  in every closure-validating mode, verdict parity with the Python
  reference and the Rust primary on the nine-case matrix. No `unsafe`
  import; stdlib only.

- **Rust primary consumes profile-pinned closure records (U06 of the
  closure-record-form promotion).** `tools/dagtoml-validate-rs` builds the
  kind-keyed pin map from the discovered profile-descriptor set (extends
  union, (field, presence) dedup) and applies SPEC 12.8.1 record emission
  and pin resolution in every closure-validating mode (auto and
  provenance), with verdicts identical to the Python reference across the
  nine-case pin parity matrix. `#![forbid(unsafe_code)]` intact; no new
  dependencies.

- **Python closure validator consumes profile-pinned closure records (U05
  of the closure-record-form promotion).** `validators/validate_closure_root.py`
  now loads every `profiles/*/PROFILE.toml` under `--repo-root`, unions
  `closure_records` across `extends`, resolves pins by `template_kind`
  (SPEC 12.8.1: no pin-free fall-through for a pinned kind; missing or
  unresolvable `framework_profile` on a pinned-kind document is rejected),
  and folds the labeled `<field> <sha256:hex>` records into the sorted
  SPEC 12.8 stream. Documents of unpinned kinds keep byte-identical
  verdicts (no shipped profile pins records until U08).

- **INV07 enforcement across the triad (U04 of the closure-record-form
  promotion).** The profile-pinned closure-record declaration rules of SPEC
  12.8.1 are now mechanically enforced by all three profile-descriptor
  validators: `validators/validate_profile_descriptor.py` (reference), the
  Rust primary, and the Go primary, with byte-identical verdicts on the new
  negative fixture
  `examples/negative/profile-descriptor-bad-closure-record.toml` (wired
  into the CI negative-agreement step under `--mode profile`). INV07 is
  declared in `core/profile-descriptor-kind.toml`. No profile pins records
  yet; the com.verivus.runtime pinning lands in U08.

- **SPEC text for profile-pinned closure records (U03 of the
  closure-record-form promotion).** Normative additions under the recorded
  U02 GO: SPEC 12.8.1 (the `[[profile.closure_records]]` declaration, the
  byte-frozen field-path grammar, `required`/`when-present` semantics, the
  labeled `<field> <sha256:hex>` record emission into the sorted 12.8
  stream, and the kind-keyed pin-resolution rule that forbids a pin-free
  fall-through for pinned kinds); the SPEC 12.1 profile-input enumeration
  amendment; the `closure_records` row and extends-union rule in the SPEC
  6.1 profile-descriptor table (INV07); and the SPEC 12.9 posture-exclusion
  cross-reference. Text only: validators, profiles, and fixtures follow in
  U04-U09; no shipped document changes verdict in this change.

- **Profile-pinned closure record forms (SPEC 12.8 promotion): planning pack
  + design review + freeze preparation.** Added the self-validating
  governance pack under
  [`docs/planning/closure-record-form-promotion/`](docs/planning/closure-record-form-promotion/)
  (design, implementation plan, 10-unit implementation DAG with a hard
  grammar-freeze gate at U02, contracts C01-C06, readiness gates G01/G02,
  evidence matrix, rollback plan) scoping the promotion that lets a
  profile-descriptor pin additional labeled closure records
  (`[[profile.closure_records]]`, new invariant INV07) into the SPEC 12.8
  stream; first user is the `com.verivus.runtime` `api-snapshot` kind, whose
  witness attestation digest becomes a `when-present` closure input so
  witness stripping is detectable at an anchored `closure_root`. Completed
  the independent cross-LLM design review (U01; evidence under
  [`docs/reviews/2026-07-13-closure-record-form-promotion-design/`](docs/reviews/2026-07-13-closure-record-form-promotion-design/),
  all required fixes applied, including the witness-downgrade RKV03
  amendment and the recast pin-resolution rule) and prepared the U02
  grammar-freeze record with the compatibility sweep (105 conforming
  documents; 100 byte-identical; exactly the 5 enumerated api-snapshot
  instances change verdicts). **No spec text, validator, profile, or fixture
  changes land in this change**; U03+ remain blocked on the operator
  STOP/GO in `research/01-grammar-freeze-decision.md`.

### Fixed

- Go stdlib pin moves 1.26.5 to 1.26.6 in `tools/dagtoml-duckdb-go` and
  `tools/dagtoml-rdf-go`, with the CI `go-version` pin tracking it. 1.26.5
  carries 16 known stdlib advisories that `osv-scanner` fails the build on.

- **Stale version comment on the no-ai-attribution checkout pin.** The
  SHA-pinned `actions/checkout` reference in
  `.github/workflows/no-ai-attribution.yml` was annotated `# v4` while
  pointing at the v6.0.3 release commit (and at v7.0.0 after the #58
  group bump preserved the stale comment); the annotation now states
  the version the hash actually resolves to. Comment-only; no
  behavioural change. (A bare-major comment also evades dependabot's comment
  updater, which is how the drift survived two bumps.)

- **Recurring lychee flake on toml.io excluded with justification.**
  The TOML spec site intermittently resets connections from GitHub
  Actions runner IPs (two CI failures on 2026-07-13) while answering
  normally elsewhere; excluded in `lychee.toml` following the existing
  fco-im.nl precedent, since the toml-1.1 migration records pin the
  spec by release tag and date, not by URL liveness.

- **CI: zizmor findings on the CLA workflow (unblocks all PR checks).**
  The workflow-security audit began failing on `.github/workflows/cla.yml`
  after upstream drift (the SHA-pinned CLA action's repository was
  archived). The app-installation token is now explicitly narrowed with
  `permission-contents: write` (resolving the `github-app` error
  properly), and the two deliberate design choices carry justified
  inline suppressions: `pull_request_target` (required by CLA Assistant;
  the job never checks out PR code) and the archived, SHA-pinned action
  (read-only upstream cannot move the pin). No behavioural change to CLA
  enforcement.

- **CI: Go stdlib advisories GO-2026-4970 / GO-2026-5856 (second
  environmental drift blocking all PR checks).** The OSV database picked
  up two stdlib advisories against Go 1.26.4 (fixed in 1.26.5) between
  CI runs, failing the lock-file CVE scan on every branch. Bumped the
  `go` directive in `tools/dagtoml-duckdb-go` and `tools/dagtoml-rdf-go`
  and the CI `setup-go` toolchain from 1.26.4 to 1.26.5 together; both
  modules build clean under the new toolchain. The primary validator
  module (`go 1.26`) is unaffected.

- **TOML 1.0 → 1.1 migration: scoping pack + parity go/no-go (GO).** Added
  the self-validating DAG-TOML governance pack under
  [`docs/planning/toml-1.1-migration/`](docs/planning/toml-1.1-migration/)
  scoping the deliberate migration of the validator/conformance stack from
  TOML 1.0 to TOML 1.1 (spec, implementation plan, 8-unit implementation
  DAG with a hard parity gate, contracts C01–C04, readiness gates G01/G02,
  evidence matrix, rollback plan). Completed the parity spike (U01,
  `research/01-parser-availability-survey.md`) and recorded the go/no-go
  decision (U02, `research/02-parity-decision.md`): **GO** — TOML 1.1.0 is
  a finalized released spec (toml-lang/toml `1.1.0` tag dated 2025-12-24;
  spec page dated 12/18/2025) and a released, default-1.1,
  no-`unsafe` parser exists for all three primaries (Rust `toml`
  `1.1.2+spec-1.1.0`; Go `BurntSushi/toml` v1.6.0, already required by the
  Go validator's `go.mod`; Python `tomli` 2.4.0+, the PEP 680 upstream of
  stdlib `tomllib`). The survey documents that the Go and Rust-RDF sides
  already moved to 1.1-default parsers via dependency bumps (#5, #1),
  leaving the repo latently split across TOML versions — the divergence
  this migration resolves deliberately. No parser has been bumped in this
  change; it lands the pack and the recorded decision only.

- **TOML 1.1 migration U03 — Rust primary validator → `toml` 1.1.** Bumped
  `tools/dagtoml-validate-rs` from `toml` 0.8 to `1.1.2+spec-1.1.0` (the
  line already used by `tools/dagtoml-rdf`). The 1.1 crate gates the
  `toml::Value` API behind its `serde` feature and narrows
  `str::parse::<Value>()` to single-value parsing, so the dependency now
  enables `["parse", "serde"]` and document parsing uses
  `toml::from_str::<Value>()`. The safe-tools policy (R5) is preserved:
  `dagtoml-validate-rs` keeps `#![forbid(unsafe_code)]` and
  `validators/check_safe_tools.sh` passes; per that policy transitive
  parser crates may use `unsafe` internally and are out of scope (e.g.
  `winnow`, which the 1.1 stack bumps 0.7→1.0, already carried internal
  `unsafe` under the 0.8 `toml_edit` stack — no new dependency-level
  `unsafe` surface is introduced by this bump). A differential check over
  all repo `*.toml` files (239 at this commit) shows zero accept/reject
  verdict changes vs. the 0.8 baseline (TOML 1.1 is a superset of 1.0),
  and `make dagtoml-conformance` keeps rs/go/py in agreement.

- **TOML 1.1 migration U04 — Go primary validator confirmed at TOML 1.1.**
  No code change: `tools/dagtoml-validate-go/go.mod` already requires
  `github.com/BurntSushi/toml` v1.6.0 (the latest release, which enables
  TOML 1.1 by default), landed via #5 before this migration. U04 records
  and verifies that the Go runtime is already at the 1.1 target — v1.6.0
  is pure Go with no `unsafe`/cgo (`validators/check_safe_tools.sh` passes
  the Go side) and the validator builds and vets clean. The Go
  *conformance evidence* (the `toml-test` decoder, still pinned v1.4.0 in
  the `Makefile`) is flipped to 1.1 in U06; that is the harness's job, not
  a parser bump.

- **TOML 1.1 migration U05 — Python reference validators → `tomli` 1.1.**
  Replaced stdlib `tomllib` (TOML 1.0 only) with hash-pinned `tomli`==2.4.1
  (the PEP 680 upstream of `tomllib`, 1.1-capable) so the Python reference
  parses TOML 1.1 in lockstep with the Rust/Go primaries (parity invariant
  C01). Added `requirements/toml.txt` (installed pure-Python via
  `--no-binary tomli` so the auditable `py3-none-any` build is used, not
  the optional mypyc wheels) and `validators/_toml11.py`, a shim that
  re-exports the `tomllib`-compatible surface and **fails loud** if `tomli`
  is absent or `< 2.4.0` — no silent fall back to TOML 1.0, which would
  reintroduce the cross-implementation divergence this migration removes.
  Swapped `import tomllib` → `import _toml11 as tomllib` across all 15
  validators, `conformance/runner.py`, the three inline TOML-parsing
  scripts in `.github/workflows/validate.yml`, and the `AGENTS.md`
  parse-the-repo command, so no stdlib TOML-1.0 parser remains in any
  operative surface, and wired the CI install. The
  reference stays authoritative: `make dagtoml-conformance` keeps rs/go/py
  agreeing on the corpus (21 cases), and the swap is verdict-preserving on
  existing documents (TOML 1.1 ⊇ 1.0). ruff (S,F) + bandit clean.

- **TOML 1.1 migration U06 — conformance harness → TOML 1.1.** Flipped the
  spec-conformance harness to the TOML 1.1 corpus: bumped the in-repo
  `toml-test-decode-rs` shim from `toml` 0.8 to 1.1, the BurntSushi
  `toml-test-decoder` pin from v1.4.0 to **v1.6.0** (matching the Go
  validator's `go.mod`, so the conformance evidence is now generated by the
  same 1.1 parser the Go validator runs), and added `-toml 1.1.0` to both
  `toml-test` invocations in the `Makefile`; retitled the two CI steps
  "TOML 1.0 → 1.1". Under `-toml 1.1.0` the Rust shim passes the full suite
  (189 valid + 362 invalid, **zero skips**), strictly stronger than the
  BurntSushi decoder, which still tolerates the same 13 dotted-key /
  inline-table-redefinition cases it always has (BurntSushi-specific
  permissiveness, unchanged by the 1.0→1.1.0 flip; documented in the
  `Makefile` skiplist). The 9 formerly-invalid 1.0 inputs that 1.1 makes
  valid (seconds-less times, `\xNN` escapes, multi-line/trailing-comma
  inline tables) now pass. The cross-implementation semantic corpus stays
  in agreement (`make dagtoml-conformance` → CONFORMANCE PASSED).

- **TOML 1.1 migration U07 — spec.md 1.1-feature disposition (§9.2).** Added
  normative [`spec.md`](spec.md) §9.2 "TOML language version and 1.1 feature
  disposition" (R4 / contract C03). Parser conformance and the conforming
  *document* syntax surface are both TOML **1.1.0**: an implementation MUST
  NOT reject a document solely because it uses TOML 1.1.0 syntax. Every
  syntactic feature TOML 1.1.0 adds over 1.0.0 (seconds-optional times,
  `\xHH` hex escapes, the `\e` (ESC) escape, newlines in inline tables, and
  trailing commas in inline tables) is **permitted** by the syntax surface.
  Decoded values remain subject to the semantic rules, field types, and
  kind-descriptor constraints stated elsewhere in this specification, and
  tools that render DAG-TOML string values to terminals, logs, reports, or
  review UIs MUST escape, replace, or otherwise safely display C0 control
  characters rather than emitting them raw. A future-version catch-all keeps
  TOML 1.2.0 and later syntactic additions outside the conforming surface
  until §9.2 and the matching cross-implementation evidence are updated
  deliberately. Every document valid before the 1.1 parser adoption remains
  valid after it, so the disposition invalidates nothing.

- **TOML 1.1 migration U08 — cross-implementation verification (complete).**
  Ran the full cross-implementation verification at TOML 1.1 and recorded the
  result in [`conformance/known-divergences-toml-1.1.toml`](conformance/known-divergences-toml-1.1.toml)
  (additive to the operative `conformance/known-divergences.toml`). Verified
  state: the dagtoml semantic corpus — the operative parity surface — has
  rs/go/py in full agreement (21 cases, CONFORMANCE PASSED, empty baseline),
  as does the toml-test 1.1 *valid* corpus (all three accept all 189). On
  the toml-test 1.1 *invalid* corpus the Rust decoder rejects all 362 (zero
  skips), but the Go `BurntSushi/toml` v1.6.0 decoder accepts **13** that
  Rust and Python reject — a genuine, but **pre-existing**, cross-impl
  divergence from BurntSushi's permissiveness on dotted-key / inline-table
  redefinition (identical 13 under TOML 1.0; *not* introduced by this
  migration). Those 13 are recorded — named, not silently skipped — in the
  baseline file; bringing the Go primary to the same strictness as Rust and
  Python (contract C01's `block, not skip` aim) needs a stricter Go parser
  and is out of scope for the version migration. Parsers are uniformly TOML
  1.1 (Rust `toml` 1.1.2+spec-1.1.0, Go `BurntSushi/toml` v1.6.0, Python
  `tomli` 2.4.1); closure-root validates 97 files. **This completes the TOML
  1.0 → 1.1 version migration**: all three primaries are at 1.1 in lockstep,
  the operative dagtoml parity baseline is empty, and full toml-test parity
  remains bounded by the documented pre-existing BurntSushi gap.

- **Static specification site.** Added the Cloudflare Pages static site
  under `site/`, including human-readable pages, Markdown mirrors,
  agent discovery metadata, a deploy workflow, favicon assets, and the
  social share image used by Open Graph and Twitter cards.
- **OSS readiness sweep.** Added public-repository metadata and ownership
  files, ignored local paper/research scratch files, added an OpenSSF
  Scorecard workflow and README badge, pinned CI to GitHub-hosted
  `ubuntu-24.04` runners with Harden-Runner audit telemetry, documented
  the non-normative status of historical review/research directories, and
  corrected public-status and release-policy wording after the `v0.1.0`
  mint.
- **CodeQL advanced-setup workflow.** Added
  [`.github/workflows/codeql.yml`](.github/workflows/codeql.yml) scanning
  `actions`, `go`, `python`, and `rust` with build-mode `none` on every
  push, every pull request, and weekly. GitHub's default-setup REST API
  does not currently accept `rust` as a language value (verified by a
  live `PATCH` probe that returned
  `Invalid property /languages/3: 'rust' is not a possible value`),
  which would have left roughly one third of this repository's source
  unscanned. Advanced-setup restores Rust coverage. All actions are
  SHA-pinned to the same versions used elsewhere in the workflow
  directory.
- **Archived multi-LLM review session + no-ai-attribution gate fixes
  (#26).** Added the non-normative process records under
  `docs/reviews/2026-05-27-agentskills-profile-pitch/` for an outbound
  pitch that was reviewed, approved, and then withdrawn unpublished;
  retained for traceability per the `docs/reviews/` convention. The same
  squash-merged commit also hardened
  [`.github/workflows/no-ai-attribution.yml`](.github/workflows/no-ai-attribution.yml):
  `persist-credentials: false` on the checkout step (zizmor) and an
  `SC2086` fix converting the commit-range `ARGS` to a bash array.

### Changed

- **Implementation-dag placeholder parity in primary validators (#27).**
  Wired the unresolved-placeholder check (`<…>` markers in
  `files_create`/`files_modify`) into the Rust and Go implementation-dag
  paths, matching the Python reference, and removed the corresponding
  `conformance/known-divergences.toml` entry. The Go predicate uses an
  implementation-dag-specific marker set (`<`, `>` only) distinct from
  the broader kind-descriptor set; a `date-literal-path.toml` fixture
  pins the split. Conformance 21/21 across rs/go/py.
- **Dependency bumps.** `toml` 0.9→1.1.2+spec-1.1.0 in `tools/dagtoml-rdf`
  (#1); `github.com/BurntSushi/toml` 1.4→1.6 in `tools/dagtoml-validate-go`
  (#5); the GitHub Actions workflow dependency group (4 updates, #20);
  `ruff` 0.14.5→0.15.15 in `requirements/ruff.txt` (#29, hash-pinned; the
  `--select S,F` lint over `validators/` passes with no new violations).
- **Primary validator coverage promoted to Rust + Go.** Ported the
  remaining CI-enforced semantic surfaces from Python-only reference
  checks into both primary validators: implementation-dag,
  traceability, review-readiness, kind-descriptor structure, IJB
  conformance, `[provenance]` source binding, cost-record,
  rollback-plan trigger-kind closure, and SPEC §13
  abstraction/capability-envelope checks. CI now runs Rust and Go over
  ontologies, every kind descriptor, every canonical example, every
  tier file, and every profile descriptor, and includes negative
  fixtures proving Rust, Go, and Python all reject malformed files.
- **Root scratch artifacts moved local-only.** Verified the loose paper
  scratch files (`all_links.txt`, `bib_keys.txt`, `cited_keys.txt`,
  `labels.txt`, `find_matches.py`, `find_matches_v2.py`) are untracked
  and unused by CI, Makefile, docs, examples, or tools; moved the local
  copies under `.local/scratch/`. Existing root-only `.gitignore` rules
  keep them from being accidentally committed.
- **Go validation toolchain updated to patched 1.26.4.** The CI Go
  setup pin and the two Go reference modules that declare a patch-level
  toolchain now agree on Go `1.26.4`, matching the OSV-reported fixed
  stdlib version.
- **`SECURITY.md` documents the full defensive posture.** Rewritten to
  describe secret scanning + push protection, Dependabot security
  updates, CodeQL advanced-setup over the four languages, the
  `main-branch-protection` ruleset, the `signing-approvers` team,
  sigstore-signed release tags (with the `gitsign verify` instruction),
  OpenSSF Scorecard publishing, and the thirteen OSS scanning tools in
  [`.github/workflows/validate.yml`](.github/workflows/validate.yml).
  The thirteen-tool section mirrors the `validate.yml` "Coverage map"
  comment block verbatim (same order, same one-line role descriptions),
  and names that comment block as the canonical source so future
  contributors know which file leads if they diverge again.
- **`CONTRIBUTING.md` references the canonical scanner inventory.** One
  paragraph appended under "Local Checks" pointing to `SECURITY.md` for
  the per-tool role descriptions and listing the thirteen-tool sequence
  in the same order as `validate.yml`.

### Fixed

- **`sha2` 0.11 digest encoding (#28).** Bumped `sha2` to 0.11 in
  `tools/dagtoml-validate-rs`; its digest output (`hybrid_array::Array`)
  no longer implements `LowerHex`, so `format!("{:x}", …)` stopped
  compiling. Hex-encode digest bytes directly in `digest_hex` and route
  the `[provenance].source_sha256` check through the same helper. Output
  is byte-identical to the previous encoding (conformance 21/21).

## [v0.1.0] - 2026-05-27

### Added

- **Initial public draft release.** Minted the specification repository as
  a clean public tree with the DAG-TOML draft specification, core kind
  descriptors, spec-reserved profiles, examples, validators, governance
  docs, and CI configuration.

## Pre-Public Development History

The entries below were retained from the private development history as
traceability evidence. They may refer to paper workspaces, review bundles,
or preparation directories that now live outside this specification repo.

### Changed

- **Public stability label changed to Draft Specification.**
  spec.md, README.md, and GOVERNANCE.md now distinguish the document
  maturity label from the on-file `schema_version` compatibility pin.
  Release tags continue to use calendar-versioned UTC timestamps
  (`v<YYYY-MM-DD>T<HH-MM-SS>Z`) rather than draft maturity labels.
- **Draft version pins made coherent.** Live schema/spec pins now use
  `schema_version = "0.1.0"` while `ontology_version = 1` remains a
  monotonic positive integer vocabulary snapshot. Validators now enforce
  `schema_version` as a semver string and `ontology_version`, when
  present, as a positive integer.
- **Terminology rename across the live spec surface to
  `spec-reserved`.** The prior prose marker for spec-published
  profiles, kinds, and the validator-discovered conformance set
  is now written as `spec-reserved` throughout spec.md, the
  ADOPTION and CONTRIBUTING docs, the three
  spec-reserved profile-descriptor headers, the ontology files,
  the kind-descriptor descriptor, and the Python/Go/Rust
  validators. The rename aligns the prose form with the
  machine-readable `namespace = "spec.reserved"` field already
  present in every profile-descriptor, closing the
  prose↔machine-readable gap that the agent-notes no-drift rule
  warns against. Python identifier renames in
  `validators/validate_closure_root.py` use the underscore
  variant `ALWAYS_SPEC_RESERVED_KINDS` /
  `spec_reserved_kinds()` / `spec_reserved` parameters,
  preserving Python identifier syntax. Go and Rust validators
  had no broken identifiers (the prior term appeared only in
  string literals). Historical records (CHANGELOG history
  below, docs/reviews/, docs/issues/, docs/planning/,
  docs/research/) are deliberately left untouched so they
  continue to reflect the terminology in use at the time of
  writing. All validators pass: closure-root discovery,
  profile-descriptor validation, IJB conformance, every kind
  descriptor under `core/` and `profiles/*/`, and the canonical
  example suite.

### Fixed

- **SPEC §12.8 closure roots now bind declared provenance source
  hashes.** The Python reference validator and both primary validators
  now compute the canonical `[provenance].source_sha256` closure stream
  instead of accepting the empty sentinel for provenance-bearing
  documents. The convert-md-to-dag skill package now carries the
  computed closure root for its declared source artifact. README.md and
  tools/README.md also distinguish current Tier-1 validator coverage
  from the remaining legacy Python-only migration backlog.
- **spec.md §2.3 / §2.5 / §6 — cost profile enumeration drift.**
  The cost profile shipped under `profiles/cost/` with
  `namespace = "spec.reserved"` and full CI integration, but
  spec.md's authoritative enumerations still listed only
  `agent-assurance` and `disclosure`. §2.3's
  `template_kind` table now includes a `cost-record` row;
  §2.5's spec-reserved-values bullet list now includes `cost`;
  §6's prose now names all three spec-reserved profile
  directories and says "Each ships a profile-descriptor
  document" rather than "Both ship". The escape hatch at §2.5
  ("the authoritative enumeration is the `profile-descriptor`
  files at `profiles/<name>/PROFILE.toml`") and the validator
  code at `validators/validate_closure_root.py:140` were
  already correct; this change resolves the prose drift only.
  No behaviour change.

### Added

- **spec.md §14 / §15 — explicit security and privacy considerations.**
  The public specification now has dedicated sections stating the
  security boundary of DAG-TOML's declarative evidence model and the
  privacy risks created by inspectable provenance, disclosure,
  redaction, closure, and metadata fields. The change consolidates
  existing posture material from the security, disclosure,
  provenance, confidentiality, and threat-model surfaces into the spec
  itself. No file-shape or validator behaviour changes.
- **OSS security + quality scanning posture (13 tools wired into CI).**
  Free-OSS-tool stack that closes the gaps from running on a free-plan
  private GitHub org (no GHAS: no CodeQL, no secret scanning, no
  branch protection). Every step uses SHA-pinned actions or
  version-pinned binaries (with SHA256 verification for downloads) and
  is configured to fail the build on any finding.
  - **Workflow integrity:** `actionlint` (GHA workflow correctness),
    `zizmor` (GHA workflow security — impostor-commit, excessive
    permissions, credential persistence). The zizmor audit caught
    three real findings on the existing workflow which were also
    fixed in this commit: top-level + job-level `permissions: contents:
    read` blocks, and `persist-credentials: false` on the checkout
    step.
  - **Content correctness:** `shellcheck` (validator shell scripts +
    paper witness scripts), `typos` (source-code spellchecker; critical
    for spec repos where misspelled ontology predicates would be silent
    semantic errors).
  - **Python:** `ruff` (configured for `--select S,F` —
    flake8-bandit security + pyflakes correctness, line-length 120;
    bugbear/style rules deferred to a dedicated cleanup PR), `bandit`
    (already wired; kept for defense-in-depth — different AST passes
    than ruff).
  - **Dependency CVEs:** `osv-scanner` (lock-file CVE check across
    requirements.txt + Cargo.lock + go.sum).
  - **Secrets:** `gitleaks` v8.30.1 binary (SHA256 verified) — secret
    leak detection in working tree + commit history.
  - **Rust:** `cargo-audit` (RustSec advisory DB) + `cargo-deny`
    (license policy allowlist Apache/MIT/BSD/MPL only; deny GPL family;
    crates.io-only source allowlist; multiple-version + wildcard
    bans). Configuration at `deny.toml`.
  - **Go:** `govulncheck` (call-graph-aware vuln check) +
    `golangci-lint` v2.12.2 (gosec + staticcheck + errcheck + govet +
    ineffassign + unused). Configuration at `.golangci.yml`.
  - **Link rot:** `lychee` (URL liveness check across .md/.toml/.tex
    files; documentation links, paper citation URLs in references.bib,
    kind-descriptor `references = [...]` URLs). Configuration at
    `lychee.toml`.
- **Dependabot expanded to four ecosystems** (`github-actions`, `pip`,
  `cargo`, `gomod`) — was previously github-actions only. Weekly bump
  cadence with distinct PR-limit caps and commit-message prefixes per
  ecosystem. Dependabot automated security fixes also enabled via the
  GitHub API.
- **First-run shake-out of the scanning stack (8 fixup commits).**
  The initial CI push of the 13-tool stack surfaced 8 distinct
  findings or false-positive classes across runs `26406653986`
  through `26412405532`. Each fixup is one commit:
  - `e7430a7` — `_typos.toml`: exclude `docs/{reviews,research,
    claim_analysis}/`, `tools/werner-style-policy.toml`,
    `foundations/ijb/examples/0{6,7}-*`, `paper/user-prompts.md`;
    allowlist `COSE` (RFC 9052 acronym), `Synopsys` (vendor name),
    `vai` (Werner shorthand for Verifiable AI in §13 label),
    plus identifier-regex skipping for structured IJB example IDs.
  - `8b3c51f` — osv-scanner: drop `--skip-git` flag removed in v2.
  - `c6c91d9` — `tools/dagtoml-validate-go`: remove unused
    `arrayOfStrings` helper (golangci-lint `unused` linter).
  - `633f23e` — osv-scanner: add `--no-resolve` to skip the flaky
    upstream gRPC service that resolves transitive deps from
    `requirements.txt`. Lockfile-based scanning (Cargo.lock,
    go.sum) covers the rest; networkx pulls in no transitive deps
    that need resolution.
  - `31a37b0` — `tools/dagtoml-rdf-go`: errcheck on
    `os.Stdout.WriteString` (wrap in `if _, err := ...`); gosec
    G306 `0o644` WriteFile permissions annotated with `//nolint:gosec`
    + rationale (regenerated reference RDF schema is intended to be
    world-readable for downstream implementers).
  - `06fb1f2` — `lychee.toml`: remove `include = ["**/*.md", ...]`
    array. The `include` key takes URL-regex patterns, not file
    globs; lychee `v0.23.0` errored with "regex parse error ...
    repetition operator missing expression". File-extension scoping
    is handled by lychee's built-in extractor selection.
  - `182dd31` — `lychee.toml`: extend `exclude_path` with
    `docs/research/` + `docs/claim_analysis/`; extend `exclude`
    URL-regex list with placeholder/example domains
    (`*.yourdomain.com`, `config.kasselman.com.au`) and the
    `file://` scheme. Repo-internal file-existence is checked by
    the path-existence validators under `validators/`, not by
    lychee.
  - `34eb281` — `lychee.toml`: exclude `www.fco-im.nl`. The
    academic-paper host cited from
    `foundations/ijb/fco-im-integration-options.md` times out from
    GitHub Actions runners; the FCO-IM papers themselves are
    stable academic references, not load-bearing dependencies.

  Final state after `34eb281`: CI run `26412405532` green on every
  step of the 13-tool stack plus all 36 pre-existing validators.

### Changed

- **`validators/check_safe_tools.sh`:** swapped literal backticks
  inside a printf format string for single quotes (shellcheck SC2006
  flagged the backticks as legacy command-substitution syntax — they
  were intended as literals); added `# shellcheck disable=SC2001`
  annotation to the documented sed indent idiom.
- **`validators/*.py`:** removed 3 unused variables (dead code from
  prior refactoring, caught by `ruff F841`); removed 1 unused `import
  sys` (caught by `ruff F401`); added `# nosec`/`# noqa` annotations
  with explicit rationale to 2 safe `subprocess.run(list, ...)` call
  sites and 1 intentional `try/except/pass` site.
- **`.github/workflows/validate.yml`:** workflow now declares
  `permissions: contents: read` at both workflow and job level
  (closes the two zizmor `excessive-permissions` findings); the
  `actions/checkout` invocation sets `persist-credentials: false`
  (closes the zizmor `artipacked` finding); job carries an explicit
  `name:` for log-grep clarity.

- **Multi-LLM end-to-end review framework — bytes-verified arc closure
  across three independent review sessions.** The spec, the chardet
  relicense paper, and the hello-world proof paper each went through a
  tier-3 multi-LLM review framework (codex + gemini + grok per session;
  mistral unavailable on host; verification_report.toml as
  corrective-program spec; reviewers iterate against bytes, not
  summaries). Total: 12 reviewer-sessions across the three arcs, 36
  individual verdicts persisted. Final state: all three arcs closed at
  unanimous unconditional_approval with zero remaining bytes-verifiable
  defects.
  - `docs/reviews/2026-05-25-spec-e2e/` (r1, 15 blockers) →
    `docs/reviews/2026-05-25-spec-e2e-r2/` (1 codex blocker: S08.1
    --help string) → `docs/reviews/2026-05-25-spec-e2e-r3/` (unanimous;
    arc terminal).
  - `docs/reviews/2026-05-25-paper-chardet-e2e/` (r1, 10 blockers) →
    `docs/reviews/2026-05-25-paper-chardet-e2e-r2/` (codex B3 Conclusion
    overclaim) → `docs/reviews/2026-05-25-paper-chardet-e2e-r3/`
    (gemini B3 §10.3 intro overclaim — same defect class, third
    location) → `docs/reviews/2026-05-25-paper-chardet-e2e-r4/`
    (unanimous; arc terminal).
  - `docs/reviews/2026-05-25-paper-hello-world-e2e/` (r1, 2 blockers
    C1+C2) → `docs/reviews/2026-05-25-paper-hello-world-e2e-r2/`
    (unanimous including original C1 filer; arc terminal).
- **Validator-help cites every invariant ID it enforces.**
  `validators/validate_gate_decision.py` argparse description now
  enumerates INV01..INV06 with one-line summaries of each — closes
  spec-e2e-r2's S08.1 recipe-literal blocker. `--help | grep -oE
  'INV0[1-6]' | sort -u` returns all six.

### Changed

- **`paper/main.tex` Conclusion and §10.3 introduction now scope
  validation claims accurately.** Three recurring B3-class
  "scipy/numpy implementation" overclaims were caught across r2 and r3
  reviews of the chardet relicense paper. The paper's Conclusion
  (closed at r3) and §10.3 introductory sentence (closed at r4) both
  now distinguish AUX1+C06a-d (validated via scipy/numpy second-source
  primitives) from C06e (validated via stdlib digest re-derivation
  plus a subprocess to the harness's behavioural-fingerprint script,
  with explicit SKIP semantics). The §10.3 intro also states why C06e
  takes a different path: "because there is no scipy or numpy primitive
  that re-derives a chardet behavioural fingerprint."
- **`paper/figures/scripts/validation_report.json` refreshed.**
  Reviewer runs of `validate_numbers.py` regenerated this artifact
  during r3+r4. Previous corpus_digest_full was stale from a pre-r2
  era; now shows the correct `58e54831f84183c755c2458f...` digest
  matching `fingerprint_behavior.py`'s computation. Adds the
  `c06e_rates` SKIP row that documents toolchain-failure explicit
  reasons.
- **`.gitignore`: add `.local/`.** The local Werner Style Spec
  working-copy directory is local-only and MUST NOT ship in the public
  repo. Now explicitly gitignored.

### Audit-trail notes (not normative)

- All three review arcs demonstrate the multi-LLM lattice's
  load-bearing redundancy: each round, different reviewers caught
  different defect classes. At r3 of the chardet arc, codex's
  recipe-literal grep (`scipy ?/ ?numpy`) and grok's
  context-redeems-framing interpretation BOTH approved while
  gemini's broader grep (`scipy|numpy`) caught the surviving §10.3
  intro overclaim. Two reviewers would have missed it; three with
  diverse approaches caught it.
- Lesson for future verification_report.toml authors: when remediating
  a prose-class defect, the next round's grep recipe must enumerate
  the FULL alternation pattern (slash, "and", "+", bare-comma), not
  narrow to the form that triggered the predecessor blocker. r4's
  recipe added explicit A/B/C/D classification (listing-specific /
  scoped-composite / unscoped-global / negative-clause-clarification)
  so reviewers could not approve a class-C hit by interpretation.

## [v2026-05-25T03-30-02Z] — 2026-05-25 03:30:02 UTC

### Added

- **Rust-side TOML parser-conformance harness (closes the
  Go/Rust asymmetry).** New `tools/toml-test-decode-rs/` binary
  (~75 lines, `#![forbid(unsafe_code)]`, two deps: `toml 0.8` +
  `serde_json 1`) reads TOML on stdin and emits the toml-test
  tagged-JSON format on stdout. The shim is built from the same
  `toml` 0.8 crate that `tools/dagtoml-validate-rs` depends on,
  so a green run is direct evidence about the parser the **Rust**
  primary validator actually uses at runtime — the symmetric half
  of the existing BurntSushi/toml conformance check that covers
  the Go primary validator. Wired into the Makefile as
  `toml-conformance-rs` (and a `toml-conformance-all` alias that
  runs both Go and Rust passes) and into
  `.github/workflows/validate.yml` as a new step adjacent to the
  existing Go-side check. Result on the current crate pin:
  **185/185 valid + 371/371 invalid pass with no skiplist needed**
  — the Rust crate is strictly more conformant than BurntSushi
  v1.4 (it correctly rejects all 13 dotted-key / inline-table
  redefinition fixtures that BurntSushi accepts, removing the need
  for the permissiveness-baseline list on this side). The
  toml-lang/toml-test runner pinned at v1.6.0 is reused — no new
  go-install step in CI.
- **Agent Assurance Profile: cross-provider gate-decision invariant
  (INV06) for self-modification.** When a `gate-decision` artifact
  adjudicates a change to the producer agent's own harness or source
  code (`decision.subject_class = "self-modification"`), the
  gate-decision MUST be issued by a model whose `provider_id` AND
  `model_family_id` BOTH differ from the proposing agent's. The
  conjunctive AND is load-bearing: same-provider/different-family and
  different-provider/same-family BOTH fail. Files changed:
  - `profiles/agent-assurance/ontology.toml` — three new attribute
    vocabularies (`subject_class`, `provider_id`, `model_family_id`),
    each IJB-tagged `constraint/structural` per KD rules.
  - `profiles/agent-assurance/gate-decision-kind.toml` — root-shape
    prose adds five optional fields (`subject_class` plus four
    `*_provider_id`/`*_model_family_id`); new hard invariant `INV06`
    encodes the conditional-required-and-inequality predicate; the
    `[kind.relation_to_ontology].attribute_vocabularies` list grows
    to include the three new vocabularies.
  - `profiles/agent-assurance/tiers/solo.toml` — contracts `C02`
    (AI self-sign) and `C05` (single-signer) carve out
    self-modification gate-decisions explicitly, deferring to INV06;
    `verified_by` adds `gate-decision-invariant:INV06@1`.
  - `profiles/agent-assurance/overview.md` — new "Scope and posture"
    section states the profile's multi-provider operating assumption,
    audience-impact note for single-provider deployments, and
    migration guidance for existing profile users.
  - `profiles/agent-assurance/tiers/README.md` — tier-table solo row
    references INV06; new "Cross-tier rule" callout makes explicit
    that INV06 is a profile-level posture, not a per-tier ratchet.
  - `examples/self-modification-gate-decision.toml` — new worked
    example with the full attribution shape (proposing anthropic/claude,
    deciding openai/gpt); existing
    `examples/minimal-gate-decision.toml` left unchanged (pre-INV06
    shape, still valid as a non-self-modification decision).
  - `reference/database/MANIFEST.toml` — `[counts]` bumped
    (attribute_vocabularies 43→46, attribute_values_declared 180→202);
    per-engine `expected_seed_counts` bumped
    (attribute_vocabulary 43→46, attribute_value_allowed 116→138 in
    postgres + duckdb + sqlite); rdf `expected_footer_counts`
    attribute_vocabularies 43→46; `expected_triple_counts.schema`
    1329→1400.
  - `reference/database/postgres/seed.sql`,
    `reference/database/duckdb/seed.sql`,
    `reference/database/sqlite/seed.sql` — each adds 3 new
    `attribute_vocabulary` rows (`subject_class`, `provider_id`,
    `model_family_id`) and 22 new `attribute_value_allowed` rows
    (2 + 10 + 10), using engine-correct array syntax
    (`ARRAY[]` / `[]` / `json_array()` respectively); header
    comments updated.
  - `reference/database/rdf/schema.ttl` — regenerated via
    `tools/dagtoml-rdf/target/release/dagtoml-rdf`; footer count
    moves from 43 to 46 vocabularies (1400 triples total).
  - `tools/dagtoml-duckdb/src/main.rs` and
    `tools/dagtoml-duckdb-go/main.go` — hardcoded `EXPECTED_COUNTS`
    mirror updated (43→46 vocab, 116→138 value rows) so the runtime
    self-check matches the new manifest.
  - `CHANGELOG.md` (this entry).

  Rationale and predecessor review: this change implements the
  proposal blocked in round-1 review at
  `docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal/`
  (terminal verdict `concrete_unresolvable_blocker` from codex + grok).
  Closures: B1 (chain-verifiable predicate via `subject_class`), B2
  (tight `AND` not "and/or" in INV06), B3 (solo tier C02/C05
  contradiction carved out), R1 (additive-optional fields + conditional
  invariant per `spec.md:482-489` versioning), R2 (migration guidance
  in overview + tiers/README), R3 (no proper-noun "agent-federator" in
  normative prose — the runtime contract is described, the broker name
  isn't). Round-2 multi-LLM review at
  `docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal-r2/`
  returned 2× `unconditional_approval` (gemini, grok) and 1×
  `concrete_unresolvable_blocker` (codex) on a single residual
  cross-cutting defect: this CHANGELOG entry's "Files changed"
  sub-bullet list initially omitted 8 of the 14 changed files (the
  list above as written closes that gap), plus a bundle metadata
  correction (see `r2/terminal_decision.toml` N2). A round-3 review
  is dispatched to verify the metadata fix without re-litigating
  the structural change.

### Fixed

- **CI: bump Node 20-deprecated actions to current major.**
  `actions/checkout` v4 → v5, `actions/setup-python` v5 → v6,
  `actions/setup-go` v5 → v6. GitHub announced Node 20 deprecation
  on runners with a 2026-06-02 hard cutoff (the older majors above
  bundle Node 20). `dtolnay/rust-toolchain@stable` is a shell-based
  action and unaffected.
- **CI: silence false positives + redact real leaks in the
  banned-markers grep.** Surfaced as a follow-on once the
  manifest-drift gate started running again (previously hidden
  behind the same CI failure). Two changes:
  1. **Workflow**: `.github/workflows/validate.yml`'s "Verify no
     banned markers" step now also excludes `docs/reviews/` from
     the `/srv/repos/internal` scan. Rationale: multi-LLM review
     audit trails legitimately discuss the banned-path policy by
     name as part of their evidence record (e.g., "Confirmed —
     banned internal path prefix absent."). The grep is meant to
     catch ACTUAL leaks in spec/example/code/paper surfaces, not
     narrative discussion of the policy in audit trails. Editing
     historical review files to obfuscate the string would
     falsify the audit record. Comment in the workflow now
     enumerates the full exclusion rationale.
  2. **Redactions**: `paper/Makefile` (1 occurrence in a header
     comment) and `paper/user-prompts.md` (2 occurrences in
     captured user-prompt history) had absolute
     `/srv/repos/internal/...` paths that genuinely should not
     ship in a public repo. The paths are now redacted in-place
     with `[internal path redacted: ...]` markers that preserve
     the substantive meaning (which internal artefact was being
     referenced) without leaking the absolute filesystem
     location. These leaks have existed since at least
     2026-05-21 (last green CI on this repo); they went
     undetected because the manifest-drift step was failing
     upstream and halting CI before "Verify no banned markers"
     ran.
- **CI: build `dagtoml-rdf` before the manifest-drift gate.** The
  count-mirror gate in `validators/check_attribute_values.py`
  (invoked by `validators/check_manifest_drift.sh`) probes
  `tools/dagtoml-rdf/target/release/dagtoml-rdf` to compute the RDF
  triple-count surface, and intentionally hard-fails when the
  binary is absent (the script's own comment: missing-binary is
  "the silent-mirror-rot pattern the gate exists to prevent"). The
  CI workflow built `dagtoml-validate-rs` and `dagtoml-validate-go`
  but never `dagtoml-rdf`, so the gate had been hard-failing on
  every push since the dependency was introduced — three
  consecutive `main` pushes before this fix (issue-ledger persist,
  SPEC §13 Phase 3 persist, toml-conformance-harness persist) all
  failed at this step despite their actual content being clean. New
  step "Build dagtoml-rdf (required by manifest-drift gate)" runs
  before the "Manifest drift" step.

### Added

- **toml-test parser-conformance harness — review approved (unanimous).**
  Round-1 multi-LLM review of commit `afe354c` returned 3/3
  `unconditional_approval` from codex, gemini, and grok. All three
  reviewers reproduced `make toml-conformance` (185/185 valid +
  358/358 invalid + 13 skipped) and independently re-ran the
  *unskipped* suite, confirming the 13-entry skiplist matches the
  actual fail set byte-for-byte. Codex additionally ran
  `go version -m` on the installed `toml-test-decoder` binary and
  observed `mod github.com/BurntSushi/toml v1.4.0` directly,
  providing binary-provenance evidence that the decoder is built
  from the same module `tools/dagtoml-validate-go` imports — the
  load-bearing claim of the change. Terminal decision persisted at
  `docs/reviews/2026-05-25-toml-conformance-harness/terminal_decision.toml`.
- **TOML 1.0 spec-conformance harness wired into CI.** New top-level
  `Makefile` ships two targets: `toml-conformance-install`
  (`go install`s the pinned `toml-lang/toml-test` runner and the
  `BurntSushi/toml` `toml-test-decoder` shim) and `toml-conformance`
  (runs the suite). The decoder is shipped by the same
  `BurntSushi/toml v1.4.0` module that `tools/dagtoml-validate-go`
  depends on, so a green run is evidence about the parser the Go
  validator actually uses at runtime — not just about some unrelated
  TOML library. Result on the pinned version: 185/185 valid and
  358/358 invalid pass, with 13 known-tolerated invalid-test misses
  enumerated in the Makefile's `TOML_CONFORMANCE_SKIPS` skiplist
  (all dotted-key / inline-table redefinition edge cases that
  pre-date the TOML 1.1 spec tightening). The skiplist is a
  baseline of permissiveness, not a permanent allowance: any bump
  of `TOML_TEST_DECODER_VERSION` requires revisiting it. Wired into
  `.github/workflows/validate.yml` as a new step adjacent to the
  Taplo lint, so both syntax-layer checks run together. Follow-up:
  a Rust decoder shim against the `toml` 0.8 crate used by
  `tools/dagtoml-validate-rs` would extend the same evidence path
  to the Rust validator's parser.
- **SPEC §13 retrofit — Phase 3 review approved (unanimous).** Round-1
  multi-LLM review of commit `3749398` (Phase 3 retrofit) returned
  3/3 `unconditional_approval` from codex, gemini, and grok. The
  R1/R2 challenge on `adapter-contract` (plan §7 row 7 + §8) was
  tested against bytes by codex (prompt-designated adversary) and
  grok (independent confirmer); both rejected R2 with file:line
  citations and upheld R1. Terminal decision persisted at
  `docs/reviews/2026-05-25-spec-13-phase-3-procedure-and-special/terminal_decision.toml`.
  With this approval the SPEC §13 retrofit arc (Phases 1 → 2 → 3)
  is fully closed; the `spec.md:1478-1486` follow-up is discharged
  and 19 of 19 blessed kinds now carry the §13 contract.
- **SPEC §13 retrofit — Phase 3 (procedure-bearing + special).
  Retrofit complete: 19 of 19 blessed kinds now declare §13.** Five
  kind descriptors retrofitted (all Family A under Reading R1):
  - `procedure-declaration.v1`:
    `profiles/agent-assurance/rollback-plan-kind.toml`. R1 header is
    explicit: the envelope bounds the descriptor parse only; runtime
    trigger evaluation (metric scraping, threshold comparison,
    paging) and procedure-step execution (flag flips, redeploys) are
    RUNTIME-SPEC and lie outside this envelope.
  - `validation-record.v1`:
    `profiles/agent-assurance/smoke-validation-kind.toml`. Records the
    outcome of a smoke run that already executed; the smoke run's own
    runtime capabilities are not constrained by this envelope.
  - `assertion-set.v1`:
    `profiles/agent-assurance/assertion-bundle-kind.toml`. SPEC-layer
    validation parses each `[[bundle.assertions]].line` against the
    ABNF and checks within-bundle ID uniqueness; hash/digest
    verification is RUNTIME-SPEC per the kind's own INV04.
  - `interface-contract.v1`:
    `profiles/agent-assurance/adapter-contract-kind.toml`. Plan §7
    flagged this kind for R1/R2 reviewer challenge; the §13 header
    comment is extra-explicit that R1 was adopted, that the runtime
    capabilities a deployed adapter is permitted at execution time
    are declared INSIDE the instance file's `[adapter].runtime_*`
    fields (NOT in this kind descriptor's envelope), and that an R2
    envelope would either be unboundedly wide or duplicate the
    instance-level declarations.
  - `cryptographic-proof.v1`:
    `profiles/disclosure/selective-disclosure-proof-kind.toml`. Per
    the kind's own prose at lines 61-62 and the plan §5
    Family-B/C-exceptions analysis (which codex r1 on the plan
    pinned against validator-vocabulary evidence): the SPEC-layer
    parse is shape-only; cryptographic verification is RUNTIME-SPEC.
    Family A — `entropy_source = "none"`, `crypto_keys.denied = true`.
  The abstraction-class validator now reports
  `19 file(s) checked; 19 declared a §13 block` (up from 14 after
  Phase 2). Closure-root validator remains green at 74 files — each
  retrofitted descriptor's declared `closure_root` stays at the
  canonical empty-closure sentinel per SPEC §12.11 because none of
  them cite upstream evidence. With Phase 3 landed, the SPEC §13
  retrofit follow-up called out at `spec.md:1478-1486` is fully
  closed: every blessed kind in the public spec now participates in
  §13's class + envelope contract and its closure-root cascade-break
  property.
- **SPEC §13 retrofit — Phase 2 (declarations).** Nine kind descriptors
  now declare the §13 contract, covering six new class ids:
  - `policy-declaration.v1` (3 kinds, each with its own kind-specific
    description per plan §6): `core/contract-declaration-kind.toml`,
    `core/readiness-gate-kind.toml`,
    `profiles/agent-assurance/spec-contract-kind.toml`.
  - `plan-decomposition.v1`: `core/implementation-dag-kind.toml`. The
    description explicitly states the envelope bounds the descriptor
    parse only (Reading R1 per plan §5); runtime capabilities of the
    units the DAG describes are declared on each unit's producer kind.
  - `extension-declaration.v1`: `core/profile-descriptor-kind.toml`.
  - `relation-ledger.v1`: `core/traceability-kind.toml`.
  - `binding-declaration.v1`:
    `profiles/agent-assurance/adapter-registry-binding-kind.toml`.
  - `threat-declaration.v1`:
    `profiles/agent-assurance/threat-model-kind.toml`. The §13 prose
    explicitly avoids the IJB-forbidden phrase "risk posture", per the
    kind's existing IJB-stance note.
  - `attestation-record.v1`:
    `profiles/disclosure/disclosure-attestation-kind.toml`. The
    description records that signature verification is RUNTIME-SPEC,
    matching the kind's existing prose at lines 69-70.
  Every retrofit uses the Family A envelope (100ms CPU, 1MB memory, all
  9 capability domains denied/zeroed) matching the cost-record /
  Phase 1 reference shape. The abstraction-class validator now reports
  `19 file(s) checked; 14 declared a §13 block` (up from 5). Closure-root
  validator remains green at 74 files — each retrofitted descriptor's
  declared `closure_root` stays at the canonical empty-closure sentinel
  per SPEC §12.11 because none of them cite upstream evidence (the
  descriptor file's SHA-256 changes; its declared closure_root value
  does not). Phase 3 (5 procedure-bearing + special kinds) remains
  follow-up work per plan §8.
- **SPEC §13 retrofit — Phase 1 (observation-record.v1).** Four kind
  descriptors now declare the §13 contract: `core/evidence-matrix-kind.toml`,
  `profiles/agent-assurance/gate-decision-kind.toml`,
  `profiles/agent-assurance/assertion-log-record-kind.toml`, and
  `profiles/disclosure/redaction-manifest-kind.toml`. Each adds
  `[kind.abstraction_class]` with `id = "observation-record.v1"` and a
  kind-specific `description` that names its own structural shape (per
  the per-kind-description rule in
  `docs/planning/2026-05-25-spec-13-retrofit-scoping.md §6`), plus a
  Family A `[kind.capability_envelope]` block (100ms CPU, 1MB memory,
  all 9 capability domains denied/zeroed) matching the cost-record
  reference at `profiles/cost/cost-record-kind.toml:282-327`. The
  abstraction-class validator now reports
  `19 file(s) checked; 5 declared a §13 block` (up from 1). Closure-root
  validator remains green at 74 files — each retrofitted descriptor's
  declared `closure_root` stays at the canonical empty-closure sentinel
  per SPEC §12.11 because none of them cite upstream evidence (the
  descriptor file's SHA-256 changes; its declared closure_root value
  does not). Phases 2 (8 declaration kinds) and 3 (5 procedure-bearing
  and special kinds) remain follow-up work per plan §8.
- **SPEC §13 — Abstraction class + capability envelope.** Folds the
  Stream F V2 + Turn-6 abstraction-class-type-safety proposals
  (`docs/research/2026-05-22-spec-foundations-research/follow-up-2/16-stream-f-synthesis-v2.md`
  + `.../10-abstraction-class-thread.md` + `.../12-canonical-thread.md`)
  into normative spec text. Every `*-kind.toml` descriptor MAY now
  declare two optional blocks: `[kind.abstraction_class]` (a single
  versioned class id of the form `<slug>.v<integer>` + a producer-
  attested description) and `[kind.capability_envelope]` (resource
  bounds + a closed-set of nine per-domain capability grants drawn
  from WASI Preview 2 WIT: filesystem, sockets, http, clocks,
  random, environment, process_spawn, ipc, crypto_keys). Both
  blocks are part of the kind descriptor's canonical bytes and
  flow into its `closure_root` per §12.1, so changing the class or
  widening the envelope cascade-breaks downstream instances. New
  subsections §13.1–§13.10 cover the rule, the two block shapes,
  the cascade-break property, scope-out (wire format, attenuation
  calculus, signing tier, enforcement backend, static-observability
  for WASM are all RUNTIME-SPEC), IJB conformance, the
  closed-vocabulary participation, a worked `data-transform.v1`
  example, four forbidden papering-over mechanisms (re-sign under
  unchanged closure_root on widening; implicit-grant on missing
  domain; ad-hoc capability fields outside the closed set; mixing
  technical+legal signing tiers), and the backwards-compatible
  introduction rule (existing kinds remain conformant; new
  declarations are opt-in).
- **Two new core ontology vocabularies** in `core/ontology.toml`:
  - `capability_envelope.domain` — closed set of 9 WIT-derived
    domain names; sub-table names under
    `[kind.capability_envelope]` are bounded by this vocabulary.
    Adding a new domain is a SPEC amendment that bumps
    `schema_version`. Fail-closed default: an omitted domain
    sub-table is treated as denied (§13.9).
  - `abstraction_class.id_pattern` — closed pattern
    `<slug>.v<integer>` with `<slug>` producer-attested and
    `v<integer>` required + monotonic. The value space is open by
    design (producers declare their own class taxonomy); the
    shape is closed so consumers can reject class-version drift
    via the §12 closure-root cascade.
- **`validators/validate_abstraction_class.py`** — dedicated
  reference validator. Enforces the structural rules of §13.2 +
  §13.3: id pattern, IJB tags, required cpu/memory bounds,
  closed-set domain names (with the single source of truth being
  the core ontology's `capability_envelope.domain` vocabulary),
  per-domain sub-table shape (preopens + read/write/exec for
  filesystem; tcp/udp/ip-resolve allowlists for sockets; etc.).
  Backwards-compatible: descriptors that omit both blocks pass.
  Wired into CI as a separate workflow step.
- **Worked example** in `profiles/cost/cost-record-kind.toml`: the
  cost-record kind now declares
  `abstraction_class.id = "observation-record.v1"` (read-only
  observation artefact, no I/O, no networking) and a minimal
  capability envelope (1MB memory, 100ms CPU, all 9 capability
  domains denied or zeroed). This is the first kind descriptor in
  the spec to declare the §13 primitive; it demonstrates the
  pattern. The other 18 kinds remain unmodified — retrofitting
  them is explicit follow-up work.
- **Reference DB updates**: 2 new attribute vocabularies + 10 new
  attribute values seeded across postgres / sqlite / duckdb.
  `expected_seed_counts.attribute_vocabulary` 41→43,
  `attribute_value_allowed` 106→116. RDF regenerated:
  `expected_triple_counts.schema` 1291→1329. Rust + Go
  `EXPECTED_COUNTS` hardcodes updated. MANIFEST `[counts]`:
  `attribute_vocabularies` 41→43, `attribute_values_declared`
  170→180, `attribute_values_closed` 99→109.
  `bash validators/check_manifest_drift.sh` is green at the new
  totals across all 28 count-mirror surfaces.

- **Cost profile (Stream G — Cost-Witnessed Decision).** New blessed
  profile under `profiles/cost/` with a single kind, `cost-record`,
  declaring the cost of one costed action so that gate-decisions and
  evidence-matrix entries can cite *which* costs witnessed a verdict
  and an auditor can see *what class of deciding entity* paid for it.
  Three closed vocabularies in `profiles/cost/ontology.toml`:
  `cost_dimension_category` (7 values: token_equivalent,
  compute_time_seconds, storage_bytes, bandwidth_bytes,
  human_review_time_seconds, energy_equivalent, evidence_run_count),
  `decider_class` (8 values: deterministic_check, llm_single,
  llm_consensus, human_reviewer, tee_attested_compute, notarisation,
  transparency_log_write, other), `cost_citing_kind` (7 values
  enumerating the kinds whose execution may pay a cost). Quantities
  are non-negative integers (no floats per canonical-form
  determinism); unit labels are producer-attested and free-form (no
  spec-fixed unit normalisation — comparability across producers
  requires an explicit conversion artefact). Minimal example at
  `examples/minimal-cost-record.toml` (smoke-validation paid for by
  three-model LLM consensus). Per the proposal under
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/13-stream-g-cost-witnessed-decision.md`,
  the cost-record is observation not policy; signatures, currency,
  vendor SKUs, allowances, and transitive aggregation are
  deliberately out of scope. The kind names Cost-Witnessed Decision
  as the third frontier primitive peer to Provable Intent
  (SPEC §12 closure-root) and Structural Governance (SPEC §3/§10
  IJB). New `validators/validate_cost.py` enforces invariants
  INV01–INV06 (closed-vocab membership × 3, integer-only quantities,
  RFC 3339 timestamps, MD5/SHA-1 forbidden). INV07 — IJB-primitive
  resolution of every entity prefix and relation predicate used in
  instance files — is delegated to the shared
  `validators/validate_ijb_conformance.py` as declared in the kind
  descriptor's `[[kind.hard_invariants]] enforced_by` field; the
  cost validator deliberately does not duplicate that cross-cutting
  check. Reference DB seeds
  (postgres / sqlite / duckdb), MANIFEST counts, and regenerated
  RDF schema all updated; `bash validators/check_manifest_drift.sh`
  is green at 20 template kinds / 27 entity kinds / 31 relation
  predicates / 41 attribute vocabularies. CI gates the cost profile
  alongside agent-assurance and disclosure.
- **Second-pass review filings + round-2 fixes for `examples/arxiv-prep-agent-dag.toml`.**
  Captured the three completed second-pass job outputs (Claude / Codex /
  Gemini) into
  `docs/reviews/2026-05-24-arxiv-prep-dag/second-pass/raw_findings/` so the
  audit trail exists. Patched `examples/arxiv-prep-agent-dag.toml` for the four
  blockers Codex enumerated (LL-001 prose-header overclaim narrowed to the
  documented corpus; LL-002 subdir/flatten policy made explicitly
  mode-selectable via `policy.instance.allow_subdirs`; NEW-001 U09
  manifest path moved into `evidence/` subdirectory to match its summary
  prose; NEW-002 U10 submission-bundle summary now states the .bbl
  inclusion rule explicitly, conditioned on U04's mode), plus the two
  STILL-PRESENT leftover overclaims Codex flagged (UC-002 "vanishingly
  unlikely" replaced with a bounded eliminates-documented-classes claim;
  SR-001 "authoritative sources" replaced with "referenced source
  corpus"). Both `validate_implementation_dag.py` and
  `validate_ijb_conformance.py --repo-root .` still PASS on the patched
  file. A third-pass review (including a non-plan-mode Claude re-run) is
  required before unconditional approval.
- **Migration note for pre-§12 producers** at spec.md §12.11. Walks
  the four-step migration mechanically: identify conforming
  documents (`[meta].template_kind` blessed per §12.1), choose the
  closure value (empty-closure sentinel for self-contained docs,
  computed digest per §12.1 otherwise), place the field before the
  first `[table]` header, re-emit + re-sign. This is a
  backwards-incompatible conformance change; per §8.2 it would
  normally bump major `schema_version`, but the rule lands
  during the Draft Specification phase so `schema_version` stays at
  `"0.1.0"`.
- **SPEC §12 — the closure-root rule (brittleness propagation).** Folds
  the proposal under
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/14-`
  into normative spec text. Every conforming DAG-TOML document MUST
  carry a root-level `closure_root` field of the form
  `<sha256|sha384|sha512>:<lowercase-hex>` computed over the canonical
  concatenation of (1) every upstream artifact hash cited and (2)
  every upstream revocation snapshot known at emission time. The
  field MUST appear before the first `[table]` header so TOML binds
  it to the document root rather than to `[meta]`. Self-contained
  documents emit the canonical empty-closure sentinel
  `sha256:e3b0…b855` (SHA-256("")), with stronger-digest analogues
  tabled in §12.1. New subsections §12.2–§12.10 cover the
  cascade-break property, producer/consumer responsibilities,
  what is deliberately out of scope (envelope format, signing
  primitive, transparency-log target), four forbidden papering-over
  mechanisms (re-signing on stale closure, storing closure in
  unsigned envelope attributes, "soft revocations", caching closure
  inputs across upstream versions), the deferred canonical-
  concatenation algorithm, interactions with §2.7 / §5 / §11 /
  the disclosure profile (redaction does NOT flip the upstream's
  closure), and the live-feed snapshot rule. Back-references added
  in §2.7 (posture fields are NOT closure-root inputs), §5
  (closure-graph acyclicity extends the §5 cycle prohibition), and
  §11 (`source_sha256` is *one input* to `closure_root`, not a
  substitute).
- **`cites_upstream` core relation predicate** in
  `core/ontology.toml`. Cross-kind marker that a `*-kind.toml`
  required field carries an upstream artifact reference that MUST
  flow into the document's closure root. Source and range are
  intentionally `unconstrained_label` — the rule fires uniformly
  across every conforming kind regardless of which concrete
  entity kinds a profile defines. Total core relation count is
  now 31 (was 30).
- **`closure_root.digest_algorithm` core attribute vocabulary** in
  `core/ontology.toml` (extensible: `sha256` | `sha384` | `sha512`).
  Closed-for-now; extension reserved for stronger / post-quantum
  digests. Weaker algorithms (MD5, SHA-1) are forbidden by SPEC
  §12.1 and MUST NOT be added. Total core attribute-vocabulary
  count is now 10 (was 9); union with profile vocabularies is 38
  (was 37).
- **`validators/validate_closure_root.py`** — dedicated reference
  validator for the §12 rule. Enforces presence at the document
  root, `<algo>:<hex>` shape, hex-length-matches-algorithm, and
  explicit rejection of MD5/SHA-1. Wired into CI as a separate
  workflow step gating every canonical example and tier file.
  Computation of the digest itself is profile/runtime work; the
  validator enforces the spec-layer rules only.
- **Empty-closure sentinel applied to every canonical example.** All
  17 minimal examples under `examples/` plus all 5 deployment-tier
  files now declare the canonical empty-closure sentinel as their
  root-level `closure_root` so the brittleness graph is a total
  function — every conforming document participates.
- **Reference database updates for §12.** `cites_upstream` and
  `closure_root.digest_algorithm` (plus its three closed values) are
  seeded in `reference/database/{postgres,sqlite,duckdb}/seed.sql`
  and in `reference/database/graph/schema.cypher`. The RDF
  reference (`reference/database/rdf/schema.ttl`) was regenerated
  via `tools/dagtoml-rdf`. `reference/database/MANIFEST.toml`
  `[counts]` updated to `relation_predicates = 31`,
  `attribute_vocabularies = 38`, `attribute_values = 84`; all
  per-engine `expected_*_counts` updated to match. `bash
  validators/check_manifest_drift.sh` is green.
- **ArXiv submission pre-flight DAG** — `examples/arxiv-prep-agent-dag.toml`.
  A 10-unit `implementation-dag` (core only) that encodes every requirement from
  Trevor Campbell's checklist, the official arXiv "Common Mistakes" FAQ, Ian Huston's
  2011 checklist, and the current `submit_tex.html` + `texlive.html` guidance
  (TeX Live 2025, bib/biber auto-processing, minted v3 cache rules, ifpdf, hyperref
  order, 4-pass typeout, filename hygiene, figure formats, 00README, hidden-file
  stripping, etc.). Uses the exact same `[policy.*]` + `proofs_mapping` + `evidence`
  + gated-compilation pattern as `claim-analysis-agent-gated-dag.toml`. All
  `ART:`, `OUT:`, `Uxx`, and predicate strings pass `validate_ijb_conformance.py`.
  The DAG produces a clean tarball + machine-readable evidence pack that makes
  arXiv rejection for packaging reasons effectively impossible. Full text of the
  three source URLs was retrieved via Exa MCP before authoring.
- **Stream F triangulation + V2 synthesis + `source-analysis` profile
  proposal** under
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/`.
  Three CLI agents (Codex/Gemini/Grok) gave independent second-opinion
  reports on the Exa Deep Researcher's capability-envelope verdict and
  converged on the same six categorical critiques. Stream F V2
  synthesis (`16-`) supersedes the Exa Deep report as the canonical
  Stream F output: CDDL stays for shape only (attenuation moves to a
  separate executable calculus); draft dCBOR is replaced by RFC 8949
  Core Deterministic Encoding + frozen profile rules (floats
  prohibited); COSE_Sign1 stays for technical integrity but **CB-AdES
  (ETSI TS 119 152-1, March 2026)** is now the recommended legal-grade
  COSE profile carrying `xRefs`/`rRefs`/`sigTst`/`arcTst` headers;
  Linux syscall names are replaced by **WASI Preview 2 WIT interfaces**
  as the canonical capability vocabulary; the seven-field envelope is
  expanded to nine capability domains plus separate resource bounds;
  and the "compression library opens a socket" example is reframed
  as static observability via WASM Component Model imports (consumer's
  CI rejects the artifact at parse time, not runtime). The
  `source-analysis` profile proposal (`15-`) drafts a three-kind
  subset of the spec (`source-record`, `semantic-extraction`,
  `source-citation`) for analyzing articles/research papers, capturing
  their logical/semantic/intent structure as IJB-typed graphs, signing
  the extraction, and emitting a cryptographically-bound citation
  format `[author24/hash8]`. Both proposals await maintainer review.
- **Stream F (capability envelopes), Stream G (Cost-Witnessed Decision),
  and the closure-root spec.md section proposal** under
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/`.
  Stream F's Exa Deep Researcher report proposes a hybrid CBOR-canonical
  serialization + typed envelope schema (CDDL over CBOR + COSE signing
  with DID-bound keys), with attenuation via monotonic set-reduction
  and enforcement via LSM/seccomp/Capsicum/CHERI per deployment; the
  three CLI-agent companion runs were lost to gateway result-retention
  ageing and are being re-launched as second-opinion triangulation.
  Stream G ("Cost-Witnessed Decision") proposes a new `cost-record`
  template kind (placement deferred to a new minimal `cost` profile),
  with a `decider_class` closed-set discriminator that makes gate
  threat-surface legible to auditors, seven closed-set cost dimensions
  with producer-attested unit labels, integer-only quantities (matching
  Stream D's no-floats consensus), and an optional `[[decision.cited_costs]]`
  cross-reference into gate-decision. The closure-root spec.md section
  proposal drafts a new top-level §12 establishing the
  brittleness-propagating attestation rule (upstream changes MUST flip
  downstream `closure_root`; signed envelopes wrapping downstream
  documents MUST become invalid; non-normative warning that this
  inverts standard PKI behaviour and enumerates four forbidden
  papering-over mechanisms). Not yet folded into spec.md — proposal
  awaits maintainer review.
- **Spec intro framing — Provable Intent + Structural Governance**
  (`spec.md`, `README.md`). Names the two load-bearing deliverables the
  spec exists to solve, anchored to the "writing code is becoming the
  new assembly language" framing and the "bicycle vs. autonomous
  self-generating infrastructure" rebuttal. Replaces the earlier dry
  "describes how agents plan, sequence, and prove work" framing as the
  reader's first encounter with the spec's purpose. Detailed rationale
  in `docs/research/2026-05-22-spec-foundations-research/follow-up-2/11-overkill-rebuttal-and-frontier-problems.md`.
- **Abstraction-class type-safety primitive** added to design directives
  (`docs/research/2026-05-22-spec-foundations-research/06-user-design-directives.md`
  Turn 6 addendum). Kind descriptors must declare both structural shape
  AND capability envelope; class violations must cascade-break
  downstream regardless of signature validity. Three-part and five-part
  thread drafts in `follow-up-2/10-` and `follow-up-2/12-` respectively.
- **Cross-LLM + Exa research dossier on spec foundations**
  (`docs/research/2026-05-22-spec-foundations-research/`). Independent
  external research conducted in parallel by Claude+Exa, Codex+Exa,
  Gemini+Exa, Grok+Exa, and Exa Deep Researcher (`exa-research-pro`),
  across three waves and 13 research streams:
  - **First wave** — six questions (IJB primitives prior art,
    TOML-only spec-design risks, self-describing-schema drift,
    agent-assurance governance, spec-design failure modes, DAG
    traceability).
  - **Follow-up wave** — four streams (kind-descriptor drift mitigation,
    legal-grade one-shot immutable attestation, separation-of-duty
    validation, alternative-format selection / new-format design).
    Convergence across four independent sources was unusually tight;
    recommended build order D → A → C → B.
  - **Third wave (`follow-up-2/`)** — cognitive-automation lineage
    ("what do we do with more processing power"), HW/SW/cognition
    layering as inference cost declines and FPGA emerges, plus
    a Grok-shared conversation about Cloudflare zero-trust TOML
    hosting (recovered via headless-Chrome render of the share URL).
  - Includes the user's design directives, per-stream synthesis,
    full prompt reproducibility (`prompts/`), and operational records
    (`raw/job-manifest.toml`, `raw/failed-attempts.md`). Total Exa Deep
    Researcher spend across waves: $10.21.
- **Pre-1.0 layering primitives** (spec.md §2.5, §2.7, §6.1, §11.1).
  Four hard-to-retrofit additions land together so the public/private
  boundary stops drifting:
  - **`profile-descriptor` kind** (`core/profile-descriptor-kind.toml`).
    Meta-meta layer documenting profiles the way `kind-descriptor`
    documents `template_kind`s. Declares `name`, `namespace`, `owner`,
    `license`, `extends`, `ontology`, `contained_kinds`. Reference
    instances at `profiles/agent-assurance/PROFILE.toml` and
    `profiles/disclosure/PROFILE.toml`.
  - **Profile namespacing partition** (SPEC §2.5). Unprefixed
    kebab-case is reserved for blessed profiles; everything else MUST
    be reverse-DNS. The DNS namespace gives adopters uniqueness
    without a central registry.
  - **`[meta].confidentiality / license / embargo_until`** (SPEC §2.7).
    Closed set for confidentiality, free-form SPDX/`LicenseRef-…` for
    license, RFC 3339 for embargo_until (REQUIRED when
    `confidentiality = "embargoed"`).
  - **`[provenance.encryption]` sub-table** (SPEC §11.1). Records the
    encryption shape so a `[provenance]` block can refer to encrypted
    source bytes without the spec ever touching keys.
- **Disclosure profile** (`profiles/disclosure/`). New blessed profile
  with three kinds — `disclosure-attestation`, `redaction-manifest`,
  `selective-disclosure-proof` — plus its own ontology extension and
  three minimal examples
  (`examples/minimal-disclosure-attestation.toml`,
  `examples/minimal-redaction-manifest.toml`,
  `examples/minimal-selective-disclosure-proof.toml`).
- **Safe-Rust + Go primary validators** under
  `tools/dagtoml-validate-rs/` and `tools/dagtoml-validate-go/`. Both
  cover profile-descriptor invariants (INV01..INV05), the disclosure
  profile, the `[provenance.encryption]` sub-table, and the §2.6 /
  §2.7 meta-field rules. Rust crate is `#![forbid(unsafe_code)]`
  (enforced by `validators/check_safe_tools.sh`); Go module uses the
  BurntSushi/toml parser. CI runs both BEFORE the Python validators;
  divergence is a build break. The pre-existing Python validators
  (`validators/validate_*.py`) are retained as cross-checks.
- **Reference Python validators for the new artifacts.**
  `validators/validate_profile_descriptor.py` and
  `validators/validate_disclosure.py`.
- **Adoption guide** at `docs/adoption.md` — non-normative,
  walks the "public spec, private profile" pattern with a worked
  `com.example.internal` example.
- **Pre-1.0 cleanups** bundled with the layering work:
  - `confidentiality = "public"` and `license = "Apache-2.0"` set on
    every canonical example and tier file so adopters see the new
    fields in practice.
  - SPEC §2.6: `[meta].docs` MUST start with `https://` and MUST NOT
    contain a query string; enforced by the primary validators.
  - `core/ontology.toml` new `[[attribute_vocabularies]]` entries:
    `confidentiality`, `license`, `framework_profile_namespace`, and
    `provenance.encryption.hash_is_over`.
  - `validators/validate_ijb_conformance.py` extended to classify the
    three new meta fields and to dispatch on
    `template_kind = "profile-descriptor"`. The §10.2 mapping note
    now permits `ijb_constraint_type = "policy"` or `"observed"` on
    `[[attribute_vocabularies]]` blocks (declared posture
    vocabularies).
- `reference/database/`: non-normative reference database schemas for
  ingesting DAG-TOML instances. Includes `postgres/schema.sql` (hybrid
  relational + JSONB, with enums for closed attribute vocabularies and
  views for DAG/coverage/gate queries), `postgres/seed.sql` (registry
  rows derived from the ontology files and `*-kind.toml` descriptors,
  covering all 15 template kinds (5 core + 9 profile + the meta
  `kind-descriptor`), all 23 entity kinds (17 core + 6 profile), all
  30 core relation rows (with `contract:`-namespaced variants for
  predicate names the ontology declares more than once), and all 29
  attribute vocabularies (5 core + 24 profile)), and
  `graph/schema.cypher` (property-graph model with constraints,
  indexes, registry seed, and example invariant + traversal queries).
  `reference/database/README.md` documents the design principles, IJB
  grounding, and ingestion model. `reference/database/MANIFEST.toml`
  provides the machine-readable companion: artifact paths, target
  versions, namespaced-predicate convention, and the ontology-derived
  counts the seed inserts (15 / 23 / 30 / 29 / 54) so an ingestion
  tool or drift check can verify load results without re-parsing the
  ontology. Nothing under `reference/database/` is conformance-required;
  the ontology files and validators remain the source of truth.
- `reference/database/sqlite/`: SQLite/libSQL (Turso) reference schema.
  Same registry shape and counts as the Postgres reference, adapted to
  SQLite STRICT tables (no `CREATE TYPE` enums — column-level CHECK
  lists instead; JSON via the json1 built-in; arrays as JSON values;
  cycle detection as a recursive view since SQLite has no stored
  functions). Verified by loading `schema.sql` + `seed.sql` into stock
  SQLite 3.51 in an alpine container — same 15/23/30/29/54 row counts,
  same invariant views fire on the same fixture. libSQL ≥0.24 supports
  every feature used; no schema changes needed for Turso.
- `validators/check_manifest_drift.sh`: pure-bash drift check. Compares
  the four counts in `reference/database/MANIFEST.toml [counts]`
  against the live ontology files (number of `[[entities]]`,
  `[[relations]]`, `[[attribute_vocabularies]]` blocks plus the count
  of `*-kind.toml` descriptors). Also parses the footer of
  `reference/database/rdf/schema.ttl` and verifies the same counts so
  a stale RDF artifact is caught even when the manifest and SQL seeds
  were correctly regenerated. Exits non-zero on either drift. Wired
  into the validate CI workflow as the step after Taplo lint.
- `reference/database/rdf/`: RDF/Turtle reference. `schema.ttl` renders
  the IJB primitives, 15 template kinds, 23 entity kinds, 30 relation
  predicates, and 29 attribute vocabularies as RDF classes and
  properties under three namespaces (`dagtoml:`, `dagprof:`, `ijb:`).
  Closed vocabularies use `owl:oneOf` ranges; open vocabularies are
  marked `dagtoml:extensible true`. `shapes.ttl` is hand-authored
  SHACL covering the graph-shaped invariants the schema alone cannot:
  single producer per artifact, depends_on/blocks symmetry,
  depends_on acyclicity, cardinality 1 on matrix claim/evidence and
  gate artifact_class, plus closed-vocab `sh:in` enforcement. Both
  files verified as well-formed Turtle (1025 + 148 triples). The
  generator is the Rust crate at `tools/dagtoml-rdf` — no Python
  dependency; SHACL is hand-authored because the invariants are
  spec-stable, not ontology-derived.
- `reference/database/duckdb/`: DuckDB reference. Native ENUM types
  (PG-style), native `LIST<VARCHAR>` arrays (no JSON encoding for
  relation domain/range), native UUID/JSON/TIMESTAMPTZ. Schema is a
  port of the Postgres reference, not the SQLite one — DuckDB sits
  closer to PG in expressive power. Cycle detection is a recursive
  `CREATE VIEW` instead of a stored function (DuckDB has no
  PG-style stored functions). Loads on `duckdb >= 1.5` with the same
  15/23/30/29/54 row counts; all four invariant views fire correctly
  on the standard fixture (multi-producer, asymmetric depends_on,
  free-form discrimination). The `.duckdb` artifact is binary and
  intentionally NOT checked in — consumers regenerate via
  `tools/dagtoml-duckdb`.
- `tools/dagtoml-rdf/`: Rust generator (edition 2024) reading
  `core/ontology.toml` + `profiles/agent-assurance/ontology.toml` +
  every `*-kind.toml` and emitting `reference/database/rdf/schema.ttl`.
  Subcommand `dagtoml-rdf verify -o <ttl>` re-parses the artifact
  with `oxttl` to confirm well-formedness. Single binary, no Python
  in any code path. Build: `cargo build --release -p dagtoml-rdf`.
- `tools/dagtoml-rdf-go/` + `tools/dagtoml-duckdb-go/`: Go counterparts
  of the Rust tools. Same logic, same outputs (matching 1188-triple
  Turtle / 19/26/30/37/81 row counts). The Go RDF generator uses
  `github.com/pelletier/go-toml/v2`; the Go DuckDB orchestrator has zero
  third-party deps. Both files explicitly do NOT `import "unsafe"`.
- `validators/check_safe_tools.sh`: CI gate enforcing that every Rust
  crate under `tools/` carries `#![forbid(unsafe_code)]` and no Go file
  under `tools/` imports `unsafe`. Wired into `.github/workflows/
  validate.yml` immediately after the manifest-drift step. Tested with
  injected violations in both languages — fails fast with a precise
  file:line citation.
- `tools/README.md`: documents the safety policy, lists current tools,
  and states that Python is supported as a third option but is no
  longer the default for new tooling.
- Both Rust crates (`tools/dagtoml-rdf` and `tools/dagtoml-duckdb`)
  now carry `#![forbid(unsafe_code)]` at the top of `src/main.rs`.
  Builds are warning-clean with the lint enforced.
- `reference/database/{postgres,sqlite,duckdb}/seed.sql` + MANIFEST
  counts resync: ontology now has 6 core `*-kind.toml` files (added
  `profile-descriptor`), a second `disclosure` profile (3 entities +
  4 vocabs + 3 kind files), and 4 new core vocabularies
  (`confidentiality`, `license`, `framework_profile_namespace`,
  `provenance.encryption.hash_is_over`). New canonical counts:
  19 / 26 / 30 / 37 / 81 (kind / entity / relation / vocab /
  allowed-value rows). All three SQL reference DBs reload cleanly
  with the new counts; the RDF generator was updated to walk all
  profiles dynamically (no profile names hardcoded). The manifest
  drift script now also walks all profiles.
- `tools/dagtoml-duckdb/`: Rust orchestrator that wraps the `duckdb`
  CLI to build a `.duckdb` from the checked-in `duckdb/schema.sql` +
  `seed.sql` and verify the post-load row counts. Zero third-party
  dependencies (no libduckdb-sys; the engine lives in the
  consumer-installed CLI). Defaults the output stem to
  `agent_assurance` because DuckDB derives the catalog name from the
  file stem and a `dagtoml.duckdb` file would collide with the
  `dagtoml` schema name. Build: `cargo build --release -p dagtoml-duckdb`.
- `spec.md §11`: optional root-level `[provenance]` table for DAG-TOML
  files that are generated from a separate source artifact. When
  present it MUST carry `source_path`, `source_sha256`, and
  `source_bytes`; validators recognising the table MUST recompute the
  SHA-256 and byte length of the referenced file and fail on mismatch.
- `validators/validate_provenance.py`: the reference validator for the
  new `[provenance]` table. Walks each TOML it is handed, treats a
  missing `[provenance]` as silent PASS, and on a present table
  enforces the SHA-256 / byte-length binding described in `spec.md §11`.
  Rejects absolute `source_path` values and rejects relative paths
  that resolve outside the repo root (containment check, per SPEC §11).
- `validators/validate_rollback_plan.py`: closure check for the
  `rollback-plan` kind's `trigger_kind` enum. The hard invariant in
  `profiles/agent-assurance/rollback-plan-kind.toml` requires every
  `[[triggers]].trigger_kind` value to come from the profile ontology's
  declared vocabulary; that rule was previously not enforced by
  `validate_ijb_conformance.py` because instance-file rules only
  inspect ID-shaped strings and declared predicate values. The new
  validator closes that gap.
- `skills/convert-md-to-dag/`: authoring skill that produces a governed
  DAG-TOML package (implementation-dag, contract-declaration,
  readiness-gate, traceability, threat-model, rollback-plan) from a
  source Markdown file. Every generated TOML includes a `[provenance]`
  table that binds the package to the originating Markdown via the
  `spec.md §11` SHA-256 contract. New top-level `skills/` directory
  documented in `README.md`.
- `validators/validate_code_symbols.py` (experimental): sqry-backed
  symbol existence check for Rust, Go, TypeScript, and Java
  traceability entries. Not yet a CI gate (sqry install in CI is
  unpinned); see `docs/language-validators.md`.
- `examples/language-validation/`: cross-language traceability fixture
  used by `validate_code_symbols.py`, plus minimal Rust, Go,
  TypeScript, and Java source stubs. Validated structurally by CI
  (path-existence + IJB conformance) and protected from symbol drift
  by a grep-level CI check.
- `docs/language-validators.md`: companion doc describing the
  experimental sqry-backed code-symbol validator and what would have
  to land before it becomes a required CI job.
- Three new `trigger_kind` values in the profile ontology vocabulary:
  `validator_failure`, `missing_evidence`, `manual_override`. These
  cover spec-authoring and audit-flow rollback triggers where the
  trigger is a tooling outcome rather than a runtime metric.
- CI: `.github/workflows/validate.yml` now also IJB-validates every
  TOML under `skills/convert-md-to-dag/` and
  `examples/language-validation/`, enforces the `[provenance]`
  binding (`validate_provenance.py`) on every file with a
  `[provenance]` table, enforces the rollback-plan `trigger_kind`
  closure on both the minimal example and the skill instance, and
  fails if any language fixture loses a declared symbol name.

### Changed

- **SPEC §13 — three independent-review blockers closed (r1 fix
  commit; Codex r1 findings F1/F2/F3 + the deeper §2.4 contradiction
  Claude surfaced during fix-plan synthesis).**
  - **F1 (high) — §13.3 cited a nonexistent normative file.**
    `spec.md:1324-1327` (commit `27c1020`) stated the full grant
    sub-table schema was "declared by the
    `core/kind-descriptor-kind.toml` descriptor's
    `[kind.capability_envelope]` schema". That file does not exist
    and §2.4 (`spec.md:128-134`) explicitly states "tooling MUST
    NOT require a `kind-descriptor-kind.toml` to exist." The §13.3
    sentence is rewritten to name the actual normative surfaces
    jointly: the closed `capability_envelope.domain` vocabulary in
    `core/ontology.toml`, the per-domain shape checks in
    `validators/validate_abstraction_class.py`, and the §13.3 prose
    itself, with an explicit cross-reference to §2.4's
    recursion-stop rule.
  - **F2 (medium) — §13.3 prose / validator syntax mismatch on
    domain denial.** `spec.md:1268-1270` (commit `27c1020`) said
    "Each domain is either denied entirely (`false`) or scoped via
    a sub-table." The validator rejects any top-level domain value
    that is not a sub-table
    (`validators/validate_abstraction_class.py:300-310`), and the
    worked example
    (`profiles/cost/cost-record-kind.toml:300-327`) uses the
    `denied = true` sub-table form on every denied domain. Prose
    is corrected to: "Each domain is a sub-table — denied via
    `denied = true` or scoped via fields that constrain the
    grant." Missing-domain fail-closed semantics are preserved by
    `spec.md:1305-1307` (the §13.3 worked example) and the §13.9
    "Missing-domain = denied" bullet.
  - **F3 (medium) — §13.9 forbade signing-tier composition,
    contradicting §13.5's scope-out.** `spec.md:1470-1472` (commit
    `27c1020`) read: "Mix the technical-tier and legal-tier
    signatures on the same artefact. Either tier carries the
    closure root; both is declared posture, not engineering."
    §13.5 (`spec.md:1363-1366`) explicitly defers signing-tier
    selection to profile/runtime, and §12.5 scopes signing-envelope
    format to profiles/RUNTIME-SPEC. Mixed-tier rules are a
    signing-profile policy, not a capability-envelope
    papering-over mechanism. The bullet is deleted; the remaining
    three §13.9 bullets (re-sign under unchanged closure_root after
    envelope widening; treating missing domain as implicit grant;
    encoding capability declarations outside
    `[kind.capability_envelope]`) are all capability-envelope
    papering-over mechanisms and structurally complete for §13.9's
    actual scope.
  - Persistent review evidence:
    `docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md`
    (Codex r1 — original blockers); `.../raw_findings/grok.md`
    (Grok r1 — methodology-split unconditional approval);
    `.../raw_findings/codex-fix-plan-r1.md` (Codex pre-implementation
    fix-plan review — `UNCONDITIONAL APPROVAL of fix plan`).
    Per ISS-001 (initiator-self-approval discipline), the merge gate
    is the r2 reviewer verdicts on this commit, not initiator
    adjudication.
- README stability table: schema, profile, and ontology versions are
  marked `Release candidate` until the first public release tag, per
  `GOVERNANCE.md`. The earlier `Stable` label was inconsistent with
  the still-private repository state.
- `spec.md` header status changed from `stable` to
  `release candidate (pending first public release tag)` to match the
  README stability table and the governance text. The label flips back
  to `stable` when the first public tag is cut.
- `examples/minimal-adapter-contract.toml` and the matching
  kind-descriptor block in
  `profiles/agent-assurance/adapter-contract-kind.toml` use
  `example-vendor:red_team_review@1` instead of the previous
  vendor-specific identifier. The example is illustrative; the
  string format is unchanged.
- `skills/convert-md-to-dag/traceability.toml`: the two
  provenance-related audit tests now invoke
  `validate_provenance.py` directly (digest + byte-length binding)
  instead of grepping for the presence of `source_hash` / a
  `[provenance]` header. Test IDs renamed accordingly
  (`source_hash_present` → `source_hash_binds`,
  `all_toml_files_cite_source` → `all_toml_files_bind_source`).

- Optional `[meta].docs` convention for DAG-TOML files and kind
  descriptors. The field points agents and tools at the canonical human
  specification or descriptor URL, but validators MUST NOT require
  network access to read it.
- Compact field reference at `docs/field-reference.md`, covering root
  metadata, core kinds, Agent Assurance Profile kinds, validator
  coverage, and the "what vs how" boundary between DAG-TOML and
  runtimes.
- IJB conformance CI loop extended to the five new profile-kind
  examples (`minimal-adapter-contract`, `minimal-adapter-registry-binding`,
  `minimal-assertion-bundle`, `minimal-assertion-log-record`,
  `minimal-gate-decision`). The validator's instance-file rules 5–6 only
  inspect strings that appear under an `id =` key or under a key that
  matches a declared ontology predicate (see
  `validators/validate_ijb_conformance.py` `validate_instance.walk`);
  for the new examples that surface is small (one `id` field across the
  five files at the time of this entry), so the practical effect today is
  to lock the structural shape of those files into CI rather than to
  resolve a large set of entity prefixes. The shape gate matters: any
  future content that introduces a `PREFIX:slug`-shaped token under a
  validated key, or a non-conforming `units.<id>` table key, will now
  fail the build. Previously CI only parsed these files as TOML.
- `taplo lint` CI step (pinned to Taplo `0.10.0`) for stricter TOML
  syntax / duplicate-key checks than Python's `tomllib` performs. New
  repo-root `.taplo.toml` declares the include/exclude file set;
  formatter rules are intentionally not enforced from this config.
- `requirements.txt` pinning `networkx>=3.0,<4`. CI installs it via
  `pip install -r requirements.txt`. `validators/validate_implementation_dag.py`
  now uses `networkx.simple_cycles` and `networkx.topological_sort` in
  place of the previous hand-rolled DFS for cycle detection and
  node-weighted longest-path (critical-path LOC) computation. Behaviour
  on the canonical example is preserved; reported cycle paths now use
  the canonical rotation so the same cycle reported from a different
  entry point dedupes deterministically.
- Deployment-tier bundles under `profiles/agent-assurance/tiers/` as
  five self-contained `contract-declaration` instances (`solo.toml`,
  `team.toml`, `group.toml`, `organization.toml`,
  `enterprise.toml`) plus a README documenting the
  solo ⊂ team ⊂ group ⊂ organization ⊂ enterprise ladder. No new
  `template_kind`; each tier file is a valid `contract-declaration`
  per the live kind schema.
- Five new Agent Assurance Profile `template_kind` values for the
  adapter / validation engine layer:
  - `adapter-contract` — declares a pure-function adapter that
    converts raw tool output into canonical IJB assertions, with
    declared runtime policies and conformance fixture references.
    Kind descriptor at
    `profiles/agent-assurance/adapter-contract-kind.toml`; example at
    `examples/minimal-adapter-contract.toml`.
  - `assertion-bundle` — sealed output of one adapter run as an
    ordered list of canonical-grammar assertion lines with
    provenance. Kind descriptor at
    `profiles/agent-assurance/assertion-bundle-kind.toml`; example at
    `examples/minimal-assertion-bundle.toml`.
  - `gate-decision` — mechanical pass/fail outcome of evaluating
    declared constraints against cited bundles. No editorialization
    surface. Verdict is a closed two-value enum; overrides are
    recorded as separate signed observations and do not toggle the
    verdict. Kind descriptor at
    `profiles/agent-assurance/gate-decision-kind.toml`; example at
    `examples/minimal-gate-decision.toml`.
  - `assertion-log-record` — one append-only log record citing an
    assertion bundle. Storage-agnostic; not git-coupled; not
    CI-coupled. Cross-record monotonicity and signature verification
    are explicitly deferred to RUNTIME-SPEC. Kind descriptor at
    `profiles/agent-assurance/assertion-log-record-kind.toml`;
    example at `examples/minimal-assertion-log-record.toml`.
  - `adapter-registry-binding` — declares how an adapter reference
    is resolved by an operator, with pluggable scheme (`file`,
    `https`, `oci`, `ipfs`, extensible) gated by trust anchor and
    policy constraint citations. Kind descriptor at
    `profiles/agent-assurance/adapter-registry-binding-kind.toml`;
    example at `examples/minimal-adapter-registry-binding.toml`.
- Eighteen new `[[attribute_vocabularies]]` entries in
  `profiles/agent-assurance/ontology.toml` declaring closed value
  sets for the new kinds: `runtime_kind`, `runtime_network_policy`,
  `runtime_clock_policy`, `input_hash_method`, `adapter_id_derivation`,
  `gate_decision_verdict`, `evidence_root_algorithm`,
  `record_signature_algorithm`, `record_hash_algorithm`,
  `record_canonical_form`, `registry_scheme`, `adapter_ref_syntax`,
  `signer_class`, `authority_role`, `severity_tier`, `autonomy_tier`,
  `override_decision_method`, `override_rule_operator`.
- Scope discipline: every new kind descriptor carries an explicit
  "validator MUST NOT" invariant naming the cross-document,
  cryptographic, and runtime behaviors that are out of scope for
  SPEC-LAYER validation (deferred to a sibling RUNTIME-SPEC).
- Initial specification publication candidate.
- Kind-descriptor pattern: each `template_kind` ships as a
  `*-kind.toml` file in `core/` or `profiles/agent-assurance/` carrying
  prose, required fields, hard-invariant pointers, and worked-example
  pointers in one machine-readable document.
- Reference validator `validators/validate_kind_descriptor.py` for the
  kind-descriptor template_kind itself.
- `LICENSE` (Apache-2.0).
- `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`.
- `.github/workflows/validate.yml` running reference validators on every
  push and pull request.
- Profile-kind minimal examples: `minimal-spec-contract.toml`,
  `minimal-threat-model.toml`, `minimal-smoke-validation.toml`,
  `minimal-rollback-plan.toml`.
- Non-normative architecture overview at `docs/architecture.md`
  describing how DAG-TOML relates to validators, per-repository
  runtimes, fleet control planes, and consumer tooling, and where the
  boundary between spec and runtime falls. Linked from `README.md`.
- IJB substrate integration. The "It's Just Business" framework ships
  under `foundations/ijb/` as relicensed (Apache-2.0) reference
  material: six-primitive definitions
  (`foundations/ijb/primitives.md`), canonical assertion grammar
  (`foundations/ijb/canonical-assertion-grammar.md`), FCO-IM
  integration notes, and worked examples. Every block in
  `core/ontology.toml` and `profiles/agent-assurance/ontology.toml`
  now carries an `ijb_primitive` annotation (`thing` / `scope` /
  `path` / `observed` / `constraint` / `time`) plus, where IJB
  itself distinguishes, an `ijb_class` (`structural` | `instance`)
  or `ijb_constraint_type` (`structural` | `policy` | `observed`)
  qualifier. Every kind-descriptor block in `core/*-kind.toml` and
  `profiles/agent-assurance/*-kind.toml` (`[kind]`,
  `[[kind.required_fields]]`, `[[kind.required_sections]]`,
  `[[kind.hard_invariants]]`, `[[kind.example]]`,
  `[kind.relation_to_ontology]`) carries the same `ijb_*` annotation
  per the SPEC §10.2 kind-descriptor mapping. The mapping is
  normative in `spec.md §10` with prose support in
  `core/ontology.md §8` and a layering diagram in
  `docs/architecture.md §5`. A new structural validator,
  `validators/validate_ijb_conformance.py`, enforces:
  every ontology block declares the required `ijb_*` fields; every
  kind-descriptor block does the same, with value classes pinned to
  the SPEC §10.2 mapping (`[kind]` is `thing/structural`,
  `[[kind.required_fields|required_sections|hard_invariants]]` and
  `[kind.relation_to_ontology]` are `constraint/structural`, and
  `[[kind.example]]` is `observed`); every value is drawn from the
  closed primitive / class / constraint-type sets; and every entity
  prefix and relation predicate used in a conforming instance file
  resolves through the loaded ontologies to a primitive-typed
  structural declaration. The validator is wired into CI alongside
  the existing four, including a per-kind-descriptor pass. Every
  kind-descriptor also gains a matching `[[kind.hard_invariants]]`
  entry pointing at the new validator. Free-text reality-check
  forbidden-concept matching is documented as a deliberate v0.2.0
  deferral in SPEC §10.4.

### Changed

- Per-kind prose documents (`core/implementation-dag.md`,
  `core/traceability.md`, `core/review-readiness.md`,
  `profiles/agent-assurance/{spec-contract,threat-model,smoke-validation,rollback-plan}.md`)
  collapsed into the matching `*-kind.toml` descriptors. Cross-references
  in `README.md` and `spec.md` updated to point at the new files.

### Notes

- `schema_version = "0.1.0"` and `ontology_version = 1` (core);
  profile `ontology_version = 1`. Pre-publication policy applies:
  versions stay at these values regardless of intervening edits until
  the first public release.

### Removed

- The previously-planned JSON Schema layer under `schemas/` has been
  dropped from the published deliverables. The machine-readable
  contract lives in TOML — in the `*-kind.toml` descriptors and the
  ontology files — and the reference validators consume those
  declarations to enforce both structural and semantic rules. The
  `schemas/` directory is retained for future generated Taplo schemas
  (an editor-tooling-only artifact derived from the kind descriptors,
  not authored by hand). See `spec.md §9` and `schemas/README.md`.
