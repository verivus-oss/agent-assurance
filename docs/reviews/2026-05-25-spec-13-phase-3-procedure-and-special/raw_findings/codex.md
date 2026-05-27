## Summary
Terminal classification: `unconditional_approval`.

I reviewed HEAD `3749398f5b6f126466832536225ba700c8ae3dc0` against parent `8a5e7157001a5f4a173030275514227a8cdddca0`. I inspected the prompt, bundle, plan lines 109-164/221/258-266, the Phase 0/1/2 reference shapes, the policy table, all five changed kind descriptors, `examples/minimal-adapter-contract.toml`, `CHANGELOG.md`, and validator code. I also rebuilt the sqry index after it reported a stale snapshot and used sqry to inspect validator symbols before confirming exact bytes with `nl`/`grep`/validators.

No blocker found. All U01-U09 units are complete.

## U01 — rollback-plan
Classification: complete.

Evidence: `profiles/agent-assurance/rollback-plan-kind.toml:173-177` declares `[kind.abstraction_class]` with `id = "procedure-declaration.v1"`, non-empty kind-specific description naming `[plan]`, `[[triggers]]`, and `[procedure].steps`, plus `ijb_primitive = "constraint"` and `ijb_constraint_type = "structural"`. Lines 179-218 declare the Family A envelope: 100 ms CPU, 1 MB memory, filesystem/sockets/http/environment/process_spawn/ipc/crypto_keys denied, clocks zeroed, and `random.entropy_source = "none"`. Existing descriptor prose and required shape at lines 33-52 and 86-95 match the description.

Bundle verify command output:

`python3 validators/validate_abstraction_class.py --repo-root . profiles/agent-assurance/rollback-plan-kind.toml`
`ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`

`grep -n closure_root profiles/agent-assurance/rollback-plan-kind.toml`
`5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`

`git show 3749398 -- profiles/agent-assurance/rollback-plan-kind.toml` was run. The added hunk begins at `@@ -151,3 +151,68 @@` and adds the §13 block whose HEAD line evidence is cited above.

## U02 — smoke-validation
Classification: complete.

Evidence: `profiles/agent-assurance/smoke-validation-kind.toml:168-172` declares `[kind.abstraction_class]` with `id = "validation-record.v1"`, a description naming `[result]`, `[[checks]]`, and the INV03 decision/status derivation rule, plus the required IJB structural tags. Lines 174-213 declare all nine Family A capability domains denied/zeroed, with `random.entropy_source = "none"` at line 201 and `crypto_keys.denied = true` at line 213. Existing root shape and required fields at lines 37-47 and 95-103 match the description.

Bundle verify command output:

`python3 validators/validate_abstraction_class.py --repo-root . profiles/agent-assurance/smoke-validation-kind.toml`
`ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`

`grep -n closure_root profiles/agent-assurance/smoke-validation-kind.toml`
`5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`

`git show 3749398 -- profiles/agent-assurance/smoke-validation-kind.toml` was run. The added hunk begins at `@@ -148,3 +148,66 @@` and adds the §13 block whose HEAD line evidence is cited above.

## U03 — assertion-bundle
Classification: complete.

Evidence: `profiles/agent-assurance/assertion-bundle-kind.toml:184-188` declares `[kind.abstraction_class]` with `id = "assertion-set.v1"`, a description naming sealed ordered `[[bundle.assertions]]`, bundle provenance/hash fields, ABNF parsing, and RUNTIME-SPEC hash/digest verification, plus the required IJB structural tags. Lines 190-229 declare the full Family A envelope. Existing prose at lines 21-33 and syntax-only validation at lines 57-63 match that SPEC-layer boundary.

Bundle verify command output:

`python3 validators/validate_abstraction_class.py --repo-root . profiles/agent-assurance/assertion-bundle-kind.toml`
`ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`

`grep -n closure_root profiles/agent-assurance/assertion-bundle-kind.toml`
`5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`

`git show 3749398 -- profiles/agent-assurance/assertion-bundle-kind.toml` was run. The added hunk begins at `@@ -162,3 +162,68 @@` and adds the §13 block whose HEAD line evidence is cited above.

## U04 — adapter-contract
Classification: complete.

Evidence: `profiles/agent-assurance/adapter-contract-kind.toml:229-233` declares `[kind.abstraction_class]` with `id = "interface-contract.v1"`, a kind-specific description naming `[adapter]`, `[adapter.runtime_artifact]`, `[[adapter.emits]]`, optional `[[adapter.declared_invariants]]`, and `[[adapter.conformance_fixtures]]`, plus the required IJB structural tags. Lines 235-274 declare the full Family A envelope.

