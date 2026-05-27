**SESSION META**

- Reviewer: Codex (GPT-5 coding agent), independent reviewer #1 for round 2 of the SPEC §13 review.
- Repo: `/srv/repos/external/verivus-oss/agent-assurance`.
- Re-derived HEAD: `7328dfd3937a1d37c7b274ce527c330e5b54d346`.
- Commit under review: `7328dfd3937a1d37c7b274ce527c330e5b54d346` (`SPEC §13: close codex r1 blockers F1/F2/F3 + §2.4 contradiction`).
- Parent/ancestry check: `git rev-list --parents -n 1 7328dfd` reports `7328dfd3937a1d37c7b274ce527c330e5b54d346 0848d34c09973e137e2ca855e85bbd682eb67b9f`; the commit object's parent is `0848d34`, not `27c1020`. `git merge-base 27c1020 7328dfd` is `27c10203d5b23a3750ee85f6fc50377234bc4303`, and `git rev-list --count 27c1020..7328dfd` is `2`.
- Sandbox / approval posture: danger-full-access filesystem, network enabled, approval policy `never`.
- MCP servers: sqry MCP used first. `mcp__sqry__.get_index_status` reported an existing index for 48 files / 7736 symbols; `mcp__sqry__.semantic_search` and `mcp__sqry__.get_document_symbols` were used to orient on `validators/validate_abstraction_class.py` before literal confirmation.
- Prior reviews read:
  - `docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md`
  - `docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/grok.md`
  - `docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/codex-fix-plan-r1.md`
- Worktree note: the working tree was already dirty before this review, including unrelated modified and untracked files. This review only added this persisted review file.

**DIFF SCOPE CHECK**

Verdict: the prompt-stated range scope is refuted; the commit object's own patch is two files.

Command:
```text
git diff 27c1020..7328dfd --stat
EXIT: 0
```

The requested range reports 43 files changed, not only `SPEC.md` and `CHANGELOG.md`. The first and last relevant stat lines are:
```text
 CHANGELOG.md                                       |  55 ++
 SPEC.md                                            |  20 +-
 arxiv-prep-agent-dag.toml                          | 406 +++++++++++++++
 ...
 tools/claim-analysis-document-review-dag.toml      | 375 ++++++++++++++
 43 files changed, 3142 insertions(+), 10 deletions(-)
```

The reason is ancestry, not the `7328dfd` commit object's patch:
```text
git rev-list --parents -n 1 7328dfd
EXIT: 0
7328dfd3937a1d37c7b274ce527c330e5b54d346 0848d34c09973e137e2ca855e85bbd682eb67b9f
```

For comparison, the commit object itself is scoped to the two expected files:
```text
git show --stat --oneline --decorate 7328dfd
EXIT: 0
7328dfd (HEAD -> main) SPEC §13: close codex r1 blockers F1/F2/F3 + §2.4 contradiction
 CHANGELOG.md | 55 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
 SPEC.md      | 20 ++++++++++----------
 2 files changed, 65 insertions(+), 10 deletions(-)
```

And:
```text
git show --name-only --pretty=format: 7328dfd
EXIT: 0
CHANGELOG.md
SPEC.md
```

**ANSWERS TO Q1-Q7**

**Q1 - F1 is mechanically closed**

Verdict: mechanically closed in `SPEC.md`; literal `git diff 27c1020..7328dfd | grep kind-descriptor-kind.toml` also returns CHANGELOG review quotes because the requested range includes the r2 CHANGELOG entry.

Evidence at the prior site is now:
```text
SPEC.md:1324 The full table of grant sub-tables is normative and is declared
SPEC.md:1325 jointly by (a) the closed `capability_envelope.domain` vocabulary
SPEC.md:1326 in `core/ontology.toml`, (b) the per-domain shape checks enforced
SPEC.md:1327 by `validators/validate_abstraction_class.py`, and (c) this
SPEC.md:1328 section's prose. Per §2.4, tooling MUST NOT require a
SPEC.md:1329 `kind-descriptor-kind.toml` to exist; the validator + ontology +
SPEC.md:1330 SPEC §13 are the recursion-stop surfaces.
```

