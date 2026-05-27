# Adopting DAG-TOML in a private codebase

**Status: non-normative.** This guide walks adopters through the
"public spec, private profile" pattern enabled by the draft layering
work. It does not change conformance — the spec itself stays
mechanical. The strategic narrative is here so the spec text does
not have to carry it.

If you are reading the spec for the first time, start with
[spec.md](../spec.md). If you only want to consume DAG-TOML files
produced by someone else, the only public surface you need to
understand is the `[meta]` table (SPEC §2) and the per-kind
descriptor for the `template_kind` you are reading.

If you are extending the spec for an internal codebase, read on.

---

## 1. The two cases adopters fall into

| Case | What you ship | What you set `framework_profile` to | Where the profile-descriptor lives |
|---|---|---|---|
| **A. Pure consumption.** You author files conforming to a spec-reserved profile (e.g. `agent-assurance`) and have no internal extensions. | Just the instance files. | The spec-reserved profile name (`"agent-assurance"`, `"disclosure"`). | Already shipped under `profiles/<name>/PROFILE.toml`. Nothing to do. |
| **B. Private extension.** You ship internal kinds or vocabularies on top of a spec-reserved profile. | A private profile-descriptor + private kind descriptors + internal instance files. | Your reverse-DNS-named profile (e.g. `"com.example.internal"`). | Inside your own repo, under whatever directory you choose; conventionally `profiles/<reverse-dns-name>/PROFILE.toml`. |

The reverse-DNS partition (SPEC §2.5) exists so case B is structurally
impossible to confuse with case A. The DAG-TOML spec itself never
needs to register or audit private profiles; the DNS namespace your
organisation already owns provides the uniqueness guarantee.

---

## 2. Worked example: `com.example.internal`

Suppose `example.com` runs an internal release-train tool that wants
to declare a custom `release-window` kind on top of the
agent-assurance profile. The org publishes everything inside their
own repo (not this one).

### 2.1 The profile descriptor

```toml
# profiles/com.example.internal/PROFILE.toml inside the example.com repo
[meta]
schema_version    = "0.1.0"
template_kind     = "profile-descriptor"
ontology_version  = 1
title             = "Example Co. internal profile descriptor"
docs              = "https://internal.example.com/dag-toml/profile"
confidentiality   = "confidential"
license           = "LicenseRef-Proprietary"

[meta.ijb_field_primitives]
template_kind     = { ijb_primitive = "scope",      ijb_class = "structural" }
schema_version    = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }
ontology_version  = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }
confidentiality   = { ijb_primitive = "constraint", ijb_constraint_type = "policy" }
license           = { ijb_primitive = "constraint", ijb_constraint_type = "policy" }

[profile]
name              = "com.example.internal"
namespace         = "com.example"
owner             = "release-train@example.com"
license           = "LicenseRef-Proprietary"
extends           = ["agent-assurance"]
ontology          = "profiles/com.example.internal/ontology.toml"
contained_kinds   = ["release-window"]
ijb_primitive     = "thing"
ijb_class         = "structural"
```

Three things to notice:

1. `name = "com.example.internal"` follows the reverse-DNS pattern
   per SPEC §2.5 — the profile is non-spec-reserved, so the unprefixed
   namespace partition does not apply.
2. `namespace = "com.example"` is the strict reverse-DNS prefix of
   the name. The validator
   ([`validators/validate_profile_descriptor.py`](../validators/validate_profile_descriptor.py)
   and the Rust + Go primaries) enforces that consistency.
3. `extends = ["agent-assurance"]` declares the inheritance edge
   machine-readably. A consumer that loads this descriptor walks
   `extends`, loads the agent-assurance profile-descriptor, and unions
   the effective contained-kind and ontology sets. There is no
   spec-side package manager; the parent descriptor MUST physically
   exist alongside the child inside the consuming environment for
   `extends` to resolve.

### 2.2 The matching ontology extension

