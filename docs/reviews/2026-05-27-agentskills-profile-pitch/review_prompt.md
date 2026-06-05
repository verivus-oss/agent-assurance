# Outbound-pitch review — agentskills profile proposal + before/after pairing (2026-05-27)

Fresh-context reviewer. Proposal-stage review (no commit, no diff). Two
units under review:

- **P01** — `docs/posts/2026-05-27-agentskills-profile-proposal-draft.md`
  (the pitch itself)
- **P02** — `docs/posts/2026-05-27-skills-corpus-before-after-pairing-draft.md`
  (the companion before/after artifact)

Both posts are OUTBOUND and PUBLIC-FACING. They will be posted under the
initiator's own name on the public Agent Skills Discussions board. Every
claim about the agentskills/agentskills repo, the agent-assurance repo,
or the mattpocock/skills repo MUST be verified against bytes — not
against this prompt, not against the bundle's summary.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- HEAD: `3a480eb` (or later, if rebased before review)
- Bundle: `docs/reviews/2026-05-27-agentskills-profile-pitch/review_bundle.toml`
- Research repo (peer of this one):
  `/srv/repos/external/verivus-oss/agent-assurance-research/` — contains
  `mattpocock-skills/` and `agentskills/` clones, both indexed via sqry.

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept the initiator's summary as evidence.
File:line + severity for every finding. `forbidden_approval_bases`:
`stated_intent`, `plan_compliance_claim`, `should_be_fixed_language`.
Terminal: `unconditional_approval` or `concrete_unresolvable_blocker`.

## Context (verify, don't trust)

The two drafts together pitch an opt-in assurance profile (separate
repo, not a core-spec change) to the Agent Skills maintainers. P01
makes the pitch; P02 walks through a concrete worked example using
Matt Pocock's `triage` skill as the "before" case and a hypothetical
`gate-decision`-wrapped equivalent as the "after."

Reviewers MUST verify these starting facts against repo bytes BEFORE
classifying any sub-claim:

1. The agentskills/agentskills repo's stated facts (stars, license,
   format shape, governance, anthropics/skills companion repo,
   homepage). Source: the README and other public pages at
   `https://github.com/agentskills/agentskills` and
   `https://agentskills.io`. A local clone exists at
   `/srv/repos/external/verivus-oss/agent-assurance-research/agentskills`
   — confirm against bytes there OR fetch the live URLs.
2. The mattpocock/skills repo's stated facts (license, attribution,
   the `triage` skill's exact contents at lines 10–14 of
   `skills/engineering/triage/SKILL.md`). Source: clone at
   `/srv/repos/external/verivus-oss/agent-assurance-research/mattpocock-skills`.
3. This project's spec facts cited in either draft:
   - `closure_root` semantics per SPEC §12, including the empty-closure
     sentinel value
     `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
   - `capability_envelope` per SPEC §13 (WASI Preview 2 domains + cpu/memory bounds + fail-closed default)
   - `gate-decision` descriptor at
     `profiles/agent-assurance/gate-decision-kind.toml` and the
     separation-of-duty rule for `subject_class = "self-modification"`
     (added 2026-05-25 via the cross-provider-self-mod-gate-proposal
     review; verify the rule actually landed in repo bytes)
   - Multi-provider-only profile posture
4. The two drafts do NOT propose changes to the Agent Skills core
   spec, do NOT name any specific runtime/broker/implementation of
   the assurance substrate, do NOT propose a JSON Schema sidecar, and
   do NOT carry a Claude/AI co-author trailer. Each of these MUST be
   confirmed by grep against the draft text.

## Sub-claims to classify (eight total)

For each, classify as `complete` / `incomplete` / `unverifiable` with
file:line evidence and severity. See bundle for the full text of each
sub-claim:

- **P01-C1**: factual accuracy about agentskills/agentskills
- **P01-C2**: factual accuracy about this project's spec
- **P01-C3**: policy compliance (memory / VAP / JSON Schema / Claude trailer)
- **P01-C4**: tone and framing
- **P02-C1**: factual accuracy about mattpocock/skills (especially the verbatim quote at lines 10–14 of triage/SKILL.md, MIT attribution, workflow shape)
- **P02-C2**: factual accuracy about this project's spec, especially the example `gate-decision` TOML block (field names plausible, illustrative fields marked, sentinel correct, subject_class correctly NOT "self-modification" for ordinary triage)
- **P02-C3**: policy compliance (same as P01-C3 plus MIT attribution to Matt Pocock present and accurate, quoted excerpt clearly attributed)
- **P02-C4**: tone and framing (small/surgical/additive delta, NOT "mattpocock is doing it wrong"; "load-bearing gap" framing is specific not vague)

## Tooling

You have sqry MCP access — use it. The research repo
(`/srv/repos/external/verivus-oss/agent-assurance-research`) is indexed
(~335k nodes, 575k edges across all cloned repos). Useful queries:
locating the exact lines in mattpocock-skills/triage/SKILL.md;
cross-referencing field names in
profiles/agent-assurance/gate-decision-kind.toml; finding any prior
review session that touched the self-modification rule.

You also have web access (the bundle's `verify` list includes fetching
agentskills.io / github.com/agentskills/agentskills). Use it for P01-C1.

## Output

Write your full review verbatim to
`/srv/repos/external/verivus-oss/agent-assurance/docs/reviews/2026-05-27-agentskills-profile-pitch/raw_findings/<your-reviewer-name>.md`
(filenames: `codex.md`, `gemini.md`, `grok.md`, `mistral.md`).

Structure:
- One section per sub-claim (P01-C1..C4, P02-C1..C4)
- Classification (complete / incomplete / unverifiable)
- File:line evidence for each claim made or refuted
- Severity (blocking / advisory / nit)
- Terminal recommendation at the end: `unconditional_approval` OR
  `concrete_unresolvable_blocker` with the blocker named

Do not add a Claude/AI co-author trailer. Do not summarize at the end
— the per-claim sections are the artifact.
