## Summary

U05 (commit ca50b2c) is **complete**. The single commit correctly flips ISS-001 to closed with a closing note whose core factual claims are verifiable against repo bytes (the 2026-05-24 tooling-sweep r1/r2 artefacts landed in 884f290, the exact codex blocker at `paper-arxiv-prep/compile-and-pdf-evidence.toml:27`, the five-file §12 sequencing gap, the absence of the two originally-proposed validators, and the live `validate_closure_root` step in `.github/workflows/validate.yml:178-199`). ISS-004 is accurately framed as a discipline gap, explicitly rejects new CI tooling per the in-session user correction, and points at the existing mechanism. Two low-severity documentation nits exist in the ISS-001 closing note (unverifiable "Listed in `MEMORY.md`" claim; "load on entry" phrasing that describes a host-environment detail with no committed supporting file). These do not rise to a concrete unresolvable blocker. The self-approval of ca50b2c itself falls inside the explicit carve-out for docs/issues/ process artefacts (see below). The review session supplies the independent persisted evidence required by policy.

## U05 — ca50b2c

- **U05-F1 low** — `docs/issues/2026-05-23-ISS-001-self-approval-discipline.md:225`: "Listed in `MEMORY.md`" is factually false. No file named `MEMORY.md`, `memory.md`, or equivalent exists anywhere under the repo root (confirmed via `find` and `ls` of all `*.md` at root + `docs/`). The entry lives only at the external Claude path recorded in `review_bundle.toml:43`. The claim appears in a durable committed artefact.
- **U05-F2 low** — same file:225: "Future initiator sessions load it on entry to this repo" describes host/Claude-specific auto-memory behaviour. `CLAUDE.md` (the only root-level agent guidance file) does not reference this entry or any auto-load convention. Not verifiable from committed bytes.
- **U05-F3 info** — same file:169-179: The "Acceptance criteria" section still lists the original Safeguard A/B CI-gate requirements verbatim. The closing note (190-243) explains the reframing but neither edits, strikes through, nor cross-references the now-obsolete list. Documentation debt, not a semantic defect in the closure.
- **U05-F4 info** — ca50b2c carries no `Reviewed-by:` trailer and was landed by the initiator (Werner Kasselman + Co-Authored-By: claude-opus-4-7). This is the exact recursive case the review bundle and prompt exist to examine (see Q4).
- Positive evidence (multiple locations): All five specific checks enumerated in `[bundle.questions.q1_iss001_factual_accuracy]` and the ISS-004 framing checks hold against live bytes (see Q1/Q3). The three changed files exactly match `bundle.units[0].changed_files`. `git show 884f290 --stat` confirms the r1+r2 artefacts described in the closing note. `validators/check_review_session_terminal.py` and `validators/check_commit_message.py` are absent at HEAD (ls + read attempts both fail). The closure_root validator step is present and active at `.github/workflows/validate.yml:178-199`.

Classification: **complete** (low-severity documentation findings only; no impact on the correctness of the ledger state or the counter-example record).

## Q1 — ISS-001 factual accuracy

**Verified with two low-severity caveats.**

- The 2026-05-24 tooling-sweep session is correctly identified as the worked counter-example (`docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels/` + `-r2/`).
- The codex r1 blocker citation is exact: `docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels/raw_findings/codex.md` (U02-F1) names `paper-arxiv-prep/compile-and-pdf-evidence.toml:27` as the first hard syntax break (bare key `(a)_...`, table-header-as-scalar, Unicode arrow in array), with both `taplo lint` and `tomllib` failures recorded.
- "Safeguards A and B as originally proposed are NOT built" is true: the two Python files named in the original body (lines 86-116) are absent at HEAD.
- The user's in-session correction is characterised consistently with the quote supplied in `review_bundle.toml:36` and the retrospective language the memory file itself uses ("when I correct the appearance of self-approval by writing elaborate CI gates (see how I framed ISS-001...)").
- Caveats (U05-F1/F2 above): the `MEMORY.md` claim and the "load on entry" phrasing are not supported by any committed file.

## Q2 — closing warranted

**Closing is warranted (reframed framing accepted).**

The original acceptance criteria (169-179) required two new CI artefacts that the user explicitly rejected during the session as over-engineering. The memory file (created in the same session) records the identical reframing: the fix is to dispatch the review via the existing rule, not to invent infrastructure as a substitute. The lived artefacts — r1 codex blocker on a real defect that self-approval would have shipped, r2 unanimous `unconditional_approval` (3/3), persisted raw findings + terminal_decision — are exactly the independent-verification outcome the symptom section of ISS-001 demanded. The closing note (190-243) accurately narrates that the original Safeguard A/B proposal was the initiator's framing and that the user correction changed the target. The note further states the correct recurrence-prevention rule: future self-approval re-opens ISS-001 rather than triggering the originally-proposed gates.

The AC list left verbatim in the file body is a documentation inconsistency (U05-F3), but it does not make the closure premature. The closing note itself functions as the audit record of the reframing and the counter-example. The policy in `tools/review-request-dag.toml:77-94` requires *persisted_review_evidence* from non-initiator reviewers; the r1/r2 sessions supply it. The argument in the closing note is therefore sound.

## Q3 — ISS-004 correctly framed

**Verified.**

