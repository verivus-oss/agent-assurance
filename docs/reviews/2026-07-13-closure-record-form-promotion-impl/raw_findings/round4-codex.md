# U10 round-4 verdict: codex (job f6270849-3b43-42b0-9b9f-718712c2e08c, 2026-07-13, reviewed ref 64fc137)

## FINAL VERDICT: FIXES REQUIRED

Two P3 issues remain. The required guard-4 mutation behavior, triad repros, robustness checks, corpus regression, and measured discover counts otherwise passed. No tracked files were modified.

### 1. R3 fix table

| Fix | Fixed | Commands run | Observed evidence |
|---|---|---|---|
| R3-1, guard-4 de-vacuation | Yes | Copied/mutated guard, then ran copied and tracked scripts with the shipped Rust and Go binaries | Mutation exited 1 with exactly one failure, `py newline name`; tracked script exited 0 with 16 `ok:` lines. The de-vacuating descriptor is at check_pin_resolution_guards.sh:121. |
| R3-2, 29-case wording | Yes | `rg -n -- '\b25\b' docs/planning/closure-record-form-promotion/evidence-matrix.toml` | Exit 1, no stale `25`. E04 says `29-case corpus` at evidence-matrix.toml:64. |
| R3-3, every count pinned to named refs | **No** | Added three clean detached worktrees and ran the CI discover command at each | Counts are correct, 79/80/80, but 02-verification-record.md:151 still says `80 after` without a named ref. |
| R3-4, guard robustness | Yes | Zero-argument and unwritable-`TMPDIR` runs | Zero args exited 2 with usage. Unwritable temp exited 2 with the explicit script diagnostic. Implementation at check_pin_resolution_guards.sh:15 and :26. |

### 2. Mutation test evidence

Confirmed the copied script resolves Python validators from its own directory via check_pin_resolution_guards.sh:23 (`HERE=`).

Before mutation, validate_profile_descriptor.py:53:

```python
UNPREFIXED_RE = re.compile(r"^[a-z][a-z0-9-]*\Z")
REVERSE_DNS_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+\Z")
```

After copying `validators/` to `/tmp/crfp-r4-codex/validators-mutated/`, only those anchors changed to:

```python
UNPREFIXED_RE = re.compile(r"^[a-z][a-z0-9-]*$")
REVERSE_DNS_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$")
```

Ran:

```bash
/tmp/crfp-r4-codex/validators-mutated/check_pin_resolution_guards.sh \
  /srv/repos/external/verivus-oss/aa-r4-codex/tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs \
  /tmp/crfp-r4-codex/dagtoml-validate-go
```

Observed (log /tmp/crfp-r4-codex/profile-anchor-mutated-guard.out):

```text
PROFILE_ANCHOR_MUTATED_EXIT=1
PROFILE_ANCHOR_MUTATED_FAILED_LINES=1
PROFILE_ANCHOR_MUTATED_OK_LINES=15
--- GUARD 4: trailing-newline profile name rejected everywhere (round 2, R2-1) ---
GUARD FAILED: py newline name (want exit 1, got 0): python3 /tmp/crfp-r4-codex/validators-mutated/validate_profile_descriptor.py ... --repo-root .../nl
  ok: rs newline name
  ok: go newline name
--- GUARD 5: newline-smuggled closure_root value rejected everywhere (round 3) ---
  ok: py newline closure_root
  ok: rs newline closure_root
  ok: go newline closure_root
PIN-RESOLUTION GUARDS FAILED
```

Tracked script with the same binaries: exit 0, 16 `ok:` lines, `PIN-RESOLUTION GUARDS PASSED` (log /tmp/crfp-r4-codex/tracked-guard.out).

All four validator helps checked before using mode syntax. Repro triads:

| Fixture | Python | Rust | Go |
|---|---:|---:|---:|
| /tmp/crfp-grok-r2/residual/name-nl.toml | 1 | 1 | 1 |
| /tmp/crfp-grok-r2/residual/unpref-nl.toml | 1 | 1 | 1 |
| /tmp/codex-r2-regex/profile-name-newline.toml | 1 | 1 | 1 |
| /tmp/codex-r2-regex/profile-reverse-name-newline.toml | 1 | 1 | 1 |
| /tmp/codex-r2-regex/closure-root-newline.toml | 1 | 1 | 1 |
| /tmp/r2-codex-kind-symlink profile fixture | 0 | 0 | 0 |

