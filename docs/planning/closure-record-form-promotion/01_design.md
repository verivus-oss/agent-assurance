# Design: profile-pinned closure record forms (the "§12.8 promotion")

Status: draft, pending grammar-freeze gate (G02) and operator STOP/GO
Created: 2026-07-12
Referenced by: [`implementation-dag.toml`](implementation-dag.toml) `[meta].spec`

## 1. Problem

At `schema_version = "0.1.0"` the SPEC-layer closure (`spec.md` §12.8) folds
exactly one cross-kind field into `closure_root`: `provenance.source_sha256`.
For the `com.verivus.runtime` `api-snapshot` kind this means the component
digests `snapshot.request.descriptor_sha256`, `snapshot.response.body_sha256`,
and the witness `snapshot.witness.attestation_sha256` ride along as fields but
are not independent closure inputs (kind descriptor, CLOSURE LAYERING block;
hard invariant RKV01).

Consequence (disclosed in the kind descriptor's own CLOSURE LAYERING prose,
`profiles/com.verivus.runtime/api-snapshot-kind.toml`, and raised independently
in the profile's external review,
`docs/reviews/2026-06-17-com-verivus-runtime-api-snapshot/`): a witness can be
stripped (`witness.present` flipped to `false`, the `[snapshot.witness]` table
removed) without changing `closure_root`. A transparency-log-anchored root therefore does not protect the
witness. This is an evidence-suppression gap, not a trust-upgrade forgery (tier
policy still rejects unwitnessed documents for witness-requiring manifests),
but it must close before the profile can claim anchored tamper-evidence over
the full evidence record.

`spec.md` already names the mechanism and its home:

- §12.1 (spec.md:941-944): profiles MAY add canonical record forms, provided
  the §12.2 cascade-break property is preserved.
- §12.8 (spec.md:1173-1175): "Profiles that pin additional record forms MUST do
  so in their `profile-descriptor` document (per §6.1) so consumers can
  enumerate them without reading code."

What is missing is everything that makes that sentence executable: §6.1 has no
field for pinned record forms, `validate_profile_descriptor.py` validates no
such field, and all three closure implementations hardcode the single
`provenance.source_sha256` record with no profile hook
(`validators/validate_closure_root.py` `canonical_source_hash_inputs`,
`tools/dagtoml-validate-rs/src/main.rs` `source_hash_records`,
`tools/dagtoml-validate-go/main.go` `sourceHashRecords`).

## 2. Non-goals

- No JSON Schema layer, no alternative rollup constructions. The positional
  `sha256(concat(h1,h2,h3))` shape proposed externally is rejected: unlabeled,
  position-dependent, no absent-field story, not extensible. The existing
  labeled sorted-record stream is the construction.
- No folding of `[meta]` or posture fields. §12.9 deliberately excludes
  `confidentiality` / `license` / `embargo_until` from closure inputs; this
  design preserves that and makes it mechanically enforced (contract C05).
- No `cites_upstream` graph-closure, `[[evidence_*]]`, or revocation-snapshot
  record forms. Those remain deferred exactly as §12.8 states today. This
  promotion covers only instance-local digest fields pinned by a profile.
- No `schema_version` / `ontology_version` bump. Pre-publication both stay
  pinned (0.1.0 / 1). No new relations enter the ontology.
- No state-mutation kind. That is a separate design.

## 3. The mechanism

### 3.1 Profile-descriptor declaration (new, §6.1)

A profile descriptor MAY carry zero or more pinned closure records:

```toml
[[profile.closure_records]]
contained_kind = "api-snapshot"
field          = "snapshot.request.descriptor_sha256"
presence       = "required"

[[profile.closure_records]]
contained_kind = "api-snapshot"
field          = "snapshot.response.body_sha256"
presence       = "required"

[[profile.closure_records]]
contained_kind = "api-snapshot"
field          = "snapshot.witness.attestation_sha256"
presence       = "when-present"
```

Constraints (a NEW profile-descriptor invariant; **INV07**, because INV06 is
already taken by `core/profile-descriptor-kind.toml`; enforced by
`validate_profile_descriptor.py` AND ported to the Rust/Go primaries, which
natively enforce the existing profile invariants):

- `contained_kind` MUST be a member of `profile.contained_kinds` (after
  `extends` union).
- `field` MUST match the frozen path grammar
  `^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$` (decoded string scalar; no spaces, no
  quoting, no empty segments), so the `<field> <value>\n` record is
  unambiguous by construction. It MUST NOT begin with `meta.`, MUST NOT name a
  §12.9 posture field, MUST NOT be `closure_root` (self-referential pin), and
  MUST NOT be `provenance.source_sha256` (already a SPEC-layer record;
  double-pinning is rejected).