- Symptom correctly identifies `47b6acd` (three new blessed-kind files without `closure_root`) + `d027178` (sentinels added two commits later), leaving the gate red on `main` in the intervening window. Matches codex r1 U01-F1 and the r2 acknowledged-findings item exactly (five files total: the three new + two pre-existing).
- Rule is stated as a human-enforceable pre-commit convention (run the already-shipped `validate_closure_root.py --discover .` locally; do not commit red). Optional per-user hook (Safeguard B) and memory entry (C) are correctly scoped as non-mandatory.
- Explicitly disclaims new CI tooling: "Per the user feedback captured in `[[memory/feedback_no_self_approval.md]]`: do NOT propose a CI gate as a substitute for the discipline. The validator already runs in CI (`validate.yml` line ~180)".
- Existing CI gate citation is accurate (the step at `.github/workflows/validate.yml:178-199` invokes `python3 validators/validate_closure_root.py --discover .` on every push and explains the blessed-kind discovery convention).

The framing honours the user's correction and treats CI red as symptom, not prevention.

## Q4 — self-approval recursion

**Position (a) is correct on the formal written rule; the spirit observation is real and is addressed by the existence of this review.**

Evidence from bytes:
- `docs/issues/README.md:7-10`: "Issues are NOT DAG-TOML documents ... They are project process artefacts." Explicit carve-out from §12.1.
- `memory/feedback_no_self_approval.md:10-12`: dispatch obligation is scoped to "SPEC.md, core/, profiles/, validators/, or any tracked DAG-TOML document". ca50b2c touches none of these.
- `tools/review-request-dag.toml:56-64` (policy.roles) and the instance rosters in both the tooling-sweep bundles name the initiator and exclude it from the *standard* reviewer set for DAG-TOML/spec-surface work. The same scope applies.
- The r2 `terminal_decision.toml:111-112` already anticipated exactly this boundary: "ISS-001 ... is closed-in-practice by this review ... but the issue file remains open. User decides whether to add a closed_by note."

Therefore landing ca50b2c without a *preceding* dispatched review did not violate the letter of the policy that ISS-001 itself exists to enforce. The commit is a pure process-artefact ledger update.

The spirit tension is genuine: the *content* of the commit is the authoritative declaration that "the discipline is now active" and that the 2026-05-24 tooling-sweep reviews constitute the proof. Independent scrutiny of the exact wording of that declaration is consistent with the ethos of ISS-001. The initiator surfaced the self-approval honestly; this review session (with fresh-context reviewers, bundle, and prompt) was created precisely to supply the missing persisted evidence for the boundary case. The recursion is therefore acknowledged and mitigated by the review that the bundle asks us to perform.

## Q5 — retcon check

**Pass.**

- The closing note does not claim "Safeguard A was the wrong framing" as a revision of history. It correctly attributes the reframing to the user's explicit in-session correction (the quote supplied in the bundle) and records that the initiator's original proposal in the issue body was the over-engineered version. The memory file created during the same session uses nearly identical retrospective language.
- ISS-004 and the closing note report the 47b6acd → d027178 sequence exactly as the r1 raw findings (codex U01-F1, grok §12 violation) and r2 acknowledged findings documented it at the time. No prior commit message is altered; no spec prose is rewritten.
- The r2 terminal even pre-figured the filing of ISS-004 (line 111). The audit trail is consistent and forward-referenced, not retconned.

Complies with `policy.process_checks.confirm_no_historical_dated_spec_retconned_without_link_or_correction_note` (the note and the review artefacts supply the link and the correction narrative).

## Process checks

- `confirm_active_user_migration_or_behavior_change_guidance`: confirmed. ISS-001 closing note + ISS-004 + `memory/feedback_no_self_approval.md` (and the parallel blessed-kind memory entry called for in ISS-004) give explicit, actionable future behaviour: dispatch via `tools/review-request-dag.toml` before treating spec/DAG-TOML changes as done; run `validate_closure_root.py --discover .` locally before committing any blessed-kind file; treat CI red as symptom of a discipline gap, not the fix; do not propose new infrastructure as a substitute for following the existing rule.
- `confirm_no_historical_dated_spec_retconned_without_link_or_correction_note`: confirmed (see Q5). The only evolution recorded is the intra-session reframing of ISS-001 itself, which is narrated with the user's quote and corroborated by the memory file created in the same session; no prior git history or spec text is altered.
- `confirm_claimed_tests_were_actually_run_with_command_output_and_status`: N/A for ca50b2c (pure documentation commit with no test or validator claims of its own). The underlying claims it records (the tooling-sweep reviews) were executed by the three reviewers with literal command output and exit status captured in the r1/r2 `raw_findings/*.md` and `terminal_decision.toml` (taplo, tomllib, `validate_closure_root.py --discover .`, full-repo sweeps, byte-identical checks). All three r2 reviewers re-ran the commands against the fix commit and recorded exit-0 results.

## Terminal verdict

`unconditional_approval`

The five questions are answered with direct, file:line-verifiable evidence against the actual repo bytes at HEAD and at 884f290. The two low-severity documentation inaccuracies in the ISS-001 closing note (non-existent `MEMORY.md` reference; host-specific "load on entry" phrasing) are real but do not constitute a concrete unresolvable blocker for a process-artefact ledger update whose core assertions (what was built, what the counter-example proved, the reframing, and the correct framing of ISS-004) are accurate. The self-approval of ca50b2c is inside the documented carve-out for docs/issues/ files. The existence of this independent review session itself supplies the persisted non-initiator evidence for the recursive boundary case. All required policy bases (`inspected_code`, `inspected_docs`, `persisted_review_evidence`) are met.
