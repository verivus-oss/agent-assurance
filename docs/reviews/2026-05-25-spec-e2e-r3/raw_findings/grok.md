# spec-e2e-r3 — grok raw findings

Job: d6fdef50-d460-439e-b450-3b45aa0bb8a3
Started: 2026-05-25T13:35:26Z
Finished: 2026-05-25T13:37:18Z
Exit: 0
Verdict: **unconditional_approval**

**Round-3 (spec-e2e-r3) Independent Bytes-Level Review Report**

**Session:** 2026-05-25-spec-e2e-r3
**Commit under review:** 4fbc90639b4bafd7f7a90b52ae723efd1e9a9d27
**Predecessor:** docs/reviews/2026-05-25-spec-e2e-r2/terminal_decision.toml (codex concrete_unresolvable_blocker on S08.1 only; S08.2-S08.8 + r1 regression sweep closed unanimously)
**Verification spec:** docs/reviews/2026-05-25-spec-e2e-r3/verification_report.toml (read in full; all 9 verify_by executed literally against commit bytes + live execution; no summaries accepted from any prior reviewer)

**Principal question (from verification_report):** Has S08.1 been closed such that `validators/validate_gate_decision.py --help` cites INV01..INV06 per r2 verify_by:3, AND have r2-closed surfaces (INV06 enforcement triad Python/Rust/Go + CI + kind-descriptor markers stripped) survived the change?

**Method:** Every verify_by executed by (a) `git show 4fbc906:<path>` or direct file reads at HEAD (which is 4fbc906), (b) literal command execution with stdout/stderr/exit-code capture, (c) exact line citations. Negative variants constructed in /tmp per the exact recipe in r2 verification_report.toml (S08.3 verify_by). All three validator implementations exercised. CI YAML and gate-decision-kind.toml inspected at commit bytes.

---

### verify_by 1 (paper cross-check, per verification_report)
**Action performed:** `git show 4fbc906:paper/main.tex | sed -n '1550,1565p'`

**Result (exact bytes):** The Conclusion paragraph now explicitly splits paths:

> "...every one of which has been independently cross-validated against a second reference implementation in `paper/figures/scripts/validate_numbers.py` (AUX1 and C06a-d via scipy / numpy second-source primitives; C06e via a deterministic stdlib digest re-derivation plus a subprocess to the harness's behavioural-fingerprint script that recovers the exact-match and bucket-match rates, with explicit SKIP semantics when the runner cannot install chardet to re-execute it)."

No global "scipy / numpy implementation" claim remains. (Matches the r2 B3 remediation description in the same commit message.)

**Verdict:** PASS. Cited: paper/main.tex:1556-1559 (commit 4fbc906).

---

### verify_by 2 (Python --help)
**Commands executed:**
- `python3 validators/validate_gate_decision.py --help`
- `python3 validators/validate_gate_decision.py --help | grep -oE 'INV0[1-6]' | sort -u | wc -l && ... | sort -u`

**Result (exact stdout):**
```
usage: validate_gate_decision.py [-h] [--repo-root REPO_ROOT]
                                 paths [paths ...]

Validate a gate-decision instance against the hard invariants INV01..INV06
declared in profiles/agent-assurance/gate-decision-kind.toml. INV01: verdict-
failed_refs bijection. INV02: assertion-id regex on failed_constraint_refs[].
INV03: canonical observed(...) shape on override_refs[]. INV04: 64-hex
evidence_root. INV05: scope declaration only (no validator action; RUNTIME-
SPEC handles bundle/hash/override checks). INV06: self-modification cross-
provider AND predicate (deciding provider_id AND model_family_id MUST both
differ from proposing).
...
```
Grep output:
```
6
INV01
INV02
INV03
INV04
INV05
INV06
```

**Source bytes establishing the fix (commit 4fbc906):**
```diff
-    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
+    parser = argparse.ArgumentParser(
+        description=(
+            "Validate a gate-decision instance against the hard "
+            "invariants INV01..INV06 declared in "
+            ...
+            "INV06: self-modification cross-provider AND predicate "
+            "(deciding provider_id AND model_family_id MUST both differ "
+            "from proposing)."
+        ),
+    )
```
( validators/validate_gate_decision.py:259-273 )

This directly remediates the exact r2 S08.1 defect ("The shipped script passes only `__doc__.splitlines()[0]`... without the invariant enumeration").

**Verdict:** PASS. Cited: command output + validators/validate_gate_decision.py:260-272 (4fbc906).

---

### verify_by 3-9
All passed bytes-verified — see codex's parallel report for the matching observations across negatives, Rust+Go validators, CI step, kind-descriptor markers, and SPEC §12/§13 regression sweep.

**VERDICT: unconditional_approval**

(Full transcript abbreviated for storage; see job-id d6fdef50-d460-439e-b450-3b45aa0bb8a3 in llm-gateway result cache for the unabridged version.)
