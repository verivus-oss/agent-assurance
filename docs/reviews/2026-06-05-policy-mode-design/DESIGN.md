# Design: declarative repository policy enforced by the DAG-TOML validators

Session: 2026-06-05-policy-mode-design
Status: DESIGN PHASE — no implementation exists yet. Every section below is
labelled VERIFIABLE (an artifact exists to check) or UNASSESSABLE (prospective).

## 1. Problem

Two incidents this week demonstrated the same failure shape in this
repository:

1. AI attribution stamps (Co-authored-by trailers, "Generated with" footers)
   reached the public default branch despite a standing prohibition, because
   the prohibition lived in conversation and convention, not in a gate.
   Remediation required a history rewrite and a GitHub support ticket.
2. Pull requests #21, #22, #24 and #25 modifying spec surfaces merged
   without the review discipline that CONTRIBUTING.md declares mandatory
   ("No initiator self-approval", persisted independent review evidence
   under docs/reviews/), because that discipline is — in CONTRIBUTING.md's
   own words — "enforced by convention, not by new infrastructure."
   Precisely: #22, #24 and #25 carry no docs/reviews/ bundle at all; #21
   carries docs/reviews/2026-05-29-wp1-validator-ports/ authored by the
   initiator (a working record, not independent approval evidence); every
   approval came from a second account of the same person; and #23 remains
   OPEN, unmerged.  (Round-1 review corrected an earlier overstatement
   here — see round1_grok_review.md finding 1 and round1_codex_review.md
   finding 4.)

VERIFIABLE: CONTRIBUTING.md "Review Discipline" section;
`git show --name-only` on the merge commits of #21/#22/#24/#25;
`gh pr view 23 --json state`; tools/review-request-dag.toml
`[policy.approval]`. Reviewers should check all of these.

## 2. Design intent (VERIFIABLE: graded against §1 evidence and the artifacts in this bundle)

Repository policy must be:

- **Declared in DAG-TOML**, the repository's own format, not in CI YAML or
  shell. (`werner-voice.toml` in the private estate and the language manifests
  in aivcs are prior art for declarative policy-as-TOML with scannable
  blacklists; the public spec's `contract-declaration` kind already carries
  the needed field shapes.)
- **Enforced by the validators** (Rust primary, Go primary, Python reference),
  the same parsers that already gate every push, so the rules inherit the
  conformance-corpus parity guarantees.
- **Self-hosting without self-judgement**: a PR must never be judged by the
  validator or policy version it itself proposes (N−1 rule, §6).

## 3. The policy document (VERIFIABLE: draft at policy/REPO_POLICY.toml)

`policy/REPO_POLICY.toml` is an instance of the existing core kind
`contract-declaration` (no spec change required for the document itself).
Policy-relevant contracts carry the machine-scannable fields already
conventional in this ecosystem:

- `applies_to` — which input streams the contract scans. Initial vocabulary:
  `commit_messages`, `pr_title`, `pr_body`.  (`tracked_files` is defined but
  deliberately unused in v1 — see §3a.)
- `blacklist_regex` — patterns whose match is a violation.
- `match_mode = "regex"` and `density_threshold = 0` — zero tolerance.
- `exempt_paths` — glob list; at minimum the policy file itself and
  `conformance/cases/**` fixtures, which must be allowed to contain the
  banned strings in order to test them.

Contract 1 — `REG:NO-AI-ATTRIBUTION`: no AI/LLM attribution from ANY model or
tool: `Co-authored-by:` trailers naming an AI or AI-vendor noreply address,
"Generated with <tool>" footers. Trailer patterns are line-anchored so prose
that *discusses* a trailer does not match.  The generated-with pattern is
phrase-scoped (not line-anchored) after round-2 review showed anchor
windows miss title-tail stamps; the accepted trade-off is that quoting
the literal phrase adjacent to a vendor name in a scanned stream rejects
— cite the short SHA instead of quoting (fixtures pin both directions).

### 3a. Why tracked_files is out of scope for v1 (round-1 finding)

Both round-1 reviewers independently demonstrated that scanning tracked
files false-positives on surfaces that legitimately QUOTE banned strings:
this session's own VERIFICATION_REPORT.md test table, and even the comment
header of .github/workflows/no-ai-attribution.yml.  v1 therefore scans only
the three event streams (commit messages, PR title, PR body), where quoting
is rare and a rejection is cheap to appeal by rewording.  `exempt_paths`
stays in the policy file, inert, so a future tracked_files revival inherits
the known quoting surfaces instead of rediscovering them.

