**SESSION META**

- Reviewer: Codex (GPT-5 coding agent), independent clean-context review.
- Repo: `/srv/repos/external/verivus-oss/agent-assurance`.
- Sandbox / approval posture: danger-full-access filesystem, network enabled, approval policy `never`.
- MCP servers: sqry MCP used first; initial index was stale for `validators/validate_abstraction_class.py`, then `mcp__sqry__.rebuild_index(force=true)` succeeded with 48 indexed files / 7621 symbols.
- Re-derived HEAD: `27c10203d5b23a3750ee85f6fc50377234bc4303`.
- Commit under review verified with `git show 27c1020 --stat`, `git diff 3697066..27c1020`, and `git log --oneline -5`.
- Review record persisted at `docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md`.

**PROCESS CONFIRMATIONS**

- Migration guidance: confirmed. `SPEC.md:1474` declares "Backwards-compatible introduction"; `SPEC.md:1476-1479` says existing kind descriptors omitting the blocks remain conformant but do not gain §13.4; `SPEC.md:1481-1486` says adopters retrofit incrementally and follow-up issues track remaining kinds.
- No retconning: confirmed for descriptors. `rg -n "\[kind\.abstraction_class\]|\[kind\.capability_envelope\]" core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml` returned only `profiles/cost/cost-record-kind.toml:282` and `profiles/cost/cost-record-kind.toml:288`. The descriptor sweep counted 19 files and 1 declaration.
- Tests-run-with-output: confirmed. Negative validator tests, full 19-descriptor sweep, IJB conformance, single-source-of-truth ontology tamper/restore, cascade hash perturbation, multi-violation diagnostic visibility, and `bash validators/check_manifest_drift.sh` were run. Outputs are quoted below in Q1-Q10.

**ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS**

**Q1 — Closed-vocabulary completeness and IJB tags**

Verdict: confirmed.

Evidence:
- `core/ontology.toml:633-650` declares `capability_envelope.domain`, `applies_to = "kind_descriptor"`, nine values, `extensible = false`, `ijb_primitive = "constraint"`, `ijb_constraint_type = "structural"`.
- `core/ontology.toml:652-659` declares `abstraction_class.id_pattern`, one value `"<slug>.v<integer>"`, `extensible = false`, `ijb_primitive = "constraint"`, `ijb_constraint_type = "structural"`.

Command:
```text
python3 validators/validate_ijb_conformance.py core/ontology.toml
EXIT: 0
last line: - template_kind: ontology
```

Parsed vocabulary check:
```text
capability_envelope.domain
values_len= 9
values= ['filesystem', 'sockets', 'http', 'clocks', 'random', 'environment', 'process_spawn', 'ipc', 'crypto_keys']
ijb_primitive= constraint
ijb_constraint_type= structural
abstraction_class.id_pattern
values_len= 1
values= ['<slug>.v<integer>']
ijb_primitive= constraint
ijb_constraint_type= structural
```

**Q2 — Validator enforces every declared rule from §13.2 + §13.3**

Verdict: confirmed for the validator rules tested. The validator emits operator-visible diagnostics for each negative perturbation.

Evidence:
- `validators/validate_abstraction_class.py:52` defines the `<slug>.v<integer>` pattern.
- `validators/validate_abstraction_class.py:125-139` checks IJB tags.
- `validators/validate_abstraction_class.py:267-294` requires `spec_version`, `cpu_bounds`, and `memory_bounds`.
- `validators/validate_abstraction_class.py:312-317` rejects unknown domains.
- `validators/validate_abstraction_class.py:396-404` prints every failure and exits 1.

Commands and exact outputs:
```text
COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/a_bad_id.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/a_bad_id.toml: [kind.abstraction_class].id: must match `<slug>.v<integer>` (lowercase slug + `.v` + non-negative integer), got 'bad-no-version'

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/b_empty_description.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/b_empty_description.toml: [kind.abstraction_class].description: must be a non-empty string, got ''

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/c_wrong_ac_ijb.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/c_wrong_ac_ijb.toml: [kind.abstraction_class].ijb_primitive: must be 'constraint', got 'observed'

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/i_missing_spec_version.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/i_missing_spec_version.toml: [kind.capability_envelope].spec_version: must be a non-empty string, got None

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/j_wrong_ce_ijb.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/j_wrong_ce_ijb.toml: [kind.capability_envelope].ijb_primitive: must be 'constraint', got 'observed'

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/d_missing_cpu_bounds.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/d_missing_cpu_bounds.toml: [kind.capability_envelope].cpu_bounds: missing required table

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/e_missing_memory_bounds.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/e_missing_memory_bounds.toml: [kind.capability_envelope].memory_bounds: missing required table

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/f_float_cpu.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/f_float_cpu.toml: [kind.capability_envelope].cpu_bounds.max_cpu_ms: must be an integer, got float: 1.5

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/g_unknown_domain.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/g_unknown_domain.toml: [kind.capability_envelope].made_up_domain: not a capability domain. Closed set: ['clocks', 'crypto_keys', 'environment', 'filesystem', 'http', 'ipc', 'process_spawn', 'random', 'sockets']. Adding a new domain requires a SPEC amendment (§13.3).

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/h_filesystem_missing_read_allowed.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/h_filesystem_missing_read_allowed.toml: [kind.capability_envelope].filesystem: missing required boolean field `read_allowed`

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).
```