- `presence` MUST be `"required"` or `"when-present"`.
- `closure_records` are inherited through `extends` exactly like
  `contained_kinds`; duplicate (`contained_kind`, `field`) pairs are rejected
  AFTER inheritance union, so an extending profile cannot re-pin or shadow a
  parent's pin.
- Pinned values are `sha256:` + 64-lowercase-hex ONLY at 0.1.0 (narrower than
  the kind-layer fields, which admit sha384/sha512); widening the alphabet is
  a future freeze decision, not a default.

### 3.2 Record emission (extends the §12.8 stream)

For a document whose `[meta].framework_profile` resolves to a profile
descriptor that pins closure records for the document's
`[meta].template_kind`:

- Each pinned `field` present in the document MUST hold a
  `sha256:` + 64-lowercase-hex digest scalar and emits exactly one UTF-8
  record: `<field> <sha256:64-lowercase-hex>\n` (identical shape to the
  existing `provenance.source_sha256` record: dotted path, single space,
  value, newline). Malformed values are a validation error.
- `presence = "required"`: a missing field is a validation error.
- `presence = "when-present"`: a missing field emits no record.
- Emitted records join the §12.8 stream: the producer sorts ALL records
  (SPEC-layer plus profile-pinned) bytewise, concatenates, and digests with
  the algorithm named by the `closure_root` prefix. The empty-input sentinel
  rule is unchanged.

Properties this buys, mechanically:

- Domain separation and ordering come from the labels (the dotted paths) and
  the bytewise sort; no positional coupling.
- Stripping detection: removing `[snapshot.witness]` removes the
  `snapshot.witness.attestation_sha256` record, which changes the expected
  root. An anchored root now detects witness stripping (closes the gap in §1).

**Witness-state binding (P0 review finding, closes the downgrade bypass).**
Because `when-present` is field-presence-based, flipping `witness.present` to
`false` while LEAVING `attestation_sha256` in place would keep the record set,
and therefore the root, identical: a downgrade the closure layer cannot see.
The kind layer must forbid that state: RKV03 is amended so that when
`witness.present = false`, the witness digest/identity fields (`scheme`,
`attester_id`, `attestation_sha256`, `attester_observed`) MUST be absent. A
new negative fixture (`api-snapshot-witness-lingering-digest.toml`) proves the
amendment bites. Enforcement scope stated honestly: RKV03 is enforced by
`validate_api_snapshot.py` (Python kind layer); the Rust/Go primaries do not
implement RKV03 today, so U02 must either schedule its port or record the
enforcement boundary explicitly in the freeze decision.
- Extensibility: a future pinned field is one more labeled record; existing
  roots for documents not carrying it are unaffected.
- §12.2 cascade-break preserved: any pinned-input change flips the root and
  breaks every downstream citation.

Documents with no `framework_profile`, or whose profile pins nothing for their
kind, are byte-identically handled as today (contract C03).

### 3.3 Spec text changes

- §12.1: amend the profile-input enumeration (currently limited to
  `cites_upstream` fields, `[[evidence_*]]` rows, and revocation snapshots) to
  admit profile-pinned instance-local digest fields; without this amendment
  the §12.8 grammar would contradict §12.1's own closed list.
- §12.8: promote the profile-pinned record-form grammar of §3.2 into normative
  text (the byte-level record shape, the frozen field-path regex, presence
  semantics, sort/concat/digest unchanged, sentinel unchanged). The
  `cites_upstream` / `[[evidence_*]]` / revocation deferral sentence stays,
  minus the now-covered instance-local digest case.
- §6.1: add `closure_records` to the profile-descriptor field table (optional,
  array of tables, constraints of §3.1) and the INV07 validation obligation.
- §12.9: add one sentence noting pinned record forms are subject to the same
  posture-field exclusion, with INV07 as the enforcement point.
- `core/profile-descriptor-kind.toml`: declare INV07 alongside the existing
  invariants (INV06 is already defined there) in the same change as the
  validator ports, per the move-together rule.

### 3.4 Validator changes (the triad, in lockstep)

All three implementations gain the same two capabilities, and CI treats any
divergence as a build break:

1. Load profile descriptors (Rust and Go already discover
   `profiles/*/PROFILE.toml` for other checks; Python gains loading under its
   existing `--repo-root`) and build a map
   contained_kind -> ordered pinned-record declarations (post-`extends`
   union).
2. In closure-record construction, after the `provenance.source_sha256`
   record: apply the frozen pin-resolution rule (below), then §3.2. The
   resolution MUST live in the closure path itself, in every mode that
   validates `closure_root` (including `--mode provenance`).

Failure-mode parity matrix (all three MUST agree):

| Condition | Verdict |
|---|---|
| pinned `required` field missing | reject |
| pinned field present, malformed digest | reject |
| pinned `when-present` field absent | accept (no record) |
| pin resolution fails (below) | reject (NEW rule, frozen at U02) |
| document outside any pinning profile | accept iff today's §12.8 accepts |

