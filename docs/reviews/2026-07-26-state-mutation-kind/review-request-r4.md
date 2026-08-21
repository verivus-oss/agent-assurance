# Independent design review request, round 4: the round-3 fix, and whether this is converging

Instantiates `tools/review-request-dag.toml`. Rounds 1 to 3 and their verdicts
are in this directory (`review-request*.md`, `raw_findings/`,
`raw_findings/r2-*.md`, `raw_findings/r3-*.md`).

- **Initiator (excluded from the standard reviewer set):** Claude (Opus 5), in
  Werner Kasselman's session, 2026-07-27.
- **Reviewer models this round:** Codex, Grok, Devin.
- **Under review:** `4b777bb` on branch `profile/state-mutation-kind`, and the
  stack `8290eb3..4b777bb` against `origin/main` (`f9a37cf`).
- **Worktree:** `/srv/repos/external/verivus-oss/aa-state-mutation`

**Devin has not reviewed this before.** Rounds 1 to 3 used Codex, Gemini, Grok
and Mistral. Devin is here for fresh eyes: read the prior rounds for facts, but
do not treat their conclusions as settled, and do not assume the questions they
asked were the right ones.

## Get the diff yourself

```sh
cd /srv/repos/external/verivus-oss/aa-state-mutation
git log --oneline origin/main..HEAD
git show 4b777bb                     # the round-3 fix, under review
git show d333d52                     # the round-2 fix, which contained it
git diff origin/main..HEAD           # the whole stack
```

Build both primaries from THIS worktree and run them. **Do not use the prebuilt
binary at
`/srv/repos/external/verivus-oss/agent-assurance/tools/dagtoml-validate-go/`**;
it is pre-12.8.1 and silently computes 1-record closures.

```sh
cd tools/dagtoml-validate-rs && cargo build --release
cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go .
```

## The pattern you are being asked to break

Three rounds, three blockers, and **each one lived inside the fix for the
previous one**. All three are the same defect wearing different clothes: a
typed accessor that collapses "absent" and "present but wrong shape" into a
single skip path.

| Round | Level | Consequence |
|---|---|---|
| 2 | proof scalars (`scheme = ""`, `scheme = 1`) | primaries accepted a proof declaring no proving system |
| 3 | forbidden table (`execution_proof = [{...}]` on a claim) | Go accepted a claim carrying a complete provider receipt |
| 3 | required tables (`mutation = 1`) | all three rejected, but reported a present field as missing |

## Priority 1: the round-3 fix, and whether the class is exhausted

`4b777bb` adds `hasKey` in Go and splits present-but-not-a-table from absent at
four sites across three implementations. It is unreviewed.

- Break it. Is there a THIRD level of this collapse that rounds 2 and 3 did not
  reach? Candidates worth trying rather than reasoning about: a table nested
  inside a required table; `[[execution_proof]]` as an array-of-tables header
  rather than an inline array; a key whose TOML type differs between the Python
  shim `validators/_toml11.py` and BurntSushi/toml and the Rust `toml` crate;
  duplicate keys; a key present with a TOML datetime rather than a string;
  `meta.template_kind` itself being non-string or absent, which is what selects
  the whole validation path.
- **`meta.template_kind` is worth its own attention.** Every kind-layer check in
  all three implementations dispatches on it. What happens when it is an
  integer, an array, or absent? Does each implementation silently validate
  NOTHING, and is that the same across all three? A document that skips
  validation entirely is a worse outcome than one that fails a check.
- Does `hasKey` have the same blind spot in the other direction? It is used for
  a forbidden field. Are there other FORBIDDEN or MUST-BE-ABSENT conditions
  anywhere in these kinds, or in `api-snapshot` (RKV03 concerns absent witness
  fields), that are still enforced through a typed accessor?

## Priority 2: is this converging, and what would end it

This is the question the initiator most wants answered, and it is a judgment
call rather than a defect hunt. Answer it explicitly.

Three rounds have each found a real bypass in the previous round's fix. Two
readings:

1. The review is working. Each round is finding genuinely rarer defects, the
   severity is dropping, and it is converging.
2. The approach is structurally defect-prone. Hand-porting kind invariants into
   three implementations in three languages, verified by fixtures the initiator
   writes after the fact, will keep producing this class indefinitely, and no
   number of rounds fixes that.

If you think it is (2), say what would actually end it. The obvious candidate
is already an open item: `conformance/cases/` as a shared corpus that all three
implementations are driven from, so a case is written once and every
implementation must agree, rather than each fixture being asserted ad hoc in
`validate.yml`. `mutation-claim` has no conformance cases at all and has not had
any since round 1. Would that have caught rounds 2 and 3? Be concrete.

## Priority 3: merge readiness

Nothing in this stack has been pushed or merged. State plainly what remains
before it should land, separating:

- defects that MUST be fixed first,
- work that should follow in a separate change,
- and things recorded as open that you think are acceptable to carry.

The recorded open items are at the end of `design-record.md`. Check whether
that list is honest and complete. Round 2 found the design record claiming a CI
sweep passed when it was red, so do not take it on trust.

## Priority 4 (Devin especially): what has nobody asked

Rounds 1 to 3 converged on one defect class and hammered it. Two rounds ago the
board missed calendar validity entirely while three reviewers independently
found the same Unicode gap, which is redundancy on one axis and a hole on
another.

Name something no round has examined. Candidates nobody has touched: the
capability envelope and abstraction-class declarations (SPEC 13); whether
`mutation-claim` promotion to `state-mutation` is genuinely mechanical when run
end to end rather than asserted in prose; what a CONSUMER is supposed to do with
these records and whether the kind descriptors say enough for one to be written;
the interaction between these kinds and the tier bindings in
`profiles/agent-assurance/tiers/`; whether the ontology vocabularies are the
right shape at all.

## Rules

- Verify against files. Cite `path:line`. Do not accept this document, the
  design record, the verification log, or any previous round's verdict as
  evidence of anything.
- Approve only what you inspected. Not on intent, not on plan-compliance, not
  on "should be fixed".
- If you cannot build or run a primary, say so explicitly and do not infer
  parity from the Python result. Round 2 produced a blocker that a single
  execution would have refuted.
- End with unconditional approval or one concrete named blocker. If you have no
  blocker, say so plainly rather than inventing one to look thorough: a fourth
  round with nothing to report is a real and useful result.
- Never use the em dash character in prose you write.