**Q3 — Backwards compatibility**

Verdict: confirmed.

Command:
```text
python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
EXIT: 0
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).
```

The one declaring descriptor is confirmed by exact search:
```text
profiles/cost/cost-record-kind.toml:282:[kind.abstraction_class]
profiles/cost/cost-record-kind.toml:288:[kind.capability_envelope]
```

**Q4 — Closed-domain vocabulary load — single source of truth**

Verdict: confirmed. I tampered with the real `core/ontology.toml`, verified accept, restored it, verified reject, and `git diff -- core/ontology.toml` was empty afterward.

Evidence:
- `validators/validate_abstraction_class.py:58-67` loads `capability_envelope.domain` from `core/ontology.toml`.
- `validators/validate_abstraction_class.py:312-317` makes the accept/reject decision against that loaded set.

Commands and exact outputs:
```text
COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-real-tamper-invented-domain3.toml
EXIT: 1
FAIL /tmp/spec13-real-tamper-invented-domain3.toml: [kind.capability_envelope].invented_domain3: not a capability domain. Closed set: ['clocks', 'crypto_keys', 'environment', 'filesystem', 'http', 'ipc', 'process_spawn', 'random', 'sockets']. Adding a new domain requires a SPEC amendment (§13.3).

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-real-tamper-invented-domain3.toml
EXIT: 0
ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).

COMMAND: python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-real-tamper-invented-domain3.toml
EXIT: 1
FAIL /tmp/spec13-real-tamper-invented-domain3.toml: [kind.capability_envelope].invented_domain3: not a capability domain. Closed set: ['clocks', 'crypto_keys', 'environment', 'filesystem', 'http', 'ipc', 'process_spawn', 'random', 'sockets']. Adding a new domain requires a SPEC amendment (§13.3).

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).

RESTORE CHECK:
```

**Q5 — Cost-record worked example structural soundness**

Verdict: structurally accepted by the validator, but the "8 of 9 domains use `denied = true`" subclaim is refuted by the file.

Evidence:
- `profiles/cost/cost-record-kind.toml:282-286` declares `id = "observation-record.v1"` and IJB tags; the id matches `validators/validate_abstraction_class.py:52`.
- `profiles/cost/cost-record-kind.toml:293-298` declares CPU and memory bounds.
- `profiles/cost/cost-record-kind.toml:300-327` declares all nine domains.
- Seven domains use `denied = true`: filesystem, sockets, http, environment, process_spawn, ipc, crypto_keys.
- `profiles/cost/cost-record-kind.toml:309-312` declares clocks as all-false with `precision_cap_ms = 0`.
- `profiles/cost/cost-record-kind.toml:314-315` declares random as `entropy_source = "none"`, not `denied = true`.

Parsed check:
```text
['filesystem', 'sockets', 'http', 'clocks', 'random', 'environment', 'process_spawn', 'ipc', 'crypto_keys']
domain_count= 9
denied_true= ['crypto_keys', 'environment', 'filesystem', 'http', 'ipc', 'process_spawn', 'sockets']
clocks= {'wall_clock_allowed': False, 'monotonic_clock_allowed': False, 'precision_cap_ms': 0}
```

Validator:
```text
python3 validators/validate_abstraction_class.py --repo-root . profiles/cost/cost-record-kind.toml
EXIT: 0
ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).
```

**Q6 — SPEC §13.4 cascade-break property is structurally enforced**

Verdict: confirmed at the file-hash propagation level requested.

Evidence:
- `SPEC.md:1235-1241` says changing class/envelope changes descriptor bytes and cascades through closure roots.
- `SPEC.md:1329-1350` restates the cascade-break property.

