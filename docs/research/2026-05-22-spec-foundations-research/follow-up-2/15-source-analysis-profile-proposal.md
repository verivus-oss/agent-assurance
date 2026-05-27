# Profile proposal — `source-analysis`

A scoped subset of the spec for analyzing text sources (articles,
research papers, internal documents, technical reports), extracting
their logical / semantic / intent structure as IJB-typed graphs,
signing the extraction with Stream B-style attestation, and emitting
a citation format that lets a downstream consumer (a) find the source
quickly and (b) cryptographically prove the source has not changed
since the extraction was made.

This is a draft proposal — not yet written into the repo's
`profiles/` directory. Maintainer review pending.

## Motivation

LLM-assisted research and AI agent workflows increasingly depend on
citing external text sources. The current state of the art for
citation has three failure modes that the spec's design ethos
(trust-as-currency, brittleness-as-feature, process-trust over
artifact-trust, producer-side responsibility) directly addresses:

1. **Citation drift.** A cited paper may be updated, retracted,
   paywalled, or moved after extraction. The citation continues to
   look valid even though the underlying source has changed. There is
   no mechanical signal in standard citation formats (BibTeX, CSL,
   DOI) that says "what was cited is no longer what is available."
2. **Extraction opacity.** When an agent summarizes or extracts
   claims from a source, the produced summary is treated as
   authoritative — even though the agent's interpretation may have
   added, dropped, or distorted claims relative to the source. There
   is no mechanical way to audit which claims came from which
   passages, or to verify the extraction is faithful to the source.
3. **Intent fluidity.** A research paper has logical structure
   (claims, evidence, inference rules), semantic content (what
   concepts and relationships are asserted), and authorial intent
   (what the authors are trying to establish). Standard citations
   collapse all three into a single string. There is no way to cite
   "the third claim on page 4" or "the author's stated motivation"
   distinctly from "the paper as a whole."

The `source-analysis` profile addresses all three by ladling spec
primitives onto the citation problem:

- A `source-record` document fixes the source's bytes via SHA-256,
  with provenance (when fetched, by whom, where archived).
- A `semantic-extraction` document captures the source's logical /
  semantic / intent structure as an IJB-typed graph, with each node
  citing the passage it was derived from.
- A `source-citation` document binds an extraction to a source with
  a closure root (per the just-proposed spec.md §12), so that any
  upstream change to the source's content hash cascades into a hard
  citation-validation failure.

The profile composes with `provable-intent` style signing ceremonies
(Stream B) so that each citation carries legally-defensible attestation
of who extracted what, when, from which source bytes.

## Scope

In:

- Text sources: research papers (PDF, HTML, LaTeX, Markdown), articles
  (news, blog posts), technical reports, RFCs, standards documents,
  legal opinions, internal whitepapers.
- Extraction of structured claims, evidence, inference chains, and
  intent from text sources.
- Cryptographic binding between extraction and source.
- A citation format compact enough for in-text use, with a full
  bibliography entry generated from the underlying TOML records.

Out:

- Non-text sources (audio, video, image, dataset). A future profile
  could cover these; the present scope is text only.
- Source acquisition (fetching, scraping, paywall negotiation).
  Producers acquire the source by whatever means; this profile only
  describes the record they produce after acquisition.
- Database / structured-data citation. Datasets are out of scope.
- Live / streaming sources. The profile assumes the source is a
  fixed, hashable artifact at the time of fetch.
- Authorship attribution and provenance of the source itself. The
  profile cites what the source says; it does not adjudicate whether
  the source's authors are who they claim to be.

## Profile placement

Recommended path: `profiles/source-analysis/`. Profile name:
`source-analysis`. Reverse-DNS unprefixed (per SPEC §2.5 it would be a
candidate for blessed-profile status if the core spec maintainers
choose to bless it; until then, it is a candidate profile in the
unprefixed kebab-case namespace).

## The three template kinds

### 1. `source-record`

Captures a single external text source by its bytes-at-fetch. One
`source-record` per source. Multiple extractions may cite the same
`source-record`.

Required fields (sketch):

