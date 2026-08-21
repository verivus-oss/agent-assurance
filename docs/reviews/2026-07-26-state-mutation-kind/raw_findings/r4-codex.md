# Round 4, Codex: NOT APPROVED

Final verdict message, reproduced as received. Em dashes normalized to commas
per the repo writing convention. Gateway job
`0b24babf-0fde-423b-b224-9bd863e891d9`, 533 KB transcript.

Not approved.

I verified the round 3 Go RKC02 fix itself: the shipped
`mutation-claim-array-proof` case now fails in Python, Rust, and Go, in
explicit `mutation-kinds` mode and primary auto mode. The committed positive
and eleven negative mutation cases also matched across all three. I built both
primaries from this worktree, ran the CI-shaped closure sweep at 90 files, and
the descriptor/profile/IJB checks passed.

The blocker is one level above the latest fix: `meta.template_kind` is still a
typed selector that can collapse "absent or wrong shape" into "nothing to
validate." `spec.md:101` says `template_kind` is a string, and
`profiles/com.verivus.runtime/state-mutation-kind.toml:127` requires
`meta.template_kind = "state-mutation"`. But Python returns success when it is
not exactly one of the two strings at `validators/validate_state_mutation.py:274`,
Rust does the same at `tools/dagtoml-validate-rs/src/main.rs:3993`, and Go at
`tools/dagtoml-validate-go/main.go:3961`. Closure pin resolution also falls
through to no pins for non-string or absent `template_kind` at
`validators/validate_closure_root.py:224`, Rust
`tools/dagtoml-validate-rs/src/main.rs:4879`, and Go
`tools/dagtoml-validate-go/main.go:2631`.

Reproduction: starting from `examples/minimal-state-mutation.toml`, set
`meta.template_kind` to `1`, `["state-mutation"]`, or delete it, then honestly
re-root to the one-record `provenance.source_sha256` closure root
`sha256:1eb6d51951dddfcdd8bc4632afb23b9b96cd52b56321dfdae0dc7f62c719b534`. Rust
auto, Go auto, Rust explicit `--mode mutation-kinds`, Go explicit
`-mode mutation-kinds`, Python closure, and Python mutation validation all exit
0. That skips the state-mutation pins and the kind-layer RKM02/RKM04/RKM06
checks entirely.

Judgment call: this is structurally defect-prone, not merely converging. Four
rounds have now found the same class at scalar fields, table fields, forbidden
presence, and now dispatch. What ends it is a shared conformance corpus, run
against all three implementations in auto and explicit modes, with malformed
selector, wrong-type, absent, array-of-tables, datetime, and duplicate-key
cases written once. That would have caught rounds 2 and 3 if the corpus had
covered `mutation-claim`; today the design record honestly says that is still
missing at `design-record.md:358`, but the open list at `design-record.md:348`
is incomplete because it omits this selector bypass.

Must fix before merge: reject absent or non-string `meta.template_kind` before
kind dispatch and closure pin resolution can fall through, then add shared
conformance cases for it. Separate follow-up: replace ad hoc negative fixtures
with a corpus and reduce CI enumeration hazards recorded at
`design-record.md:369`.

BLOCKER: TEMPLATE-KIND-DISPATCH-BYPASS at
`validators/validate_state_mutation.py:274`,
`tools/dagtoml-validate-rs/src/main.rs:3993`, and
`tools/dagtoml-validate-go/main.go:3961`.

---

## Initiator note

Accepted in part. The reproduction is exact, including the fallback root, which
matches what the initiator independently computed before the verdicts returned
(`initiator-kind-dispatch-r4.md`).

The remedy Codex asks for is too broad in one respect: "reject absent **or**
non-string". SPEC 12 explicitly ratifies an ABSENT `template_kind` as an escape
from conformance scope, in the same sentence that ratifies a non-spec-reserved
string. Rejecting absence would break that ratified behaviour and is not what
landed. See the round-4 adjudication in `design-record.md`.