### 3. Guard-5 assessment

Tracked guard has all three guard-5 rejections at check_pin_resolution_guards.sh:144-146. Manual reconstruction under /tmp/crfp-r4-codex/guard5-manual/ ran the exact three commands by hand; all exited 1. Python reported the newline-bearing raw value, while Rust and Go rejected the digest length.

**The requested honest in-script comment is missing.** There is no comment block above guard 5 (transition at lines 129-140 goes straight from the guard-4 expects to the guard-5 echo).

The verification record itself is honest: "Guard 5 added to pin the newline closure_root parity verdict (not mutation-detectable by design: the raw-value equality downstream also rejects; the guard pins the three-way verdict)" (02-verification-record.md:167). That matches observed behavior: with only `CLOSURE_ROOT_RE` mutated `\Z` to `$` in /tmp/crfp-r4-codex/validators-root-anchor-mutated/, the copied guard exited 0 with all 16 checks ok (`ROOT_ANCHOR_MUTATED_EXIT=0`, `ROOT_ANCHOR_MUTATED_OK_COUNT=16`), following the raw equality check at validate_closure_root.py:373. A tracked-source grep found no other executable mutation-detecting closure-anchor test; the record does not falsely claim one. The finding is specifically that the required label is absent from the guard script.

### 4. Discover counts

CI invocation read at validate.yml:379 and run verbatim in detached clean worktrees (wt-c1be19c, wt-bef13ad, wt-987a4e8 under /tmp/crfp-r4-codex/):

```bash
python3 validators/validate_closure_root.py \
  --discover . --exclude examples/negative \
  --exclude conformance/cases/implementation-dag/invalid \
  --exclude conformance/cases/api-snapshot/invalid
```

| Ref | Observed output | Exit |
|---|---|---:|
| `c1be19c` | `CLOSURE-ROOT VALIDATION PASSED (79 file(s)).` | 0 |
| `bef13ad` | `CLOSURE-ROOT VALIDATION PASSED (80 file(s)).` | 0 |
| `987a4e8` | `CLOSURE-ROOT VALIDATION PASSED (80 file(s)).` | 0 |

All three worktrees removed after measurement.

### 5. Regression results

- `make dagtoml-conformance`: exit 0, `conformance: 29 cases`, `CONFORMANCE PASSED`, 29 `rs=... go=... py=... ok` rows counted (Makefile:96; log /tmp/crfp-r4-codex/dagtoml-conformance.out).
- Negative-agreement: CI body at validate.yml:644 executed via `RUNNER_TEMP=/tmp/crfp-r4-codex bash -euo pipefail < <(sed -n '644,846p' .github/workflows/validate.yml | sed 's/^          //')`. Exit 0: 47 expected-rejection checks passed (Rust 14, Go 14, Python 19); grep for `REGRESSION`/`unexpectedly passed`/`No such file` found nothing.
- `git diff --check $(merge-base)..HEAD`: MERGE_BASE=489d6490a01bded7e9c9fd2edc502b530c91bb1b, no output, exit 0.

### 6. New findings

- **P3: Guard 5 lacks the required in-script honest-label comment.**
  Fixture: /tmp/crfp-r4-codex/validators-root-anchor-mutated/.
  Repro: run the copied script command shown in section 3, then inspect check_pin_resolution_guards.sh:133. The anchor-only mutation exits 0 with all 16 checks, proving why the comment must identify guard 5 as a parity pin rather than a mutation-sensitive anchor guard.
  Fix: add a `#` comment immediately above line 133 that explicitly says the guard pins the three-way parity verdict and does not detect a `CLOSURE_ROOT_RE` anchor-only reversion because downstream raw-value equality still rejects the fixture.

- **P3: One discover-count claim remains unpinned.**
  Fixture: /tmp/crfp-r4-codex/r3-3-verification-record-fixture.md:151.
  Repro: `rg -n -- 'counts pinned to refs \(79 at c1be19c, 80 after\)'` on that file gives line 151: `3. R2-3/R2-5/R2-8: counts pinned to refs (79 at c1be19c, 80 after),`.
  Fix: replace `80 after` with explicitly named measured refs, such as `80 at bef13ad and 987a4e8`.

### 7. Final worktree status

`git status --porcelain` empty for /srv/repos/external/verivus-oss/aa-r4-codex; nested worktrees removed.