```toml
[meta]
schema_version  = "1.0.0"
template_kind   = "source-record"
framework_profile = "source-analysis"

id              = "SRC:smith-2024-emergent"

# Identity surface — at least one MUST be present
[identity]
doi             = "10.1234/jmlr.2024.025"
isbn            = ""                              # if applicable
urn             = ""                              # archival URN (urn:arxiv:..., urn:rfc:..., urn:nbn:...)
url             = "https://jmlr.org/papers/v25/24-001.html"
content_hash    = "sha256:abc123def456..."        # MUST be present; hash of the canonical fetched bytes
content_type    = "application/pdf"
byte_length     = 1234567

# Bibliographic surface — informational, may be empty if structured fields are not extractable
[bibliographic]
authors         = ["Smith, J.", "Lee, A.", "Garcia, M."]
title           = "Emergent capabilities of large language models"
container       = "Journal of Machine Learning Research"
volume          = "25"
issue           = "1"
pages           = "1-30"
publication_date = "2024-01-15"
publisher       = "JMLR Press"
language        = "en"

# Fetch provenance — REQUIRED
[fetch]
fetched_at      = "2026-05-22T14:30:00Z"
fetched_by      = "did:example:agent-name-or-org" # signer identity
fetched_from    = "https://jmlr.org/papers/v25/24-001.pdf"
archival_uri    = "https://web.archive.org/web/2026.../"  # optional but RECOMMENDED
fetch_method    = "http-get"                       # closed set: http-get, http-post, file-read, manual
http_etag       = "..."                            # if applicable
http_last_modified = "..."                         # if applicable

# Optional: canonical text extraction
# When present, contains the text-as-read for the bytes hashed in [identity].content_hash
# Useful for downstream extractions to point at offsets in a stable text representation
[canonical_text]
extractor        = "pdftotext-4.05"                # tool used
extractor_args   = "-layout"
extracted_at     = "2026-05-22T14:31:00Z"
text_hash        = "sha256:..."                    # hash of the canonical text bytes
text_uri         = "ledger://text/sha256/..."      # optional content-addressed pointer

# Per the upcoming spec.md §12 (closure-root rule), the source-record
# is itself a leaf in the closure DAG. Downstream extractions cite
# this source-record's full identity hash; if the source bytes are
# re-fetched and differ, a new source-record document MUST be created
# (with a different content_hash, and therefore a different identity
# hash). Downstream citations referencing the old source-record
# continue to be valid for the old bytes; citations to the new
# source-record reflect the new bytes.
```

Hard invariants (enforced by the profile validator):

- `[identity].content_hash` MUST be present. SHA-256 minimum.
- At least one of `doi`, `urn`, `url` MUST be present in `[identity]`.
- `[fetch].fetched_at` MUST be present and MUST be a RFC 3339 UTC
  timestamp.
- `[fetch].fetched_by` MUST be present and MUST resolve to an
  identity recognized by the deployment's identity registry.
- If `[canonical_text]` is present, `text_hash` and `extractor` MUST
  both be present.

### 2. `semantic-extraction`

Captures the structured extraction of logical, semantic, and intent
content from a `source-record`. The extraction is an IJB-typed graph
where each node carries an `ijb_primitive` tag and references the
passage it was derived from.

Required fields (sketch):