**Pin resolution is a NEW closure-layer rule, not existing behavior (P0 review
finding).** No closure implementation reads `framework_profile` today: the
Python closure validator never references it, the Rust/Go `framework_profile`
checks live in separate meta-mode code paths, and the CI closure step runs
`--mode provenance`, which skips those paths entirely. A silent
no-descriptor-found fall-through would be a pin bypass: strip or rename
`framework_profile` and the pins vanish while the source-only root stays
valid. U02 must therefore freeze the resolution rule inside the closure path
itself. Candidate rule (this design's recommendation): pins resolve by
`template_kind` over the FULL discovered profile-descriptor set (kind names
are namespace-partitioned per the existing profile invariants, so a kind maps
to at most one profile); a document whose `template_kind` is pinned by any
discovered descriptor folds those pins regardless of what its
`framework_profile` field says, and an unresolvable `framework_profile` on
such a document is rejected. The frozen rule, whatever U02 records, MUST make
"pins silently not applied" impossible for a pinned kind.

### 3.5 Profile and fixture changes (one atomic change, per repo rules)

- `profiles/com.verivus.runtime/PROFILE.toml`: add the three
  `[[profile.closure_records]]` entries of §3.1.
- `profiles/com.verivus.runtime/api-snapshot-kind.toml`: rewrite the CLOSURE
  LAYERING prose and RKV01 (closure now folds source + descriptor + body +
  attestation-when-present; sub-part-to-artefact consistency remains a
  producer obligation via `validate_api_snapshot.py`).
- `examples/minimal-api-snapshot.toml`: recompute `closure_root` to the
  four-record value under the frozen §3.2 grammar. Correction from review:
  independent recomputation shows the four-record stream over the shipped
  digests yields exactly `sha256:013f3d34...`, the value the old negative
  fixture carries, so its record forms DID anticipate this grammar. Expect
  that value if the digests are unchanged; verify by recomputation, never by
  copying.
- `examples/negative/`: rewrite `api-snapshot-bad-closure.toml` (a source-only
  root on a witnessed document is now the rejected shape; note this fixture is
  deliberately UNBLESSED, `template_kind = "api-snapshot-bad-closure"`, so it
  receives no pins and sits outside §12 discovery, same as today); RE-ROOT the
  four blessed negatives that carry `template_kind = "api-snapshot"` and
  therefore acquire pinned records (`api-snapshot-bad-subpart-digest.toml`,
  `api-snapshot-inlined-secret.toml`, `api-snapshot-raw-header.toml`,
  `api-snapshot-witness-incomplete.toml`; CI closure-discovers the whole tree
  with no negative-directory exclusion); add
  `api-snapshot-witness-stripped.toml` (witness table removed, stale
  four-record root kept: MUST be rejected; proves C02) and
  `api-snapshot-witness-lingering-digest.toml` (`present = false` with
  `attestation_sha256` retained: MUST be rejected by amended RKV03, §3.2).
- `CHANGELOG.md` under `[Unreleased]`.

### 3.6 Conformance corpus

- New `conformance/cases/api-snapshot/{valid,invalid}/` cases covering the
  parity matrix of §3.4.
- `conformance/runner.py`: register `api-snapshot` in `PY_VALIDATORS`
  (pointing at `validators/validate_api_snapshot.py`) AND add an explicit
  Python closure step (`validate_closure_root.py`) for every fixture of every
  kind. Today the runner exercises closure only through the Rust/Go auto
  modes; without the Python step, cross-implementation closure parity (C01)
  would be vacuous on the Python side.

## 4. Compatibility and migration

Expected blast radius, to be verified (not assumed) by the U02 sweep:

- Every conforming document outside `profiles/com.verivus.runtime` keeps a
  byte-identical closure verdict (no other shipped profile pins records).
- The `com.verivus.runtime` instances (the shipped example and the negative
  fixtures) change deliberately; the cascade-break is the feature. They are
  enumerated and re-emitted in U08.
- Downstream producers validating against a pinned pre-promotion ref are
  unaffected until they bump their pin; the bump is their deliberate act.

## 5. Sequencing with downstream and the carve-out

The reference-runtime emitter work and the public carve-out are planned in the
runtime repository's own planning bundle, gated on this promotion landing and
verifying (its entry unit consumes this DAG's terminal output). This public
bundle deliberately contains no details of that repository.

## 6. Review protocol

Per repo rules this design and every implementing PR require independent
multi-LLM review (no initiator self-approval), dispatched via
`tools/review-request-dag.toml`, evidence persisted under `docs/reviews/`.
The design-stage review gate is G02 in
[`readiness-gate.toml`](readiness-gate.toml); no unit past U02 starts before
it records GO plus operator sign-off.