R1/R2 check: I found no byte-level evidence requiring an R2 blocker. Existing prose says the contract carries runtime policy declarations but "does NOT carry the adapter binary itself" and that execution, hermeticity enforcement, and digest verification are RUNTIME-SPEC and out of SPEC-layer validation scope at `profiles/agent-assurance/adapter-contract-kind.toml:26-31`. The existing required fields make runtime policy an instance surface at `adapter.runtime_kind`, `adapter.runtime_network_policy`, and `adapter.runtime_clock_policy` in lines 107-121. The worked example puts those same fields in the instance `[adapter]` table at `examples/minimal-adapter-contract.toml:17-24`, with `runtime_env_allowlist = []` also instance-level. The new §13 prose is consistent with that: lines 201-210 say the descriptor envelope bounds text parse / closed-vocabulary / ABNF / digest-shape checks, while deployed adapter runtime capabilities are declared inside the instance `[adapter]` table; lines 212-218 reject R2 as unbounded or duplicative.

Bundle verify command output:

`sed -n '185,220p' profiles/agent-assurance/adapter-contract-kind.toml`
```text
ijb_constraint_type = "structural"

# ============================================================================
# SPEC §13 — abstraction class + capability envelope
# ============================================================================
#
# An adapter-contract is an interface-contract: it declares a pure-
# function adapter's identity, declared invariants, runtime policy
# declarations, and conformance fixture references. The adapter binary
# itself is NOT in the descriptor; execution, hermeticity enforcement,
# fixture dereferencing, and digest verification are RUNTIME-SPEC per
# the kind's own INV04.
#
# R1 vs R2 (plan §5 + §8 Phase 3): adapter-contract is the kind the
# plan explicitly flagged for R1/R2 ambiguity. There are two readings:
#
#   R1 (narrow, this descriptor adopts): the envelope bounds the
#       processing of THIS descriptor (text parse + closed-vocabulary
#       checks + ABNF-of-emits + digest-shape checks). The runtime
#       capabilities a deployed adapter is permitted at execution time
#       are declared INSIDE the instance file's [adapter] table
#       (runtime_kind, runtime_network_policy, runtime_clock_policy,
#       runtime_env_allowlist). Those instance-level fields are the
#       adapter's effective runtime policy; the kind descriptor's
#       envelope does not enumerate or constrain them beyond requiring
#       they exist and draw from closed vocabularies.
#
#   R2 (wide, NOT adopted): the envelope would have to cover whatever
#       any conforming adapter might require at runtime — which is
#       unbounded (LLM adapters need network, sandbox adapters need
#       process_spawn, signing adapters need crypto_keys). An R2
#       envelope is therefore either maximal (defeats §13's
#       failure-mode-bounding intent) or it duplicates the
#       instance-level runtime_* declarations (creating drift).
#
# Plan §5 explicitly chose R1 across the board; plan §7 row 7 noted
```

`python3 validators/validate_abstraction_class.py --repo-root . profiles/agent-assurance/adapter-contract-kind.toml`
`ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`

`grep -n closure_root profiles/agent-assurance/adapter-contract-kind.toml`
`5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`

`cat examples/minimal-adapter-contract.toml` output included:
```text
[adapter]
input_source            = "example-vendor:red_team_review@1"
input_hash_method       = "sha256-bytes"
id_derivation           = "content-hash"
runtime_kind            = "wasi-component"
runtime_network_policy  = "denied"
runtime_clock_policy    = "injected"
runtime_env_allowlist   = []
```

`git show 3749398 -- profiles/agent-assurance/adapter-contract-kind.toml` was run. The added hunk begins at `@@ -183,3 +183,92 @@` and adds the §13 block whose HEAD line evidence is cited above.

## U05 — selective-disclosure-proof
Classification: complete.

Evidence: `profiles/disclosure/selective-disclosure-proof-kind.toml:167-171` declares `[kind.abstraction_class]` with `id = "cryptographic-proof.v1"`, a description naming `[[proofs]]` rows, SDP ids, `subject`, `bound_source`, `proof_scheme`, `covers` / `proof_artifact`, and the SPEC-layer-only boundary, plus the required IJB structural tags. Lines 173-212 declare the full Family A envelope, including `entropy_source = "none"` at line 200 and `crypto_keys.denied = true` at line 212.

Family A is byte-supported: existing prose at `profiles/disclosure/selective-disclosure-proof-kind.toml:61-62` says "The SPEC layer enforces shape only. Verifying the proof against the published bytes is RUNTIME-SPEC." The plan's Family-B/C exception paragraph at `docs/planning/2026-05-25-spec-13-retrofit-scoping.md:141-154` reaches the same boundary. Validator code accepts only `os`, `deterministic_seed`, or `none` for `entropy_source` at `validators/validate_abstraction_class.py:182-191`, and `crypto_keys` grants are limited to `read_keys`, `use_keys`, and `generate_allowed` at lines 214-223.

Bundle verify command output:

