# Link checking outcomes

At source `24ece13835c385ddb7352861c9aae5c22ced471f`, the active wrapper
discarded a nonzero scanner's temporary report and emitted a generic error.
The link step failed that way in CI at
`b83953fb8e209aa34e1a9060559709ec6defe687`; the failed endpoint cannot be
recovered from that log. Controlled process/report injection reproduces
the loss. Separate native HTTP 500 and timeout controls establish the pinned
supplier's report format. They do not identify the historical failed link.
The preparer at that same source used an ambient foreign Git index while
the metadata transport ignored it. Both operations now use the same owned
Git environment, with complete NUL framing and canonical tracked paths.

The wrapper retains the pinned Lychee release and the existing exact path
and host exceptions. It checks the complete prepared HTTP URL population,
then validates every success, error and timeout entry against those inputs.
Counts must conserve the population. Entries must have the expected input
source, unique declared URLs and valid status shapes. Successful statuses
must satisfy the configured 200 through 299, 403 or 429 policy. Missing
outcomes, repeated or substituted URLs, unexpected native exclusions, cached
or remapped results and contradictory exit statuses make the run incomplete.

Exit zero means the prepared candidates passed. Exit one means complete
outcomes include link errors or timeouts. Exit two means checking or report
delivery was incomplete. A uniform set of failed outcomes still fails the
gate. Missing subjects, binaries, extraction results and admission records
cannot produce a passing result.

`--report` defaults to `.local/link-scan/report.json`; `--summary` optionally
appends the sanitized JSON to a CI job summary. Outputs must be outside the
checkout or in an untracked `.local/` output path. Tracked paths, including
hidden workflow sources, are refused after symlink resolution. Report and
summary destinations must differ. CI explicitly supplies both destinations.

Retained results identify the named commit and clean/working-file state,
source-state digests, executable identity, phase, prepared URL identities,
declared exceptions, outcome counts and failed URL/status pairs. Native
producer messages, input-source keys, durations and line/column metadata
remain transient and are omitted from the retained schema. The source and
executable identities are rechecked before final outcomes are published.
Phase records remain incomplete until the source and executable checks
finish. Report-delivery errors fail the command.

These controls validate the prepared candidate set and preserve operator
diagnostics. Complete source extraction, native scanner dependencies and
applicable installer/build paths remain under audit. A successful link
result does not establish repository policy compliance or approve a PR.
