# Language Validators

The reference validators in this repository start with the DAG-TOML
files themselves. Language validators add the next layer: they check
that traceability claims about code resolve to real AST symbols in the
source tree.

This follows the useful pattern from Microsoft's Agent Governance
Toolkit: keep the specification explicit, publish executable
conformance checks, and test language surfaces independently. DAG-TOML
does not adopt AGT's runtime policy engine scope; it remains a data
format and validation contract.

## Target Languages

The first supported language set is the sqry-backed set with the best
repository-analysis fit for this project:

- Rust
- Go (`golang` is accepted as an alias)
- TypeScript (`ts` is accepted as an alias)
- Java

## Validator

The primary Rust and Go validators enforce the traceability document's
structural rules, including path presence for `[[code]]` entries. Use
`validators/validate_code_symbols.py` for the optional AST-aware layer
against any traceability file that declares `[[code]]` entries with
`path` plus either `symbol` or `symbols`.

```sh
python3 validators/validate_code_symbols.py \
  examples/language-validation/traceability.toml \
  --repo-root .
```

The validator:

- reads the traceability TOML;
- collects symbol-bearing `[[code]]` entries;
- infers language from `path` or accepts explicit `language` / `lang`;
- invokes `sqry` with exact symbol matching;
- fails when a symbol-bearing entry points to a missing path or an AST
  symbol that cannot be found in that path.

**Status: experimental.** This validator depends on a pinned `sqry`
binary and is therefore not yet a required CI gate. The repository's
main CI workflow performs cheaper, sqry-independent checks against the
fixture set:

- primary Rust + Go traceability validation of
  `examples/language-validation/traceability.toml`;
- Python reference traceability validation of the same fixture;
- IJB conformance for the fixture;
- a grep-level fixture-symbol drift check that fails if any declared
  symbol name disappears from its referenced source file.

The full AST-aware sqry check is run locally and in any environment
that has `sqry` installed. It will become a required CI job once the
sqry install path and version pin are settled — see the open work in
[`docs/language-validators.md#next-ci-step`](#next-ci-step).

## AGT Lessons To Borrow

Microsoft's Agent Governance Toolkit is useful as a release-discipline
reference, not as a scope reference. The parts to copy are:

- per-language validation surfaces instead of one undifferentiated
  runtime package;
- conformance examples that exercise the language surface;
- path-filtered CI when language packages become large;
- license/header and supply-chain gates before public launch;
- documentation that separates quickstart, specification, testing, and
  release process.

The parts not to copy into DAG-TOML are runtime policy enforcement,
identity, sandboxing, audit-log signing, and framework adapters. Those
belong in runtimes or control planes that consume DAG-TOML.

## Next CI Step

Add a workflow job after sqry is pinned:

```sh
python3 validators/validate_code_symbols.py \
  examples/language-validation/traceability.toml \
  --repo-root . \
  --strict-language-set
```