`sed -n '140,170p' profiles/disclosure/selective-disclosure-proof-kind.toml`
```text

# ============================================================================
# SPEC §13 — abstraction class + capability envelope
# ============================================================================
#
# A selective-disclosure-proof is a cryptographic-proof (SPEC-layer
# shape only): it names the proof scheme and records the bound source
# hash that ties a redaction manifest to its source artifact. Per the
# kind's own prose at lines 61-62: "The SPEC layer enforces shape
# only. Verifying the proof against the published bytes is
# RUNTIME-SPEC." It MUST NOT, at the kind layer, become a transport
# for arbitrary capability assertions. Naming the class here binds
# future selective-disclosure-proof producers to the contract;
# widening this envelope cascade-breaks downstream
# selective-disclosure-proofs (per §13.4).
#
# Family A is correct here per plan §5 (Family-B/C-exceptions
# paragraph) — codex r1 on the plan caught two defects in an earlier
# draft that proposed a Family C envelope for this kind: (a) the
# descriptor's parse needs no crypto capabilities, only shape checks;
# (b) field names like `entropy_source = "system"` and
# `crypto_keys.sign/verify` are not in the validator's accepted
# vocabularies (validate_abstraction_class.py:182 accepts only
# os|deterministic_seed|none; :214 accepts only
# read_keys|use_keys|generate_allowed). Cryptographic work is
# RUNTIME-SPEC and lies outside this envelope.

[kind.abstraction_class]
id          = "cryptographic-proof.v1"
description = "Cryptographic-proof artefact (SPEC-layer shape only): declares `[[proofs]]` rows — each carrying `id` (`SDP:` prefix), `subject`, `bound_source` (literal `sha256:` prefix + 64 lowercase hex chars per INV01), closed-vocabulary `proof_scheme` (per INV02), and at least one of `covers` (list of `RED:` ids per INV03) or `proof_artifact` (repo-relative path to the binary proof blob). Cryptographic verification of the proof against the published bytes is RUNTIME-SPEC and lies outside this envelope (per the kind's prose lines 61-62). The SPEC layer enforces ID/shape rules only; cross-file resolution of `covers` to actual `RED:` entries is delegated to higher-level audit pipelines (per INV03). No I/O outside the canonical-form text serialisation; no networking; no process spawn."
ijb_primitive       = "constraint"
```

`python3 validators/validate_abstraction_class.py --repo-root . profiles/disclosure/selective-disclosure-proof-kind.toml`
`ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`

`grep -n closure_root profiles/disclosure/selective-disclosure-proof-kind.toml`
`5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`

`sed -n '180,225p' validators/validate_abstraction_class.py`
```text


def _check_domain_random(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    src = table.get("entropy_source")
    if src not in ("os", "deterministic_seed", "none"):
        return [
            f"{loc}.entropy_source: must be one of "
            f"['os', 'deterministic_seed', 'none'], got {src!r}"
        ]
    return []


def _check_domain_environment(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    return _check_string_list(table, "var_allowlist", loc)


def _check_domain_process_spawn(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    return _check_string_list(table, "allowed_programs", loc)


def _check_domain_ipc(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    errors = _check_bool_field(table, "shared_memory_allowed", loc)
    errors.extend(_check_bool_field(table, "fd_passing_allowed", loc))
    return errors


def _check_domain_crypto_keys(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    errors = []
    for key in ("read_keys", "use_keys"):
        if key in table:
            errors.extend(_check_string_list(table, key, loc))
    if "generate_allowed" in table:
        errors.extend(_check_bool_field(table, "generate_allowed", loc))
    return errors
```

`git show 3749398 -- profiles/disclosure/selective-disclosure-proof-kind.toml` was run. The added hunk begins at `@@ -137,3 +137,76 @@` and adds the §13 block whose HEAD line evidence is cited above.

## U06 — validators green at 19/19
Classification: complete.

All commands exited 0.

`python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml`
```text
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).
```

`for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do python3 validators/validate_ijb_conformance.py "$f"; done | grep -c 'IJB CONFORMANCE VALIDATION PASSED'`
```text
19
```

`for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do python3 validators/validate_kind_descriptor.py "$f" --repo-root . --check-references-exist; done | grep -c 'KIND DESCRIPTOR VALIDATION PASSED'`
```text
19
```

`python3 validators/validate_closure_root.py --discover .`
```text
CLOSURE-ROOT VALIDATION PASSED (74 file(s)).
```

