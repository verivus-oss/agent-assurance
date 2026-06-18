# Verification report — harden the `no-ai-attribution` gate

**Date:** 2026-06-18
**Change:** `.github/workflows/no-ai-attribution.yml` (+57 / −12)
**Reproducible evidence:** `./verify.sh` (19 assertions, all PASS)
**Cross-LLM review:** UNCONDITIONAL APPROVAL from both reviewers at HEAD
`200fdb9` (Codex r3 + Grok r3). Codex raised two evidence-backed blockers on the
push fallback (tip-only, then stale-local-$DEF); both fixed and regression-tested
(see §6).

This report is the corrective-program spec. Every claim below is recomputable
from the repository with the commands shown; reviewers must verify against the
code and real git history, not against this prose.

---

## 1. Problem this corrects (how AI attribution reached the public repo)

Investigation of the actual GitHub state (`gh api`, `git`):

1. **Branch commits carried the trailer.** PRs #21 (`fix/2026-05-29-five-weaknesses`)
   and #22 (`feat/dagtoml-conformance-corpus`) contained commits authored as
   `Werner Kasselman <werner@verivus.com>` with `Co-Authored-By: Claude Opus 4.8
   <noreply@anthropic.com>` trailers — e.g. `4a8668c`, `5bc75c9`, `5ca3666`,
   `cf5b7c0`. Source: Claude Code's default commit convention in prior sessions.
