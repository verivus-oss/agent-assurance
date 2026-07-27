# Round 4, Devin: NOT APPROVED (first review in this series; static only)

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention. Gateway job `61a55d7b-e17f-4f2b-b649-7b90ca2e2fef`.

---

I attempted the requested build commands, but the session rejected `cargo`,
`go`, and `git` exec calls because it is running in non-interactive mode
without `--permission-mode dangerous`. I therefore inspected the Rust and Go
source directly and did not infer parity from the Python reference.

Priority 1: the round-3 `hasKey` / `tableOf` split closes the table-level
absent/wrong-typed collapse for `execution_proof` and `mutation`. I then looked
at the routing key itself.

Priority 4 / blocker: no earlier round tested what happens when
`meta.template_kind` is absent or not a string. SPEC 2 says every file MUST
have `[meta]` with `template_kind` as a string (`spec.md:61-68`,
`spec.md:101-104`), and `state-mutation-kind.toml` declares
`meta.template_kind` required with `must_equal = "state-mutation"`
(`state-mutation-kind.toml:127-132`). Both primaries read it with an accessor
that defaults a non-string or missing value to `""`, and then their auto-mode
switch has an empty `""` case that performs no kind-specific validation. A
`state-mutation` with `template_kind = 1` (or missing `template_kind`) skips
RKM02/RKM03/RKM04/RKM06; a `mutation-claim` carrying `[execution_proof]` with
`template_kind = 1` skips RKC02. The closure layer does not save this because
`pinnedClosureInputs` returns an empty pin list for an unresolvable
`template_kind`, and IJB instance validation does not require `template_kind`
either.

Citations:

- Go dispatch collapse: `tools/dagtoml-validate-go/main.go:3489` (`stringOf`
  default to `""`), `main.go:3537` (`case ""` with no validation), and
  `main.go:2291-2306` (`validateMeta` checks `schema_version`,
  `ontology_version`, `docs`, `confidentiality`, but never `template_kind`).
- Rust dispatch collapse: `tools/dagtoml-validate-rs/src/main.rs:5118-5122`
  (`as_str().unwrap_or("")`), `main.rs:5194` (`"" => {}`), and
  `main.rs:4466-4470` (`validate_meta_fields` returns early if `[meta]` is not
  a table and never requires `template_kind`).

Priority 2 judgment: this is not a rarer residual defect; it is a top-level
routing bypass. A shared `conformance/cases/state-mutation/` corpus would
likely have caught it, because a single `template_kind = 1` fixture would be
accepted by all three implementations unless the dispatch is fixed. I leave the
conformance corpus as a follow-up.

Priority 3: before merge, the primaries must reject a missing or non-string
`meta.template_kind` in `validateMeta` / `validate_meta_fields`.

BLOCKER: `META-TEMPLATE-KIND-TYPE-AND-PRESENCE-BYPASS` at
`tools/dagtoml-validate-go/main.go:3489` (same collapse in
`tools/dagtoml-validate-rs/src/main.rs:5118`).

---

## Initiator note

Accepted in part, and a good first showing: Devin found the deepest defect in
the series on its first pass, having read the code rather than run it.

Two corrections, both to the same half of the finding.

**The "missing `template_kind`" half is wrong.** Devin cites `spec.md:61-68`
and `spec.md:101-104` for a MUST, but SPEC 12 (`spec.md:972-985`) says the
opposite in as many words: "Producers that want a file outside the rule's scope
MUST give it a non-spec-reserved `template_kind` (or no `template_kind` at
all)." Absence is a ratified escape from conformance scope, not a bypass.
Rejecting it would break behaviour the spec guarantees. Only the non-string
case is malformed, because SPEC 2.3 says `template_kind` IS a string.

**Devin could not execute anything.** That is the second static-only reviewer
in this series. Unlike Mistral in round 2, Devin's finding did reproduce
exactly, so the record should be fair: static reading found a real and serious
defect here. It also produced the over-broad remedy, which one execution of the
absent-`template_kind` case against a re-rooted document would have flagged,
since that case legitimately passes.

The gateway invocation used `permissionMode: "auto"`, which was not sufficient
for build commands. A future Devin dispatch needs `dangerous`, or the reviewer
should be treated as a static analyst by design.
