# U07 — initiator rebuttal record

Per `[policy.evidence].disagreement_requires_code_or_doc_evidence` in
`tools/review-request-dag.toml`, if the initiator disagrees with a
reviewer finding the response must cite code or doc evidence, not
assertion. This file lists every reviewer-vs-prior-art disagreement
and the initiator's response with evidence.

## Disagreements

There is exactly one disagreement between a reviewer and the
prior-art self-review across the 29 findings + 6 independent
findings:

### Disagreement #1 — S1-F03 (Codex refutes)

**Finding (self-review, prior art):** S1-F03, low severity.
"This passage promises 'the same five aspects below' but the
enumerated list at lines 288-319 contains FIVE items only by
virtue of treating the validators-and-no-JSON-Schema item as one
aspect and the separation of contract-declaration from
verification-report as another. The mapping is reasonable but a
reader counting items 'below' may briefly look for an explicit
'(1) ... (5)' enumerate of *aspects*, not of TOML mechanics."

**Codex classification:** `refuted_with_evidence`.
"`paper/main.tex:288-319` contains a five-item enumerate list.
The promised 'five aspects below' are present; adding labels would
be optional clarity, not a confirmed defect."

**Initiator response — Codex is right.**

Direct verification: I (the initiator) opened
`paper/main.tex:288-319` and counted the items in the `\begin{enumerate}
... \end{enumerate}` block. There are five `\item` entries. Codex's
structural claim that the five-item list IS present is correct.

The self-review's S1-F03 was a stylistic suggestion (add explicit
'Aspect N:' labels) presented as a finding. It does NOT identify a
content defect — the count of items below matches the promise of
'five aspects below'. The lack of explicit textual labels is a
nice-to-have, not a defect.

**Disposition:** S1-F03 is downgraded from "finding" to "stylistic
suggestion" per Codex's refutation. The self-review erred in
elevating an optional-label suggestion to a finding line. No edit
to the manuscript is required on this point.

**Evidence cited by the initiator (not by assertion):**
- `paper/main.tex:288-319` contains exactly 5 `\item` lines under
  the single `\begin{enumerate}[leftmargin=*,nosep]` block:
  item 1: schema_version + template_kind discriminator;
  item 2: the five template_kind values used (implementation-dag,
          traceability, contract-declaration, readiness-gate,
          evidence-matrix);
  item 3: the closed verdict set;
  item 4: Python-validators-no-JSON-Schema;
  item 5: contract-declaration vs verification-report separation.

## No other disagreements

The remaining 28 prior-art findings + 6 independent findings have
no reviewer-vs-prior-art conflict that requires initiator rebuttal:

- S2-F05 and C5-F04 were marked `unverifiable` by one or two
  reviewers due to sandbox restrictions (no live GitHub API; no
  venue-policy ground truth). These are not refutations.
- All three reviewers agree on the structural facts of the
  remaining 27 prior-art findings.
- The 6 independent findings (IF-CX-01, IF-CX-02, IF-CX-03,
  I-F01, I-F02, I-F03) are NEW findings the prior-art self-review
  missed; the initiator confirms them rather than disputes them.
  IF-CX-01 in particular was directly verified by the initiator
  at aggregation time (see process_confirmations.toml).

## What the initiator does NOT do

Per `[policy.evidence].reviewers_must_not_accept_summary_as_evidence`,
the initiator may not paper over reviewer findings with assertions
of intent ("we meant the spec layer in general") or with
plan-compliance claims ("the next revision will fix this"). The
manuscript has the wording it has, and the reviewers have read
that wording against the cited artefacts. The rebuttal above is
the ONLY instance where the initiator pushes back on a reviewer,
and it pushes back with evidence (five items, counted) rather
than with framing.
