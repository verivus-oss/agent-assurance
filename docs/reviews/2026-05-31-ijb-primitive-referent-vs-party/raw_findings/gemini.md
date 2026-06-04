## Process Checks
- **Collision Scan**: Re-run confirmed. `referent` has 0 hits outside the current review directory (`docs/reviews/2026-05-31-ijb-primitive-referent-vs-party/`). However, the `reference` family (`reference`, `references`, `referenced`) has over 1300 hits combined. `party` has 132 hits (primarily "third-party", "multi-party").
- **Upstream Citations**: Citations in files 04/05 (e.g., `foundations/ijb/primitives.md` and canonical grammar) resolve correctly at HEAD without drift.
- **Slopscan**: Factual claims in both drafts hold up against `tools/README.md#standard-slopscan`. No hallucinated file paths or invented lexical facts detected.

## 1. Per-axis verdict

- **1. Official meaning of primitive #1**: `party`
  - **Evidence**: `foundations/ijb/primitives.md:10` ("Objects that exist")
  - **Justification**: `referent` forces a semantic shift from existence-anchoring to reference-first framing, whereas `party` maintains the original existence focus.
- **2. Internal collision**: `party`
  - **Evidence**: `foundations/ijb/canonical-assertion-grammar.md:43` ("Replay must dereference referenced assertion IDs")
  - **Justification**: The `reference` family is deeply saturated (>1300 hits), creating a massive confused-by-proximity risk for `referent`, while `party` uses are distinct and unambiguous.
- **3. Legal / regulatory risk**: `referent`
  - **Evidence**: `profiles/agent-assurance/tiers/enterprise.toml:68` ("third-party re-derivation party")
  - **Justification**: `party` carries heavy legal register baggage ("third-party", "relying party") risking audit misinterpretation, whereas `referent` has no legal standing.
- **4. Brand / tone**: `party`
  - **Evidence**: `foundations/ijb/why-this-matters.md:73` ("Resistance to abstraction")
  - **Justification**: IJB's brand is explicitly plain-spoken; `referent` is an academic semiotics term that violates this, while `party` is plain business English.
- **5. Replay & ergonomics**: `tie`
  - **Evidence**: `06-drafts-for-party.md:39` / `07-drafts-for-referent.md:104`
  - **Justification**: Both drafts adopt the identical strategy of dropping the noun in high-frequency replay ("X exists within Scope Y"), mooting the ergonomic difference.
- **6. Directional ambiguity**: `party`
  - **Evidence**: `07-drafts-for-referent.md:27` (Merriam-Webster: "one that refers or is referred to")
  - **Justification**: `referent` has bidirectional dictionary meaning requiring a SPEC carve-out to restrict it to passive-only, which is a precision liability.

## 2. Findings list

- **Finding**: `referent` introduces severe confused-by-proximity risk due to the massive saturation of the `reference` family in the codebase.
  - **file:line**: `foundations/ijb/canonical-assertion-grammar.md:43`
  - **severity**: blocker
  - **counts against**: `referent`
- **Finding**: `referent` forces a semantic reframe from existence-anchoring to reference-anchoring, diverging from the current primitive #1 definition.
  - **file:line**: `foundations/ijb/primitives.md:10`
  - **severity**: major
  - **counts against**: `referent`
- **Finding**: `party` carries heavy legal-register baggage and is used heavily in "third-party" contexts, creating potential audit-misinterpretation exposure.
  - **file:line**: `profiles/agent-assurance/tiers/enterprise.toml:68`
  - **severity**: major
  - **counts against**: `party`
- **Finding**: `referent` is an academic/semiotic term that violates IJB's explicit anti-abstraction and plain-spoken brand.
  - **file:line**: `foundations/ijb/why-this-matters.md:73`
  - **severity**: major
  - **counts against**: `referent`
- **Finding**: `referent` contains directional ambiguity, requiring explicit SPEC documentation to lock it to the passive sense.
  - **file:line**: `07-drafts-for-referent.md:27`
  - **severity**: minor
  - **counts against**: `referent`

## 3. Terminal recommendation

`adopt_party` (with the concrete reason `referent`'s cost is disqualifying)

## 4. The decisive factor

The massive codebase saturation of the `reference` family makes `referent` an unmanageable proximity-collision risk, which, alongside its academic tone and semantic reframe, thoroughly disqualifies it as a primitive name.