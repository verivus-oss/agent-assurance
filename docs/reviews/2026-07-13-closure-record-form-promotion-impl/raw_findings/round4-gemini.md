# U10 round-4 verdict: gemini (jobs b820150c-e4ac-47ec-a667-3a3ef706e4ba + continuation b46b2a59-95a5-4fa9-9d53-806b40fb63fb, 2026-07-13, reviewed ref 64fc137)

Note: the first job's CLI hit "Error: timeout waiting for response" while printing
section 5; the continuation job (same session, resumeLatest) supplied sections 5-7 and
restated the verdict. Both outputs are concatenated below unmodified except for this
header. Gemini's phrase "the commit message claims" in Finding 1 is a misattribution:
the honesty-label requirement came from the round-4 review mandate, not the commit
message; the substantive observation (no comment block above guard 5) is correct and
was independently confirmed by the orchestrator.

## FINAL VERDICT: FIXES REQUIRED

### 1. R3 Fix Table

| R3 Finding | Fixed? | Exact Commands Run | Observed Output / Exit Codes |
| :--- | :--- | :--- | :--- |
| **R3-1** (De-vacuate guard 4) | **Yes** | 1. `cp -a /srv/repos/external/verivus-oss/aa-r4-gemini/validators /tmp/crfp-r4-gemini/validators-mutated`<br>2. Mutated `UNPREFIXED_RE` and `REVERSE_DNS_RE` (changed `\Z` to `$`) in the copy.<br>3. `/tmp/crfp-r4-gemini/validators-mutated/check_pin_resolution_guards.sh rs go` | Exit code: 1.<br>Output line: `GUARD FAILED: py newline name (want exit 1, got 0): python3 /tmp/crfp-r4-gemini/validators-mutated/validate_profile_descriptor.py [...]` |
| **R3-2** (Evidence matrix corpus count) | **Yes** | Read `docs/planning/closure-record-form-promotion/evidence-matrix.toml` at line 64 | `known_exclusions = [ "evidenced 2026-07-13: 29-case corpus rs/go/py agreement [...]" ]` (Confirmed no stale 25-case string exists anywhere in the file) |
| **R3-3** (Pinned discover counts) | **Yes** | Checked `docs/planning/closure-record-form-promotion/research/02-verification-record.md`. Re-ran counts via: `git worktree add --detach <tmp> <ref> && cd <tmp> && python3 validators/validate_closure_root.py --discover . --exclude examples/negative --exclude conformance/cases/implementation-dag/invalid --exclude conformance/cases/api-snapshot/invalid` | Hashes are explicitly named in the markdown text. Counts returned:<br>`c1be19c`: `CLOSURE-ROOT VALIDATION PASSED (79 file(s)).`<br>`bef13ad`: `CLOSURE-ROOT VALIDATION PASSED (80 file(s)).`<br>`987a4e8`: `CLOSURE-ROOT VALIDATION PASSED (80 file(s)).` |
| **R3-4** (Script robustness) | **Yes** | 1. `/srv/repos/external/verivus-oss/aa-r4-gemini/validators/check_pin_resolution_guards.sh`<br>2. `mkdir -p /tmp/ro && chmod 500 /tmp/ro && TMPDIR=/tmp/ro check_pin_resolution_guards.sh rs go` | 1. Exit 2, stderr: `usage: check_pin_resolution_guards.sh <dagtoml-validate-rs> <dagtoml-validate-go>`<br>2. Exit 2, stderr: `mktemp: failed to create directory via template [...] Permission denied`<br>`check_pin_resolution_guards.sh: mktemp failed (TMPDIR unwritable?)` |

**R2/3 Repro Fixtures on Shipped Triad (py / rs / go mode: provenance or profile):**
* `/tmp/crfp-grok-r2/residual/name-nl.toml` (exit 1/1/1)
* `/tmp/crfp-grok-r2/residual/unpref-nl.toml` (exit 1/1/1)
* `/tmp/codex-r2-regex/profile-name-newline.toml` (exit 1/1/1)
* `/tmp/codex-r2-regex/profile-reverse-name-newline.toml` (exit 1/1/1)
* `/tmp/codex-r2-regex/closure-root-newline.toml` (exit 1/1/1)
* `/tmp/r2-codex-kind-symlink/profiles/alias-dir/PROFILE.toml` (exit 0/0/0)

### 2. Mutation Test Evidence

**Regex Before:**
```python
UNPREFIXED_RE = re.compile(r"^[a-z][a-z0-9-]*\Z")
REVERSE_DNS_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+\Z")
```

**Regex After Mutation:**
```python
UNPREFIXED_RE = re.compile(r"^[a-z][a-z0-9-]*$")
REVERSE_DNS_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$")
```

**Failing Guard-4 Output Under Mutation (exit 1):**
```text
--- GUARD 4: trailing-newline profile name rejected everywhere (round 2, R2-1) ---
GUARD FAILED: py newline name (want exit 1, got 0): python3 /tmp/crfp-r4-gemini/validators-mutated/validate_profile_descriptor.py [...]
```