This confirms:
- (a) `core/ontology.toml` is named at `SPEC.md:1326`.
- (b) `validators/validate_abstraction_class.py` is named at `SPEC.md:1327`.
- (c) §2.4's "MUST NOT require `kind-descriptor-kind.toml`" rule is referenced at `SPEC.md:1328-1329`; the source rule remains at `SPEC.md:133-134`.
- The old normative `core/kind-descriptor-kind.toml` surface is removed from §13.3. `rg -n "core/kind-descriptor-kind\.toml" SPEC.md` returns no matches.

Command:
```text
git diff 27c1020..7328dfd | grep 'kind-descriptor-kind.toml'; printf 'EXIT:%s\n' $?
EXIT: 0
```

Output:
```text
+    `core/kind-descriptor-kind.toml` descriptor's
+    NOT require a `kind-descriptor-kind.toml` to exist." The §13.3
-`core/kind-descriptor-kind.toml` descriptor's
+`kind-descriptor-kind.toml` to exist; the validator + ontology +
```

The only `core/kind-descriptor-kind.toml` addition is the CHANGELOG quote of the r1 text being replaced, not a normative reintroduction in `SPEC.md`.

**Q2 - F2 is mechanically closed**

Verdict: mechanically closed.

The `(false)` denial syntax is removed from the old `SPEC.md:1268-1270` site. HEAD says:
```text
SPEC.md:1268 The envelope is organised by *capability domain*, not by primitive
SPEC.md:1269 operation. Each domain is a sub-table -- denied via `denied = true`
SPEC.md:1270 or scoped via fields that constrain the grant. Resource bounds
SPEC.md:1271 (CPU + memory) are declared separately.
```

Missing-domain fail-closed semantic is still present in §13.3 and §13.9:
```text
SPEC.md:1305 # Capability grants -- each is `denied = true` to forbid the whole
SPEC.md:1306 # domain, or a sub-table to scope it. A domain whose table is
SPEC.md:1307 # entirely missing is treated as `denied = true` (fail closed).
SPEC.md:1468 - Treat a missing capability domain table as an implicit grant.
SPEC.md:1469   Missing-domain = denied; the failure mode is fail-closed.
```

The worked example uses sub-tables:
```text
profiles/cost/cost-record-kind.toml:300 [kind.capability_envelope.filesystem]
profiles/cost/cost-record-kind.toml:301 denied = true
profiles/cost/cost-record-kind.toml:303 [kind.capability_envelope.sockets]
profiles/cost/cost-record-kind.toml:304 denied = true
profiles/cost/cost-record-kind.toml:306 [kind.capability_envelope.http]
profiles/cost/cost-record-kind.toml:307 denied = true
profiles/cost/cost-record-kind.toml:317 [kind.capability_envelope.environment]
profiles/cost/cost-record-kind.toml:318 denied = true
profiles/cost/cost-record-kind.toml:320 [kind.capability_envelope.process_spawn]
profiles/cost/cost-record-kind.toml:321 denied = true
profiles/cost/cost-record-kind.toml:323 [kind.capability_envelope.ipc]
profiles/cost/cost-record-kind.toml:324 denied = true
profiles/cost/cost-record-kind.toml:326 [kind.capability_envelope.crypto_keys]
profiles/cost/cost-record-kind.toml:327 denied = true
```

Validator behavior matches the prose:
```text
validators/validate_abstraction_class.py:142 def _check_domain_filesystem(table: dict, loc: str) -> list[str]:
validators/validate_abstraction_class.py:143     if table.get("denied") is True:
validators/validate_abstraction_class.py:144         return []
...
validators/validate_abstraction_class.py:214 def _check_domain_crypto_keys(table: dict, loc: str) -> list[str]:
validators/validate_abstraction_class.py:215     if table.get("denied") is True:
validators/validate_abstraction_class.py:216         return []
```