Command/output:
```text
sha256sum profiles/cost/cost-record-kind.toml
sed 's/max_cpu_ms      = 100/max_cpu_ms      = 200/' profiles/cost/cost-record-kind.toml | sha256sum

cc424b1aadcb2eefa916116c4c98d77a175161b47682507971956c29941c5a15  profiles/cost/cost-record-kind.toml
e7c8fdf534c5d94e839a00ffeefff0bddcdaba2bd101931de998b9c553499635  -
```

The hashes differ.

**Q7 — §13.5 scope-out is honest**

Verdict: confirmed for implementation surface. The commit introduces textual scope-outs and a structural validator only; I found no CBOR encoder, attenuation algorithm, CB-AdES schema, seccomp emitter, or WASM Component Model import-check in the changed files.

Evidence:
- `SPEC.md:1352-1376` explicitly scopes out wire format/CDDL, attenuation calculus, signing tier, enforcement backend, WASM static observability, and runtime-observation-attestation.
- `validators/validate_abstraction_class.py:32-39` states it does not enforce attenuation, runtime conformance, or WASM static observability.
- `git show --name-only --format='' 27c1020` lists 13 changed files: docs/spec/ontology/seed/count hardcodes and one validator, no runtime or encoder module.

Targeted grep over changed files found only textual mentions or pre-existing seed vocabulary values:
```text
validators/validate_abstraction_class.py:33:- The attenuation calculus (child envelope ⊆ parent envelope) —
validators/validate_abstraction_class.py:36:  envelope) — that is the future `runtime-observation-attestation`
validators/validate_abstraction_class.py:38:- The WASM Component Model static-observability check — that is
core/ontology.toml:648:notes       = "Closed set ... enforcement backends (Linux seccomp+landlock, FreeBSD Capsicum, macOS sandbox-exec, Wasmtime) ..."
SPEC.md:1356:  CBOR wire shape for cross-runtime signing is a separate
SPEC.md:1357:  document (Stream F V2's `capability-envelope` CDDL).
SPEC.md:1358:- **The attenuation calculus.** "Child envelope ⊆ parent
SPEC.md:1364:  technical-tier COSE_Sign1 or legal-tier CB-AdES (ETSI TS 119
SPEC.md:1367:- **The enforcement backend.** Linux seccomp+landlock, FreeBSD
SPEC.md:1371:  proposal recommends WASM Component Model + WIT imports as the
```

**Q8 — Forbidden mechanisms list (§13.9) is structurally complete**

Verdict: refuted in one item.

Evidence:
- §12.7 at `SPEC.md:1059-1071` forbids stale re-signing, unsigned closure root, soft revocations, and cached closure inputs. These address identity/closure-root failure modes.
- §13.9 at `SPEC.md:1459-1469` forbids stale re-signing after envelope widening, missing-domain implicit grant, and ad-hoc capability declarations. These are the right behavioral-envelope failure modes and are orthogonal except the first intentionally maps back to §12.7.
- §13.9 at `SPEC.md:1470-1472` forbids mixing technical-tier and legal-tier signatures on the same artefact. That is not a capability-envelope papering-over mechanism, and it conflicts with §13.5's signing-tier deferral at `SPEC.md:1363-1366`.

Conclusion: the first three §13.9 bullets are structurally appropriate; the fourth is not part of the abstraction-class/capability-envelope failure mode and should not be in this forbidden-mechanisms list as written.

**Q9 — Reference DB + count-mirror gate are clean after §13**

Verdict: confirmed.

Evidence:
- `reference/database/MANIFEST.toml:36` has `attribute_vocabularies = 43`.
- `reference/database/MANIFEST.toml:42` has `attribute_values_declared = 180`.
- `reference/database/MANIFEST.toml:51` has `attribute_values_closed = 109`.
- `reference/database/MANIFEST.toml:277`, `:308`, and `:318` have per-engine seed counts at 43 / 116.
- `reference/database/MANIFEST.toml:298-299` has RDF footer 43 and schema triples 1329.
- `tools/dagtoml-duckdb/src/main.rs:24-30` and `tools/dagtoml-duckdb-go/main.go:38-47` hardcode 43 / 116.

Command/output:
```text
bash validators/check_manifest_drift.sh
EXIT: 0
COUNT-MIRROR OK — every surface agrees with reality.

OK — manifest matches ontology + every count-mirror surface agrees
```

The full command output listed all 28 count-mirror comparisons as `==`.

**Q10 — Validator structure mirrors validate_cost.py pattern**

Verdict: confirmed, including operator-visible multi-failure output.

Evidence:
- `validators/validate_cost.py:53-76` loads closed vocabularies from ontology; `validators/validate_abstraction_class.py:58-67` mirrors this for core `capability_envelope.domain`.
- `validators/validate_cost.py:225-234` prints each `FAIL ...` and exits 1; `validators/validate_abstraction_class.py:396-404` does the same.