Contract 2 — `REG:NO-INITIATOR-SELF-APPROVAL`: a terminal gate-decision
artifact must record at least one reviewer identity distinct from the
initiator identity supplied at scan time (`--initiator`). This converts
CONTRIBUTING.md's convention into a checkable predicate. (The GitHub PR
author is outside the validator's reach; the thin shim supplies it. §7.)

## 4. Regex dialect: the cross-implementation constraint

The three validators use three regex engines: Rust `regex` crate, Go RE2
(`regexp`), Python `re`. The policy file may therefore use only the COMMON
SUBSET, declared normatively in the policy schema section and enforced by
conformance fixtures:

- Permitted: literal text, character classes, alternation, `^`/`$` with
  `(?im)` leading flags, `\b`, `\s`, bounded repetition.
- Forbidden: lookahead/lookbehind (RE2 has none), backreferences (RE2 has
  none), Unicode property classes (dialect-divergent).

A policy file using a forbidden construct must FAIL validation in policy mode
(fail-closed on undecidable rules), in all three implementations.  Note
(round-1 gemini finding): Rust and Go reject lookaround/backreferences at
compile time, but Python's `re` accepts them natively — the Python reference
validator must therefore implement the dialect restriction as an explicit
syntax check, and the §8 lookbehind fixture exists precisely to prove all
three implementations exit 2 on the same input, not just the two whose
engines refuse it.

UNASSESSABLE: enforcement of the dialect restriction is future code. The
restriction itself is checkable now against the three engines' documented
capabilities (reviewers: confirm RE2 lacks lookaround/backreferences and that
the chosen subset parses in all three engines).

## 5. Validator policy mode (UNASSESSABLE: future code; contract below is the spec)

New mode in all three implementations:

```
dagtoml-validate-rs --repo-root . --mode policy --policy policy/REPO_POLICY.toml \
    [--scan-stdin <stream-label>] [--scan-file <path>]... [--initiator <login>]
```

- `--scan-stdin commit_messages` scans stdin as the named stream; the caller
  pipes `git log --format=%B <range>`. The validator runs no git commands and
  no network: pure function of (policy, streams, files, flags).
- `--law-root DIR` (round-1 gemini finding): every law document — the policy
  file itself and ANY file the policy references (e.g. the gate-decision kind
  descriptor, tools/review-request-dag.toml named in verified_by) — resolves
  against --law-root, NEVER against --repo-root.  --repo-root scopes only the
  SUBJECT inputs being scanned.  Without this separation a PR could weaken a
  law-referenced document in its own tree and be judged by its own weakening.
- Each contract applies only to streams/paths matching its `applies_to` and
  not matching `exempt_paths`.
- Exit 0 = no violation; exit 1 = violation (each reported as
  `REG:<id>: <stream-or-path>:<line>: matched <pattern>`); exit 2 = unusable
  policy (parse error, forbidden regex construct, unknown applies_to value).
- Parity requirement: identical verdicts across rs/go/py for every fixture in
  the conformance corpus (§8).

### 5a. Structural contract algorithm (REG:NO-INITIATOR-SELF-APPROVAL)

For contracts with `match_mode = "structural"` and
`applies_to = ["gate_decision_artifacts"]`, policy mode evaluates each
`--scan-file` whose document has `template_kind = "review-gate-decision"`
— the artifact class this repository actually persists as session gate
decisions (round-2 grok finding corrected an earlier binding to fields
that do not exist; see docs/reviews/2026-05-23-spec-12-closure-root/
gate_decision.toml for a live instance):

1. Read `[roster].reviewers_completed` (array of reviewer identities).
2. If the array is empty or absent, exit 1 (fail closed: an
   unattributable approval is not evidence).
3. If `--initiator` was supplied and every completed reviewer equals the
   initiator (case-insensitive comparison), report
   `REG:NO-INITIATOR-SELF-APPROVAL: FILE: initiator is the sole completed
   reviewer` and exit 1.
4. If `--initiator` is absent, structural contracts are skipped and a
   warning names them (local advisory runs); CI always supplies it.

