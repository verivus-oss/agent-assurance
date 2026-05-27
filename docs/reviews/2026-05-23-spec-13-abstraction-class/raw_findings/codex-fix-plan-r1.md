**SESSION META**

- Reviewer: Codex (GPT-5 coding agent), independent fix-plan review.
- Repo: `/srv/repos/external/verivus-oss/agent-assurance`.
- Re-derived HEAD: `0848d34c09973e137e2ca855e85bbd682eb67b9f`.
- Prompt-stated HEAD mismatch: the prompt named `27c10203d5b23a3750ee85f6fc50377234bc4303`; the checked-out repository is currently at `0848d34c09973e137e2ca855e85bbd682eb67b9f`.
- Worktree posture: dirty before this review, with existing modified and untracked files. This review did not edit source/spec files; it only persisted this advisory note.
- Sandbox / approval posture: danger-full-access filesystem, network enabled, approval policy `never`.
- MCP servers used: sqry MCP first. `mcp__sqry__.get_index_status` reported an existing index for 48 files / 7736 symbols; `mcp__sqry__.semantic_search` was used to orient on `validators/validate_abstraction_class.py`.
- Prior review read: `docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md`, including F1/F2/F3 at lines 298-335 and terminal blockers at lines 337-343.
- Grok review read: `docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/grok.md`.

**PRECONDITION CHECK**

`SPEC.md:128-134` is present as Claude described:

```text
128 self-describing file would be the recursion stop. This spec does not
129 ship that self-descriptor; the descriptor format is defined
130 normatively by §2.3 above (the table and the paragraph following it)
131 and by
132 [validators/validate_kind_descriptor.py](validators/validate_kind_descriptor.py).
133 Recursion stops here; tooling MUST NOT require a
134 `kind-descriptor-kind.toml` to exist.
```

This is load-bearing for F1: `validators/validate_kind_descriptor.py:9-11` independently says "The recursion stops at the prose definition in SPEC.md §2.4 plus this validator; no `kind-descriptor-kind.toml` is shipped or required."

`SPEC.md:1268-1270` is present as Claude described:

```text
1268 The envelope is organised by *capability domain*, not by primitive
1269 operation. Each domain is either denied entirely (`false`) or
1270 scoped via a sub-table. Resource bounds (CPU + memory) are
```

`SPEC.md:1361-1366` is present as Claude described:

```text
1361 pinned in a separate executable specification per the
1362 multi-language safe-language strategy (Stream D).
1363 - **The signing tier.** Whether the descriptor is signed under
1364   technical-tier COSE_Sign1 or legal-tier CB-AdES (ETSI TS 119
1365   152-1) is profile/runtime choice. Either tier carries the
1366   closure root.
```

`SPEC.md:1470-1472` is present as Claude described:

```text
1470 - Mix the technical-tier and legal-tier signatures on the same
1471   artefact. Either tier carries the closure root; both is
1472   declared posture, not engineering.
```

`SPEC.md:1323-1327` is present as Claude described:

```text
1323
1324 The full table of grant sub-tables is normative and declared by the
1325 `core/kind-descriptor-kind.toml` descriptor's
1326 `[kind.capability_envelope]` schema; this section names the
1327 domains and the fail-closed default.
```

The referenced file is absent: `find core -maxdepth 1 -name '*-kind.toml' -print | sort` lists six descriptors (`contract-declaration`, `evidence-matrix`, `implementation-dag`, `profile-descriptor`, `readiness-gate`, `traceability`) and no `core/kind-descriptor-kind.toml`. `rg -n "kind-descriptor-kind\.toml"` finds only the §2.4 recursion-stop text, the F1 site, the prior review, and `validators/validate_kind_descriptor.py:11`.

**EVALUATION OF F1 FIX**

Verdict: sound as proposed.

F1 still holds against the current checkout. `SPEC.md:1324-1327` points to `core/kind-descriptor-kind.toml`, but §2.4 says the spec does not ship that self-descriptor and tooling must not require it (`SPEC.md:128-134`). The validator repeats the same recursion boundary at `validators/validate_kind_descriptor.py:9-11`.

Adding `core/kind-descriptor-kind.toml` would contradict that recursion boundary. Rewriting §13.3 to name the actual normative surfaces is the right direction.

The actual surfaces are:

- `SPEC.md:1273-1288` names the closed domain set in prose table form, and `SPEC.md:1305-1307` states the `denied = true` / missing-domain fail-closed shape in the TOML example.
- `core/ontology.toml:633-650` declares the machine-readable closed domain vocabulary, including `extensible = false` and the note that missing sub-tables are denied.
- `validators/validate_abstraction_class.py:58-67` loads `capability_envelope.domain` from `core/ontology.toml`; `validators/validate_abstraction_class.py:300-321` rejects non-table domain entries and unknown domain names, then dispatches to the per-domain shape checkers.
- `validators/validate_abstraction_class.py:142-223` defines the structural shape of each known domain and accepts `denied = true` as the whole-domain denial form.