```toml
# profiles/com.example.internal/ontology.toml
[meta]
schema_version    = "0.1.0"
template_kind     = "ontology"
ontology_version  = 1
framework_profile = "com.example.internal"
title             = "Example Co. internal ontology extension"
extends           = "../agent-assurance/ontology.toml"
confidentiality   = "confidential"
license           = "LicenseRef-Proprietary"

[meta.ijb_field_primitives]
framework_profile = { ijb_primitive = "scope",      ijb_class = "structural" }
template_kind     = { ijb_primitive = "scope",      ijb_class = "structural" }
schema_version    = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }
ontology_version  = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }
confidentiality   = { ijb_primitive = "constraint", ijb_constraint_type = "policy" }
license           = { ijb_primitive = "constraint", ijb_constraint_type = "policy" }

[[entities]]
id_prefix    = "WIN"
section      = "windows"
schema       = "release-window"
profile      = "com.example.internal"
description  = "Time-bounded release window during which deploys are gated."
extensible   = false
ijb_primitive = "thing"
ijb_class     = "structural"

[extension_rules]
entity_kinds       = "closed_within_profile"
relation_predicates = "must_be_namespaced_as_com.example.internal:<predicate>"
version_bump_rule  = "Internal: bump this file's ontology_version when an entity, vocabulary value, or namespaced predicate is added."
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"
```

### 2.3 A private instance file

```toml
# planning/window-2026Q3.toml
[meta]
schema_version    = "0.1.0"
template_kind     = "release-window"
framework_profile = "com.example.internal"
title             = "Q3 2026 release window"
created           = "2026-06-01"
confidentiality   = "embargoed"
license           = "LicenseRef-Proprietary"
embargo_until     = "2026-09-01"

[[windows]]
id          = "WIN:q3-2026"
opens_at    = "2026-07-15T00:00:00Z"
closes_at   = "2026-09-15T23:59:59Z"
owner       = "release-captain@example.com"
```

This file:

- Selects the private profile via `framework_profile`.
- Declares `confidentiality = "embargoed"` and provides the SPEC §2.7
  required `embargo_until` companion field.
- Carries `license = "LicenseRef-Proprietary"` — the `LicenseRef-`
  prefix is the SPDX convention for non-SPDX-listed licenses.

The IJB substrate (SPEC §10) carries over unchanged: `WIN` is
`thing/instance`; the timestamps are `time` primitives; the
disclosure-posture fields are `constraint/policy`.

---

## 3. Picking a confidentiality posture

The SPEC §2.7 vocabulary is closed; pick the value that matches what
your control plane should actually do, not what feels safest.

| Value | Use when | What control planes typically do |
|---|---|---|
| `public` | The file may be mirrored, archived, or indexed by anything that can read it. | Mirror freely. |
| `restricted` | The file is org-internal but does not need encryption at rest. | Block external mirrors; allow internal CI. |
| `confidential` | The file contains material the org would not share with a competitor. | Require auth on any retrieval path. |
| `trade-secret` | The file contains material whose disclosure would create a competitive or legal harm. | Encrypt at rest; restrict retrieval to a named audience. |
| `embargoed` | The file is intended to become more public at a specific time (e.g. a launch). MUST carry `embargo_until`. | Block disclosure until `embargo_until`; flip to a less-restricted posture afterwards. |

Validators do not act on the value — they only enforce the closed
set and the cross-field requirement for `embargoed`. Acting on the
posture is the control plane's job.

---

## 4. Disclosing a redacted artifact

The disclosure profile (SPEC §6.1, `profiles/disclosure/`) ships
three kinds for the case where you publish a partial or redacted
view of a source artifact and want a recipient to verify the
disclosure was faithful:

1. **`disclosure-attestation`** — the entry-point document. One
   signed posture statement per subject.
2. **`redaction-manifest`** — one entry per redaction performed,
   naming the locator, method, and reason.