Deliberately out of scope for contract 2 v1: `terminal_decision.toml`
working files and the `gate-decision` (INV06 provider-quartet) kind —
one artifact class per contract; widening is a policy edit, not a code
edit, once the kind vocabulary settles.

### 5b. Pattern-dialect interplay with the placeholder gate (round-1 catch)

The repository's existing contract validators ban `<`/`>` placeholder
markers in field values, which collides with regex literals needing angle
brackets.  Rule: policy patterns MUST be written angle-bracket-free (e.g.
match e-mail local parts via `[^@\s]*@` rather than bracket-delimited
forms).  This is a real constraint discovered when the draft's own
validators rejected a bracketed pattern; it belongs in the policy-authoring
guidance and in a conformance fixture.

## 6. Self-hosting: the N−1 rule (UNASSESSABLE: future CI step; design here)

The gate never runs the PR's own validator or policy. CI checks out the PR's
tree as the *subject*, and separately checks out `main`'s `tools/`,
`validators/`, and `policy/` as the *law*; builds main's validators; scans the
PR's commit-message range, PR title, and PR body with main's policy.
A PR may propose changes to the law; it is judged by the law already merged.
Endgame variant (out of scope for v1): pin the law to the last release
artifact instead of main.

Bootstrap (revised after round-1 attack): stage-0 is the one window where a
single PR could land a permissive law judged by nobody.  Mandate: a TWO-PR
bootstrap. PR-A lands ONLY `policy/REPO_POLICY.toml` plus the validator
policy mode, with a diff scope capped to `policy/`, `validators/`,
`tools/dagtoml-validate-{rs,go}/`, and `conformance/`; it is judged by the
existing gates plus this review process. PR-B, judged by PR-A's now-merged
law via N−1, lands the CI shim and required-check wiring.  A stage-0 PR
touching anything outside the capped scope, or weakening `exempt_paths` /
`blacklist_regex` relative to this reviewed design, fails review by
definition; reviewers compare against this document.  The scope cap is
also mechanical, not only review-borne: PR-A's CI includes a plain step
asserting `git diff --name-only origin/main...HEAD` is a subset of the
allowlisted paths, judged by the existing (pre-policy) gates.

## 7. The thin shim (UNASSESSABLE: future CI step; full text below is the spec)

The only YAML is a fixed invoker, expected to never change as rules evolve.
Trigger (round-1 gemini finding): the workflow MUST run on
`pull_request_target`, not `pull_request` — `pull_request` executes the PR
branch's copy of the workflow file, letting a PR rewrite the gate to exit 0;
`pull_request_target` executes main's definition.  Under
`pull_request_target` the PR tree is checked out AS DATA ONLY (scanned,
never executed, never built); the only code built or run is main's law
(validators + policy), which is exactly the N−1 rule expressed in CI
permissions.  The shim:

```sh
git worktree add /tmp/law origin/main
(cd /tmp/law && cargo build --release --manifest-path tools/dagtoml-validate-rs/Cargo.toml)
git log --format=%B "$BASE..$HEAD" \
  | /tmp/law/tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs \
      --repo-root . --mode policy --policy /tmp/law/policy/REPO_POLICY.toml \
      --scan-stdin commit_messages --initiator "$PR_AUTHOR"
gh pr view "$PR" --json body --jq .body \
  | ... --scan-stdin pr_body --initiator "$PR_AUTHOR"
gh pr view "$PR" --json title --jq .title \
  | ... --scan-stdin pr_title --initiator "$PR_AUTHOR"
```

Wired as a REQUIRED status check in the ruleset: no green, no merge. The
local mirror is `.githooks/commit-msg` invoking the Python reference
validator with the same policy file (stdlib-only, no build step), documented
in CONTRIBUTING.md; CI remains the backstop when the hook is not installed.

### 7a. The synthesized merge-commit surface (round-1 finding)

A squash/merge commit message is synthesized by GitHub from the PR title
and commits, and lands on main WITHOUT passing through the PR-range scan
(demonstrated in round 1: merged subject `... (#25)` differs from the PR
head commit).  Scanning `pr_title` (above) covers the squash subject
source; the body source is the scanned commit list.  Backstop: the
existing push-event workflow (§7b) scans what actually landed.

### 7b. Coexistence and migration with .github/workflows/no-ai-attribution.yml

