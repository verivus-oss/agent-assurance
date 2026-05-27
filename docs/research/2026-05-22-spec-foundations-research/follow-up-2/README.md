# Follow-up wave 2 — "more processing power" + HW/SW/cognition + Grok share

Third research wave launched in response to:

1. The user's Turn 5 request to explore "what do we do with more processing
   power" — the historical lineage of cognitive-task automation creating
   new problem frontiers, and the rebuttal to "this is overkill" framing.
2. The Turn 5 addendum on HW/SW/cognition layering as inference costs
   decline and FPGA emerges.
3. The Turn 5 request to fetch the Grok share URL conversation about
   secure .toml hosting on Cloudflare / zero trust.

## Contents

- `codex-more-processing-power.md` — Codex's grounded historical lineage,
  6 sections, 30+ primary-source citations
- `gemini-more-processing-power.md` — Gemini's parallel report
  (originally written to repo root, relocated here)
- `grok-hw-sw-cognition.md` — Grok's per-layer HW/SW/cognition ratio
  analysis (today vs 2030, 10×/100×/1000× inference-cost projections,
  DSP→GPU→TPU→inference-ASIC migration pattern)
- `exa-deep-more-processing-power.md` — Exa Deep Researcher (`exa-research-pro`)
  on cognitive-automation lineage *(may still be in flight at commit time)*
- `exa-deep-hw-sw-cognition.md` — Exa Deep Researcher on HW/SW/cognition
  layering *(may still be in flight at commit time)*
- `grok-share-secure-toml-cloudflare-raw.md` — full conversation
  extracted from the Grok share URL via headless Chrome rendering
  (Grok's share UI is client-rendered Next.js; static HTML has zero
  content. Headless Chrome rendered the JS, then we extracted DOM text.)
- `grok-share-fetch-failure-trail.md` — diagnostic record of the
  fetch attempts that failed before the headless-Chrome approach worked
- `09-synthesis.md` — synthesis once all results are in
  *(may be deferred to next session if Exa Deep is still running)*

## Key findings (preview)

The four independent sources converge on a single argument:

1. **Cognitive automation creates new problem frontiers; it does not
   end work.** Each wave (calculator → compiler → search → LLM)
   removes a bottleneck and exposes the next one.
2. **What does not change across waves**: synthesis, judgment, taste,
   trust. These are the load-bearing skills that survive every
   automation wave — they are made *more* important by the next wave,
   not less.
3. **Trust infrastructure is the load-bearing primitive of this wave.**
   When output is cheap, scarcity disappears and verification becomes
   the bottleneck. Brittleness becomes a feature because silent
   acceptance scales the wrong way.
4. **The "too complex / too brittle / too hard" objection is a category
   error.** It applies floor-economics to a frontier system. The
   correct reference class for DAG-TOML / Agent Assurance is not
   `serde` parsing a developer preference file — it is qualified
   electronic signatures, evidence preservation, supply-chain
   provenance, and court-admissible accountability.

For the HW/SW/cognition layering question, the converged answer is
**layer-dependent ratios that shift with cost curves**:

- Determinism-critical layers (canonicalization, hash, signature,
  reproducibility) trend toward hardware over time.
- Validator/parser layers are software-first at the floor; FPGA at
  the throughput frontier.
- Policy/reasoning layers want cognition (LLMs) within
  hardware-attested boundaries.
- Authoring stays cognition-primary, but tooling shifts dramatically
  as inference gets cheap.

The strategic implication for the spec: keep all three doors open at
every layer. **What keeps the door open**: deterministic canonical
form, no Turing-complete primitives in canonical form, no eval, no
remote includes, safe-language validators, hardware-rooted signing
ceremonies. **What closes the door**: mandatory JSON Schema, mandatory
remote contexts, mandatory single-vendor inference, mandatory
features that depend on a Turing-complete evaluator.