And top-level non-table values are rejected:
```text
validators/validate_abstraction_class.py:300     # Domain sub-tables: closed set; unknown names are rejected.
validators/validate_abstraction_class.py:303     for key, val in block.items():
validators/validate_abstraction_class.py:306         if not isinstance(val, dict):
validators/validate_abstraction_class.py:307             errors.append(
validators/validate_abstraction_class.py:308                 f"{loc}.{key}: top-level value must be a sub-table, "
validators/validate_abstraction_class.py:309                 f"got {type(val).__name__}"
validators/validate_abstraction_class.py:310             )
```

Command:
```text
rg -n "false\)|denied entirely \(`false`\)|Each domain is either denied" SPEC.md validators profiles core || true
EXIT: 0
```

Output was empty.

**Q3 - F3 is mechanically closed**

Verdict: mechanically closed.

The mixed-tier bullet is absent from §13.9. The remaining three bullets are intact and complete:
```text
SPEC.md:1464 - Re-sign an instance document under an unchanged `closure_root`
SPEC.md:1465   after widening the kind descriptor's capability envelope. The
SPEC.md:1466   closure root MUST flip; if it does not, the implementer has
SPEC.md:1467   introduced the same papering-over hazard §12.7 enumerates.
SPEC.md:1468 - Treat a missing capability domain table as an implicit grant.
SPEC.md:1469   Missing-domain = denied; the failure mode is fail-closed.
SPEC.md:1470 - Encode capability declarations outside `[kind.capability_envelope]`
SPEC.md:1471   in ad-hoc kind-specific fields. The vocabulary is closed at the
SPEC.md:1472   domain level; novel domains require a SPEC amendment.
```

The §13.5 signing-tier deferral remains:
```text
SPEC.md:1366 - **The signing tier.** Whether the descriptor is signed under
SPEC.md:1367   technical-tier COSE_Sign1 or legal-tier CB-AdES (ETSI TS 119
SPEC.md:1368   152-1) is profile/runtime choice. Either tier carries the
SPEC.md:1369   closure root.
```

Relocation check:
```text
rg -n "Mix the technical-tier|mixed.*signing.*tier" SPEC.md validators profiles core || true
EXIT: 0
```

Output was empty. A broader repo search still finds the old text only in CHANGELOG/review records, not as normative spec text:
```text
CHANGELOG.md:553:    `27c1020`) read: "Mix the technical-tier and legal-tier
docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md:328:- Mix the technical-tier and legal-tier signatures on the same
docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/codex-fix-plan-r1.md:51:1470 - Mix the technical-tier and legal-tier signatures on the same
```

**Q4 - No collateral regressions**

Verdict: all three required commands exit 0. The required status lines are present.

Command:
```text
python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
EXIT: 0
last line: ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).
```

Command:
```text
bash validators/check_manifest_drift.sh
EXIT: 0
last line: OK -- manifest matches ontology + every count-mirror surface agrees
required line present: COUNT-MIRROR OK -- every surface agrees with reality.
```

The raw command output uses an em dash in both lines:
```text
COUNT-MIRROR OK — every surface agrees with reality.
OK — manifest matches ontology + every count-mirror surface agrees
```

Command:
```text
python3 validators/validate_ijb_conformance.py core/ontology.toml
EXIT: 0
first line: IJB CONFORMANCE VALIDATION PASSED
last line: - template_kind: ontology
```

The third command's required success string is present as the first line, not the last line.

**Q5 - CHANGELOG.md hygiene**

Verdict: entry exists and contains the required review-record pointers. The r1 replaced text is quoted sufficiently to identify all three replacements; the F1 quote is partial rather than the full four-line sentence. I do not treat that as a defect because `codex-review.md` itself only quoted the `SPEC.md:1324-1326` part as the F1 blocker, and the CHANGELOG cites that exact range. One citation nuance is recorded below.

