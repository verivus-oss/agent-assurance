# Security policy

## Reporting a vulnerability

Email **security@verivus.com** with:

- A short description of the issue and the file(s) or rule(s) affected.
- A minimal reproduction if applicable (a TOML snippet that demonstrates
  the problem, plus the validator invocation that triggers or fails to
  trigger).
- Whether you believe the issue is exploitable in the spec text, the
  kind-descriptor TOMLs, the ontology files, or the reference
  validators.

We aim to acknowledge reports within five business days.

## Scope

This is a specification repository. The threat surface is narrower than
a runtime project, but the following classes of finding are in scope:

- **Specification ambiguities** that allow two conforming implementations
  to disagree about whether a document is valid.
- **Path-traversal or injection patterns** in published examples that
  could mislead automated tooling.
- **Reference validator bugs** (under `validators/`) that accept
  malformed input or reject conforming input, especially where the
  consequence is a false-positive review-readiness pass.
- **Kind-descriptor or ontology bugs** (under `core/` and
  `profiles/agent-assurance/`) where the declared structural contract
  diverges from the prose specification or the reference validators.

Out of scope:

- Vulnerabilities in third-party runtimes that consume DAG-TOML files
  (report to the runtime project).
- Aesthetic preferences about the spec.

## Disclosure

We coordinate disclosure: the reporter, the maintainers, and (if the
finding affects published profiles) the profile owners agree on a
disclosure date. Default embargo is 30 days from acknowledgement; we
extend if a fix needs more time.

We credit reporters in `CHANGELOG.md` for the release that fixes the
finding, unless the reporter requests otherwise.
