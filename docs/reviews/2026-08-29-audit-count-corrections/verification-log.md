# Verification log: audit count corrections and the commit-citation gate

Initiator-side verification for the branch `docs/audit-count-corrections`,
landed as PR #98 against issue #97, and merged as `f64bfa0`.

Every commit named here is one this repository carries. The measurements were
taken on the branch head, but that head did not survive: this pull request was
squash-merged, so every branch commit was discarded at merge and no pre-merge
SHA was durable. That is no longer true of new work. `main` accepts merge
commits only as of 2026-08-30, so a branch commit cited today remains an
ancestor of `main` after merge. The figures below were re-confirmed
against `f64bfa0`, which is the commit a reader can check.

Per `CONTRIBUTING.md` Review Discipline section 1, the author of these
commits must not issue the approving verdict. This file records what was run
and what it produced. It is not an approval.

## What was corrected, and against what

Every figure was re-derived at `703f59e`, after the branch was rebased from
its original base `38cd729`. The four count surfaces hold at both commits.

| Surface | Was | Is | Derived from |
| --- | --- | --- | --- |
| `reference/database/README.md` | 15 / 23 / 30 / 29, and "the 14 kinds" | 23 / 27 / 31 / 50, and 23 | `MANIFEST.toml [counts]`, all five ontologies |
| `core/ontology.md` section 3 | 30 predicate rows | 31; `cites_upstream` added as section 3.5 | `grep -c '^\[\[relations\]\]' core/ontology.toml` |
| `reference/database/graph/schema.cypher` header | 21 template kinds, one `com.verivus.runtime` kind, `expected_node_counts` 21/27/31 | 23, three, 23/27/31 | `MANIFEST.toml`, `profiles/com.verivus.runtime/PROFILE.toml` |
| `conformance/README.md` | `api-snapshot` 2/6, `state-mutation` 3/9 | 2/18 and 3/13 | `find conformance/cases/<kind>/{valid,invalid} -name '*.toml' ! -name '*.expected.toml'` |

`schema.cypher` seed data is unchanged. The absent UNWIND rows are ISS-002
and stay open.

Section 3.5 is numbered after 3.4 rather than inserted after 3.2, because
`profiles/agent-assurance/ontology.toml`, `profiles/cost/ontology.toml` and
`profiles/disclosure/ontology.toml` cite the section 3.3 anchor.

## Gate results at `f64bfa0`

Working tree carried one untracked local build artifact and no modifications.

```
check_commit_citations                     exit=0   (30 files, 17 tokens, 13 recorded)
validate_closure_root --exclude negative   exit=0   (92 files)
check_manifest_drift                       exit=0
check_safe_tools                           exit=0
check_attribute_values                     exit=0
ruff --select S,F validators/              exit=0
bandit --recursive validators/ ...         exit=0
shellcheck (the two gate scripts)          exit=0
zizmor .github/workflows/                  exit=0
typos                                      exit=0
taplo lint                                 exit=0
gitleaks detect --source .                 exit=0
conformance/runner.py --rs --go            exit=0   (60 cases)
conformance/discrimination.py              exit=0
conformance/coverage_audit.py              exit=0
```

Canonical examples through all three implementations:
`minimal-implementation-dag.toml` and `minimal-traceability.toml`, rs=0 go=0
py=0. `validate_ijb_conformance.py core/ontology.toml` exit 0.

GitHub Actions: all thirteen checks pass on the pull request, and all five
workflows pass on `f64bfa0` after merge.

## Controls on `check_commit_citations.py`

Each probe was written into a tracked file, the check run, the file restored
from a copy, and the restoration confirmed by sha256 comparison.

```
mixed-case citation in a scanned file            exit 1
recorded SHA at a site not in its cited list     exit 1, reported by name
object present but reachable from no ref         exit 1, reported by name
shallow clone                                    exit 2
valid repo, zero files under the scanned dirs    exit 2
--repo-root that is not a git repository         exit 2
git absent from PATH                             exit 2
unmodified tree                                  exit 0
```

