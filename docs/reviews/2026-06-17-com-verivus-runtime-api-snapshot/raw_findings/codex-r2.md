# Codex review — iteration 2 — UNCONDITIONAL APPROVAL

Job 77be605a-f326-47ea-a20a-228a496a8637 (codex-cli 0.140.0, gpt-5.5), exit 0.
Both prior blockers closed on inspected code + re-run command output:
- Probe 1 (raw `accept`): now FAILS with RKV02 "snapshot.request.accept is not an
  allowed field", RC=1.
- Probe 2 (zeroed descriptor_sha256): now FAILS with RKV01 "does not equal the
  SHA-256 of the request-descriptor sub-part", RC=1.
- Positive instance passes (RC=0).
- New negatives api-snapshot-raw-header (RKV02) and api-snapshot-bad-subpart-digest
  (RKV01) both reject; bad-subpart also fails validate_provenance (declared 621 vs
  actual 620).
- No closure regression: discovered set excluding examples/negative = 86 targets;
  Rust, Go, Python all RC=0. bad-closure and bad-ijb rejected by all three.
- The non-DAGTOML-API-CAPTURE/1 skip judged "a documented RUNTIME-SPEC boundary,
  not a hole". No remaining concrete blocker.