Multi-violation command/output:
```text
python3 validators/validate_abstraction_class.py --repo-root . /tmp/spec13-review-neg/multi_violation.toml
EXIT: 1
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.abstraction_class].id: must match `<slug>.v<integer>` (lowercase slug + `.v` + non-negative integer), got 'bad-no-version'
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.abstraction_class].description: must be a non-empty string, got ''
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.abstraction_class].ijb_primitive: must be 'constraint', got 'observed'
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.capability_envelope].spec_version: must be a non-empty string, got ''
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.capability_envelope].ijb_primitive: must be 'constraint', got 'observed'
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.capability_envelope].cpu_bounds: missing required table
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.capability_envelope].memory_bounds: missing required table
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.capability_envelope].filesystem: missing required boolean field `read_allowed`
FAIL /tmp/spec13-review-neg/multi_violation.toml: [kind.capability_envelope].made_up_domain: not a capability domain. Closed set: ['clocks', 'crypto_keys', 'environment', 'filesystem', 'http', 'ipc', 'process_spawn', 'random', 'sockets']. Adding a new domain requires a SPEC amendment (§13.3).

ABSTRACTION-CLASS VALIDATION FAILED: 9 error(s) across 1 file(s).
```

**INDEPENDENT FINDINGS**

1. `SPEC13-F1` — high — `SPEC.md:1324-1326`

Verbatim quote:
```text
The full table of grant sub-tables is normative and declared by the
`core/kind-descriptor-kind.toml` descriptor's
`[kind.capability_envelope]` schema;
```

Problem: the referenced file does not exist in the commit. `find core -maxdepth 1 -name '*-kind.toml' -print | sort` lists six core kind descriptors and no `core/kind-descriptor-kind.toml`; `git show 27c1020:core/kind-descriptor-kind.toml` fails with `fatal: path 'core/kind-descriptor-kind.toml' does not exist in '27c1020'`. The spec points readers to a normative schema surface that is absent.

Fix: either add the promised `core/kind-descriptor-kind.toml` schema with the §13 grant sub-table shape, or change §13.3 to name the actual normative enforcement surface (`SPEC.md` plus `validators/validate_abstraction_class.py` and `core/ontology.toml`) without claiming a nonexistent descriptor.

2. `SPEC13-F2` — medium — `SPEC.md:1268-1270`

Verbatim quote:
```text
The envelope is organised by *capability domain*, not by primitive
operation. Each domain is either denied entirely (`false`) or
scoped via a sub-table.
```

Problem: the spec says domain denial is expressed as `false`, but the examples and validator implement denial as a sub-table containing `denied = true`. A literal `filesystem = false` under `[kind.capability_envelope]` is rejected by `validators/validate_abstraction_class.py:306-310` as a non-table top-level value. This is a normative syntax mismatch.

Fix: change the §13.3 prose from ``(`false`)`` to ``(`denied = true`)`` / "a domain sub-table with `denied = true`", or extend the validator and examples to accept the boolean syntax.

3. `SPEC13-F3` — medium — `SPEC.md:1470-1472`

Verbatim quote:
```text
- Mix the technical-tier and legal-tier signatures on the same
  artefact. Either tier carries the closure root; both is
  declared posture, not engineering.
```

Problem: §13.5 says the signing tier is out of scope and a profile/runtime choice (`SPEC.md:1363-1366`). This §13.9 bullet then introduces a `MUST NOT`-style prohibition in a non-normative warning for a signing-tier composition question that is not a capability-envelope papering-over mechanism. It is not orthogonal to §12.7 in the same way as missing-domain grants or ad-hoc capability fields; it is a separate signing-profile policy.

Fix: remove this bullet from §13.9, or move a precisely scoped signing-tier rule to the runtime/profile signing specification instead of making it a §13 forbidden mechanism.

**TERMINAL VERDICT**

CONCRETE UNRESOLVABLE BLOCKERS:

1. `SPEC.md:1324-1326` points to nonexistent normative schema file `core/kind-descriptor-kind.toml`; unblocking action: add that descriptor/schema or rewrite §13.3 to name the actual normative surfaces.
2. `SPEC.md:1268-1270` says denied domains are represented as `false`, while the validator rejects non-table domain values and examples use `denied = true`; unblocking action: align the normative syntax and validator/examples.
3. `SPEC.md:1470-1472` forbids mixed technical/legal signing tiers inside §13.9 despite §13.5 deferring signing-tier choice and despite the item not being a capability-envelope papering-over mechanism; unblocking action: remove or relocate/reframe that rule in the signing-profile layer.