3. **`selective-disclosure-proof`** — the cryptographic commitment
   binding the redaction manifest to the source artifact.

A typical flow:

```
source bundle              published artifact set
─────────────              ────────────────────────────────
bundle/12345 (private)     bundle/12345-redacted (public)
                           DISCLOSURE_ATTESTATION.toml      ──┐
                           redaction_manifest.toml          ──┼── disclosure profile
                           SELECTIVE_DISCLOSURE_PROOF.toml  ──┘
                           bundle-12345.proof.bin
```

The SPEC layer names the proof family (`merkle-leaf-omission`,
`field-commitment-omission`, etc.) and records the bound source
SHA-256; the wire shape of the proof itself is RUNTIME-SPEC. A
recipient combining the published bytes, the proof, and the
redaction manifest can confirm the published bytes are a faithful
redaction of the source without ever seeing the redacted bytes.

Worked minimal examples ship under:

- [`examples/minimal-disclosure-attestation.toml`](../examples/minimal-disclosure-attestation.toml)
- [`examples/minimal-redaction-manifest.toml`](../examples/minimal-redaction-manifest.toml)
- [`examples/minimal-selective-disclosure-proof.toml`](../examples/minimal-selective-disclosure-proof.toml)

---

## 5. Encrypted source artifacts in `[provenance]`

When a DAG-TOML file is generated from an encrypted source (e.g. an
age-sealed planning document), declare the encryption shape with the
`[provenance.encryption]` sub-table (SPEC §11.1):

```toml
[provenance]
source_path     = "planning/2026Q3.md.age"
source_sha256   = "sha256:<digest of the ciphertext bytes>"
source_bytes    = 4096
captured_at     = "2026-06-01T12:00:00Z"

[provenance.encryption]
sealed       = true
hash_is_over = "ciphertext"
scheme_hint  = "age"
```

If `hash_is_over = "ciphertext"`, the standard SPEC §11 SHA-256 and
byte-length recomputation runs unmodified (the file on disk is what
the digest commits to). If `hash_is_over = "plaintext"`, the
validator skips the recomputation and emits an advisory note; a
separate decrypt-and-verify step (outside SPEC scope) closes the
gap.

The spec deliberately does not touch keys, recipients, or signing
material. The sub-table only records the shape so that a future
consumer recomputing the hash knows what bytes the hash committed
to.

---

## 6. What stays out of the spec

The draft layering work intentionally adds layering primitives, not
disclosure infrastructure. The following remain RUNTIME-SPEC and
are NOT added by the spec:

- Key management, recipient lists, signing fields, key-management URIs.
- Cryptographic verification of selective-disclosure proofs.
- Embargo enforcement against wall-clock time.
- A central registry of private profile names (the reverse-DNS
  partition makes one unnecessary).
- Auto-generated JSON Schemas for the new kinds (the descriptors are
  the contract; editors that want JSON Schema can derive it from the
  descriptors — see [spec.md §9.1](../spec.md#91-why-no-json-schema-layer)).

---

## 7. Checklist for an internal adopter

1. Pick a reverse-DNS profile name. Verify it isn't already used by
   anyone else inside your organisation.
2. Write `profiles/<your.profile>/PROFILE.toml` with `extends`
   pointing at the spec-reserved profile you build on.
3. Write `profiles/<your.profile>/ontology.toml` with `extends`
   pointing at the same parent's ontology.
4. Write one `*-kind.toml` per internal `template_kind` you introduce.
5. Add `confidentiality` and `license` to your `[meta]` defaults.
   Use `LicenseRef-…` for internal licenses.
6. Run the primary validators (Rust or Go) on every PR.
7. Keep the parent profile's descriptor on disk so `extends` resolves.

You do not need to coordinate with the upstream spec for any of
these steps. The spec's only obligation is to keep the partition
mechanics (SPEC §2.5, §6.1) and the substrate (SPEC §10) stable
across minor versions so that your private profile keeps validating
without churn.
