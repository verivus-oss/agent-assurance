# U10 round-4 verdict: grok (job e38ff343-4c80-408b-809f-38b5aedbd703, 2026-07-13, reviewed ref 64fc137)

## FINAL VERDICT: UNCONDITIONAL APPROVAL

All R3-1 through R3-4 claims were verified by running commands against commit `64fc137` in `/srv/repos/external/verivus-oss/aa-r4-grok`. No new findings of any severity.

---

### 1. R3 fix table

| ID | Fixed? | Commands / evidence |
|----|--------|---------------------|
| **R3-1** | **yes** | Mutated copy of `validators/` under `/tmp/crfp-r4-grok/validators-mutated/`: flipped `UNPREFIXED_RE` and `REVERSE_DNS_RE` `\Z` to `$`. Mutated run exit **1**, single failure: `GUARD FAILED: py newline name (want exit 1, got 0)`. rs/go guard-4 still ok; other guards unchanged (15 ok + 1 fail). Unmutated tracked script: **16** `ok:` lines, `PIN-RESOLUTION GUARDS PASSED`, exit **0**. Residual triad all **1/1/1** (5 files) and symlink root **0/0/0**. |
| **R3-2** | **yes** | `rg -n "case corpus\|25\|29" evidence-matrix.toml` -> E04 known_exclusions line 64: `"... 29-case corpus ..."`. No `25-case` / `25 case` phrases. Only other `25` hits are inside the empty-SHA-256 hex. |
| **R3-3** | **yes** | Hashes present in `02-verification-record.md` (lines 44-45, 71-73, 151, 172). Clean worktree discover counts (CI discover logic from `.github/workflows/validate.yml`): **c1be19c=79**, **bef13ad=80**, **987a4e8=80**. Nested worktrees removed. |
| **R3-4** | **yes** | Zero args: exit **2**, stderr `usage: check_pin_resolution_guards.sh <dagtoml-validate-rs> <dagtoml-validate-go>`. `TMPDIR=/tmp/crfp-r4-grok/ro` (chmod 500): exit **2**, stderr includes `check_pin_resolution_guards.sh: mktemp failed (TMPDIR unwritable?)`. Dir chmod restored. |

---

### 2. Mutation test evidence (R3-1)

**Before (tracked / copy initial):**
```text
UNPREFIXED_RE = re.compile(r"^[a-z][a-z0-9-]*\Z")
REVERSE_DNS_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+\Z")
```

**After (mutated copy only):**
```text
UNPREFIXED_RE = re.compile(r"^[a-z][a-z0-9-]*$")
REVERSE_DNS_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$")
```

`HERE="$(cd "$(dirname "$0")" && pwd)"` confirmed at line 23 of the copied script (so the mutated Python validators are used).

**Mutated run** (`/tmp/crfp-r4-grok/validators-mutated/check_pin_resolution_guards.sh` + built rs/go):
```text
--- GUARD 4: trailing-newline profile name rejected everywhere (round 2, R2-1) ---
GUARD FAILED: py newline name (want exit 1, got 0): python3 /tmp/crfp-r4-grok/validators-mutated/validate_profile_descriptor.py ...
  ok: rs newline name
  ok: go newline name
...
PIN-RESOLUTION GUARDS FAILED
exit=1
```
Only that one check flipped (guards 1-3 and 5 stayed green).

**Unmutated tracked run:**
```text
  ok: ... (16 lines)
PIN-RESOLUTION GUARDS PASSED
exit=0
```
`rg -c '  ok:'` -> **16**.

**Residual triad (worktree py + built rs/go):**

