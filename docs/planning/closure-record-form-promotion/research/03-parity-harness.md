# U05-U07 parity harness: persisted evidence (U10 review fix 10)

Synthetic pinning root used to exercise the frozen failure-mode parity
matrix before the real profile pinned records in U08. Persisted here so
the m1-m9 evidence is reproducible from the repo alone: recreate the
tree below under any scratch directory and run all three validators
with --repo-root pointing at it (provenance mode for the primaries).

Verdict matrix (recorded during U05-U07 and re-verified after the U10
review fixes): m1 A/A/A, m2 R/R/R, m3 R/R/R, m4 A/A/A, m5 R/R/R,
m6 R/R/R, m7 R/R/R, m8 A/A/A, m9 A/A/A (py/rs/go).

The 30-row U06/U07 regression baseline (shipped tree, pre-change vs
post-change binaries, IDENTICAL TO BASELINE) and the U10 reviewer
adversarial roots (duplicate-name, symlink) are recorded in the U10
review evidence directory; the duplicate-name and symlink cases cannot
be tracked in-tree without adding conflicting PROFILE.toml directories
to the repository's own profile set.

## docs/m1-valid-full.toml

```toml
closure_root = "sha256:037f3aafbacec453a825d886bfbcfb0f0671ee0c07cae40c320bdefdc4fc907c"
[meta]
schema_version = "0.1.0"
template_kind  = "pinned-note"
framework_profile = "com.example.pin"
[provenance]
source_sha256 = "sha256:25a6634263c1b1f6fc4697a04e2b9904ea4b042a89af59dc93ec1f5d44848a26"
[notes]
body_sha256 = "sha256:230d8358dc8e8890b4c58deeb62912ee2f20357ae92a5cc861b98e68fe31acb5"
extra_sha256 = "sha256:c8dee78f8c7b466c881847accc196998bad00e2b96c5ef913dfbe454d3807c96"
```

## docs/m2-required-missing.toml

```toml
closure_root = "sha256:c8da8daf2a09aea2d60304bc7f50dc3b2d1c631e8ac09c1846189540d273d49b"
[meta]
schema_version = "0.1.0"
template_kind  = "pinned-note"
framework_profile = "com.example.pin"
[provenance]
source_sha256 = "sha256:25a6634263c1b1f6fc4697a04e2b9904ea4b042a89af59dc93ec1f5d44848a26"
[notes]
extra_sha256 = "sha256:c8dee78f8c7b466c881847accc196998bad00e2b96c5ef913dfbe454d3807c96"
```

## docs/m3-malformed-digest.toml

```toml
closure_root = "sha256:c8da8daf2a09aea2d60304bc7f50dc3b2d1c631e8ac09c1846189540d273d49b"
[meta]
schema_version = "0.1.0"
template_kind  = "pinned-note"
framework_profile = "com.example.pin"
[provenance]
source_sha256 = "sha256:25a6634263c1b1f6fc4697a04e2b9904ea4b042a89af59dc93ec1f5d44848a26"
[notes]
body_sha256 = "sha256:zznotahash"
```

## docs/m4-whenpresent-absent.toml

```toml
closure_root = "sha256:c8da8daf2a09aea2d60304bc7f50dc3b2d1c631e8ac09c1846189540d273d49b"
[meta]
schema_version = "0.1.0"
template_kind  = "pinned-note"
framework_profile = "com.example.pin"
[provenance]
source_sha256 = "sha256:25a6634263c1b1f6fc4697a04e2b9904ea4b042a89af59dc93ec1f5d44848a26"
[notes]
body_sha256 = "sha256:230d8358dc8e8890b4c58deeb62912ee2f20357ae92a5cc861b98e68fe31acb5"
```

## docs/m5-no-profile.toml

```toml
closure_root = "sha256:037f3aafbacec453a825d886bfbcfb0f0671ee0c07cae40c320bdefdc4fc907c"
[meta]
schema_version = "0.1.0"
template_kind  = "pinned-note"

[provenance]
source_sha256 = "sha256:25a6634263c1b1f6fc4697a04e2b9904ea4b042a89af59dc93ec1f5d44848a26"
[notes]
body_sha256 = "sha256:230d8358dc8e8890b4c58deeb62912ee2f20357ae92a5cc861b98e68fe31acb5"
extra_sha256 = "sha256:c8dee78f8c7b466c881847accc196998bad00e2b96c5ef913dfbe454d3807c96"
```

