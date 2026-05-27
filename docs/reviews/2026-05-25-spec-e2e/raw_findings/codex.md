method

Fresh-context byte review at repository HEAD `1e0e155e32829a3830187815e566893421b931e2`. I read the required files in order: `docs/reviews/2026-05-25-spec-e2e/verification_report.toml`, `SPEC.md`, `CLAUDE.md`, the core/profile descriptors and ontologies, validators and primary validator tools, `.github/workflows/validate.yml`, `Makefile`, `README.md`, and `tools/review-request-dag.toml` policy tables. I used sqry for workspace/code-tool discovery where applicable, then exact byte inspection and the required validator recipes for the closure checks.

Executed evidence includes:

- `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml` -> `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).`
- `rg '^\\[kind\\.abstraction_class\\]$' ... | wc -l` and `rg '^\\[kind\\.capability_envelope\\]$' ... | wc -l` -> `19` and `19`.
- `python3 validators/validate_closure_root.py --discover .` -> `CLOSURE-ROOT VALIDATION PASSED (75 file(s)).`
- `python3 validators/validate_ijb_conformance.py core/ontology.toml` -> pass.
- The exact multi-file IJB recipe for profile ontologies failed because `validate_ijb_conformance.py` accepts one `file` positional argument, not multiple. Running the three files individually passed.
- The literal S04 loop over every file under `examples/` failed on `examples/README.md` with a TOML parse error. A TOML-only loop with `--repo-root .` passed for 50 TOML files.
- `cd tools/dagtoml-validate-rs && cargo build --release --locked` -> pass, with two dead-code warnings.
- `cd tools/dagtoml-validate-go && go build -o /tmp/go ./...` -> pass.
- Rust and Go primaries both passed the 26-file canonical sweep from `.github/workflows/validate.yml:156-183`; an additional per-file loop returned `rs=PASS go=PASS` for all 26 targets.
- `make toml-conformance-install && make toml-conformance` failed at install because the sandbox blocks network/DNS access to `proxy.golang.org`; `make toml-conformance` alone passed using installed binaries with `185/185 valid + 358/358 invalid`, 13 skips. `make toml-conformance-rs` passed with `185/185 valid + 371/371 invalid`, zero skips.
- `python3 validators/validate_review_readiness.py profiles/agent-assurance/tiers/{solo,team,group,organization,enterprise}.toml` -> all five pass.
- `python3 validators/validate_profile_descriptor.py profiles/...` failed exactly as written because the CLI requires `--repo-root`; the corrected `--repo-root .` command passed for all three descriptors.
- `python3 validators/validate_implementation_dag.py tools/review-request-dag.toml` -> pass, 10 units, connected DAG.
- Banned-marker command from S10 returned empty output.

S01 - partial

SPEC anchors for the cited sections exist as headers: `SPEC.md:136` (§2.5), `SPEC.md:182` (§2.6), `SPEC.md:206` (§2.7), `SPEC.md:417` (§6.1), `SPEC.md:482` (§8), `SPEC.md:521` (§9.1), `SPEC.md:541` (§10), `SPEC.md:746` (§11), `SPEC.md:793` (§11.1), `SPEC.md:851` (§12), `SPEC.md:864` (§12.1), `SPEC.md:1142` (§12.11), and `SPEC.md:1195` (§13). The version-pin check is closed: `CLAUDE.md:115-121` requires pre-publication `schema_version = "1.0.0"` and `ontology_version = 1`, and a TOML parse script found `meta.schema_version checked 140`, `meta.ontology_version checked 31`, `bad count 0`.

The descriptor check is not closed. The verify_by list includes `kind-descriptor`, but the descriptor inventory maps every listed kind except `kind-descriptor` to an actual `*-kind.toml`; `kind-descriptor => MISSING`. This is not an accidental filesystem miss: `SPEC.md:124-134` explicitly says the spec does not ship `kind-descriptor-kind.toml` and tooling must not require it. That makes S01's verify_by inconsistent with SPEC bytes.

S02 - closed

The required abstraction validator passed exactly: `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).` Header counts across `core/*-kind.toml profiles/*/*-kind.toml` were `abstraction_class=19` and `capability_envelope=19`. SPEC §13 defines these blocks at `SPEC.md:1213-1233`.

S03 - open

The validator itself passed: `CLOSURE-ROOT VALIDATION PASSED (75 file(s))`, matching SPEC §12's conforming-document scope at `SPEC.md:864-898`. The spot-check requirements do not close. First, counting all TOML files carrying a root-level `closure_root` returned `114`, while the validator reports `75`; this is explainable by unblessed process TOMLs being skipped per `SPEC.md:878-883`, but it does not match S03's byte recipe wording. Second, a repository-wide TOML scan found `non-empty closure_root count 0`; every found `closure_root` is the empty sentinel. S03 requires at least one descriptor with a non-empty `closure_root` citing real upstream evidence, and no such bytes exist at HEAD.

