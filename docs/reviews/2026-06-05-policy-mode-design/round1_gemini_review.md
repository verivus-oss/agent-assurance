# Round 1 review — Gemini (job be4c15e7, 2026-06-04T16:35Z)

VERDICT: REVISE

Verified: C1, C2, C3, C4, C5, C7 (each re-executed). C6 partially (its claim "PRs #21–#25 merged without any docs/reviews/" is itself inaccurate per codex/grok evidence: #21 carries an initiator-authored bundle, #23 is OPEN; superseded by corrected DESIGN.md §1).

Findings:
1. tracked_files false positives: "generated with" pattern's 12-char prefix window matches .github/workflows/no-ai-attribution.yml:4 and the verification report's quoted PASS line; gate would fail on the repo's own codebase. [Already addressed in round 2: applies_to narrowed to streams; §3a.]
2. Revert commits quoting historically stamped messages are flagged by the commit_messages stream — breaks standard git-revert flows for those commits. [Round-2 position: intended fail-closed behaviour, documented with fixture + reword-the-quote guidance; to be re-argued before Gemini in round 2.]
3. NEW — N−1 bypass via --repo-root: the shim loads the policy from /tmp/law but the validator resolves workspace-referenced law files (e.g. tools/review-request-dag.toml named by contract 2) against --repo-root = the PR checkout; a PR can weaken forbidden_approval_bases in its own branch. N−1 broken for any law file resolved from the subject tree.
4. NEW (from unassessable critique, structural) — on: pull_request executes the PR branch's workflow definition; a PR can edit the gate workflow to exit 0. The design must mandate pull_request_target (main's workflow definition) with PR tree checked out as data only.
5. Python re natively supports lookaround: the py validator must implement the dialect restriction manually; named artifacts: py syntax-restriction code + exit-2 lookbehind fixture.

Named artifacts required to make UNASSESSABLE sections assessable: rs CLI arg-parsing impl; policy.yml on pull_request_target; conformance policy fixtures + runner branch; spec.md self-application text.