The `[Unreleased] / Changed` entry begins at:
```text
CHANGELOG.md:521 - **SPEC §13 -- three independent-review blockers closed (r1 fix
CHANGELOG.md:522   commit; Codex r1 findings F1/F2/F3 + the deeper §2.4 contradiction
CHANGELOG.md:523   Claude surfaced during fix-plan synthesis).**
```

F1 entry and quote:
```text
CHANGELOG.md:524   - **F1 (high) -- §13.3 cited a nonexistent normative file.**
CHANGELOG.md:525     `SPEC.md:1324-1327` (commit `27c1020`) stated the full grant
CHANGELOG.md:526     sub-table schema was "declared by the
CHANGELOG.md:527     `core/kind-descriptor-kind.toml` descriptor's
CHANGELOG.md:528     `[kind.capability_envelope]` schema".
```

F2 entry and quote:
```text
CHANGELOG.md:537   - **F2 (medium) -- §13.3 prose / validator syntax mismatch on
CHANGELOG.md:538     domain denial.** `SPEC.md:1268-1270` (commit `27c1020`) said
CHANGELOG.md:539     "Each domain is either denied entirely (`false`) or scoped via
CHANGELOG.md:540     a sub-table."
```

F3 entry and quote:
```text
CHANGELOG.md:551   - **F3 (medium) -- §13.9 forbade signing-tier composition,
CHANGELOG.md:552     contradicting §13.5's scope-out.** `SPEC.md:1470-1472` (commit
CHANGELOG.md:553     `27c1020`) read: "Mix the technical-tier and legal-tier
CHANGELOG.md:554     signatures on the same artefact. Either tier carries the
CHANGELOG.md:555     closure root; both is declared posture, not engineering."
```

Persistent review pointers:
```text
CHANGELOG.md:567   - Persistent review evidence:
CHANGELOG.md:568     `docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md`
CHANGELOG.md:569     (Codex r1 -- original blockers); `.../raw_findings/grok.md`
CHANGELOG.md:570     (Grok r1 -- methodology-split unconditional approval);
CHANGELOG.md:571     `.../raw_findings/codex-fix-plan-r1.md` (Codex pre-implementation
CHANGELOG.md:572     fix-plan review -- `UNCONDITIONAL APPROVAL of fix plan`).
```

All three referenced review files exist in the workspace:
```text
docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md EXIT:0
docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/grok.md EXIT:0
docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/codex-fix-plan-r1.md EXIT:0
```

The r1 citations match `git show 27c1020:SPEC.md`:
```text
27c1020 SPEC.md:1268-1270 contains the false denial sentence.
27c1020 SPEC.md:1324-1327 contains the core/kind-descriptor-kind.toml sentence.
27c1020 SPEC.md:1470-1472 contains the mixed signing-tier bullet.
```

Citation nuance: `CHANGELOG.md:556` cites `SPEC.md:1363-1366` for §13.5's signing-tier deferral. That is correct for commit `27c1020`; at HEAD the same text is `SPEC.md:1366-1369` because this commit inserted three lines earlier in §13.3. Since the F3 paragraph is explicitly about the r1 contradiction, this is not a functional defect, but it is not explicitly annotated with `(commit 27c1020)` the way the F3 removed-text citation is.

**Q6 - No drift from the approved fix plan**

Verdict: no defective drift.

