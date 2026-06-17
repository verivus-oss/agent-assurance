# Unified design record — `com.verivus.runtime` / `api-snapshot`

Date: 2026-06-17. Scope: land the `com.verivus.runtime` profile with one kind,
`api-snapshot` — a digest-pinned, optionally witnessed capture of one external
request/response interaction an agent observed at runtime. Every decision below
was resolved to a single position against the shipped spec and validators (HEAD
of branch `toml-1.1-u08-cross-impl-verify`), not against a summary.

## D1 — Closure model: **(a) source-only**

The SPEC-layer closure folds exactly one field, `provenance.source_sha256`, and
the fold is byte-identical across the three implementations:

- Python `validators/validate_closure_root.py:84` — `f"provenance.source_sha256 {raw}\n"`
- Rust `tools/dagtoml-validate-rs/src/main.rs:3988` — `format!("provenance.source_sha256 {s}\n")`
- Go `tools/dagtoml-validate-go/main.go:2441` — `fmt.Sprintf("provenance.source_sha256 %s\n", …)`

records sorted, concatenated, hashed; empty set → empty-closure sentinel.
`spec.md §12.8` pins this and explicitly defers descriptor/body/attestation and
other record forms to "profile / runtime work until a future `schema_version`
promotes those record forms into normative spec text."

Decision: the api-snapshot puts the **whole captured-artefact digest** in
`provenance.source_sha256`, so the §12 brittleness cascade runs through it.
`descriptor_sha256` and `body_sha256` are **component digests** over sub-parts
of that same artefact; `attestation_sha256` pins a separate witness artefact.
None of the three are folded at 0.1.0. We do **not** take option (b) (promoting
a four-input record form into §12.8): it would be a spec amendment touching
three closure validators for a single profile kind, against the spec's own
deferral and the "minimal, precedent-faithful" constraint.

Trust property given to a downstream consumer: the §12 value commits to the
**outer** captured-artefact digest only. It is *not* proof of sub-part
integrity — a document whose `source_sha256` names artefact X while its
sub-digests come from Y still yields a valid `closure_root` over X. Sub-part
consistency is therefore a **producer obligation** (RKV01 prose +
`validate_api_snapshot.py` digest typing), not a §12 guarantee. RKV01's wording
is kept exact on this boundary.

The bad-closure negative carries the four-input value; all three closure
validators reject it because they expect the source-only fold. This both proves
the rule and documents the rejected alternative.

## D2 — Entity model: **entity-light (`entities_introduced = []`)**

Verified against the real consumers, not assumed: DuckDB's `instance_file`
table stands alone (no required FK to `entity`; `tools/dagtoml-duckdb-go`
schema), `gate-decision` is entity-light today and ingests to a document-level
row, and the RDF schema (`tools/dagtoml-rdf*`) never requires entity instances
(SHACL shapes target `sh:targetClass`; zero instances → zero constraints). A
flat api-snapshot maps to a single document-level node/row exactly as
gate-decision does. First-class snapshot nodes are unnecessary; introducing
SNAP/WIT/ATT prefixes would add graph surface no consumer needs. Mirrors the
shipped `gate-decision-kind.toml` (`entities_introduced = []`).

## D3 — Abstraction class: **reuse `observation-record.v1`** (changed from the draft)

`validate_abstraction_class.py` enforces only the *shape*
`^[a-z0-9][a-z0-9._-]*\.v\d+$` — there is no registry, so both
`external-observation.v1` and `observation-record.v1` pass the validator. This
is a §13 anti-proliferation judgment. The repo has 19 kinds across 13 classes;
`observation-record.v1` is already shared by five flat single-subject read-only
records (gate-decision, cost-record, evidence-matrix, assertion-log-record,
redaction-manifest), all deny-all envelope. api-snapshot is structurally
identical (flat single subject, digest-pinned, no editorial surface, deny-all
envelope) — the draft itself repeatedly says "like gate-decision." The bespoke
`external-observation.v1` (used by nothing) would mint a class for a distinction
that does not change the structural family or the capability envelope; the
"external capture" trust semantics live in the witness vocabulary, not the
abstraction class. Decision: reuse `observation-record.v1`. (This does not
change the descriptor's `closure_root` — descriptors carry no
`provenance.source_sha256`, so they keep the empty sentinel regardless.)

## D4 — RKV02 / RKV03 enforcement: **ship `validators/validate_api_snapshot.py` (Python), no primary**