Verified additionally in a fresh full clone with no private refs: resolve 3,
recorded 13, exit 0.

## Controls on `.gitleaks.toml`

The risk a gitleaks config carries is that it replaces the default rule set
and the scan can then no longer fail. Measured rather than assumed, with a
planted `token = "..."` of the shape the `generic-api-key` rule catches:

```
clean tree, CI history mode                      exit 0
same secret planted in another tracked file      exit 1, named
same secret planted in the allowlisted file      exit 1, named
```

The third line is why the allowlist is scoped to the literal and not to a
path. An earlier draft carried `paths` with `condition = "AND"`; that
condition is not honoured by gitleaks 8.30.1, the path matched on its own,
and the whole file was exempt.

## Three CI failures, each in the gate rather than the repository

1. **Shallow clone.** `actions/checkout` clones at depth 1, so no cited
   commit was present and all seventeen tokens reported as unresolvable. The
   workflow now uses `fetch-depth: 0`, as `no-ai-attribution.yml` already
   did, and the check refuses to run on a shallow clone rather than emitting
   a false report.

2. **Object existence versus reachability.** With full history, CI resolved 3
   where the initiator resolved 5. The two extra were ISS-005's `91e050a` and
   `4176bf9`, which postdate the mint but were made on
   `fix/2026-05-29-five-weaknesses`, squash-merged and deleted. No ref
   reaches them. The initiator's clone still holds the pre-squash objects, so
   `git rev-parse` succeeded there and nowhere else, and the baseline
   recorded them as resolving. `resolves` now tests ancestry of HEAD, which
   is the history the document ships in and gives one answer in both places.
   `git for-each-ref --contains` is not sufficient either: this clone has
   private refs that reach both commits.

3. **gitleaks.** The recorded hex alphabet reads as a generic API key,
   because the TOML key is named `token` and the value has entropy 4.0.

## Instrument failures recorded because each changed a result

- `ruff check validators` with the default rule set passes on a file the CI
  form rejects; the default set excludes the flake8-bandit `S` rules. The CI
  form found S603 and S607 on both subprocess calls in the new checker, and
  bandit found the same pair at high confidence.

- An earlier ruff run reported an F841 in `validators/validate_state_mutation.py`
  that does not exist in the file. `coverage_audit.py` was running
  concurrently and mutates that file in place to measure check coverage; ruff
  read it mid-mutation.

- A planted-secret control using the AWS documentation example key reported
  nothing under every configuration, including no config at all. It was
  measuring a probe that no default rule matches, so it said nothing about
  the allowlist it was supposed to test.

- A control for the citation gate's site-binding was first run against a file
  already named in that SHA's `cited` list, so it passed for the wrong
  reason. Re-run against a site not in the list, it failed as intended.

- A control that ran the pre-fix checker from outside `validators/` exited 1
  on a `_toml11` import error, which is the same exit code a real finding
  produces. The exit code alone did not distinguish them; the printed
  citation list did.

## Not covered

The four commits added after the branch's review rounds had no independent
review of their own before merge. Three of them exist only because CI rejected
the gate.

Two limits of the gate this session added, both found after merge and neither
fixed by it:

- Its scanned population is `docs/issues/` and `validators/`. This file is
  under `docs/reviews/`, which CONTRIBUTING.md names as the home of persisted
  review evidence and which the gate does not read. The two stale citations
  corrected in this file were therefore invisible to it.
- Its token rule was sound only in a population containing no UUIDs. A UUID is
  hyphen-separated hex, and hyphens are non-word characters, so each segment
  satisfied the rule. The scanned trees contain no UUID today, which is a
  property of their current contents and not a guarantee. Now excluded, with
  the precondition stated in the checker rather than left implicit. Measured
  on one planted gateway job id:

  ```
  before   two phantom citations reported, exit 1
  after    none reported, exit 0
  ```

  A real unresolvable SHA on the same line as a job id is still reported, and
  so is one written immediately after it, so the exclusion does not swallow
  its neighbours.
