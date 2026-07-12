# U02: grammar-freeze decision record

Status: **GO recorded 2026-07-13** (operator sign-off received in session;
see section 5). U03+ cleared to proceed under the frozen grammar below.
Prepared: 2026-07-13.
Inputs: the reviewed design pack (U01;
`docs/reviews/2026-07-13-closure-record-form-promotion-design/`) and the
compatibility sweep recorded in §3 below.

## 1. The frozen grammar

Once GO is recorded, the following is byte-frozen; any change re-opens U02.

### 1.1 Declaration (profile descriptor)

`[[profile.closure_records]]` with exactly three keys:

- `contained_kind`: string; MUST be a member of the post-`extends`-union
  `profile.contained_kinds`.
- `field`: string; MUST match `^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$` applied to
  the decoded TOML string scalar (segment-wise lookup; the emitted label is
  the identical normalized string). MUST NOT begin with `meta.`; MUST NOT be a
  SPEC 12.9 posture field (`confidentiality`, `license`, `embargo_until` at
  any path position rooted in `meta`); MUST NOT be `closure_root`; MUST NOT be
  `provenance.source_sha256`.
- `presence`: `"required"` or `"when-present"`.

Inheritance: `closure_records` unions across `extends` exactly like
`contained_kinds`; duplicate (`contained_kind`, `field`) pairs are rejected
AFTER the union. Declared invariant id: **INV07** (INV06 is taken), declared
in `core/profile-descriptor-kind.toml`, enforced by
`validate_profile_descriptor.py` and both primaries.

### 1.2 Record emission (closure stream)

For a document whose `template_kind` is pinned (per §1.3): each pinned
`field`, if present, MUST hold `sha256:` + 64-lowercase-hex (sha256-only at
0.1.0; sha384/sha512 widening is a future re-freeze) and emits exactly one
UTF-8 record `<field> <value>\n` (single 0x20 separator, single trailing
0x0A). `required` + absent field: reject. `when-present` + absent field: no
record. Malformed value: reject. Records join the SPEC 12.8 stream; the union
of SPEC-layer and pinned records is sorted bytewise, concatenated, and
digested with the algorithm named by the `closure_root` prefix; the
empty-input sentinel rule is unchanged.

### 1.3 Pin resolution (NEW closure-path rule)

Frozen rule: pins resolve by `template_kind` over the FULL discovered
profile-descriptor set (kind names are namespace-partitioned by the existing
profile invariants, so a kind maps to at most one profile). A document whose
`template_kind` is pinned by a discovered descriptor folds those pins in
EVERY mode that validates `closure_root`, including provenance mode,
regardless of the document's `framework_profile` value; additionally, such a
document with a missing or unresolvable `framework_profile` is rejected by
the closure check. Rationale: no closure implementation reads
`framework_profile` today and reverse-DNS names are not hard-rejected on
missing descriptors, so any profile-field-keyed resolution would make "pins
silently not applied" reachable (review P0 finding 2). Under this rule it is
unreachable: the pins follow the kind.

### 1.4 Witness-state binding (RKV03 amendment)

RKV03 is amended: when `snapshot.witness.present = false`, the fields
`scheme`, `attester_id`, `attestation_sha256`, and `attester_observed` MUST
be absent. Enforcement boundary, recorded explicitly: the amendment is
enforced by `validate_api_snapshot.py` (Python kind layer). The Rust/Go
primaries do not implement RKV03; the all-three closure-level test remains
the witness-stripped stale-root fixture, and the lingering-digest fixture is
a Python kind-layer rejection until an RKV03 port is scheduled (out of scope
for this promotion; recorded as a known boundary, not a gap to be silently
assumed away).

### 1.5 First pinning (com.verivus.runtime)

api-snapshot: `snapshot.request.descriptor_sha256` (`required`),
`snapshot.response.body_sha256` (`required`),
`snapshot.witness.attestation_sha256` (`when-present`).

## 2. Failure-mode parity matrix (frozen; all three implementations MUST agree)

| Condition | Verdict |
|---|---|
| pinned `required` field missing | reject |
| pinned field present, malformed digest | reject |
| pinned `when-present` field absent | accept (no record) |
| pinned kind, `framework_profile` missing/unresolvable | reject |
| document of an unpinned kind | accept iff pre-promotion SPEC 12.8 accepts (byte-identical) |

## 3. Compatibility sweep (run 2026-07-13, tree at branch profile/com.verivus.runtime-api-snapshot)

Method: every conforming document (the same discovery set as
`validate_closure_root.py --discover .`, 105 documents, all PASS today) had
its post-promotion expected root computed under §1.2/§1.5 and compared with
its declared root.

Result: **100 of 105 byte-identical; exactly 5 verdict-changing, all
`com.verivus.runtime` api-snapshot instances, all enumerated in U08:**

| Document | Records | Declared root | Post-promotion root |
|---|---|---|---|
| `examples/minimal-api-snapshot.toml` | 4 | `sha256:f251f64b...` | `sha256:013f3d34bab26a1b9d9fd77ff03aae76a3b07ee112c4995dc5ef448b2d1796db` |
| `examples/negative/api-snapshot-bad-subpart-digest.toml` | 3 | `sha256:f251f64b...` | `sha256:4beda7c3...` |
| `examples/negative/api-snapshot-inlined-secret.toml` | 2 | sentinel | `sha256:03e3be2c...` |
| `examples/negative/api-snapshot-raw-header.toml` | 2 | sentinel | `sha256:03e3be2c...` |
| `examples/negative/api-snapshot-witness-incomplete.toml` | 2 | sentinel | `sha256:03e3be2c...` |

Notes: (a) the positive example's post-promotion root equals the value the
old bad-closure negative carries, now independently computed three times
(grok, gemini, this sweep), confirming the U08 guidance to verify by
recomputation; (b) the three sentinel-rooted negatives carry no
`[provenance]` table, so their post-promotion streams are the two required
pins alone; they remain kind-layer rejections and get re-rooted in U08 so the
closure gate keeps passing on them for the reasons their fixtures intend;
(c) no document outside `profiles/com.verivus.runtime` changes verdict
(contract C03 satisfied at sweep time).

## 4. GO criteria (all met at preparation time)

- Design pack complete, validated, and independently reviewed with all
  required fixes applied (U01; evidence in
  `docs/reviews/2026-07-13-closure-record-form-promotion-design/`).
- Grammar stated byte-level in §1 with no open options except those
  explicitly deferred (sha384/512 widening, RKV03 primary port).
- Sweep shows zero unenumerated invalidations (§3).

## 5. Operator decision

DECISION: GO
Signed: werner (operator; recorded from the interactive session instruction "GO")
Date: 2026-07-13

Recorded constraints on a GO: U03+ proceed as the DAG orders; any change to
§1 or §2 after GO re-opens U02; the U10 implementation review is still
required before merge (this GO does not pre-approve the implementation).
