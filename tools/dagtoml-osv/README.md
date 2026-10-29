# Locked package advisory evaluation

This replacement is under validation against the repository contract at
`82f10ba69328b94e5b831baad5ddc6a0ad9ed2f6`. The existing required OSV workflow
remains active until extraction, evaluation, dependency and failure controls
support its retirement. A scanner result does not establish repository policy
compliance or approve a pull request.

The native Linux command is `dagtoml-osv CHECKOUT`. Build with
`cargo build --release --locked`; Rust 1.85 is the declared floor. The command
requires its complete current source and an empty Git porcelain status. It
returns zero for no listed advisories, one for affected packages, and two for
an incomplete evaluation. Results identify the commit, source hashes, byte
populations, package identities, archive generations and advisory record
hashes. Native parser diagnostics and advisory metadata are not returned as
source coordinates.

The proposed evaluator contract is:

- Derive all tracked Cargo locks, Go module declarations, Python requirements
  entry points and requirements-directory locks from the Git index. Reject
  unsupported recognized lock formats and unregistered local Cargo sources.
  Cargo registry packages need checksums. Each local root must match its
  tracked owning manifest and receives no registry advisory claim.
  Requirement basenames containing the literal text `requirements` and ending
  in `.txt` are included, alongside every `.txt` file in `requirements/`.
  Recognize the complete pinned lockfile preset and both SBOM entry points
  before admitting the three implemented extractors. Other recognized
  subjects stop evaluation instead of disappearing from its scope.
- Select every exact Python marker branch without executing marker syntax.
  Validate Python, Cargo and Go versions with explicit typed parsers. Include
  each Go module's declared standard library.
  Go declarations require a full patch version at least 1.17.0. Older graphs
  need checksum-file dependency recovery and are unsupported. Two-component
  versions and toolchain directives also stop extraction.
- Fetch complete [published ecosystem archives](https://google.github.io/osv.dev/data/)
  over HTTPS. Require the exact object URL, status 200, media type, byte
  length, object generation and entity identity. Bound cached responses to
  one hour, clock disagreement to five minutes, and archive age to 48 hours.
  No advisory verdict is delegated to the semantic query service.
- Read every archive member without filesystem extraction. Check member
  identity, regularity, CRC, record identity, expansion bounds and complete
  member accounting. Structurally parse every record and evaluate every
  applicable package entry. Missing independent historical controls fail.
  The owned reader accepts single-disk ZIP32 with stored or DEFLATE members,
  including checked data descriptors. ZIP64, encryption, other compression,
  overlapping records and unaccounted local bytes stop evaluation. Compressed
  input is limited to 256 MiB, each record to 4 MiB, total declared expansion
  to 2 GiB and the member population to 65,534.
- Use [OSV range semantics](https://ossf.github.io/osv-schema/) with typed
  release ordering, inclusive introductions, exclusive fixes, inclusive
  last-affected boundaries, and the union of limit ceilings. Do not mix fixed
  and last-affected events within one range. Stable schema major version one
  permits backward-compatible minor and patch additions.
- Keep Git commit ancestry outside the version subject. Named Git ranges
  require their enumerated versions. Mixed Git entries may contain opaque
  tags: compare those literally and report their count, without assigning a
  release order. Non-Git version and boundary parse failures stop evaluation.
  Package names that do not parse in a supported namespace cannot equal a
  validated query identity. Disclose those records by identity and digest;
  do not guess a correction, such as stripping a URL prefix from a Go module
  name. Publisher data quality remains part of the ingestion trust boundary.
- Exercise affected and unaffected versions against a known record from each
  actual ecosystem. These control versions describe that particular record,
  not general safety. Require the final assessment identities to equal the
  complete derived query set. Recheck source, index, executable and compiled
  instrument identities before returning a result.

At OSV Scanner v2.7.0 commit
`bfe2f84abd2f09fe0b83ba7f6dad40d296762f40`, the active lock preset selects
SCALIBR's Go module extractor. Its pinned supplier at
`5be78a00e3c294c19a0b03949e4eb643653c0218` uses module declarations for
Go 1.17 and later; checksum recovery belongs to the older-graph branch.
The native parser at `80fc9813caab7d58d542b5cd705e7d9f722f2c77` accepted
that older version range without implementing its graph recovery. The
replacement contract therefore rejects it. The four module inputs at that
commit declare Go 1.26.10 and remain inside the accepted graph scope.

`data/extractor-scope.toml` records every extractor in that lockfile preset
and the separately enabled SBOM preset, with pinned supplier source objects.
Controls compare the complete inventory with the native classifier and
exercise actual tracked filename variants and unsupported subjects. Node
module lock candidates, the previously guarded binary Bun name and marked
SPDX names with unsupported extensions are conservatively refused too.
`data/directory-scope.toml` separately records the two directory extractors.
At the same pinned scanner commit, the source command defaults
`include-git-root` to false, and `getPlugins` disables `vcs/gitrepo` when
that flag is absent. The current workflow does not enable it. Root commit
ancestry is therefore not an active protection of this workflow.

The directory preset still enables `filesystem/vendored`. The native snapshot
at `16233b65fb855f9bad7582603d5064e6d7e45f27` admitted a package-only result
after a tracked vendored C directory was added. It now derives directory
prefixes from the complete index and refuses child roots under the supplier's
eleven exact parent names, including nonregular root entries, rather than
issuing a package-only verdict over that input. Git submodule entries also
stop evaluation because their contents are outside the captured file index.
Neighboring names and direct files that the upstream directory predicate does
not select remain admitted. This is a refusal boundary, not fingerprint
identification.

The next repair uses the discovery boundary at project baseline
`7d871361d4275860dab54b628894a54d20d977e6`. It enumerates actual visible
directories independently of the index, including empty directories and
directories containing only ignored files. Git checks each literal directory
path against its ignore rules; a visible directory is not excluded merely
because all its contents are ignored. Results retain the complete visible
directory set and the ignored subtree roots, and compare them again before
returning a verdict. Repository metadata and ignored subtrees are outside
that filesystem subject, matching the existing workflow's default ignore
selection. Directory enumeration errors, non-UTF-8 names and exceeded
discovery bounds stop evaluation. New controls exercise every supplier parent
name with both empty and ignored-content roots, accepted neighboring names,
literal subtree ignores and directory changes. The original required workflow
gate remains active while the dependency/build audit supports replacement.

The semantic query prototype is retired. At upstream OSV commit
`2550f6d61565de3a813e19f64a24b04b8af0ce39`, the current Go API dispatches both
package-matching backends through the Python ecosystem coarse-version helper,
which executes regular expressions. The historical Python server helper does
not establish that current purpose. Local record evaluation removes that
remote semantic dependency; it still trusts the publisher's ingestion and
archive completeness.

`examples/read-datasets.rs` and `examples/fetch-datasets.rs` are development
probes. They identify dirty subjects and their skipped work explicitly. They
do not produce a final clean-candidate verdict. Unit controls cover malformed
pins, missing subjects, affected/unaffected boundaries, archive corruption,
HTTP identity and freshness, bounded process streams and descendant-held
pipes. Documentation tests with no cases are not additional coverage.

Complete dependency, generated-source and native transport audits,
omission and stale-instrument controls, clean candidate
validation and fresh cumulative review remain required before retirement of
the existing gate. CI runs the native controls and evaluation alongside that
gate during replacement validation. No transitive, vendored or remote consumer has an automatic
policy exception.
