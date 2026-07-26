# Initiator verification log

Initiator: Claude (Opus 5), Werner Kasselman's session, 2026-07-26.
Target: commit `8290eb3` on `profile/state-mutation-kind`.

Written AFTER the review was dispatched and deliberately kept out of the
reviewed commit, so the artefacts under review did not move mid-flight. This
records evidence, not changes.

## Cross-implementation parity for RKM01 and RKM02-by-deletion

The design record's central claim is that deleting `[execution_proof]` and
honestly re-rooting removes two REQUIRED pins and is therefore rejected by all
three closure implementations, unlike the api-snapshot witness, whose
`when-present` pin permits an honestly re-rooted unwitnessed document.

When the review was dispatched, that claim had been run against the **Python**
validator only. It has now been run against all three.

| Implementation | api-snapshot positive (control) | state-mutation positive | `state-mutation-no-proof` |
|---|---|---|---|
| Python `validate_closure_root.py` | PASSED | PASSED | REJECTED, 2 missing required pins |
| Go primary | PASSED | PASSED | REJECTED, 2 missing required pins |
| Rust primary | PASSED | PASSED | REJECTED, 2 missing required pins |

Both primaries emit the identical diagnostic pair:

```
pinned closure record `execution_proof.binds_sha256` (required by profile
`com.verivus.runtime`, SPEC §12.8.1) is missing
pinned closure record `execution_proof.proof_sha256` (required by profile
`com.verivus.runtime`, SPEC §12.8.1) is missing
```

The two deliberately closure-valid negatives behave as designed in the
primaries as well: `state-mutation-unbound-proof` and
`state-mutation-inlined-proof` both PASS the Rust closure layer, confirming
they are kind-layer-only rejections (RKM04 and RKM03) rather than closure
failures.

The control column matters: without it, a primary that rejected everything
would look like it was enforcing the new pins.

## A trap that cost a false negative, recorded so the next person avoids it

The first Go run used the prebuilt binary at
`agent-assurance/tools/dagtoml-validate-go/dagtoml-validate-go`. It rejected
the state-mutation positive, computing a **1-record** closure. That looked like
the pins failing to resolve for a new kind.

It was a stale binary. The control test settles it: the same binary also
rejects the shipped, known-good `examples/minimal-api-snapshot.toml`,
computing the pre-promotion source-only root
`sha256:f251f64b...`. The binary was built from the
`/srv/repos/external/verivus-oss/agent-assurance` checkout, which sits on a
pre-12.8.1 branch and has no pin support at all.

**Action for the repo, outside this change:** that prebuilt binary produces
silently wrong verdicts on every pinned document. It should be rebuilt or
removed. A stale primary that passes documents it should reject is worse than
no primary, because CI-shaped commands run against it look green.

Both primaries used for the table above were built from this worktree:

```sh
cd tools/dagtoml-validate-go && go build -o <path> .
cd tools/dagtoml-validate-rs && cargo build --release
```

## Not yet verified

- No conformance cases exist for this kind, so the frozen parity matrix has no
  `conformance/cases/state-mutation/` entries. Design record gap 2 stands.
- The CI negative-agreement block added in `8290eb3` was verified by running
  its commands by hand, not by executing the workflow.
