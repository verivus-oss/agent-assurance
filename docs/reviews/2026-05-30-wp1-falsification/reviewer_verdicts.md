# WP1 Falsification — Reviewer Verdicts

Date: 2026-05-30 UTC
Target commit: `4f48edd`.
Falsification target: `falsification_target.md` (this directory).
Initiator: Claude (the session that authored the findings). Reviewers
were instructed to **refute**, default-to-refuted, and verify against
the actual source — not approve the initiator's summary.

## Dispatch transport

All three dispatched via the llm-gateway MCP async API against the live
repo at `/srv/repos/external/verivus-oss/agent-assurance`.

| Reviewer | Model | Job | Result |
| --- | --- | --- | --- |
| Gemini | gemini pro | `2df4c494-21b3-4535-8f28-b68fc764c9a5` | completed, inspected files, CONFIRMED #1 + #2 |
| Codex | gpt-5.4 | `07abda2c-6e9c-47d9-bf09-8f72cbbcb63f` | completed, inspected files, CONFIRMED #1 + #2 |
| Grok | latest | `59a37f5e…`, `a8992eb6…` (x2) | environment blocker — worker-init transport crash before any read; no verdict |

Grok failure is identical to the 2026-05-29 round: `worker quit with
fatal: unexpected server response: expect initialized` on this host,
independent of permission mode and MCP-server selection. Recorded as a
provider-environment blocker, not a finding against the commit.

## Gemini verdict (verbatim)

> FINDING #1: CONFIRMED — All refutation attempts fail. The spec at
> `spec.md` §11 requires `source_path` to resolve under the repo root.
> The Python validator at `validators/validate_provenance.py:95-109`
> correctly implements this containment check. The Rust and Go
> validators do not. The call sites in `…rs/src/main.rs:4112` and
> `…go/main.go:2978` show that unsanitized input from the TOML file is
> passed directly to the vulnerable path-joining logic at
> `…rs/src/main.rs:898` and `…go/main.go:692`. There is no prior
> validation. A minimal negative fixture that passes in Rust/Go but
> fails in Python is a provenance attestation with
> `source_path = "/etc/passwd"`.
>
> FINDING #2: CONFIRMED — All refutation attempts fail. The Go
> implementation at `…go/main.go:3085-3096` has a helper function
> `gdAsTableArray` that silently filters out any non-table elements
> from `failed_constraint_refs` before the invariant `verdict == "pass"
> iff failed_constraint_refs is empty` is checked against the filtered
> length at `main.go:3180`. The Rust implementation at
> `…rs/src/main.rs:3447` iterates the unfiltered array… A minimal
> negative fixture is a `gate-decision` document with `verdict = "pass"`
> and `failed_constraint_refs = ["not-a-table"]`. This input is accepted
> by Go but rejected by Rust.

## Codex verdict (verbatim)

> FINDING #1: CONFIRMED — I could not refute the repo-escape defect.
> Both primaries invoke provenance binding directly with no prior
> `source_path` sanitization in auto/provenance-binding mode
> (`…rs/src/main.rs:4106-4113`, `…go/main.go:2973-2979`), and the
> binding checks themselves only read `repo_root.join(source_path)` /
> `os.ReadFile(filepath.Join(repoRoot, sourcePath))` with no
> absolute-path rejection or containment check (`…rs/src/main.rs:921-931`,
> `…go/main.go:692-695`). Python does reject both… (`validate_provenance.py:95-109`),
> which matches SPEC §11 (`spec.md:786-804`). **The only narrowing I
> found is that auto mode separately validates `source_sha256` shape via
> closure-root code (`…rs/src/main.rs:3894-3914`, `…go/main.go:2366-2378`),
> so that subpoint is overstated, but it does not fix containment.**
> Minimal negative fixture: take `examples/negative/provenance-wrong-source-sha.toml`
> and set `source_path = "../../../../../etc/passwd"`…
>
> FINDING #2: CONFIRMED — I could not make the Rust and Go verdicts
> agree. Go normalizes `failed_constraint_refs` through `gdAsTableArray`,
> which keeps only table elements… `failed_constraint_refs = ["A-1"]`
> becomes empty/nil before INV01, and Go then checks
> `len(failedRefs) == 0` and reports no INV01/INV02 defect
> (`…go/main.go:3177-3197`). Rust instead preserves the raw TOML array
> for INV01 and explicitly reports non-table elements in INV02
> (`…rs/src/main.rs:3427-3453`). The gate-decision path is definitely
> live in both validators. Minimal negative fixture: start from
> `examples/minimal-gate-decision.toml`, change `verdict = "pass"` and
> replace the refs with `failed_constraint_refs = ["A-1"]`; Go accepts,
> Rust reports INV01 plus `INV02 violated: failed_constraint_refs[0] is
> not a table`.

## Terminal state

- **Finding #1 (provenance repo-escape):** CONFIRMED by two independent
  reviewers. Correction adopted: the initiator's sub-claim that
  `source_sha256` hex-shape is unvalidated in Rust/Go is **withdrawn** —
  auto mode validates the shape via the closure-root path. The
  **containment** defect stands.
- **Finding #2 (gate-decision INV01 Rust/Go divergence):** CONFIRMED by
  two independent reviewers.

Both findings proceed to fix. The fix is itself a validator change and
will be dispatched for independent review per the no-self-approval rule.
