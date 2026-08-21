# Round 6, Mistral: APPROVED (executed, but repeats the blocked assertion)

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention. Gateway job `0a6d1da0-efa1-423b-b848-8cc14bae9349`,
correlation `adacg-r6-mistral`, 3589 bytes, 9m14s. The job reported zero stdout
bytes and no provider activity for its first nine minutes, then completed in
one burst, which is worth knowing before anyone reads a silent Mistral job as
dead.

**Mistral executed this round**, which is the standing ask after round 2, where
it raised a blocker that did not reproduce because it could not run anything.
It cloned `/tmp/r6-mistral`, built both primaries and `dagtoml-rdf` from the
tree, and ran the gates.

## Where it was right

- **Q1, executed.** Reverted the RKC02 check from `hasKey` to `tableOf`,
  rebuilt, and got `array-proof` exit 0 (Go accepts, so the conformance case
  reddens) and `table-proof` exit 1 (still rejected). Fourth independent
  reproduction of the initiator's result.
- **Q2, executed.** `is_conformance_invalid` returns true for relative,
  absolute and cwd-shifted forms. Fix is general.
- **Q3, executed.** Both mutation-claim negatives fail `validate_provenance.py`
  (225 vs 224), pass `validate_closure_root.py`, and fail the Go primary with
  RKC02.
- **Q4, correct.** The profile pins only `mutation.authorization_sha256` and
  `mutation.effect_sha256` for `mutation-claim`; `execution_proof` is not
  pinned, so its shape cannot affect `closure_root`.
- **Q5, partly.** Recomputed `attribute_values_closed` = 123 with its own script
  and verified 1476 triples with its own `dagtoml-rdf` build.

## Where it was wrong

**Q5, the assertion that Grok made a blocker.** Mistral wrote that
`attribute_value_allowed` "staying at 144 while `attribute_values_closed` moved
by 8 is expected as they count different surfaces". That is the same unverified
explanation Devin gave, and it is false in the way that matters: the two new
vocabularies are not enum-backed, so under the rule the seed states about itself
at `postgres/seed.sql:232` their eight values belong in that table. See
`initiator-seed-gap-r6.md`. Two of four reviewers asserted this; one tested it
and found the defect.

**Q3, the fixture count.** Mistral reported "all 16 negative fixtures with
`[provenance]`". The correct number is 18, independently obtained by both Devin
and the initiator, who enumerated them. A miscount in the direction of fewer
files is a weaker sweep than it appears.

**Q6.** Mistral cited `validate.yml:960-967` and `:656-666` as evidence that
coverage is adequate and the gap correctly deferred. That describes the
per-fixture assertions that exist, not the absence of any assertion that a
negative fails every gate it is subject to, which is the actual open item.
