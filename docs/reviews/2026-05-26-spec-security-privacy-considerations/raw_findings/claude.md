# Independent Review — Claude (claude-opus-4-7[1m])

- Review session: `2026-05-26-spec-security-privacy-considerations`
- Base commit: `1c16bf9`
- Diff under review: `git diff -- SPEC.md CHANGELOG.md`
- Reviewer: Claude, called from `/srv/repos/external/verivus-oss/agent-assurance`
- Date: 2026-05-26

## 0. Method

I followed the order in `verification_report.toml [reading_order]`:

1. Read `verification_report.toml` (sha-binding `sha256:e3b0c44298…`,
   closures C01-C06, `[approval] required_bases` and
   `[approval] terminal_states`).
2. Read `review_bundle.toml` (units U01-U04 and the four required
   validation commands).
3. Read `review_prompt.md`.
4. Inspected the full diff:
   `git diff --stat -- SPEC.md CHANGELOG.md` →
   `CHANGELOG.md | 9 +++++++++`, `SPEC.md | 65 +++++++++…+++`,
   2 files changed, 74 insertions(+), 0 deletions.
   The full unified diff confirms the change is purely additive,
   appended at `SPEC.md` line 1490 after the prior §13 close, and
   inserted under `[Unreleased] / Added` in `CHANGELOG.md`.
5. Read SPEC.md:1485–1554 (the entire post-`§13` tail, including the
   new §14 and §15) and CHANGELOG.md:1–80 (the full `[Unreleased]`
   block plus the affected `Added` entry).
6. Ran the four required validation commands and captured exit
   status. None were skipped; none required substitution.

Tools used: `Read`, `Grep`, `Bash` (for `git diff`, `grep -c`, the four
validator commands, `taplo --version`, `ls`). No claim below relies on
Codex's summary, the verification report's stated intent, or
plan-compliance language. Every claim is grounded in observed file
bytes or observed command exit status.

## 1. Closure verification

### C01 — SPEC.md §14 header & framing

- `grep -n '^## 14\. Security Considerations' SPEC.md` →
  `1491:## 14. Security Considerations`.
  `grep -c '^## 14\. Security Considerations' SPEC.md` → `1`. The
  "exactly one hit" requirement is met.
- SPEC.md:1493–1498 reads, verbatim: *"DAG-TOML is a declarative
  format. It does not execute plans, verify signatures, decrypt
  artifacts, fetch registries, enforce sandbox policy, or decide
  whether a change may be deployed. Those are RUNTIME-SPEC concerns.
  A conforming validator checks structure, declared semantics, closed
  vocabularies, digest shapes, and the invariants defined by this
  spec."* All six "does not …" capabilities required by C01/2
  (execute, verify, decrypt, fetch, enforce, decide) are named.
- SPEC.md:1500–1502: *"Security-sensitive consumers MUST NOT treat a
  syntactically valid DAG-TOML document as proof that the described
  work is safe, authorized, complete, correctly reviewed, or
  correctly executed."* Satisfies C01/3 (uppercase MUST NOT + every
  enumerated property).

C01 status: **closed**. Evidence: SPEC.md:1491, 1493-1498, 1500-1502.

### C02 — §14 enumerated limits & threats

Bullets at SPEC.md:1504–1520:

- `closure_root` bullet (SPEC.md:1504–1506): names the field and
  states it "does not prove that the upstream evidence is true,
  complete, non-malicious, authorized, or current". ✓
- `[provenance]` bullet (SPEC.md:1507–1509): names the table and
  states it "does not establish trust in the source author, signing
  key, transport, or generation process". ✓
- "Signature fields, registry references, trust anchors, adapter
  contracts, assertion bundles, and gate decisions" bullet
  (SPEC.md:1510–1513): all six items from C02/1 enumerated, with the
  shape-checked-only-unless-runtime-verifies caveat. ✓
- Capability-envelope bullet (SPEC.md:1514–1517): *"They are not a
  sandbox. Runtimes that execute tools, agents, or adapters MUST
  enforce their own filesystem, network, process, environment, clock,
  random, IPC, and key-access controls."* All eight controls required
  by C02/2 appear in the requested order, and the MUST is upper-case.
  ✓
- Quarantine/reject bullet (SPEC.md:1518–1520): non-required but
  consistent with the rest of the section.

