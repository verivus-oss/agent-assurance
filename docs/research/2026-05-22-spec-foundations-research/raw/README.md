# Raw operational state

Operational records preserved for reproducibility. None of these are
research output — they are records about *how* the research was run.

- `job-manifest.toml` — every async LLM and Exa Deep Researcher job:
  IDs, models, costs, durations, exit codes, output-file pointers.
  Includes per-wave totals and CLI configuration changes made before
  research could run.
- `failed-attempts.md` — verbatim error logs for the four CLI runs
  that failed before being retried, plus the two cases of transient
  rate-limiting that recovered on their own.

For prompts (the "asks"), see [`../prompts/`](../prompts/).
For responses (the answers), see [`..`](../) (first wave) and
[`../follow-up/`](../follow-up/) (Streams A/B/C/D).
For synthesis, see [`../README.md`](../README.md) and
[`../08-follow-up-synthesis.md`](../08-follow-up-synthesis.md).