S04 - partial

The core ontology passed IJB conformance. The three profile ontologies passed when run one at a time. The exact recipe `python3 validators/validate_ijb_conformance.py profiles/agent-assurance/ontology.toml profiles/cost/ontology.toml profiles/disclosure/ontology.toml` failed with `unrecognized arguments` because the CLI declares a single `file` positional. The literal "every file under examples/" loop also failed on `examples/README.md` because it is Markdown, not TOML. A corrected TOML-only loop over 50 TOML files with `--repo-root .` passed. The primitive set is present in SPEC §10 at `SPEC.md:568` and in the validator as `IJB_PRIMITIVES = ("thing", "scope", "path", "observed", "constraint", "time")`.

S05 - closed

Both primary validators built. The workflow's canonical target list is at `.github/workflows/validate.yml:143-187`; both binaries passed the whole list, and the per-file outcome comparison returned `rs=PASS go=PASS` for all 26 targets. README's claimed primary surface is at `README.md:140-144`; Rust exposes the modes and routes at `tools/dagtoml-validate-rs/src/main.rs:48-60` and `tools/dagtoml-validate-rs/src/main.rs:1031-1062`, while Go exposes the analogous routes at `tools/dagtoml-validate-go/main.go:822-833`. Profile-descriptor, disclosure kinds, §2.5-§2.7 meta checks, and §11.1 provenance encryption are reachable in both.

S06 - partial

Parser harnesses are wired to the parsers the primaries import: `tools/dagtoml-validate-go/go.mod:5` requires `github.com/BurntSushi/toml v1.4.0`; `tools/dagtoml-validate-rs/Cargo.toml` depends on `toml = { version = "0.8", ... }`; `tools/toml-test-decode-rs/Cargo.toml` uses the same `toml` 0.8 crate. `Makefile:16-19` pins `toml-test` and BurntSushi decoder versions, and `Makefile:65-83` wires the Go and Rust conformance targets. The full install command could not be completed in this sandbox because network is disabled, but the already-installed conformance binaries produced the expected pass counts for both Go and Rust.

S07 - partial

All five tier files validate as `contract-declaration` instances. The `[[contracts]].id` sets are non-decreasing: solo has C01-C05, team adds C06, group adds C07, organization adds C08-C09, and enterprise has C01-C09. The tiers README documents the ladder and cross-tier INV06 callout at `profiles/agent-assurance/tiers/README.md:13-37`. However, the same README says each tier's contract set is a strict superset at `profiles/agent-assurance/tiers/README.md:13-17`, and the files' header comments say enterprise is a strict superset of organization; by contract ID set, organization and enterprise are equal. The enterprise content strengthens statements, but the strict set-ladder claim is not literally true by the `[[contracts]]` list.

S08 - open

The invariant prose exists and is well-formed in the descriptor: `profiles/agent-assurance/gate-decision-kind.toml:92-105` explains the cross-provider/family rule, and `profiles/agent-assurance/gate-decision-kind.toml:199-204` defines hard invariant INV06 with BOTH inequalities and "same-provider/different-family" plus "different-provider/same-family" failure cases. The ontology vocabularies exist with `constraint/structural` tags at `profiles/agent-assurance/ontology.toml:349-374`. The worked example demonstrates anthropic/claude proposing and openai/gpt deciding at `examples/self-modification-gate-decision.toml:24-41`, and both primaries parse/pass it.

The closure is still open because the promised validator behavior does not exist. `python3 validators/validate_review_readiness.py examples/self-modification-gate-decision.toml` failed with `unable to detect template kind from TOML content`; there is no `validators/validate_gate_decision.py`; and both primary validators auto-route only profile-descriptor and disclosure kinds, not gate-decision (`tools/dagtoml-validate-rs/src/main.rs:1043-1055`, `tools/dagtoml-validate-go/main.go:822-829`). I created two negative variants in `/tmp`: same-provider/different-family and different-provider/same-family. Both variants passed both primaries. That directly contradicts the descriptor's claim that the SPEC layer verifies field presence, vocabulary membership, and inequality predicates at `profiles/agent-assurance/gate-decision-kind.toml:101-103`.

S09 - partial