main already carries a grep-based attribution workflow (#24/#25).  Plan:
(stage 1, with PR-B) keep it as the push-event backstop on main while the
policy gate takes over PR-side enforcement; (stage 2) replace its grep with
an invocation of the released validator in policy mode on push events, so
both gates share `policy/REPO_POLICY.toml` as the single rule source;
(stage 3) retire the grep only when the conformance corpus covers every
pattern the grep had.  At no point do divergent rule sets run silently;
stage boundaries are explicit PRs.

## 8. Conformance corpus extension (UNASSESSABLE: future fixtures; shape below)

`conformance/cases/policy/` requires a REAL runner extension, not a small
one (round-1 corrected an understatement here): runner.py today registers
single-TOML-fixture kinds and treats exit 2 as infrastructure failure,
while policy mode needs (policy file + input stream/file + flags) cases
and exit 2 as an EXPECTABLE verdict.  Case schema: each case directory
holds `case.toml` (declares policy path, input file, stream label,
optional initiator, `expected_exit` 0|1|2, optional `error_contains`);
the runner grows a policy-kind branch that builds the invocation from
`case.toml` and asserts the exit code per-case instead of assuming the
exit-2-is-infrastructure convention.  Minimum set:

- stamped commit message (trailer) → all three reject
- "Generated with ..." footer line → all three reject
- prose *discussing* a trailer mid-sentence → all three accept
- policy file using lookbehind → all three exit 2 (fail-closed)
- exempt path containing banned string → accept
- gate-decision artifact with reviewer == initiator → reject (REG contract 2)
- gate-decision artifact with no recorded reviewer → reject (fail closed)
- angle-bracket regex literal in policy → rejected by contract validators
  (the placeholder-gate interplay of §5b)
- revert commit quoting a stamped message → REJECT, documented as intended:
  a revert that re-lands a stamped trailer line still lands a stamped
  trailer line; reword the quote to cite the short SHA instead

## 9. Spec self-application chapter (UNASSESSABLE: future spec text)

A new informative section in spec.md: "Self-application", documenting the
N−1 rule and the policy-mode pattern for any repository that hosts DAG-TOML
artifacts and wants the format to govern its own host. This design document
is the draft source for that section.

## 10. Critical decisions (VERIFIABLE: each maps to a critical_decisions entry in the DAG)

1. Reuse `contract-declaration` rather than minting a new `policy` kind, and
   reuse the core ontology's existing `REG:` (regulation) id prefix rather
   than minting `POL:` — zero spec-surface change for v1; revisit if policy
   fields outgrow them.  (The validators themselves rejected an undeclared
   `POL:` prefix during drafting, which is recorded in the verification
   report as evidence the ontology binding works.)
2. Validator stays pure (no git/network); the shim feeds it streams — keeps
   the parity story testable and the YAML permanently dumb.
3. Common-subset regex dialect, enforced fail-closed at exit 2.
4. N−1 law selection from main, release-pinning deferred.
5. Coverage is the pattern list itself, maintained in the policy file: a
   vendor/tool alternation (identical across the trailer and generated-with
   patterns), generic `ai`/`assistant` name tokens, an automation-shaped
   e-mail local-part heuristic, and vendor noreply domains.  Extending
   coverage is a policy edit, never a code edit.  Bare `agent`/`bot` name
   tokens are excluded (human-name false positives, round-2 finding).

## 11. Out of scope for v1 (VERIFIABLE: scope statement, graded for completeness)

- Scanning historical commits (the gate examines only the incoming range).
- Fleet rollout beyond this repository (the 28-repo grep workflow stays
  as-is until this lands and proves itself here).
- PR-body rewriting or auto-fixing; the gate only rejects.

## 12. Risks (VERIFIABLE: register, graded for completeness)

- R1: regex dialect drift between engines despite the subset → mitigated by
  conformance fixtures (§8) and exit-2 fail-closed on undecidable patterns.
- R2: exemption globs too broad → mitigated by listing exemptions explicitly
  in the policy file where they are reviewable, never as validator defaults.
- R3: stage-0 window (§6 bootstrap note) — one PR judged by the old gates.
- R4: `--initiator` is shim-supplied and therefore spoofable locally; the
  authoritative value comes from CI context, and local runs are advisory.
