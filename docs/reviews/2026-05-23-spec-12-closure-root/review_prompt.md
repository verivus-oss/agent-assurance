# Independent spec-change review — SPEC §12 closure-root rule

You are an independent reviewer dispatched per the workflow defined
in `tools/review-request-dag.toml`. This is a fresh / clean-context
session: you have no prior memory of this artefact. Treat any prior
claim about it as a hypothesis to verify, not as evidence.

## What you are reviewing

- **Repo:** `/srv/repos/external/verivus-oss/agent-assurance` (DAG-TOML
  public spec; main branch).
- **Commits under review (cumulative range, current HEAD):**
  - `bc2a7c5` — initial §12 fold (titled "SPEC §12: closure-root
    rule (brittleness propagation)").
  - `dc3a7b0` — follow-up resolving Grok round-1 F1 + F2.
  - `5c145c8` — round-2 resolving Codex round-1 (scope tightening,
    CI broadened, 8 missed sentinels patched).
  - `20c6207` — round-3 resolving Grok round-2 + Codex round-2:
    5 missed `examples/proof-hello-world/*.toml` sentinels;
    SPEC §12.1 carve-out rewritten to be value-keyed not
    purpose-keyed; SPEC §12.11 migration note added.
    **This is HEAD.**
  - Prior reviewer outputs are persisted under
    `docs/reviews/2026-05-23-spec-12-closure-root/raw_findings/grok.md`
    and `raw_findings/codex.md` — read them only AFTER you have
    formed your own independent view of HEAD. They are PRIOR ART,
    not ground truth.
- **Parent commit (pre-§12):** `638a90e`.
- **What changed (cumulative):** 78 files across three commits.

**This is a re-review round (U09 iterate-until-terminal).** Both
prior reviewers issued `CONCRETE UNRESOLVABLE BLOCKERS`, the
initiator implemented fixes, and the workflow's
`policy.approval.required_approval_bases` requires reviewers
independently verify the fixes. Your job in this round is:

1. Run the same 10 substantive questions against current HEAD.
2. After your own independent verification, open the prior raw
   finding for YOUR model (`raw_findings/grok.md` if you're Grok,
   `raw_findings/codex.md` if you're Codex). For each blocker /
   high-severity finding listed in your prior review, report
   `resolved` / `not_resolved` / `partially_resolved` with file:line
   evidence at HEAD. The expectation: every prior blocker should
   now be `resolved`.
3. Issue a fresh terminal verdict against HEAD. If everything is
   resolved AND no new blockers emerge, `UNCONDITIONAL APPROVAL`
   is the correct outcome. If anything remains, list the
   `CONCRETE UNRESOLVABLE BLOCKERS`. The commit folds the
  closure-root rule from
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/14-closure-root-spec-section-proposal.md`
  into normative SPEC text (new §12, §12.1–§12.10) plus the
  supporting infrastructure (new core ontology entries, a dedicated
  validator, CI wiring, and the canonical empty-closure sentinel
  applied to every conforming example, tier, kind descriptor,
  profile descriptor, and ontology).

Inspect the commit and its working tree with:

```bash
git -C /srv/repos/external/verivus-oss/agent-assurance show bc2a7c5
git -C /srv/repos/external/verivus-oss/agent-assurance diff 638a90e..bc2a7c5
git -C /srv/repos/external/verivus-oss/agent-assurance log --stat -1 bc2a7c5
```

## Inputs you have

Authoritative changed surfaces (open these directly, do not rely on
the initiator's paraphrase):

1. **SPEC.md §12** — entire new section (`SPEC.md` after the commit).
   Subsections §12.1 (rule), §12.2 (cascade-break), §12.3 (producer
   responsibility), §12.4 (consumer responsibility), §12.5
   (out-of-scope), §12.6 (worked example), §12.7 (forbidden
   mechanisms), §12.8 (deferred canonical concatenation),
   §12.9 (cross-section interactions), §12.10 (live-feed snapshot
   rule). Plus back-references in §2.7 (posture not in closure),
   §5 (closure-graph acyclicity), §11 (`source_sha256` is one input).
2. **`core/ontology.toml`** — two additions: the `cites_upstream`
   `[[relations]]` block, and the `closure_root.digest_algorithm`
   `[[attribute_vocabularies]]` block.
3. **`validators/validate_closure_root.py`** — dedicated reference
   validator: presence at document root, `<algo>:<hex>` shape,
   hex-length matches algorithm, MD5/SHA-1 rejected, empty-closure
   sentinel recognised.
4. **`.github/workflows/validate.yml`** — new CI step
   "Validate closure_root (SPEC §12) on every canonical example
   + tier" running `validate_closure_root.py` against every
   canonical TOML.
5. **Empty-closure sentinel applied** to every conforming TOML:
   every `examples/minimal-*.toml`, every
   `profiles/agent-assurance/tiers/*.toml`, every `*-kind.toml`,
   every `PROFILE.toml`, every `ontology.toml`. Sentinel value is
   `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
6. **Reference database updates** —
   `reference/database/{postgres,sqlite,duckdb}/seed.sql`,
   `reference/database/graph/schema.cypher`,
   `reference/database/rdf/schema.ttl` (regenerated),
   `reference/database/MANIFEST.toml` counts updated to
   `relation_predicates = 31`, `attribute_vocabularies = 38`,
   `attribute_values = 84`.

## Inputs you have AS PRIOR ART (NOT as ground truth)

- The original proposal at
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/14-closure-root-spec-section-proposal.md`.
  Every claim it makes is a HYPOTHESIS for you to confirm against
  the actual committed text, not to accept.
- The pre-existing spec ethos / brittleness narrative in
  `docs/research/2026-05-22-spec-foundations-research/08-follow-up-synthesis.md`
  (Stream B). Not ground truth — the question is whether the
  committed §12 text actually implements it.

## Workflow rules (binding, from `tools/review-request-dag.toml`)

These are non-negotiable. Read them once and apply them throughout.

1. **Verify against code and docs, not the initiator's summary.**
   Open the cited files. Check the cited lines. Run the cited
   commands. Do not accept a claim because the initiator says it is
   true.
2. **Search order:** `sqry` (AST-based semantic) first; literal /
   text search only for exact confirmation. The repo has a `sqry`
   MCP server with `mcp__sqry__*` tools — use them. For text
   matches, use `grep` / `rg` only to confirm a sqry hit.
3. **Every finding requires file + line + severity.** Verbatim
   quote the document part. No paraphrase. Severity ∈ {high,
   medium, low}.
4. **Process confirmations to report on:**
   (a) Active-user best-effort migration / behaviour-change
       guidance — does §12 (or the CHANGELOG entry, or the README
       update) tell existing producers how to migrate? Is the
       breaking nature of "every conforming document must now
       carry `closure_root`" surfaced?
   (b) No historical dated spec was retconned without a link /
       correction note. (§12 is additive; check this is honoured.)
   (c) All claimed tests were actually run, with command output
       and status. The CHANGELOG claims
       `validators/check_manifest_drift.sh` is green and that the
       new validator passes on every canonical example. RUN THEM:
       ```
       cd /srv/repos/external/verivus-oss/agent-assurance
       bash validators/check_manifest_drift.sh
       python3 validators/validate_closure_root.py \
         examples/minimal-*.toml \
         examples/minimal-review-readiness/*.toml \
         profiles/agent-assurance/tiers/*.toml \
         core/*-kind.toml core/ontology.toml \
         profiles/agent-assurance/*-kind.toml \
         profiles/agent-assurance/PROFILE.toml \
         profiles/agent-assurance/ontology.toml \
         profiles/disclosure/*-kind.toml \
         profiles/disclosure/PROFILE.toml \
         profiles/disclosure/ontology.toml
       ```
       Capture the exit code and the summary line.
5. **Forbidden approval bases:** stated intent, plan-compliance
   claims, "should be fixed" language. APPROVAL MUST BE BASED ON
   INSPECTED CODE, EXECUTED TESTS WITH OUTPUT, INSPECTED DOCS, AND
   PERSISTED REVIEW EVIDENCE.
6. **Terminal states:** issue either `UNCONDITIONAL APPROVAL` or
   a list of `CONCRETE UNRESOLVABLE BLOCKERS`. Do not approve
   conditionally. Do not approve subject to fixes.
7. **Persist your full review verbatim.** Your output IS the
   review record. Do not summarise — be specific and quote.

## Substantive questions you MUST answer

These are the spec-design questions the commit makes binding
commitments about. Each one has a yes/no/unverifiable answer
backed by file+line evidence.

1. **Universal-requirement consistency.** SPEC §12.1 makes
   `closure_root` REQUIRED on every conforming document. Does the
   committed text actually enforce that, including the
   `validators/validate_closure_root.py` behaviour? Are there any
   documents in the repo that would FAIL the validator if it were
   run today? (Run it and report.)
2. **TOML root-binding correctness.** §12.1 says `closure_root`
   MUST appear before the first `[table]` header so TOML binds it
   to the document root. Inspect at least three patched files
   (one minimal example, one tier, one kind descriptor) — does the
   inserted sentinel actually parse at the document root, not
   nested under `[meta]`? Confirm by running
   `python3 -c 'import tomllib; print(tomllib.loads(open(F).read()).keys())'`
   and check `closure_root` is a top-level key.
3. **Empty-closure sentinel correctness.** Is the sentinel
   `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
   actually `SHA-256("")`? Compute it independently:
   ```
   printf '' | sha256sum
   ```
   Report the result.
4. **Forbidden-algorithm enforcement.** The validator's
   `FORBIDDEN_ALGOS` list at `validators/validate_closure_root.py`
   includes `md5` and `sha1`. Construct a single-line TOML file
   `closure_root = "md5:abc"` and run the validator against it.
   Does it reject? Report the exit code and the failure message
   verbatim.
5. **Ontology additions are well-typed.** Inspect the new
   `cites_upstream` `[[relations]]` and
   `closure_root.digest_algorithm` `[[attribute_vocabularies]]`
   blocks in `core/ontology.toml`. Do they carry the IJB tags
   (`ijb_primitive`, `ijb_class` / `ijb_constraint_type`) required
   by SPEC.md §10 / `foundations/ijb/`? Run
   `python3 validators/validate_ijb_conformance.py core/ontology.toml`
   and report.
6. **Cross-section back-reference accuracy.** §12.9 / §2.7 /
   §5 / §11 cross-reference each other. Do they all point to
   the right subsection numbers? Quote each back-reference
   verbatim and check the target.
7. **Forbidden mechanisms list is closed and complete.** §12.7
   lists four forbidden papering-over mechanisms. Are they the
   right four for the brittleness ethos? Is anything obviously
   missing that a profile or runtime implementer could exploit?
8. **Deferred canonical concatenation (§12.8).** §12.8 says the
   exact byte-level canonical-concatenation algorithm is deferred
   to a future `schema_version`. Is this defensible? Does it
   leave a hole large enough that two conforming runtimes could
   compute different `closure_root` values for the same logical
   inputs, silently?
9. **Disclosure-profile interaction (§12.9 last bullet).** Is the
   "redaction does NOT flip upstream `closure_root`" rule
   correctly stated, and does it match the disclosure profile's
   own kind-descriptor semantics? Open
   `profiles/disclosure/disclosure-attestation-kind.toml` and
   confirm.
10. **Manifest-drift integrity.** Run
    `bash validators/check_manifest_drift.sh` and report exit
    code + output. Does it agree the ontology and reference DB
    are in sync?

## What I need from you

Produce a single review report with these sections, in order.

### 1. SESSION META

- Reviewer model name and version.
- Sandbox / approval posture for this session.
- MCP servers available.
- Commit / sha of the document you actually opened (re-derive,
  do not trust mine):
  ```
  git -C /srv/repos/external/verivus-oss/agent-assurance rev-parse HEAD
  ```

### 2. PROCESS CONFIRMATIONS

For each of the three checks in rule 4 above
(migration guidance, no retconning, tests-run-with-output), report:
`confirmed` / `refuted` / `unverifiable` with file+line evidence.

### 3. ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS

One subsection per question. For each:

- The question (one-liner).
- Your verdict (`confirmed` / `refuted_with_evidence` /
  `unverifiable`).
- The file+line evidence (verbatim quotes, no paraphrase).
- For executed commands: the exact command, its exit code, and the
  output (verbatim, fenced).

### 4. INDEPENDENT FINDINGS

Findings you uncovered that the substantive questions didn't
cover. Same shape: id (you assign), severity (high/medium/low),
file+line, verbatim quote, problem explanation, suggested fix.

### 5. TERMINAL VERDICT

One of:

- `UNCONDITIONAL APPROVAL — <one-line justification, anchored to a
  specific piece of inspected evidence>`
- `CONCRETE UNRESOLVABLE BLOCKERS:` followed by a numbered list,
  each blocker stating: what is wrong, where (file:line), what
  evidence proves it is wrong, and what would unblock it.

Do not output anything outside this five-section structure. Do not
preface with "Here is my review:" — start with section 1.

## Disagreement protocol

If you believe the commit is correct and the proposal document
(`14-closure-root-spec-section-proposal.md`) differs, you MUST
cite which version the COMMITTED §12 text follows and why the
divergence (if any) is intentional or accidental. Quote both.

If you cannot tell, mark the finding `unverifiable` and explain
which piece of evidence you would need to resolve it.

Begin.