That covers everything the deleted prose claimed: the closed domain list, sub-table structural shape, and fail-closed default. The replacement should not imply that `core/ontology.toml` alone defines per-domain field schemas; those schemas are in `validators/validate_abstraction_class.py` plus the §13.3 prose/example.

**EVALUATION OF F2 FIX**

Verdict: sound as proposed.

F2 still holds against the current checkout. The current prose says a domain can be denied as bare `false` at `SPEC.md:1268-1270`, but the validator rejects any top-level domain value that is not a sub-table:

```text
validators/validate_abstraction_class.py:300 # Domain sub-tables: closed set; unknown names are rejected.
validators/validate_abstraction_class.py:303 for key, val in block.items():
validators/validate_abstraction_class.py:306 if not isinstance(val, dict):
validators/validate_abstraction_class.py:307     errors.append(
validators/validate_abstraction_class.py:308         f"{loc}.{key}: top-level value must be a sub-table, "
validators/validate_abstraction_class.py:309         f"got {type(val).__name__}"
validators/validate_abstraction_class.py:310     )
```

The proposed prose matches the actual acceptance behavior. Each declared domain entry is a sub-table; whole-domain denial is represented inside that sub-table as `denied = true`. The domain checkers short-circuit on `denied = true`, for example filesystem at `validators/validate_abstraction_class.py:142-144`, sockets at `validators/validate_abstraction_class.py:152-154`, and crypto_keys at `validators/validate_abstraction_class.py:214-216`.

The worked example matches the proposed syntax: `profiles/cost/cost-record-kind.toml:300-327` declares every domain as a sub-table; filesystem, sockets, http, environment, process_spawn, ipc, and crypto_keys use `denied = true`; clocks and random use scoped fields.

The missing-domain fail-closed default remains expressible after this line edit. It is already stated in the same §13.3 TOML example at `SPEC.md:1305-1307` ("A domain whose table is entirely missing is treated as `denied = true`") and reinforced by §13.9 at `SPEC.md:1465-1466` ("Missing-domain = denied; the failure mode is fail-closed."). It is also recorded in the validator docstring at `validators/validate_abstraction_class.py:27-30` and in ontology notes at `core/ontology.toml:648`.

The proposed F2 sentence does not need to repeat the missing-domain rule at `SPEC.md:1268-1270` because the surrounding §13.3 example and §13.9 already preserve that semantic. Reading "Each domain is a sub-table" as "each declared domain entry is a sub-table" is consistent with the validator and the immediately following fail-closed example.

**EVALUATION OF F3 FIX**

Verdict: sound as proposed.

F3 still holds against the current checkout. §13.5 explicitly excludes signing tier selection from this section: `SPEC.md:1363-1366` says whether the descriptor is signed under technical-tier COSE_Sign1 or legal-tier CB-AdES is profile/runtime choice and that either tier carries the closure root. The §13.9 bullet at `SPEC.md:1470-1472` then forbids mixing those tiers on the same artefact. That is a signing-profile policy assertion, not a capability-envelope papering-over mechanism.

Deleting the bullet leaves §13.9 structurally complete for its actual scope:

- `SPEC.md:1461-1464` forbids re-signing under an unchanged closure root after envelope widening.
- `SPEC.md:1465-1466` forbids treating a missing capability domain as an implicit grant.
- `SPEC.md:1467-1469` forbids ad-hoc capability declarations outside `[kind.capability_envelope]`.

Those three bullets are all about hiding or bypassing the class/envelope contract. The deleted signature-tier bullet is not. There is no current normative signing-profile home in the repo that defines technical-tier/legal-tier composition rules: §12.5 also scopes signing-envelope format and cryptographic choices to profiles or RUNTIME-SPEC at `SPEC.md:990-1008`. Deletion is therefore the correct current remediation. A future signing-profile document may add a precise rule, but relocation is not required for this fix plan.

**TERMINAL VERDICT**

UNCONDITIONAL APPROVAL of fix plan — F1: §2.4 forbids requiring `kind-descriptor-kind.toml` (`SPEC.md:128-134`), so naming SPEC §13 + `core/ontology.toml` + `validators/validate_abstraction_class.py` matches the real normative surfaces (`core/ontology.toml:633-650`, `validators/validate_abstraction_class.py:58-67`, `:300-321`); F2: bare `false` is rejected because domain entries must be sub-tables (`validators/validate_abstraction_class.py:300-310`) and the worked example uses `denied = true` sub-tables (`profiles/cost/cost-record-kind.toml:300-327`), while fail-closed remains stated at `SPEC.md:1305-1307` and `SPEC.md:1465-1466`; F3: §13.5 defers signing tier to profile/runtime (`SPEC.md:1363-1366`), and removing the mixed-tier bullet leaves only capability-envelope papering-over mechanisms in §13.9 (`SPEC.md:1461-1469`).