Threats sentence (SPEC.md:1522–1526): *"Threats to consider when
processing DAG-TOML include stale upstream evidence, forged or
replayed digests, incomplete closure roots, malicious examples copied
into operational systems, confused-deputy use of adapter or registry
references, validator/runtime disagreement, and author or agent
self-approval where independent review is required."* Cross-walked
against C02/3:

| Required threat                                  | Present at SPEC.md:1522-1526 |
| ------------------------------------------------ | ---------------------------- |
| Stale upstream evidence                          | ✓                            |
| Forged or replayed digests                       | ✓                            |
| Incomplete closure roots                         | ✓                            |
| Malicious examples                               | ✓ ("copied into operational systems") |
| Confused-deputy use                              | ✓ (adapter/registry refs)    |
| Validator/runtime disagreement                   | ✓                            |
| Self-approval where independent review required  | ✓                            |

C02 status: **closed**. Evidence: SPEC.md:1504-1520, 1522-1526.

### C03 — SPEC.md §15 header & examples

- `grep -n '^## 15\. Privacy Considerations' SPEC.md` →
  `1528:## 15. Privacy Considerations`.
  `grep -c …` → `1`. Exactly one hit. ✓
- SPEC.md:1530–1533: *"DAG-TOML documents often describe evidence,
  review state, provenance, costs, disclosure posture, and
  relationships between artifacts. Even when the documents contain no
  source code or runtime secrets, they can reveal sensitive
  information …"* Satisfies C03/2. ✓
- SPEC.md:1533–1536 enumerates: *"… internal process structure,
  reviewer identity, incident timing, dependency relationships,
  model/provider choices, operational costs, regulatory posture, or
  the existence of withheld evidence."* All eight categories from
  C03/3 are named. ✓

C03 status: **closed**. Evidence: SPEC.md:1528, 1530-1536.

### C04 — declared-posture vs access-control wording

- SPEC.md:1544–1545 names `[meta].confidentiality`, `[meta].license`,
  and `[meta].embargo_until` verbatim (cross-checked with
  `grep -n '\[meta\]\.confidentiality\|\[meta\]\.license\|\[meta\]\.embargo_until' SPEC.md`
  → lines 1544 and 1545). C04/1 ✓.
- SPEC.md:1545: *"… fields are declared posture, not access
  control."* C04/2 ✓.
- SPEC.md:1546–1549: *"Publishing a document with `confidentiality =
  \"restricted\"`, `\"confidential\"`, `\"trade-secret\"`, or
  `\"embargoed\"` does not protect the document's contents.
  Repositories, runtimes, and distribution systems MUST enforce
  access control outside this format."* C04/3 ✓ (all four
  confidentiality values listed, plus the MUST sentence at the
  required-fields edge).

C04 status: **closed**. Evidence: SPEC.md:1544-1549.

### C05 — CHANGELOG entry

- `grep -n 'SPEC.md §14 / §15' CHANGELOG.md` →
  `58:- **SPEC.md §14 / §15 — explicit security and privacy`. C05/1
  requires a hit under `[Unreleased]`. The bracketed-section header
  `## [Unreleased]` is at CHANGELOG.md:8, and the next top-level `##`
  header after the new entry does not appear until well past line 65;
  the awk-bounded scan `awk 'NR>=8 && NR<=66' CHANGELOG.md` shows the
  entry lives strictly under the `[Unreleased]` heading with no
  intervening release header. ✓
- CHANGELOG.md:59–60: *"Added top-level `Security Considerations` and
  `Privacy Considerations` sections to the normative specification."*
  C05/2 ✓ (both phrases present).
- CHANGELOG.md:64–65: *"… RUNTIME-SPEC boundaries. No file-shape or
  validator behaviour changes."* C05/3 ✓.

C05 status: **closed**. Evidence: CHANGELOG.md:8, 58-65.

### C06 — required validation commands

I ran the four commands exactly as listed in
`verification_report.toml [closures] id = "C06"` and
`review_bundle.toml [bundle.validation_required]`:

1. `taplo lint` →
   - Exit status: `0`
   - Output: `INFO taplo:lint_files:collect_files: found files
     total=194 excluded=0 …` — 194 TOML files lint-clean; no error
     lines emitted. SPEC.md and CHANGELOG.md are markdown and are
     correctly excluded from the collection.