2. **Squash-merge propagated it to `main`.** Both PRs were **squash-merged** on
   2026-06-04 (14:34 / 14:40 UTC). GitHub auto-appends co-author trailers into
   the squash commit body, so the squash commits `a3e86f6` (#21 `merge_commit_sha`)
   and `b8d7a026` (#22) landed carrying the trailer. Both still show it today.
3. **No gate existed yet.** The `no-ai-attribution` workflow (PR #24) merged at
   2026-06-04 **15:09** — ~30 min *after* #21/#22. The client-side global
   `commit-msg` hook (`~/.config/git/hooks/commit-msg`) was added **2026-06-05**.
   Both defenses postdate the leak.
4. **`main` was later rewritten clean.** `a3e86f6`/`b8d7a026` are no longer on
   `main`; they were replaced by `aa5a0b2` (#21) and `57b1350` (#22),
   `verivusOSS-releases`-authored, no trailer. `git log origin/main` →
   **0** `Co-Authored-By: Claude` commits; GitHub commit search on the default
   branch → 0; the contributors API lists only `verivusOSS-releases`,
   `verivus-open`, `dependabot[bot]`, `verivusai` (no Anthropic/Claude account).
5. **Residue persists on PR refs.** The original commits remain reachable via
   `refs/pull/21/*` and `refs/pull/22/*` (PR "Commits" tab, direct SHA). These
   are **not deletable self-serve** — only GitHub Support can purge them. This
   is out of scope for this code change and is tracked separately.

**Conclusion:** `main` is clean; the recurrence path is what needs hardening.

## 2. Defense-in-depth model (post-change)

| Layer | Where | Trigger | Status |
|-------|-------|---------|--------|
| Client `commit-msg` hook | `~/.config/git/hooks/commit-msg` (global) | local `git commit` | exists since 2026-06-05 (machine-local; not shared) |
| Server gate (this change) | `.github/workflows/no-ai-attribution.yml` | `push` + `pull_request` | hardened here |
| Branch protection | repo setting | required-check enforcement on merge | **NOT configured** — see §5 |

The server gate is the only shared, machine-independent control. This change
makes it a strict **superset** of the client hook (broader patterns + an
identity check the hook lacks).

## 3. The change

Two independent checks over the same introduced-commit range. Range selection:
`base..head` on `pull_request`; `before..after` on `push` with a usable
`before`; and — when `before` is null/missing (new-branch push, force-push) —
the **introduced range relative to the default branch**, trusting ONLY the
authoritative remote-tracking ref (`refs/remotes/origin/$DEFAULT_BRANCH..$AFTER`)
and otherwise failing **closed** with a full scan of `$AFTER`. A *local* branch
of the default name is deliberately NOT trusted (it can be stale/divergent and
silently exclude introduced commits). The earlier `-n 1 $AFTER` fallback was a
fail-open vector (scanned only the tip) — see §6. Both checks must pass; `rc`
accumulates so both report before exit.

- **(a) MESSAGE** — `co-authored-by:.*(claude|anthropic)|generated with.*claude`
  over `%h %s%n%b`. Catches branch-commit trailers *and* the trailer GitHub
  auto-appends into squash commits.
- **(b) IDENTITY** *(new)* — `anthropic|claude` over `%h|%an|%ae|%cn|%ce`.
  Catches a commit *authored or committed* by a Claude/Anthropic identity
  (e.g. `noreply@anthropic.com`) even when the message is clean.

**Scope guard:** the gate inspects commit **messages and identities only,
never file content** — the spec legitimately uses `anthropic`/`claude` as
domain terms (`proposing_provider_id = "anthropic"` in `validate.yml:531`), so
a content scan would false-positive on the spec itself. Comparison vs the
client hook pattern (`co-authored-by:.*(claude|noreply@anthropic)|generated
with \[?claude code`): the server `MSG_PATTERN` is intentionally broader
(`anthropic` vs `noreply@anthropic`; `.*claude` vs `\[?claude code`).

## 4. Verification matrix (`./verify.sh`, all 14 PASS)

Each row applies the **exact** workflow patterns. `msg`/`id` = which check fires.

**Real commits (agent-assurance):**

| Commit | Description | msg | id | Expected |
|--------|-------------|-----|----|----------|
| `4a8668c` | leaked branch (Werner + Claude co-author) | HIT | miss | caught |
| `5bc75c9` | leaked branch | HIT | miss | caught |
| `a3e86f6` | leaked SQUASH (#21 `merge_commit`) | HIT | miss | caught |
| `b8d7a026` | leaked SQUASH (#22 `merge_commit`) | HIT | miss | caught |
| `aa5a0b2` | clean #21 replacement | miss | miss | pass (no FP) |
| `57b1350` | clean #22 replacement | miss | miss | pass (no FP) |
| `3419e1a` | current `main` tip | miss | miss | pass (no FP) |
| `21d40e4` | PR#27 GitHub + Werner co-author | miss | miss | pass (no FP) |
| `5fe8f98` | PR#29 dependabot co-author | miss | miss | pass (no FP) |

**Synthetic vectors (throwaway repo; `--no-verify` to bypass the local hook
purely to *create* the fixtures):**

| Fixture | msg | id | Expected |
|---------|-----|----|----------|
| clean commit | miss | miss | pass |
| co-author trailer | HIT | miss | caught (message) |
| `Generated with [Claude Code]` footer | HIT | miss | caught (message) |
| author `Claude <noreply@anthropic.com>`, clean message | miss | HIT | caught (identity) |
| simulated squash, clean subject + appended co-author trailer | HIT | miss | caught (message) |

**New-branch push fallback regression (§6):**

| Check | Result | Expected |
|-------|--------|----------|
| OLD fallback `-n 1 <tip>` on (bad-first-commit, clean-tip) branch | miss | miss — documents the fail-open bug |
| FIX fallback `main..<tip>` (introduced range) | HIT | catches the earlier bad commit |

Run: `bash docs/reviews/2026-06-18-no-ai-attribution-gate-hardening/verify.sh`
(exit 0 = all 16 pass).

## 5. Out of scope / follow-ups (not in this diff)

- **Branch protection:** `main` has no protection rule, so this check is not
  *required* to merge. Making it required is a repo-admin setting (Werner's
  action), not a file change. Without it the gate detects but cannot *block*.
- **PR-ref residue (#21/#22):** removing the already-public trailered commits
  requires a GitHub Support request; tracked separately.
- **CI self-test (optional):** `verify.sh` could be wired as a CI step to guard
  the gate against regression; deferred to keep this diff minimal.

## 6. Cross-LLM review log

Reviewers ran with full filesystem access against the worktree, verified every
claim against the code/git themselves, and ran `verify.sh`.

- **Grok (r1): UNCONDITIONAL APPROVAL.** Verified A–E by direct file reads +
  `git log` pattern reproduction + harness execution. Noted the `-n 1` fallback
  but classed it pre-existing/out-of-scope (range block was byte-identical to
  `origin/main`).
- **Codex (r1): BLOCKER** — *"new-branch push fallback scans only the tip commit
  and can miss AI attribution in earlier introduced commits."* Reproduced a
  two-commit new-branch push (bad first commit, clean tip): the `-n 1 $AFTER`
  fallback matched nothing and would PASS while an introduced commit carried
  `Co-Authored-By: Claude <noreply@anthropic.com>`. Correct: it is a fail-open.
- **Resolution (r2):** replaced the `-n 1 $AFTER` fallback with an
  introduced-range computation against the default branch, degrading to a
  fail-closed full `$AFTER` scan if unavailable. Added fallback-regression
  assertions to `verify.sh`.
- **Grok (r2): UNCONDITIONAL APPROVAL** of the fixed commit — re-verified the
  diff, ran `verify.sh` (16/16), and constructed its own adversarial
  multi-commit new-branch cases; confirmed no new fail-open / false-positive and
  that the full-scan over-scan is an acceptable fail-closed trade-off (main has
  0 attribution commits).
- **Codex (r2): BLOCKER** — *"missing `origin/$DEFAULT_BRANCH` can fall back to a
  stale local `$DEFAULT_BRANCH..$AFTER` range and miss a buried attribution
  commit."* Proved it: in the worktree `refs/heads/main` (`5fe8f98`) ≠
  `refs/remotes/origin/main` (`3419e1a`); a buried bad commit was excluded by the
  local-branch range while the true range and full scan both caught it. Correct.
- **Resolution (r3):** removed the local-branch tier entirely. The fallback now
  trusts only `refs/remotes/origin/$DEFAULT_BRANCH`; if absent it fails closed
  with a full `$AFTER` scan. Added the stale-local-`$DEF` regression to
  `verify.sh` (now **19/19**). Re-dispatched both reviewers.
- **Codex (r3): UNCONDITIONAL APPROVAL** — re-ran its r2 adversarial repro
  (`origin_ref_exists=no`, `removed_local_main_range=miss`, `selected=fullscan`,
  `workflow_message_scan=HIT`); confirmed the buried commit is now caught and no
  new fail-open/false-positive.
- **Grok (r3): UNCONDITIONAL APPROVAL** — re-verified the diff, ran 19/19, and
  constructed its own missing-remote-ref + stale-local-main and clean-multi-commit
  adversarial cases (fullscan catches the buried bad; no false-positive on clean).
- **Outcome:** both reviewers unconditionally approved HEAD `200fdb9`. Ready for
  Werner's manual review.