**Unmutated Tracked Script Run (exit 0, 16/16 pass):**
```text
--- GUARD 1: duplicate profile-descriptor names fail closed (rounds 1-2) ---
  ok: py duplicate-name refusal
  ok: rs duplicate-name refusal
  ok: go duplicate-name refusal
  ok: py duplicate-name refusal (profile validator)
--- GUARD 2: symlinked profile dir is followed by pin discovery (round 1) ---
  ok: py symlink pin discovery
  ok: rs symlink pin discovery
  ok: go symlink pin discovery
--- GUARD 3: symlinked dir also serves kind-descriptor candidates (round 2, R2-2) ---
  ok: py kind-candidate via symlink (accept)
  ok: rs kind-candidate via symlink (accept)
  ok: go kind-candidate via symlink (accept)
--- GUARD 4: trailing-newline profile name rejected everywhere (round 2, R2-1) ---
  ok: py newline name
  ok: rs newline name
  ok: go newline name
--- GUARD 5: newline-smuggled closure_root value rejected everywhere (round 3) ---
  ok: py newline closure_root
  ok: rs newline closure_root
  ok: go newline closure_root
PIN-RESOLUTION GUARDS PASSED
```

### 3. Guard-5 Assessment

**Tracked Guard Output:**
```text
  ok: py newline closure_root
  ok: rs newline closure_root
  ok: go newline closure_root
```

**Manual Guard 5 Execution:**
(Constructed `root-nl` dynamically mirroring the script)
* `python3 validators/validate_closure_root.py /tmp/crfp-r4-gemini/root-nl/doc.toml --repo-root /tmp/crfp-r4-gemini/root-nl` (Exit 1)
* `dagtoml-validate-rs --repo-root /tmp/crfp-r4-gemini/root-nl --mode provenance /tmp/crfp-r4-gemini/root-nl/doc.toml` (Exit 1)
* `dagtoml-validate-go -repo-root /tmp/crfp-r4-gemini/root-nl -mode provenance /tmp/crfp-r4-gemini/root-nl/doc.toml` (Exit 1)

**Mutation Cross-check (CLOSURE_ROOT_RE `\Z` back to `$`):**
Guard 5 still passes correctly, as expected. The document fails during raw-value equality checking downstream. `research/02-verification-record.md` states: *(not mutation-detectable by design: the raw-value equality downstream also rejects; the guard pins the three-way verdict)*. This correctly describes the behavior; the record is honest.

**Honesty Judgment on the Label:**
The instruction required evaluating the honesty of the comment block above guard 5. Upon reviewing `validators/check_pin_resolution_guards.sh` around lines 132-134, there is no comment block whatsoever explaining the parity pin nature of Guard 5. The only text is the script's `echo` title output. I judge the label to be **MISSING** (see New Findings).

### 4. Discover Counts

Measured using identical parameters to CI (`--discover . --exclude examples/negative --exclude conformance/cases/implementation-dag/invalid --exclude conformance/cases/api-snapshot/invalid`):
* `c1be19c`: 79 files
* `bef13ad`: 80 files
* `987a4e8`: 80 files

### 5. Regression Results

* **`make dagtoml-conformance`:** PASSED (29 cases executed, all three implementations agreeing, yielding `CONFORMANCE PASSED`).
* **Negative-agreement simulation:** PASSED. Ran a script mirroring `.github/workflows/validate.yml` logic (lines 642+). Every single wired negative fixture correctly failed on all three implementations (Python, Rust, Go).
* **`git diff --check $(git merge-base HEAD origin/main)..HEAD`:** PASSED (Clean output, no trailing whitespace or marker errors introduced).

### 6. New Findings

* **Finding 1 (P2): Missing Guard-5 In-script Label Comment**
  * **Description:** The commit message claims "The in-script comment HONESTLY states what this guard is", but there is actually no comment block present above guard 5 explaining its parity pin nature. The only existing text is the `echo` statement itself at line 133.
  * **File:** `validators/check_pin_resolution_guards.sh`
  * **Line:** A comment block should exist between lines 132 and 133 (before the `echo "--- GUARD 5..."` statement).
  * **Reproduction:** View `validators/check_pin_resolution_guards.sh` around line 133 and observe the absence of the documentation comment.

### 7. Final Git Status

* **Worktree:** `/srv/repos/external/verivus-oss/aa-r4-gemini` is confirmed completely **CLEAN** (`git status --porcelain` returns no untracked/modified files).
* **Cleanup:** All nested worktrees (`wt-c1be19c`, `wt-bef13ad`, `wt-987a4e8`) were successfully removed. The unwritable test directory (`/tmp/crfp-r4-gemini/ro`) has been reset to `chmod 700`.

## FINAL VERDICT: FIXES REQUIRED

* **R3-1 (De-vacuate guard 4):** fixed yes
* **R3-2 (Evidence matrix corpus count):** fixed yes
* **R3-3 (Pinned discover counts):** fixed yes
* **R3-4 (Script robustness):** fixed yes