`taplo lint core/*-kind.toml profiles/*/*-kind.toml`
```text
 INFO taplo:load_config: found configuration file path="/srv/repos/external/verivus-oss/agent-assurance/.taplo.toml"
 INFO taplo:lint_files:collect_files: found files total=19 excluded=0 files=["/srv/repos/external/verivus-oss/agent-assurance/core/contract-declaration-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/core/evidence-matrix-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/core/implementation-dag-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/core/profile-descriptor-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/core/readiness-gate-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/core/traceability-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/adapter-contract-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/adapter-registry-binding-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/assertion-bundle-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/assertion-log-record-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/gate-decision-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/rollback-plan-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/smoke-validation-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/spec-contract-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/threat-model-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/cost/cost-record-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/disclosure-attestation-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/redaction-manifest-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/selective-disclosure-proof-kind.toml"] cwd="/srv/repos/external/verivus-oss/agent-assurance"
```

## U07 — no forbidden-phrase leak
Classification: complete.

Required grep exited 0 and produced exactly:

```text
--- profiles/agent-assurance/rollback-plan-kind.toml ---
(no matches)
--- profiles/agent-assurance/smoke-validation-kind.toml ---
(no matches)
--- profiles/agent-assurance/assertion-bundle-kind.toml ---
(no matches)
--- profiles/agent-assurance/adapter-contract-kind.toml ---
(no matches)
--- profiles/disclosure/selective-disclosure-proof-kind.toml ---
(no matches)
```

I also inspected broader `MUST NOT` hits. Existing adapter/assertion SPEC-layer invariants are not violated by the §13 headers: adapter execution/hermeticity/digest checks remain RUNTIME-SPEC at `profiles/agent-assurance/adapter-contract-kind.toml:75-77` and `:162`; assertion bundle hash/digest verification remains RUNTIME-SPEC at `profiles/agent-assurance/assertion-bundle-kind.toml:147` and `:180-182`.

## U08 — closure_root sentinel preserved
Classification: complete.

`grep -n 'closure_root' profiles/agent-assurance/rollback-plan-kind.toml profiles/agent-assurance/smoke-validation-kind.toml profiles/agent-assurance/assertion-bundle-kind.toml profiles/agent-assurance/adapter-contract-kind.toml profiles/disclosure/selective-disclosure-proof-kind.toml`
```text
profiles/agent-assurance/rollback-plan-kind.toml:5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
profiles/agent-assurance/smoke-validation-kind.toml:5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
profiles/agent-assurance/assertion-bundle-kind.toml:5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
profiles/agent-assurance/adapter-contract-kind.toml:5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
profiles/disclosure/selective-disclosure-proof-kind.toml:5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

`python3 validators/validate_closure_root.py --discover .`
```text
CLOSURE-ROOT VALIDATION PASSED (74 file(s)).
```

## U09 — scope discipline
Classification: complete.

`git show --stat 3749398` exited 0. Its stat summary was:

```text
 CHANGELOG.md                                       | 44 +++++++++++
 .../agent-assurance/adapter-contract-kind.toml     | 89 ++++++++++++++++++++++
 .../agent-assurance/assertion-bundle-kind.toml     | 65 ++++++++++++++++
 profiles/agent-assurance/rollback-plan-kind.toml   | 65 ++++++++++++++++
 .../agent-assurance/smoke-validation-kind.toml     | 63 +++++++++++++++
 .../selective-disclosure-proof-kind.toml           | 73 ++++++++++++++++++
 6 files changed, 399 insertions(+)
```

`git diff --name-only 8a5e715..3749398`
```text
CHANGELOG.md
profiles/agent-assurance/adapter-contract-kind.toml
profiles/agent-assurance/assertion-bundle-kind.toml
profiles/agent-assurance/rollback-plan-kind.toml
profiles/agent-assurance/smoke-validation-kind.toml
profiles/disclosure/selective-disclosure-proof-kind.toml
```

Scope excludes `SPEC.md`, the plan file, Phase 1/2 descriptors, validators, and ontology files.

## Process checks
Active-user migration/behavior-change guidance present? Complete. The change is documented in `CHANGELOG.md:12-55` under Unreleased, including the phase-terminal 19/19 state, R1 runtime boundary, closure-root effect, and selective-disclosure Family A details.

No historical dated spec retconned without link/correction note? Complete. The commit scope is exactly the five Phase 3 descriptors plus `CHANGELOG.md`; no historical dated spec/planning file was edited.

Claimed tests actually run with command output and status? Complete. U01-U09 commands above were run locally from `/srv/repos/external/verivus-oss/agent-assurance`; all listed commands exited 0 with the quoted output.

## Terminal verdict
`unconditional_approval`.

Rationale: inspected descriptor bytes, plan/policy/docs, validator code, and the adapter worked example support the Phase 3 R1 Family A retrofit. Aggregate validators are green at 19/19, closure-root validation is green at 74 files, the required forbidden-phrase grep has zero matches, and the commit scope is exactly the five intended descriptors plus `CHANGELOG.md`. This persisted file is the review evidence at `docs/reviews/2026-05-25-spec-13-phase-3-procedure-and-special/raw_findings/codex.md`.
