# WP1 Validator Ports — Falsification Target

Date: 2026-05-30 UTC
Target commit: `4f48edd` ("feat: port validator coverage to primary tools").
Repo (if you have read access): `/srv/repos/external/verivus-oss/agent-assurance`.

## Your task — REFUTE, do not approve

Two findings are stated below. Your job is to **try to prove each one
WRONG**. Default to "refuted" if you are not convinced. Approve a finding
as REAL only if, after inspecting the cited code (or the verbatim excerpts
below if you cannot reach the repo), you cannot construct a way it is
mistaken.

This repo's entire value proposition: multiple independent native
validators (safe **Rust** + safe **Go**) are the *primary normative*
implementations and must enforce **identical** rules; Python is a
*cross-check*. A place where Rust and Go disagree, or where the primary
validators are *weaker* than the Python cross-check, is a defect the repo
exists to surface.

For each finding return exactly one of:
- `REFUTED — <reason with file:line or a concrete counter-input>`
- `CONFIRMED — <why the refutation attempts fail>`

and, if CONFIRMED, the minimal **negative fixture input** that
distinguishes the two behaviours.

---

## Finding #1 — Provenance `source_path` can escape the repo; Rust+Go are weaker than the Python cross-check

**Claim.** The provenance source-sha binding check — the load-bearing
"this attestation is bound to these exact bytes under repo root" check —
joins `repo_root` with the attacker-controlled `source_path` and reads it
with **no absolute-path rejection and no containment check**, in both
primary validators. The Python cross-check *does* reject both. So a
malicious attestation can bind its provenance hash to a file outside the
repo (e.g. `source_path = "/etc/passwd"` or `"../../secret"`), and the
primary validators accept what Python rejects.

**Rust** — `tools/dagtoml-validate-rs/src/main.rs:898` (fn starts :892):
```rust
let full = repo_root.join(source_path);
let data = match std::fs::read(&full) {
    Ok(data) => data,
    Err(e) => {
        errors.push(format!(
            "{}: [provenance].source_path does not resolve under repo root ({source_path}): {e}",
            path.display()
        ));
        return errors;
    }
};
```
Note: the error string *claims* "does not resolve under repo root" but
nothing checks that. `Path::join` with an absolute argument discards the
base, so `repo_root.join("/etc/passwd") == "/etc/passwd"`. `..` segments
are not normalised away.

**Go** — `tools/dagtoml-validate-go/main.go:692` (fn starts :674):
```go
data, err := os.ReadFile(filepath.Join(repoRoot, sourcePath))
if err != nil {
    return []string{fmt.Sprintf("%s: [provenance].source_path does not resolve under repo root (%s): %v", path, sourcePath, err)}
}
```
Note: `filepath.Join(repoRoot, "../../etc/passwd")` cleans to an escaping
path; `filepath.Join(repoRoot, "/etc/passwd")` does NOT discard the base
(differs from Rust) — so Rust and Go *also* differ on absolute paths.

**Python cross-check** — `validators/validate_provenance.py:95-109`:
```python
if pathlib.PurePath(source_path).is_absolute():
    return [... "must be relative to repo root, got absolute path ..."]
resolved = (repo_root / source_path).resolve()
repo_root_resolved = repo_root.resolve()
try:
    resolved.relative_to(repo_root_resolved)
except ValueError:
    return [... "resolves outside repo root ... SPEC §11 requires source_path to point to a file under repo root"]
```
Python also validates the sha256 hex shape (64 lowercase hex); the Rust/Go
binding path does not.

**Spec basis.** SPEC §11 invariant: `source_path` resolves to an existing
file **under repo root**.

**How to refute #1 (please try all):**
1. Find an earlier guard — does the caller / dispatcher validate or
   reject absolute or `..`-containing `source_path` before
   `validate_provenance_binding` / `validateProvenanceBinding` is called?
   (Grep the call sites.)
2. Does the kind descriptor or schema constrain `source_path` to a safe
   character set that excludes `/` and `..`?
3. Is containment enforced somewhere else in the validator pipeline?
4. Does the spec actually NOT require containment (i.e. is the Python
   check over-strict and the Rust/Go behaviour correct)?
5. Construct an input where the claimed escape does *not* happen.

---

## Finding #2 — Rust and Go disagree on the gate-decision separation-of-duty invariant (INV01)

**Claim.** For a `gate-decision` document, Go silently drops non-table
elements of `failed_constraint_refs`, then counts the *post-drop* length
in INV01 ("verdict == pass iff failed_constraint_refs is empty"). Rust
flags non-table elements as violations. So the input
`verdict = "pass"` with `failed_constraint_refs = ["A-1"]` (an array of
**strings**, not tables) is **accepted by Go** (drops to zero refs →
"pass" with empty refs → INV01 holds) and **rejected by Rust** (1 entry →
"pass" with non-empty refs → INV01 violated, plus INV02 "is not a table").
This is a hard accept/reject disagreement on the proof/audit gate.

**Go** — `tools/dagtoml-validate-go/main.go`:
```go
// :3085  gdAsTableArray drops non-table elements
func gdAsTableArray(v any) []map[string]any {
    switch x := v.(type) {
    case []map[string]any:
        return x
    case []any:
        out := make([]map[string]any, 0, len(x))
        for _, e := range x {
            if m, ok := e.(map[string]any); ok {   // non-tables silently skipped
                out = append(out, m)
            }
        }
        return out
    }
    return nil
}
// :3178
failedRefs := gdAsTableArray(decision["failed_constraint_refs"])
// :3180 INV01: verdict == "pass" iff failed_constraint_refs is empty.
isPass := verdict == "pass"
isEmpty := len(failedRefs) == 0   // length AFTER the silent drop
```

**Rust** — `tools/dagtoml-validate-rs/src/main.rs:3447`:
```rust
for (i, ref_v) in failed_refs.iter().enumerate() {
    let Some(t) = ref_v.as_table() else {
        defects.push(format!(
            "{}: INV02 violated: failed_constraint_refs[{}] is not a table", location, i));
        continue;
    };
    ...
}
```
(Rust derives `failed_refs` from the raw array length, so INV01's
emptiness test sees the string element; Go does not.)

**How to refute #2 (please try all):**
1. Does the BurntSushi/toml decoder actually deliver
   `failed_constraint_refs = ["A-1"]` as something `gdAsTableArray`
   keeps (e.g. could it error at decode time, or deliver a type the
   `[]any` branch doesn't hit)?
2. Is there an earlier type/shape check that rejects a string-typed
   `failed_constraint_refs` before INV01 runs in Go?
3. Does Rust *also* drop/ignore the string element, making the verdicts
   agree after all?
4. Is the gate-decision file even routed to this validator path (check
   kind detection / dispatch)?
5. Show that the two implementations reach the same accept/reject verdict
   on the input `{verdict="pass", failed_constraint_refs=["A-1"]}`.

---

## Output format

```
FINDING #1: REFUTED|CONFIRMED — <evidence>
FINDING #2: REFUTED|CONFIRMED — <evidence>
```
Cite file:line. If you cannot reach the repo, say so and reason from the
verbatim excerpts above — but mark which you could not independently
verify.