```toml
[meta]
schema_version  = "1.0.0"
template_kind   = "semantic-extraction"
framework_profile = "source-analysis"

id              = "EXT:smith-2024-emergent/v1"

[source]
source_record   = "SRC:smith-2024-emergent"
source_content_hash = "sha256:abc123def456..."     # MUST match the source_record's identity.content_hash
source_canonical_text_hash = "sha256:..."          # OPTIONAL but RECOMMENDED — pins the canonical text version

[extraction]
extracted_at    = "2026-05-22T14:35:00Z"
extracted_by    = "did:example:agent-name"
extractor_kind  = "llm-assisted"                   # closed set: llm-assisted, human-annotated, hybrid, programmatic
extractor_identity = "claude-opus-4-7@1M-context"  # informational
extraction_method = "..."                          # free-form short description; tool prompts SHOULD NOT be embedded here

# IJB-typed claim graph. Each entry is one extracted unit of meaning.
# claim_kind is closed: claim | evidence | inference | assumption | definition | intent | quotation
[[node]]
id              = "EXT:smith-2024-emergent/v1#claim-1"
claim_kind      = "claim"
ijb_primitive   = "observed"
ijb_class       = "instance"
text            = "GPT-4 demonstrates emergent reasoning capabilities at >10^22 parameters."
location        = { page = 3, paragraph = 2, char_range = [1024, 1187] }
confidence      = "high"                           # closed: low, medium, high; reflects extractor's reading
attribution     = "authors"                         # closed: authors, quoted-other, paraphrase

[[node]]
id              = "EXT:smith-2024-emergent/v1#evidence-1"
claim_kind      = "evidence"
ijb_primitive   = "observed"
ijb_class       = "instance"
text            = "Table 3 shows accuracy on multi-step arithmetic rising from 14% (1B params) to 87% (175B params)."
location        = { page = 5, table = 3 }
supports        = ["EXT:smith-2024-emergent/v1#claim-1"]

[[node]]
id              = "EXT:smith-2024-emergent/v1#inference-1"
claim_kind      = "inference"
ijb_primitive   = "path"
ijb_class       = "structural"
text            = "Therefore scaling drives capability acquisition (causal claim)."
location        = { page = 7, paragraph = 1 }
derives_from    = ["EXT:smith-2024-emergent/v1#evidence-1"]
yields          = ["EXT:smith-2024-emergent/v1#claim-2"]

[[node]]
id              = "EXT:smith-2024-emergent/v1#assumption-1"
claim_kind      = "assumption"
ijb_primitive   = "constraint"
ijb_class       = "instance"
text            = "Benchmark accuracy is a valid measure of reasoning capability."
location        = { page = 2, paragraph = 1 }
constrains      = ["EXT:smith-2024-emergent/v1#inference-1"]
declared_in_source = false                          # the authors do not state this; extractor surfaces it

[[node]]
id              = "EXT:smith-2024-emergent/v1#intent-1"
claim_kind      = "intent"
ijb_primitive   = "scope"
ijb_class       = "structural"
text            = "Establish scaling as the primary driver of emergent capabilities."
location        = { section = "abstract" }
covers          = ["EXT:smith-2024-emergent/v1#claim-1", "EXT:smith-2024-emergent/v1#claim-2"]

[[edge]]
# Edges encode relationships not captured by intra-node fields above.
# edge_kind is closed: cites_other_source | contradicts | qualifies | extends | depends_on
edge_kind       = "cites_other_source"
from            = "EXT:smith-2024-emergent/v1#evidence-1"
to_source       = "SRC:kaplan-2020-scaling"         # another source-record
to_passage      = { page = 4, paragraph = 3 }       # optional

# closure_root per spec.md §12 (assuming that proposal lands)
closure_root    = "sha256:..."                      # SHA-256 over canonical concatenation of source_content_hash
                                                    # + each [[edge]].to_source's content_hash + revocation snapshot
```

Hard invariants:

- `[source].source_content_hash` MUST match the `source_record`'s
  `identity.content_hash`. If a re-fetch detects a different hash,
  the extraction is invalidated.
- Every `[[node]]` MUST have an `ijb_primitive` and an `ijb_class`.
- Every `[[node]]` with `claim_kind = "inference"` MUST declare
  `derives_from` (≥1 node id) and `yields` (≥1 node id or claim id).
- Every `[[node]]` with `attribution = "quoted-other"` MUST have an
  `[[edge]]` of `edge_kind = "cites_other_source"` referencing the
  cited source.
