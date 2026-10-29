# Source spelling gate

This is the replacement for the source spelling workflow at project commit
`a3420ad83ab0758e389fca86dbdfb837e86df5bc`. The upstream command, configuration
patterns and file walkers are retired from that workflow. Other verification
tools and cold reference-store imports remain separate policy work.

From the repository root:

```sh
cargo build --locked --manifest-path tools/dagtoml-spell/Cargo.toml
tools/dagtoml-spell/target/debug/dagtoml-spell --repo-root .
```

The command derives tracked paths from the Git index and reads their current
working files. It records the named HEAD commit, whether the working tree is
clean, every selected path and its disposition, policy source hashes, and the
compiled instrument source digest. Findings contain a source SHA256, byte span,
token and literal proposed corrections. Exit status is 0 for no corrections,
1 for findings, and 2 for an incomplete or invalid scan. Identity-only output
explicitly says that no scan ran.

The instrument compares its compiled source stamp with the current complete
package source before and after scanning. A stale executable fails. If a newly
added package-root file was not observed by a cached build script, clean this
package with `cargo clean --manifest-path tools/dagtoml-spell/Cargo.toml -p dagtoml-spell`
and rebuild. The command never repairs or rebuilds itself.

Scope uses exact path components, basenames and prefix/suffix predicates in
`scope.rs`. Historical reviews, research, claim analysis, the existing
anti-pattern word dictionary, dependency locks, local working copies and the
declared canonical identifier examples keep their preceding exclusions. The
report names those exclusions. PNG/ICO signatures and external gitlinks get
filename checks with an explicit content omission. Other binary or invalid
UTF-8 source fails. Symlinked or missing selected files fail. Archive contents
and untracked paths are outside this source population.

`data/project.toml` preserves the preceding literal accepted words and pins
the credential identity catalogue and Python byte-table operands. Its complete
`identifiers` table replaces the former hardcoded acceptance set with exact,
case-sensitive code names. At baseline
`b506356cd82aa85b8217104357f45a16a51bf952`, four word findings split components
from the captured supplier enums `NdArray` and `NdDatetime`. Those complete names
join the preceding four exact code identities. The component word, case
variants, longer identifiers and adjacent prose still receive dictionary checks.
Only named catalogue identities, declared complete code names and validated
data spans are outside word checking.
Comments and adjacent prose remain governed. The correction-control TOML
likewise exempts only its declared input and expected-value spans. Unsupported,
absent, changed or repeated data roles fail instead of widening a file exclusion.
All policy source hashes are checked again before a result is returned.

`--stdin NAME` is a component probe using the declared file identity's data
context. Its report explicitly omits filenames and the tracked-file scan.
Empty input and input without any language words fail. It is not the CI entry
point.

The structured text lexer is adapted from `crate-ci/typos` at
`7f9d0819ca1c008ade73f4b41fa9d258d48f605b`, together with its exact
`crates/typos-dict/assets/words.csv`. The supplier licenses are retained here.
The CSV SHA256 is
`a13ac44993f5f85724161107172b3bd5a69afefe784912b094497129939b001c`.
It is literal correction data. The supplier code generator, byte-input
optimization, inactive locale machinery, default filetype tables, glob/ignore
walkers and regex configuration are not used by this command.

The lockfile pins the required parser, Unicode predicates, case folding,
SHA256 and typed TOML serialization dependencies. No supplier generator runs
during build. The local build script emits only a source-digest constant;
Serde derives emit typed field visitors. Dependency advisory and license
checks cover this manifest through the derived native-tool population. The
Git executable and compiler are external tools, not components covered by
the spelling lexer's source audit.

Validation controls exercise independently declared corrections and accepted
text, every pinned literal dictionary lookup, lexer boundaries and byte spans,
typed data roles beside governed prose, derived source populations, stale
source, absent files and malformed inputs. Dictionary-input comparison with
the previous engine is agreement evidence only; it does not establish
equivalence for arbitrary inputs, filetypes or locales.