The fix-plan review did not contain a patch block with exact replacement prose; it approved content constraints:
```text
docs/reviews/.../codex-fix-plan-r1.md:76-81:
- `SPEC.md:1273-1288` names the closed domain set in prose table form, and `SPEC.md:1305-1307` states the `denied = true` / missing-domain fail-closed shape in the TOML example.
- `core/ontology.toml:633-650` declares the machine-readable closed domain vocabulary, including `extensible = false` and the note that missing sub-tables are denied.
- `validators/validate_abstraction_class.py:58-67` loads `capability_envelope.domain` from `core/ontology.toml`; `validators/validate_abstraction_class.py:300-321` rejects non-table domain entries and unknown domain names, then dispatches to the per-domain shape checkers.
- `validators/validate_abstraction_class.py:142-223` defines the structural shape of each known domain and accepts `denied = true` as the whole-domain denial form.
```

F1 implementation matches those constraints:
```text
SPEC.md:1324-1330 names `core/ontology.toml`, `validators/validate_abstraction_class.py`, this section's prose, and §2.4's recursion stop.
```

F2 implementation matches the approved syntax:
```text
SPEC.md:1268-1271 says each domain is a sub-table, denied via `denied = true` or scoped via fields.
```

F3 implementation matches the deletion plan:
```text
git diff 27c1020..7328dfd -- SPEC.md
```
shows deletion of:
```text
- Mix the technical-tier and legal-tier signatures on the same
  artefact. Either tier carries the closure root; both is
  declared posture, not engineering.
```

The only wording difference worth noting is that the final F1 prose says the table is "declared jointly" by ontology, validator, and prose. That is consistent with the plan's warning not to imply `core/ontology.toml` alone defines per-domain field schemas; no defect.

**Q7 - Independent re-scan**

Verdict: I found no new §13 blocker introduced by the r2 fix and no additional r1-style issue in §13.1-§13.10 that I would now classify as a concrete unresolved blocker.

Independent checks:
- §13.1 still makes the blocks optional at schema version 1.0.0 and says consumers cannot reject behavioural artefacts when the blocks are omitted (`SPEC.md:1229-1233`).
- §13.2 still defines the versioned abstraction class id and IJB tags (`SPEC.md:1243-1264`), with matching ontology shape at `core/ontology.toml:652-659`.
- §13.3 now aligns denial syntax, closed-domain vocabulary, validator, and fail-closed semantics (`SPEC.md:1268-1330`; `validators/validate_abstraction_class.py:58-67`, `:142-223`, `:300-322`).
- §13.5 still honestly scopes out wire format, attenuation calculus, signing tier, enforcement backend, WASM static observability, and runtime observation (`SPEC.md:1355-1379`).
- §13.9 is now limited to capability-envelope papering-over mechanisms (`SPEC.md:1460-1472`).

No findings with file:line + severity are raised for the §13 text.

**TERMINAL VERDICT**

CONCRETE UNRESOLVABLE BLOCKERS:

1. medium -- range-scope/ancestry blocker -- the requested review range is not the claimed two-file range. `git rev-list --parents -n 1 7328dfd` shows the r2 fix commit's parent is `0848d34c09973e137e2ca855e85bbd682eb67b9f`, not `27c10203d5b23a3750ee85f6fc50377234bc4303`; `git rev-list --count 27c1020..7328dfd` returns `2`; and `git diff 27c1020..7328dfd --stat` reports 43 files changed, including `arxiv-prep-agent-dag.toml` and `tools/claim-analysis-document-review-dag.toml`, not only `SPEC.md` and `CHANGELOG.md`. Unblocking action: either rebase/squash the r2 fix commit directly onto `27c1020` so the mandated range is the two-file SPEC/CHANGELOG patch, or issue a corrected review request that identifies the actual base `0848d34` and separates the unrelated arxiv-prep commit from this SPEC §13 review.

No implementation blocker is raised for F1/F2/F3: `SPEC.md:1324-1330` names the actual normative surfaces and §2.4 recursion stop; `SPEC.md:1268-1271` aligns denial syntax with `validators/validate_abstraction_class.py:300-310` and `:142-223`; `SPEC.md:1464-1472` removes the mixed signing-tier bullet while preserving the three capability-envelope papering-over bullets; and all three required validators exit 0.