- `closure_root` MUST be present and MUST be computed per the spec.md
  §12 algorithm over (source_content_hash + every transitively cited
  source's content_hash + revocation snapshot).

### 3. `source-citation`

The reference-style artifact. Binds a citing document to one or more
`semantic-extraction` nodes (or to a whole extraction, or to a whole
`source-record`) via a signed, closure-rooted record. This is what
generates the in-text citation and bibliography entry.

Required fields (sketch):

```toml
[meta]
schema_version  = "1.0.0"
template_kind   = "source-citation"
framework_profile = "source-analysis"

id              = "CIT:my-paper-2026/ref-12"

[citation]
cited_at        = "2026-05-22T14:40:00Z"
cited_by        = "did:example:my-agent-or-author"
citing_document = "did:example:my-paper/v1"         # the document doing the citing
cite_text       = "Smith et al. 2024 [abc1234]"     # human-readable in-text form

# What is being cited
[[reference]]
# reference_kind is closed: whole-source | whole-extraction | specific-nodes | passage-range
reference_kind  = "specific-nodes"
source_record   = "SRC:smith-2024-emergent"
source_content_hash = "sha256:abc123def456..."
extraction      = "EXT:smith-2024-emergent/v1"
extraction_content_hash = "sha256:..."
cited_nodes     = [
  "EXT:smith-2024-emergent/v1#claim-1",
  "EXT:smith-2024-emergent/v1#evidence-1",
]
# Optional: a snippet of the source's text at the cited location.
# Snippet MUST match the canonical_text at the offsets declared in the
# cited node(s) — validators verify this when canonical_text is
# present on the source_record.
quoted_snippet  = "GPT-4 demonstrates emergent reasoning capabilities..."

# Bibliographic rendering hints for citation styles (CSL, BibTeX, etc.)
[render]
in_text_short   = "[smith24/abc1234]"               # the compact form
in_text_long    = "(Smith, Lee & Garcia, 2024)"     # human-prose form
bibliography_csl = "..."                             # optional CSL JSON for rendering
disambiguation  = ""                                 # if multiple Smith 2024 sources are cited

# Cryptographic binding
closure_root    = "sha256:..."                       # closes over source_content_hash + extraction_content_hash
                                                     # + every [[reference]].source_content_hash + revocation snapshot
```

Hard invariants:

- `[citation].cited_at`, `cited_by`, `citing_document` MUST be
  present.
- `[[reference]].source_content_hash` MUST match the
  `source_record`'s `identity.content_hash`.
- If `[[reference]].extraction` is present,
  `extraction_content_hash` MUST match the `semantic-extraction`'s
  canonical bytes.
- If `quoted_snippet` is present AND the `source_record` has a
  `canonical_text` block, the validator MUST verify the snippet
  matches the canonical text at the declared offsets of every cited
  node.
- `closure_root` MUST be present (per spec.md §12).

## End-to-end worked example

An agent is writing a paper and wants to cite a passage from Smith
et al. 2024. The full pipeline:

1. **Acquire source.** Agent fetches the PDF from JMLR. Computes
   `sha256:abc123…`. Archives to Wayback. Emits a `source-record`
   document with the content hash, fetch metadata, and bibliographic
   surface. Signs the source-record with a one-shot legal-grade
   attestation per Stream B. The agent's signing ceremony declares
   intent: "I fetched this source from `https://jmlr.org/...` on
   `2026-05-22T14:30:00Z`. The bytes are `sha256:abc123…`."

2. **Extract canonical text.** Agent runs `pdftotext -layout`, hashes
   the result as `sha256:def456…`, and stores it as a content-
   addressed artifact. Updates the `source-record` with the
   `[canonical_text]` block.

3. **Semantic extraction.** Agent (an LLM-assisted pipeline) reads
   the canonical text and produces a `semantic-extraction` document.
   Each claim, evidence, inference, assumption, and authorial-intent
   node is tagged with an IJB primitive and the byte range in the
   canonical text. Computes the closure root over the source's
   content hash and every cited upstream source's content hash. Signs.

4. **Cite.** The agent's paper-in-progress emits a `source-citation`
   document for each citation. The in-text marker is
   `[smith24/abc1234]` (compact) or `(Smith et al., 2024)` (prose);
   the bibliography is generated from the `source-citation` records.
   Computes the closure root over the source + extraction + every
   transitive citation. Signs.

5. **Consumer verification.** A reader of the agent's paper wants to
   verify the citation. The reader's tooling:
   - Looks up `[smith24/abc1234]` in the bibliography → finds the
     `source-citation` record.
   - Pulls the `source-record` referenced by the citation. Re-fetches
     the source URL (or pulls from archival URI). Computes
     `sha256(fetched bytes)`. If it does not match the source
     record's `content_hash`, **citation fails visibly** — the source
     has drifted.
   - Pulls the `semantic-extraction` record. Re-computes the closure
     root. If it does not match, **citation fails visibly**.
   - Verifies the signatures on source-record, extraction, and
     citation via Stream B verification (signature valid against
     declared intent and current revocation snapshot).
   - If `quoted_snippet` is present, verifies the snippet matches
     the canonical text at the declared offsets.

If any step fails, the citation is rejected. The brittleness is the
feature: a journal silently re-publishing a paper with updated bytes
breaks every downstream citation that referenced the old bytes. The
citing agent or reader can then make an informed decision about
whether to update the citation, retract it, or annotate it.

## Reference-style ergonomics

The compact form `[author24/hash8]` is designed for in-text density:

```
Recent work on scaling [smith24/abc1234] suggests that emergent
capabilities scale predictably [kaplan20/9f3e8b1c]. However,
extraction-quality concerns [garcia26/d4e5f6a7] complicate the
interpretation.
```

The `hash8` portion is the first 8 hex characters of the
`source_record.identity.content_hash` (or, optionally, the first 8
hex characters of the `source-citation`'s `closure_root` for
disambiguation when the same source is cited at different extraction
versions). Eight characters is unique enough across millions of
sources while remaining readable.

The full bibliography is generated by tooling from the underlying
TOML records:

```
[smith24/abc1234] Smith, J., Lee, A., & Garcia, M. (2024).
   "Emergent capabilities of large language models."
   Journal of Machine Learning Research, 25, 1–30.
   DOI: 10.1234/jmlr.2024.025
   Source content hash: sha256:abc123def456...
   Extraction: EXT:smith-2024-emergent/v1
     by did:example:agent-name on 2026-05-22T14:35Z
     content hash: sha256:def456...
   Citation: CIT:my-paper-2026/ref-12
     by did:example:my-agent on 2026-05-22T14:40Z
     closure root: sha256:bcd123...
   Archival: https://web.archive.org/web/2026.../
```

CSL (Citation Style Language) output can be generated from
`[bibliographic]` for compatibility with existing tooling (Zotero,
Mendeley, BibTeX). The cryptographic surface (`content_hash`,
`closure_root`, signing identity) is additive, not replacing the
human-prose bibliography.

## Composition with existing spec primitives

- **spec.md §10 (IJB foundation):** Every `[[node]]` in
  `semantic-extraction` carries `ijb_primitive` and `ijb_class`. The
  primitive distribution is meaningful: `claim`/`evidence` nodes are
  typically `observed/instance`; `inference` nodes are
  `path/structural`; `assumption` nodes are `constraint/instance`;
  `intent` nodes are `scope/structural`. This validates the IJB
  primitives as a semantic-extraction vocabulary.
- **spec.md §11 (`[provenance]`) + §12 (closure-root, proposed):**
  Every kind in this profile carries `closure_root`. Re-fetched
  source bytes that differ from the source-record's content_hash
  cascade-break the extraction, which cascade-breaks every citation.
- **Stream B (legal-grade one-shot attestation):** Each kind is
  signed with a one-shot intent attestation. The producer's intent
  is declared in the signing ceremony: "I extracted this content
  from these specific source bytes at this specific time using this
  specific method."
- **Stream C (separation-of-duty):** The agent that performs the
  extraction MAY be the same as the agent that performs the
  citation; that is permissible because the user-author is the one
  taking responsibility for the citation. But the agent that
  validates a citation (the consumer's verification tooling) MUST
  be a distinct identity from the agent that produced it. Per Stream
  C separation-of-duty, validating one's own citation is gameable.
- **Disclosure profile:** When citing a confidential source, the
  `source-record` MAY carry `confidentiality = "embargoed"` per
  spec.md §2.7. The citation can selectively disclose only the
  passages necessary for the argument, using
  `selective-disclosure-proof` records to prove the snippet matches
  the unredacted source without revealing the source itself.
- **Stream G (`cost-record`, proposed):** Each extraction emits a
  `cost-record` capturing the LLM tokens / human-review-time
  consumed. Auditors can verify that, for high-stakes citations, the
  extraction was performed at an appropriate decider class (LLM
  consensus or human-annotated, not single-LLM-best-effort).

## Open questions

1. **Versioning of extractions.** A new pipeline (or model upgrade)
   may produce a different extraction from the same source bytes. Is
   that a v2 of the same `semantic-extraction` (with the same ID) or
   a fresh extraction (new ID)? Recommendation: fresh ID per
   pipeline-major-version; the closure root makes the lineage visible
   without enforcing identity collapse.
2. **Canonical-text portability.** `pdftotext -layout` is a specific
   tool; other tools produce different canonical text from the same
   PDF. Should the spec require a single canonical extractor, or
   permit any extractor that emits its hash + identity? Recommendation:
   permit any, require declaration, validators verify hash match.
3. **Cross-language sources.** Translations introduce a new
   canonical text layer. Recommendation: model translations as
   distinct `source-record`s with a `translation_of` edge to the
   original, preserving the original source's content hash.
4. **Non-text source handling.** Out of scope for this profile, but
   the architecture should compose cleanly when image/audio/video
   profiles arrive.
5. **In-text disambiguation.** Two sources with the same author-year
   collide in the `[smith24/...]` form unless the hash8 disambiguates.
   Recommendation: require the hash8 suffix unconditionally; the
   tooling can omit it visually when the prefix is unique within a
   citing document.
6. **Confidentiality leakage via citation.** The fact of citing a
   confidential document may itself be sensitive (a competitor can
   infer subject matter). Recommendation: the
   `selective-disclosure-proof` lets the citing party prove the
   citation without revealing source identity in the bibliography.
7. **Network availability of archival URIs.** Wayback can disappear.
   Recommendation: producers MAY archive to multiple targets and
   list all archival URIs; consumers verify against the content hash,
   not the URI.

## Validator behavior summary

For each kind in this profile, the validator (per the spec's safe-
Rust / safe-Go / safe-C primary implementations) MUST:

- Verify the TOML parses against the kind's canonical shape.
- Verify all IDs resolve (intra-document and cross-document
  references).
- Recompute and verify `closure_root` values per spec.md §12.
- Verify each cited `source_content_hash` matches its referenced
  `source-record`'s `identity.content_hash`.
- Verify quoted snippets (where present) match the canonical text
  at declared offsets.
- Verify Stream B signing-ceremony attestations on each document.

A failed citation is a hard CI failure for any pipeline that consumes
documents carrying citations in this profile. Brittleness is the
feature.

## What this profile does NOT do

- Does not assert the source is correct or true.
- Does not adjudicate the quality of the extraction.
- Does not enforce a citation style — `[render]` is hints; tools
  generate prose.
- Does not specify the LLM model, prompt, or extraction algorithm.
- Does not provide a global naming registry for sources. The
  identity surface (`doi`, `urn`, `url`, `content_hash`) is the
  source's identity; the deployment chooses how to resolve it.

## Recommended next moves

If the proposal lands acceptably, the maintainer should:

1. Create `profiles/source-analysis/PROFILE.toml` (a
   `profile-descriptor` per `core/profile-descriptor-kind.toml`).
2. Create `profiles/source-analysis/{source-record,semantic-extraction,source-citation}-kind.toml`.
3. Create a minimal `examples/` instance for each kind.
4. Add the profile's ontology entries to a new
   `profiles/source-analysis/ontology.toml`.
5. Wire validators (one per kind) following the pattern of
   `validators/validate_implementation_dag.py` etc.
6. Add a small `tools/source-analysis/` CLI for citation rendering
   from the underlying TOML records.

Then commit as a single coherent profile-introduction PR.
