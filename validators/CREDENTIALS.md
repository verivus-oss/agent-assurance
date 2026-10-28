# Credential candidate contract

`check_secret_scan.py` is the POSIX credential gate. Run its cold controls with
`python3 -S validators/test_credential_cold_start.py`, repeat with `-O`, and run
`python3 -S validators/check_secret_scan.py --repo-root .` in a full checkout.
The optional `--report` path receives a JSON report with source identities,
digests and byte spans. Candidate values remain outside the report.

The migration starts from the Gitleaks workflow at candidate
`fa8c3051e3cafd83ddcbd8898f4c0028d824c450`. The prior rule-name population is
in `credential-rule-population.toml`; supplier commit and config blob identity
are in `requirements/credential-source-revision.toml`. The literal generic
stopwords retain their supplier's MIT license in `credential-data-LICENSE`.
The rule-name record and source revision are provenance data. Matching does
not interpret expressions from either record.

The versioned candidate contract is `credential-candidates-v1`. Provider
prefixes, body alphabets, length bounds, entropy thresholds, assignment
contexts and compound structures define review obligations. Generic bindings
also apply the pinned literal stopwords. Provider checks remain independent
of those stopwords. Protocol fields use ASCII alphabets; Unicode case-folding
quirks of the prior engine are outside this contract. File-kind checks cover
PKCS#12 filenames and the declared PHP, Terraform, NuGet and Kubernetes
containers. These checks do not establish that a service issued a value or
that an arbitrary XML, YAML, PHP or Terraform document is valid.

The decoder contract is `credential-encodings-v1`. Percent, Unicode escape,
Unicode point, hex and base64 views recurse through at most five stages.
Derived findings identify their encoded source container and its digest,
plus a derived-view digest and byte span. Each record identifies its named
rule. A generic capture wholly contained in a provider capture in the same
view is subsumed by that provider obligation.

The history subject is every commit reachable from named refs and HEAD,
including disconnected branches, deletion-only commits and each merge parent.
The reader visits complete stored trees, verifies each Git blob's content
identity, and scans each distinct blob/path pair. A candidate event occurs
when the count for a path, rule and value digest exceeds the minimum count
in any parent, or zero at a root. A rename creates a new path identity. Event
captures describe the current blob; they do not claim which duplicate
occurrence was added. This state comparison is distinct from a textual patch
comparison. It does not promise byte-for-byte reporting parity with the
retired engine.

The event filter recognizes only the four historical public-literal events
named by `KNOWN_COMMITS`, with their exact path, rule, value digest and single
capture. Missing, repeated or altered controls fail. Inline suppression
annotations and local scanner configuration do not remove obligations.
Shallow or grafted history, malformed object framing, corrupt blob identities,
empty subjects and reference movement fail. Replacement refs and environment
Git overrides do not rewrite the subject. Symlink target text is scanned as
a stored blob, without following an external target.

The scan excludes uncommitted and untracked file contents, external gitlink
repositories, reflog-only or unreachable objects, and expanded archive members.
Stored archive bytes remain in the blob population. Filename and vendor path
allowlists from the prior executable are retired. The report records external
gitlinks and the archive boundary explicitly.

Canonical public examples cover each declared rule name. Malformed provider
bodies, compound rejection cases, decoding limits and independently built Git
graphs constrain the implementation. Fresh-process checks observe Python
matcher calls and reject imported regex machinery. Those checks do not
instrument native Git internals or other verification tools. Full dependency
policy compliance and final approval require the separate cumulative audit.