## docs/m6-unresolvable-profile.toml

```toml
closure_root = "sha256:037f3aafbacec453a825d886bfbcfb0f0671ee0c07cae40c320bdefdc4fc907c"
[meta]
schema_version = "0.1.0"
template_kind  = "pinned-note"
framework_profile = "com.example.ghost"
[provenance]
source_sha256 = "sha256:25a6634263c1b1f6fc4697a04e2b9904ea4b042a89af59dc93ec1f5d44848a26"
[notes]
body_sha256 = "sha256:230d8358dc8e8890b4c58deeb62912ee2f20357ae92a5cc861b98e68fe31acb5"
extra_sha256 = "sha256:c8dee78f8c7b466c881847accc196998bad00e2b96c5ef913dfbe454d3807c96"
```

## docs/m7-stale-root-witness-strip.toml

```toml
closure_root = "sha256:037f3aafbacec453a825d886bfbcfb0f0671ee0c07cae40c320bdefdc4fc907c"
[meta]
schema_version = "0.1.0"
template_kind  = "pinned-note"
framework_profile = "com.example.pin"
[provenance]
source_sha256 = "sha256:25a6634263c1b1f6fc4697a04e2b9904ea4b042a89af59dc93ec1f5d44848a26"
[notes]
body_sha256 = "sha256:230d8358dc8e8890b4c58deeb62912ee2f20357ae92a5cc861b98e68fe31acb5"
```

## docs/m8-unpinned.toml

```toml
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
[meta]
schema_version = "0.1.0"
template_kind  = "kind-descriptor"
describes_kind = "whatever"
[kind]
name = "whatever"
```

## docs/m9-extends-single-emission.toml

```toml
closure_root = "sha256:037f3aafbacec453a825d886bfbcfb0f0671ee0c07cae40c320bdefdc4fc907c"
[meta]
schema_version = "0.1.0"
template_kind  = "pinned-note"
framework_profile = "com.example.ext"
[provenance]
source_sha256 = "sha256:25a6634263c1b1f6fc4697a04e2b9904ea4b042a89af59dc93ec1f5d44848a26"
[notes]
body_sha256 = "sha256:230d8358dc8e8890b4c58deeb62912ee2f20357ae92a5cc861b98e68fe31acb5"
extra_sha256 = "sha256:c8dee78f8c7b466c881847accc196998bad00e2b96c5ef913dfbe454d3807c96"
```

## profiles/com.example.ext/PROFILE.toml

```toml
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
[meta]
schema_version = "0.1.0"
template_kind  = "profile-descriptor"
[profile]
name            = "com.example.ext"
namespace       = "com.example"
owner           = "example"
license         = "Apache-2.0"
extends         = ["com.example.pin"]
ontology        = "profiles/com.example.pin/ontology.toml"
contained_kinds = []
```

## profiles/com.example.pin/PROFILE.toml

```toml
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
[meta]
schema_version = "0.1.0"
template_kind  = "profile-descriptor"
[profile]
name            = "com.example.pin"
namespace       = "com.example"
owner           = "example"
license         = "Apache-2.0"
extends         = []
ontology        = "profiles/com.example.pin/ontology.toml"
contained_kinds = ["pinned-note"]

[[profile.closure_records]]
contained_kind = "pinned-note"
field          = "notes.body_sha256"
presence       = "required"

[[profile.closure_records]]
contained_kind = "pinned-note"
field          = "notes.extra_sha256"
presence       = "when-present"
```

## profiles/com.example.pin/ontology.toml

```toml
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
[meta]
schema_version = "0.1.0"
template_kind  = "ontology"
title = "mini ontology"
```

## profiles/com.example.pin/pinned-note-kind.toml

```toml
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
[meta]
schema_version = "0.1.0"
template_kind  = "kind-descriptor"
describes_kind = "pinned-note"
[kind]
name = "pinned-note"
```