2. `python3 validators/validate_closure_root.py --discover .` →
   - Exit status: `0`
   - Output: `CLOSURE-ROOT VALIDATION PASSED (75 file(s)).`
3. `bash validators/check_manifest_drift.sh` →
   - Exit status: `0`
   - Tail of output:
     `COUNT-MIRROR OK — every surface agrees with reality.` and
     `OK — manifest matches ontology + every count-mirror surface
     agrees`.
   - All entity, relation, attribute-vocabulary, and triple counts
     match their declared expected values across the Python/Rust/Go
     mirrors.
4. `python3 validators/validate_profile_descriptor.py --repo-root .
   profiles/agent-assurance/PROFILE.toml profiles/disclosure/PROFILE.toml
   profiles/cost/PROFILE.toml` →
   - Exit status: `0`
   - Output: `PROFILE DESCRIPTOR VALIDATION PASSED` (3 files
     validated, 3 profiles in resolution set).

C06 status: **closed**. Evidence: shell exit codes and final-line
output for each command, captured above.

## 2. Unit classification (U01-U04)

| Unit | Name                                                        | Closures | Classification | File/line evidence                |
| ---- | ----------------------------------------------------------- | -------- | -------------- | --------------------------------- |
| U01  | security-considerations-section-present-and-specific        | C01+C02  | **complete**   | SPEC.md:1491-1526                 |
| U02  | privacy-considerations-section-present-and-specific         | C03+C04  | **complete**   | SPEC.md:1528-1549                 |
| U03  | changelog-records-change                                    | C05      | **complete**   | CHANGELOG.md:8, 58-65             |
| U04  | validation-remains-green                                    | C06      | **complete**   | exit-0 output for the 4 commands  |

No unit is incomplete or unverifiable.

## 3. Additional sanity checks (non-required, but useful)

- Diff blast radius: `git diff --stat -- SPEC.md CHANGELOG.md`
  reports 74 insertions and 0 deletions. Inspecting the unified diff
  confirms a single hunk in SPEC.md at line 1487 onward and a single
  hunk in CHANGELOG.md at line 55 onward; nothing in either file was
  removed or rewritten. This rules out incidental drift outside the
  intended scope.
- The change does not touch any `examples/` file, so the CI
  "no bare `kind =` in examples" invariant is not engaged. No new
  `template_kind` is introduced; the manifest-drift run above
  confirms ontology/profile counts are unchanged.
- New section text contains no internal-source-tree path leaks
  (`/srv/repos/…/private` style strings); the only paths it
  references are field names (e.g. `[meta].confidentiality`,
  `closure_root`, `[provenance]`) and the documentation pointer
  inside §13 that was already present.
- All four required validation commands also exercise content this
  diff does not change. They are still informative because a careless
  prose edit can break taplo's UTF-8 / no-BOM assumption or wedge a
  drift-check checksum; both kept passing here.

## 4. Findings

**None.** The diff is prose-only, additive, scoped strictly to
SPEC.md §14/§15 plus a matching `[Unreleased] / Added` CHANGELOG
entry, and every literal requirement enumerated by closures C01-C05
is present at the cited line numbers. Closure C06's four validator
commands all returned exit status 0 with the success strings shown
above.

Severity scale not applicable: no defect was found.

Inspected files: `SPEC.md`, `CHANGELOG.md`, plus the four review
artefacts under
`docs/reviews/2026-05-26-spec-security-privacy-considerations/`.

Executed commands (all exit 0): `taplo lint`,
`python3 validators/validate_closure_root.py --discover .`,
`bash validators/check_manifest_drift.sh`,
`python3 validators/validate_profile_descriptor.py --repo-root .
profiles/agent-assurance/PROFILE.toml profiles/disclosure/PROFILE.toml
profiles/cost/PROFILE.toml`, plus structural greps
(`grep -n '^## 14\. Security Considerations' SPEC.md`,
`grep -n '^## 15\. Privacy Considerations' SPEC.md`,
`grep -n 'SPEC.md §14 / §15' CHANGELOG.md`,
`grep -c …` for hit-count) and `git diff --stat`.

## 5. Terminal state

**unconditional_approval**