| File | py/rs/go |
|------|----------|
| `/tmp/crfp-grok-r2/residual/name-nl.toml` (profile) | 1/1/1 |
| `/tmp/crfp-grok-r2/residual/unpref-nl.toml` (profile) | 1/1/1 |
| `/tmp/codex-r2-regex/profile-name-newline.toml` (profile) | 1/1/1 |
| `/tmp/codex-r2-regex/profile-reverse-name-newline.toml` (profile) | 1/1/1 |
| `/tmp/codex-r2-regex/closure-root-newline.toml` (provenance / `validate_closure_root.py`) | 1/1/1 |
| `/tmp/r2-codex-kind-symlink/profiles/alias-dir/PROFILE.toml` (profile) | 0/0/0 |

CLI confirmed via `--help` / `-h`: rs `--mode profile|provenance`, go `-mode`, py dedicated scripts.

---

### 3. Guard-5 assessment

**(a) Three-way reject** (tracked guard output):
```text
  ok: py newline closure_root
  ok: rs newline closure_root
  ok: go newline closure_root
```
Hand-built mirror under `/tmp/crfp-r4-grok/guard5-hand/` (multi-line `closure_root = """\n<sentinel>\n"""`): **py_ec=1**, **rs_ec=1**, **go_ec=1**.

**(b) Honesty.** In-script region is only the header (lines 133-146 of `validators/check_pin_resolution_guards.sh`):
```text
echo "--- GUARD 5: newline-smuggled closure_root value rejected everywhere (round 3) ---"
```
No multi-line `#` block like guard 4. The header states a true, load-bearing property (three-way rejection). It does **not** claim the guard is an anchor-mutation detector. Verification record (lines 167-170) is explicit:
```text
Guard 5 added to pin the newline
closure_root parity verdict (not mutation-detectable by design: the
raw-value equality downstream also rejects; the guard pins the
three-way verdict).
```
**Judgment: honest enough; not a decorative guard.** Label is brief but accurate; detailed non-mutation design is recorded where R3 said it would be.

**(c) Optional mutation cross-check.** Clean copy with only `CLOSURE_ROOT_RE` `\Z` to `$` still yields full guard script **exit 0** (all 16 ok), matching "not mutation-detectable by design." No tracked test would flip solely on that anchor revert; the record does **not** claim otherwise. No finding.

---

### 4. Discover counts (R3-3)

CI discover snippet from `.github/workflows/validate.yml` (conforming `template_kind` walk, skip `examples/negative/` and `conformance/.../invalid/`), run in detached worktrees:

| Ref | Measured count | Command basis |
|-----|----------------|---------------|
| `c1be19c` | **79** | `git worktree add --detach /tmp/crfp-r4-grok/wt-c1be19c c1be19c` + discover Python |
| `bef13ad` | **80** | same for `bef13ad` |
| `987a4e8` | **80** | same for `987a4e8` |

Matches the pinned wording in `02-verification-record.md`. Worktrees removed with `git worktree remove --force`.

---

### 5. Regression results

**`make dagtoml-conformance`** (from worktree root):
```text
conformance: 29 cases
CONFORMANCE PASSED
```
All 29 cases three-way agreement (`rs=go=py`).

**Negative-agreement** (CI step "Negative fixtures - primary/reference agreement" from `validate.yml`, same checks with local rs/go binaries): all expected rejects (`ok: ... rejected` for kind-descriptor, IJB, provenance, implementation-dag, traceability, review-readiness, cost, rollback, abstraction-class, profile-descriptor closure-records, gate-decision string-refs, api-snapshot bad-closure / witness-stripped / bad-ijb).
Result: **NEGATIVE-AGREEMENT SIMULATION PASSED**.

**`git diff --check $(merge-base HEAD origin/main)..HEAD`**: clean, exit **0**.

---

### 6. New findings

**None.**

---

### 7. Final git status of the worktree

```text
Not currently on any branch.
nothing to commit, working tree clean
64fc13724ad9fa0387e1e7b3b7f13a9d4542959d
```

No nested worktrees under `/tmp/crfp-r4-grok/`. All mutation/build artifacts stayed under `/tmp/crfp-r4-grok/` (not in the worktree). Main checkout `/srv/repos/external/verivus-oss/agent-assurance` was not touched.