The profile descriptor contents match profile kind files: agent-assurance lists the nine kind files at `profiles/agent-assurance/PROFILE.toml:27-44`; cost lists `cost-record` at `profiles/cost/PROFILE.toml:49-58`; disclosure lists its three kinds at `profiles/disclosure/PROFILE.toml:32-43`. A Python comparison of `contained_kinds` to actual `*-kind.toml` filenames returned `match = True` for all three. The corrected validator command with `--repo-root .` passed. The exact S09 command failed because `validate_profile_descriptor.py` requires `--repo-root`, so the verify_by recipe is not executable as written.

S10 - closed

The workflow has a single job `validate` at `.github/workflows/validate.yml:9-12`. The step matrix covers the requested surfaces: pinned third-party actions at `.github/workflows/validate.yml:13-40`; primary validator builds at `.github/workflows/validate.yml:42-53`; Taplo at `.github/workflows/validate.yml:72-84`; TOML conformance at `.github/workflows/validate.yml:86-113`; manifest drift and safe-tools at `.github/workflows/validate.yml:115-122`; parse all TOML at `.github/workflows/validate.yml:124-141`; primary canonical sweep at `.github/workflows/validate.yml:143-187`; Python cross-checks at `.github/workflows/validate.yml:189-204`; §13 and §12 at `.github/workflows/validate.yml:206-245`; kind descriptors, examples, IJB, tiers, rollback, provenance, skills, language fixtures, banned markers, and documented examples at `.github/workflows/validate.yml:247-505`. All `uses:` references are SHA-pinned. The S10 banned-marker command returned empty output.

S11 - partial

The review DAG itself is well-formed: `tools/review-request-dag.toml:31-44` declares `template_kind = "implementation-dag"` and 10 tier1 units; `python3 validators/validate_implementation_dag.py tools/review-request-dag.toml` passed with 10 units. A parsed edge walk over `depends_on` and `blocks` reached all U01-U10, so the DAG is connected. Policy tables enumerate the required roles, evidence, approval bases, unit classifications, process checks, permissions, persistence, and completion rules at `tools/review-request-dag.toml:56-128`.

The historical-review claim is not fully closed from bytes. Git log since 2026-05-21 shows many commits touching SPEC/core/profiles/validators, including 2026-05-21 commits `b1a4f38`, `9f2fecf`, `9db54c4`, `7965aa4`, and `7a159ca`, while the discovered `docs/reviews/*/terminal_decision.toml` sessions begin at 2026-05-23 for the listed terminal decisions. Later major arcs have clear review records in `CHANGELOG.md` and `docs/reviews/`, but "every commit touching SPEC.md / core/ / profiles/ / validators/ since 2026-05-21" is stronger than the persisted evidence I found.

S12 - open

The README accurately points to SPEC §13, the multi-profile surfaces, INV06, validation tooling, and the release tag exists: `git tag -l v2026-05-25T03-30-02Z` returned the tag and `git rev-parse` resolved it. The repository-map requirement is not closed. `README.md:99-126` lists many top-level directories and all seven `tools/<X>/` subdirectories, but `find . -maxdepth 1 -type d` shows additional top-level directories `paper/`, `paper-arxiv-prep/`, and `paper-hello-world/` that are not listed. Dot/tooling directories can reasonably be excluded from a human repo map, but these paper directories are ordinary top-level repo content. README also claims the full CI matrix at `README.md:184-192`; that broadly matches the workflow.

final blockers

1. S08 is a concrete blocker: INV06 is documented as SPEC-layer verified, but no shipped validator rejects either negative case. Both primary validators passed same-provider/different-family and different-provider/same-family self-modification gate-decision variants.
2. S03 is open: no non-empty `closure_root` exists anywhere, contradicting S03's required spot-check.
3. S12 is open: README's repository map omits ordinary top-level paper directories.
4. S01/S04/S09 contain verify_by/spec inconsistencies: required recipes demand impossible or unsupported checks.

Terminal verdict: concrete_unresolvable_blocker
Blocker: `profiles/agent-assurance/gate-decision-kind.toml:101-103` says the SPEC layer verifies INV06 field presence, vocabulary membership, and both inequality predicates, and `profiles/agent-assurance/gate-decision-kind.toml:201-202` marks INV06 as a hard invariant, but no shipped validator enforces it: `tools/dagtoml-validate-rs/src/main.rs:1043-1055` and `tools/dagtoml-validate-go/main.go:822-829` route auto-mode only to profile-descriptor and disclosure validators, `validators/validate_gate_decision.py` is absent, `validate_review_readiness.py` cannot detect the self-modification gate-decision kind, and both primary validators accepted same-provider/different-family plus different-provider/same-family negative variants that INV06 says must fail.