The two invariants are profile-layer **producer obligations**, not the
cross-kind closure/IJB rules that require three-implementation parity. Precedent:
`threat-model` declares its validator with the same convention. RKV02 enforces
closed key-sets on `[snapshot.request]` / `[snapshot.response]` / `[snapshot.witness]`
/ `[snapshot]` (any field outside the digest-bearing set is a raw header/payload
value and is rejected — including non-secret ones like a raw `accept`), bare
lowercase significant-header names, and well-formed `<algo>:<hex>` digest
scalars. RKV01 sub-part consistency is recomputed: when `source_path` resolves
to a `DAGTOML-API-CAPTURE/1` capture, the validator hashes the request-descriptor
and response-body sub-parts and requires them to equal `descriptor_sha256` /
`body_sha256` (foreign capture formats are RUNTIME-SPEC). RKV03 (witness conditional:
`present = true` ⇒ scheme ∈ `witness_scheme`, `attester_id`, `attestation_sha256`,
`observed` ∈ `attester_observed`). `enforced_by` now resolves to the real file
(no `(planned)` marker), so `validate_kind_descriptor.py --check-references-exist`
passes. Two negatives (`api-snapshot-inlined-secret`, `api-snapshot-witness-incomplete`)
exercise RKV02/RKV03; both are rejected. The shared cross-kind negatives
(bad-closure under provenance, bad-ijb under ijb) are rejected by Rust + Go +
Python alike.

## D5 — Provenance binding: **mint a real capture artefact**

`validate_provenance.py` (spec.md §11) resolves `source_path` under repo root,
recomputes SHA-256 + byte length, and requires an exact match. The draft's
illustrative digest cannot be a preimage of any shippable file, so we mint:
`examples/captures/2026-06-17T091402Z-usd-aud.capture` (620 bytes) and a
companion `.attestation`. Every cited digest — `source_sha256`,
`descriptor_sha256`, `body_sha256`, `attestation_sha256`, and both
`closure_root` values — is a real SHA-256 over real bytes, regenerated by
`docs/reviews/2026-06-17-com-verivus-runtime-api-snapshot/build_api_snapshot_digests.py`, so a reviewer recomputes the entire
chain. The positive instance passes the provenance sweep. The bad-closure
negative lives in `examples/negative/` (excluded from the provenance positive
sweep) and carries a deliberately wrong `source_bytes` so it is also rejected by
the provenance-negative gate; it is kept out of the closure positive sweep by
its unblessed `template_kind` (see the conformance-scope note below).

## D6 — Reconcile history

No `dagtoml-api-snapshot-kind.md` or `dagtoml-request-descriptor-canonicalization.md`
exists in the repo at HEAD (searched). The "four-input closure" is therefore not
a shipped doc to reconcile but the **profile-proposed / post-§12.8 path** the
closure validator and `spec.md §12.8` already flag as deferred; the bad-closure
negative captures it as the explicitly-rejected alternative, and this record
states it is not adopted at 0.1.0. RKV02's normative basis is authored here:
`docs/profiles/com.verivus.runtime/request-descriptor-canonicalization.md`, and
RKV02's `see_also` points at it.

## Bad-closure fixture is out of conformance scope (CI note)

`validate_closure_root.py --discover .` validates every spec-reserved document
in every directory, including `examples/negative/`; that is why every prior
negative carries a *valid* `closure_root`. A deliberately-wrong-closure fixture
cannot carry the spec-reserved `api-snapshot` kind without breaking that sweep.
Per `spec.md §12.1`, documents with an **unblessed `template_kind`** are
intentionally out of §12 conformance scope (process artifacts). So
`examples/negative/api-snapshot-bad-closure.toml` declares
`template_kind = "api-snapshot-bad-closure"`: it is invisible to the positive
discovery sweep (no CI closure-sweep change is needed, and bare
`validate_closure_root.py --discover .` stays green), while the dedicated
negative-agreement gate runs all three closure validators on it explicitly
(`--mode provenance` / `validate_closure_root.py`) and they reject it — the
closure rule is cross-kind and kind-agnostic, so the rejection reason is the
source-only fold mismatch regardless of `template_kind`. (Verified: Rust, Go,
and Python all reject it for the closure-mismatch reason in explicit mode.) The
other api-snapshot negatives keep the `api-snapshot` kind because their
`closure_root` is valid (sentinel, or the correct source-only fold) and their
defect is elsewhere.
