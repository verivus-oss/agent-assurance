# Codex r2 review: README defect-fix commit 953691b

## Method

Scope reviewed: commit `953691b` (`README: fix factual defects flagged by r1 review`) and the requested correction diff `git diff b759eaf..953691b -- README.md`.

I inspected the required artifacts from bytes rather than accepting the initiator summary:

- `docs/reviews/2026-05-25-readme-restructure-r2/verification_report.toml`
- `docs/reviews/2026-05-25-readme-restructure/raw_findings/codex.md`
- `docs/reviews/2026-05-25-readme-restructure/raw_findings/grok.md`
- `README.md` at current `HEAD` (`953691b`)
- `git diff b759eaf..953691b -- README.md`
- `tools/review-request-dag.toml` policy blocks

Repository state checks:

```sh
$ git log --oneline -2
953691b README: fix factual defects flagged by r1 review
0bac872 paper-hello-world: update for post-§13 spec state + validator triad

$ git show --stat --oneline 953691b
953691b README: fix factual defects flagged by r1 review
 README.md | 9 +++++----
 1 file changed, 5 insertions(+), 4 deletions(-)

$ git diff --numstat b759eaf..953691b -- README.md
5	4	README.md
```

Note: the wider ancestry range `b759eaf..953691b` also includes intervening commit `0bac872` and therefore `paper-hello-world/main.tex`; `git show 953691b` confirms the defect-fix commit itself is README-only. I treated the requested README correction diff as the review scope.

Additional executed checks included the D1-D4 `verify_by` recipes, source inspections of the Rust and Go primary validator mode sets, CI workflow inspection around the primary-validator and Python-only steps, a re-check of C01-C07 surfaces, and an internal README link audit:

```sh
$ python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).

$ python3 - <<'PY'
from pathlib import Path
import re
def slug(s):
    s = s.strip().lower()
    s = re.sub(r'`([^`]*)`', r'\1', s)
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'\s+', '-', s)
    return s.strip('-')
root = Path('.')
readme = Path('README.md').read_text()
links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', readme)
missing = []
checked = 0
for link in links:
    if re.match(r'^[a-z]+://', link):
        continue
    path, frag = (link.split('#', 1) + [''])[:2] if '#' in link else (link, '')
    if not path:
        continue
    p = root / path
    checked += 1
    if not p.exists():
        missing.append((link, 'missing path'))
        continue
    if frag and p.suffix.lower() in {'.md', ''}:
        headings = set()
        for line in p.read_text(errors='ignore').splitlines():
            m = re.match(r'^(#{1,6})\s+(.*)$', line)
            if m:
                headings.add(slug(m.group(2)))
        if frag not in headings:
            missing.append((link, 'missing anchor'))
print(f'internal_checked={checked} missing={len(missing)}')
PY
internal_checked=40 missing=0
```

Policy confirmations: this README-only correction does not introduce active-user migration or behavior-change guidance changes; the README still points backwards-incompatible changes to migration notes and SPEC §8 at `README.md:47-50`. I found no historical dated spec retcon without a link or correction note. Claimed checks that I relied on were run locally with command output recorded here. This file is the persisted review evidence required by policy.

## Per-D classification

### D1: closed

The invalid `--discover` invocation for `validate_abstraction_class.py` is gone:

```sh
$ grep -n 'validate_abstraction_class.*--discover' README.md
```

Output: no lines, exit status 1.

The README now shows the explicit `--repo-root` plus kind-descriptor glob invocation:

```sh
$ grep -A2 -n 'validate_abstraction_class' README.md
180:python3 validators/validate_abstraction_class.py --repo-root . \
181-  core/*-kind.toml profiles/*/*-kind.toml                        # SPEC §13
182-```
```

Executing the documented command from the repository root exits 0:

```sh
$ python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).
```

Evidence: `README.md:180-181`, `.github/workflows/validate.yml:217-222`, and the executed command output above.

### D2: closed

The README no longer claims the Rust primary is authoritative for `cost`:

```sh
$ grep -n 'Authoritative for.*cost' README.md
```

Output: no lines, exit status 1.

The replacement row is:

```text
README.md:142: Authoritative for profile-descriptor, the disclosure-profile kinds, §2.5–§2.7 meta surface, and §11.1 `[provenance.encryption]` sub-table
```

The primary validator mode sets still do not include `cost`:

```text
tools/dagtoml-validate-rs/src/main.rs:45-56 defines Auto, Profile, Disclosure, Provenance, Meta.
tools/dagtoml-validate-rs/src/main.rs:78-87 accepts --mode auto|profile|disclosure|provenance|meta.
tools/dagtoml-validate-go/main.go:113-118 defines modeAuto, modeProfile, modeDisclosure, modeProvenance, modeMeta.
tools/dagtoml-validate-go/main.go:121-134 accepts auto|profile|disclosure|provenance|meta.
```

The Python cost validator exists:

```sh
$ ls validators/validate_cost*.py
validators/validate_cost.py
```

CI also places cost-record validation in the Python cross-check step:

```text
.github/workflows/validate.yml:189-204 runs validators/validate_profile_descriptor.py, validators/validate_disclosure.py, and validators/validate_cost.py.
```

Evidence supports the revised README wording and closes the r1 `cost` overclaim.

### D3: closed

The old bytewise-agreement claim is gone:

```sh
$ grep -n 'bytewise agreement' README.md
```

Output: no lines, exit status 1.

The replacement row accurately describes the CI gate:

```sh
$ grep -A1 -n 'CI runs both' README.md
143:| Semantics — **primary** | `tools/dagtoml-validate-go/` (safe Go, no `unsafe` import) | Same surface as Rust; CI runs both against every canonical example + tier file + profile descriptor on each push, and both must exit 0 |
144-| Semantics — reference | `validators/*.py` | Cross-check on the primaries' surface, plus the kind-specific surfaces currently Python-only (cost-record, abstraction-class §13, closure-root §12, rollback-plan trigger closure, IJB conformance) |
```

The CI workflow runs both primary validators sequentially over the same target array, and both must exit 0:

```text
.github/workflows/validate.yml:143-187 defines the Rust + Go primary sweep, builds the shared target list, runs "$rs" --repo-root . "${targets[@]}", then runs "$go_bin" --repo-root . "${targets[@]}".
```

The compare-step grep returned no lines:

```sh
$ grep -nE 'diff|cmp.*output|compare.*primary' .github/workflows/validate.yml
```

Output: no lines, exit status 1.

This closes the r1 bytewise-agreement defect.

### D4: closed

The Python reference row now enumerates the Python-only surfaces:

```sh
$ grep -A1 -n 'Semantics — reference' README.md
144:| Semantics — reference | `validators/*.py` | Cross-check on the primaries' surface, plus the kind-specific surfaces currently Python-only (cost-record, abstraction-class §13, closure-root §12, rollback-plan trigger closure, IJB conformance) |
145-| Symbol traceability (optional) | `validators/validate_code_symbols.py` (sqry-backed) | Confirms `[[code]]` symbols in traceability files exist in real Rust/Go/TypeScript/Java sources |
```

Each named Python-only validator exists:

```sh
$ ls validators/validate_cost*.py validators/validate_abstraction_class.py validators/validate_closure_root.py validators/validate_rollback_plan.py validators/validate_ijb_conformance.py
validators/validate_abstraction_class.py
validators/validate_closure_root.py
validators/validate_cost.py
validators/validate_ijb_conformance.py
validators/validate_rollback_plan.py
```

CI evidence also matches the distinction: cost is under the Python cross-check at `.github/workflows/validate.yml:202-204`, abstraction-class is under `.github/workflows/validate.yml:217-222`, and the primary sweep remains `.github/workflows/validate.yml:143-187`.

## Regression check on C01-C07

### C01: closed

The obsolete public-release premise remains absent, while the calendar-UTC tag convention remains present:

```sh
$ grep -nE 'after.*made public|calendar-versioned UTC' README.md
45:Release tags use calendar-versioned UTC timestamps

$ git tag --list 'v*'
v2026-05-25T03-30-02Z
```

No regression.

### C02: closed

The repository still has seven `tools/*/` subdirectories, all still listed in the README Repository Map along with `Makefile`:

```sh
$ ls -d tools/*/
tools/dagtoml-duckdb-go/
tools/dagtoml-duckdb/
tools/dagtoml-rdf-go/
tools/dagtoml-rdf/
tools/dagtoml-validate-go/
tools/dagtoml-validate-rs/
tools/toml-test-decode-rs/

$ grep -nE '^tools/|^Makefile' README.md
113:tools/dagtoml-validate-rs/      Primary safe-Rust validator
114:tools/dagtoml-validate-go/      Primary safe-Go validator
115:tools/dagtoml-rdf/              Rust generator → RDF/Turtle
116:tools/dagtoml-rdf-go/           Go port of dagtoml-rdf
117:tools/dagtoml-duckdb/           Rust generator → DuckDB
118:tools/dagtoml-duckdb-go/        Go port of dagtoml-duckdb
119:tools/toml-test-decode-rs/      toml-test conformance shim (Rust parser)
125:Makefile                        Developer convenience targets (toml-conformance{,-rs,-all})
```

No regression.

### C03: closed

The Start Here enforcement pointers remain present:

```sh
$ grep -nE 'SPEC\.md#12|SPEC\.md#13|INV06|profiles/cost|profiles/disclosure|tiers/README' README.md
80:| Declare abstraction boundaries and capability envelopes | [SPEC.md §13](SPEC.md#13-abstraction-class-and-capability-envelope) |
81:| Propagate brittleness through upstream evidence | [SPEC.md §12](SPEC.md#12-the-closure-root-rule-brittleness-propagation) |
83:| Pick a deployment tier (`solo` ⊂ `team` ⊂ `group` ⊂ `organization` ⊂ `enterprise`) | [profiles/agent-assurance/tiers/README.md](profiles/agent-assurance/tiers/README.md) |
84:| Forbid an agent from approving its own self-modifying gate-decision (INV06) | [profiles/agent-assurance/gate-decision-kind.toml](profiles/agent-assurance/gate-decision-kind.toml) (search for `INV06`) |
85:| Account for cost as a first-class artifact | [profiles/cost/PROFILE.toml](profiles/cost/PROFILE.toml), [profiles/cost/cost-record-kind.toml](profiles/cost/cost-record-kind.toml) |
86:| Redact or selectively disclose evidence | [profiles/disclosure/PROFILE.toml](profiles/disclosure/PROFILE.toml), [profiles/disclosure/disclosure-attestation-kind.toml](profiles/disclosure/disclosure-attestation-kind.toml), [profiles/disclosure/redaction-manifest-kind.toml](profiles/disclosure/redaction-manifest-kind.toml), [profiles/disclosure/selective-disclosure-proof-kind.toml](profiles/disclosure/selective-disclosure-proof-kind.toml) |
108:profiles/cost/                  Optional Cost Profile (cost-record kind)
109:profiles/disclosure/            Optional Disclosure Profile

$ grep -nE '^### If you want to (understand|author|enforce|implement)' README.md
56:### If you want to understand the format
66:### If you want to author DAG-TOML
76:### If you want to enforce policy
88:### If you want to implement a validator
```

No regression.

### C04: closed

The Local Validation block still references the full validator workflow, and the r1-invalid abstraction command is now executable:

```sh
$ grep -nE 'taplo lint|cargo build --release|go build|make toml-conformance-install|make toml-conformance-all|validate_ijb_conformance|validate_closure_root|validate_abstraction_class' README.md
160:taplo lint
163:cd tools/dagtoml-validate-rs && cargo build --release && cd -
164:cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./... && cd -
167:make toml-conformance-install
168:make toml-conformance-all   # runs both Go-parser and Rust-parser suites
178:python3 validators/validate_ijb_conformance.py core/ontology.toml
179:python3 validators/validate_closure_root.py --discover .         # SPEC §12
180:python3 validators/validate_abstraction_class.py --repo-root . \

$ ls validators/validate_ijb_conformance.py validators/validate_closure_root.py validators/validate_abstraction_class.py validators/validate_implementation_dag.py validators/validate_traceability.py validators/validate_review_readiness.py
validators/validate_abstraction_class.py
validators/validate_closure_root.py
validators/validate_ijb_conformance.py
validators/validate_implementation_dag.py
validators/validate_review_readiness.py
validators/validate_traceability.py

$ grep -nE '^(toml-conformance-install|toml-conformance-all|toml-conformance|toml-conformance-rs):' Makefile
64:toml-conformance-install: ## Install pinned toml-test + BurntSushi decoder under $GOBIN.
68:toml-conformance: ## Run TOML 1.0 spec-conformance suite against the BurntSushi parser used by tools/dagtoml-validate-go.
73:toml-conformance-rs: ## Run TOML 1.0 spec-conformance suite against the `toml` crate used by tools/dagtoml-validate-rs.
85:toml-conformance-all: toml-conformance toml-conformance-rs ## Run both Go-parser and Rust-parser conformance suites.
```

No regression.

### C05: closed

The Validation tooling section and triad rationale remain present, with D2/D3 wording corrected:

```sh
$ grep -nE '## Validation tooling|Taplo|toml-lang/toml-test|#!\[forbid\(unsafe_code\)\]|unsafe-free|cross-check|one implementation cannot self-vouch' README.md
94:| Python reference validators (cross-check, not normative) | [validators/](validators/) |
112:validators/                     Python reference validators (cross-check)
132:## Validation tooling
140:| Syntax | [Taplo](https://taplo.tamasfe.dev/) | TOML 1.0 lint, duplicate-key detection |
141:| Parser conformance | `toml-lang/toml-test` suite | Verifies the parsers the primary validators import (`BurntSushi/toml` for Go, `toml 0.8` crate for Rust) |
142:| Semantics — **primary** | `tools/dagtoml-validate-rs/` (safe Rust, `#![forbid(unsafe_code)]`) | Authoritative for profile-descriptor, the disclosure-profile kinds, §2.5–§2.7 meta surface, and §11.1 `[provenance.encryption]` sub-table |
148:legal-grade artifacts; one implementation cannot self-vouch. Rust and
150:parsers exist (`#![forbid(unsafe_code)]` Rust crates, `unsafe`-free
151:Go modules); Python is the historical reference and cross-check.
159:# Install Taplo per https://taplo.tamasfe.dev/cli/installation/
187:cross-checks, IJB conformance, closure-root, abstraction-class +
```

No regression.

### C06: closed

The cost and disclosure profile Status rows remain present and match the profile descriptors:

```sh
$ grep -A2 -nE 'Cost Profile schema|Disclosure Profile schema' README.md
39:| Cost Profile schema | `1.0.0` | Release candidate |
40:| Disclosure Profile schema | `1.0.0` | Release candidate |
41-| Core ontology | `1` | Release candidate |
42-

$ grep schema_version profiles/cost/PROFILE.toml
schema_version    = "1.0.0"
schema_version    = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }

$ grep schema_version profiles/disclosure/PROFILE.toml
schema_version    = "1.0.0"
schema_version    = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }
```

No regression.

### C07: closed

The Governance section still links the independent-review policy file, and the file is real:

```sh
$ grep -n 'review-request-dag.toml' README.md
217:multi-LLM review under [tools/review-request-dag.toml](tools/review-request-dag.toml)

$ head -20 tools/review-request-dag.toml
# Reusable multi-reviewer independent-review workflow, encoded as a
# DAG-TOML `implementation-dag`. Author: Werner Kasselman.
#
# PURPOSE
#
# This DAG is the durable, machine-readable form of an instruction
# that was previously a free-text prompt. From now on, when a piece
# of work needs an independent multi-LLM review, instantiate this
# DAG, fill the [policy.instance] block, and execute the units in
# order.
#
# The DAG does NOT mock the review — it sequences the real steps
# (assemble bundle, dispatch reviews to named models, classify each
# DAG unit under review, rebut disagreements with code/doc evidence,
# persist the verbatim review text, iterate until terminal). The
# [policy] table carries the hard process rules that the units must
# obey; comments above each unit map the rule to the unit.
#
# LINEAGE
#
```

No regression.

## Final blockers

None.

Terminal verdict: unconditional_approval
