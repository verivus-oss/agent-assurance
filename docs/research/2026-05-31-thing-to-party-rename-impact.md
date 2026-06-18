# Impact Report: Renaming IJB Primitive #1 `thing` → `party`

> **STATUS: FURTHER RESEARCH ONLY — NOT A DECISION OR APPROVED CHANGE.**
> This is an exploratory impact analysis of a *hypothetical* `thing`→`party`
> primitive rename. It is **not** a sanctioned review with a terminal decision,
> **not** an approved migration, and **not** authorization to modify the spec.
> Standing state is unchanged: `party` is the chosen primitive *name* (per the
> 2026-05-31 naming review at `docs/reviews/2026-05-31-ijb-primitive-referent-vs-party/`),
> but **no rename of the `thing` primitive has been decided, scheduled, or
> authorized.** Do not act on §6 (migration order) without an explicit,
> separately-approved decision.

**Date**: 2026-05-31
**Method**: Multi-agent workflow — 10 exhaustive per-group readers + adversarial
per-group verifiers + 2 completeness rounds + synthesis. 43 agents, 391 tool calls,
388,951 output tokens (cap 900k). 189 sites confirmed (0 false positives), 411
follow-up sites surfaced across 2 rounds. Headline claims independently re-verified
against bytes by the initiator.

---

## 1. Verdict & overall risk

Renaming IJB primitive #1 from `thing` to `party` is a **mechanically tractable but
wide-blast-radius rename touching ~189 sites**, ~70 of them hard breakages that fail
parsing/validation/graph-resolution if not changed in lockstep; the rest are prose.
The rename is **safe with respect to the closure_root/sha attestation layer** —
`closure_root` is a SHA-256 over the §12.8 `[provenance].source_sha256` source-hash
closure stream (spec.md:1044), **not** over canonical assertion bytes, so the IJB
primitive token never flows into any committed `closure_root`.

**Risk rating: MEDIUM.** Load-bearing reason: the **inverse collision** — unlike
`thing` (never a domain noun here), `party` already appears as live English in
normative-adjacent prose ("third-party" spec.md:177; "appropriate party" spec.md:1544),
introducing ambiguity that `thing` was immune to and that no validator can
mechanically disambiguate. A naive unanchored replace also corrupts
`anything`→`anyparty` (spec.md:648). Medium, not high, only because the sha/immutability
core is provably untouched.

## 2. Hard breakages (BREAK parsing/validation/sha if not changed — must change atomically)

**Grammar token & ABNF** (`foundations/ijb/canonical-assertion-grammar.md`):
- L50 `primitive-call = thing-call / …`
- L52 `thing-call = "thing(" (thing-struct / thing-inst) ")"` — the constructor token `thing(` + rule names
- L53–54 `thing-struct` / `thing-inst`
- L58 `scope-use = "thing=" ref "," "within=" ref` — the field-key literal `thing=`
- L112 / L124 validation-rule prose binding the `thing=` field token

**Replay templates** (same file, L98–101): `Structural Thing <id> exists.`,
`Thing <id> exists as instance of <instance_of>.`, `Thing <thing> exists within Scope
<within>.` — both the `Thing` label and the `<thing>` placeholder.

**Worked-example assertion bytes**: grammar L139–145 (`thing(id=…)`, `scope(thing=Alice,…)`);
`examples/05-*.md` (~12 tokens), `examples/07-*.md` (~31 tokens).

**ijb_primitive pins** (closed-set literal `"thing"`):
- spec.md:598 (closed-set def), 629/652/663 (§10.2 mapping cells)
- `core/ontology.toml` — **17** `ijb_primitive = "thing"`
- core `*-kind.toml` (6): readiness-gate:71, evidence-matrix:80, implementation-dag:93, traceability:112, profile-descriptor:111, contract-declaration:66
- all three profiles' kind files + ontology.toml + PROFILE.toml (~50 pins total incl. disclosure PROFILE.toml:44, ontology.toml:45/56/67)
- examples/minimal-adapter-contract.toml:30, examples/negative/kind-descriptor-name-mismatch.toml:18

**Validator string-literals — all three normative implementations**:
- Go `tools/dagtoml-validate-go/main.go:308` `ijbPrimitives = []string{"thing", …}` (+ 375/456/484)
- Rust `tools/dagtoml-validate-rs/src/main.rs:379` `IJB_PRIMITIVES = &["thing", …]` (+ 469/598/662)
- Python `validators/validate_ijb_conformance.py:56` `IJB_PRIMITIVES = ("thing", …)` (+ 177/413/488)

**RDF emitters + generated artifact**:
- Go `tools/dagtoml-rdf-go/main.go:401` `{"Thing","thing"}` (+ 409/418/421/551)
- Rust `tools/dagtoml-rdf/src/main.rs:319` `("Thing","thing")` (+ 343/361/367)
- Generated `reference/database/rdf/schema.ttl`: class def L18, label L19, **30 `ijb:Thing`** (IRI `#Thing`→`#Party` + ~28 `rdfs:subClassOf ijb:Thing`)

**DB enum / CHECK constraints**:
- Postgres `schema.sql:41` enum member `'thing'` + defaults L125/222
- SQLite `schema.sql` CHECK `ijb_primitive IN ('thing',…)` at L51/66/141/169
- DuckDB `schema.sql:37` enum + L160 default
- All three `seed.sql` carry ~27 `'thing'` row values that must match the renamed enum

**Cypher**: `graph/schema.cypher:144` `k.ijb_primitive = 'thing'`, L213 comment, `:IjbThing` label (L19–20).

## 3. The closure_root / sha cascade — the deepest impact (and the reassuring one)

Intuition says "immutable sha-bound attestations will all break." The bytes say **they will not.**

`closure_root` (spec.md:1044) is a SHA-256 over the §12.8 source-hash closure stream
for `[provenance].source_sha256` — inputs are upstream **source file hashes**, not
assertion grammar bytes. The entire §12 closure/sentinel/sha machinery
(spec.md:883–1232) contains **zero** thing-primitive tokens.

- **0 committed `closure_root`/sha values must be recomputed.** Of 36 committed
  `closure_root` literals, 35 are the empty-closure sentinel
  `sha256:e3b0c442…7852b855` (SHA-256 of "") and 1 is a provenance example; none
  hashes assertion bytes.
- Worked-example assertion blocks carry **no committed** closure_root/digest/hash.
  The verifier's "feeds any sha over the block" is conditional (a sha a downstream
  consumer *might* compute at replay), not an in-repo value.

**Ethos interaction (correct & intended)**: the brittleness graph (spec.md:962–988)
scopes the cascade to provenance source hashes, not vocabulary spelling. A
vocabulary rename is a **new spec version** (bump `schema_version`), not a mutation of
an attested document — prior documents stay byte-identical and their shas stay valid.
The only genuine "break" is an external party who already hashed old-grammar
assertion bytes seeing a mismatch — which is exactly the visible-invalidation property
the ethos wants.

## 4. The inverse collision — the load-bearing risk

`thing` was *safe* because "thing"/"things" here is only the primitive or English
filler, and filler never collides with grammar. `party` lacks that property:

- **spec.md:177** — "non-spec-reserved (private or **third-party**) profiles" — normative adopter guidance; fixed compound, must not become a primitive reference.
- **spec.md:1544** — "approved by an **appropriate party**" — normative gate prose; the English legal noun, the exact sense a security/legal-grade reader assumes.
- General: future "the requesting party", "third parties", "party to the contract" now read ambiguously.
- **Substring hazard (spec.md:648)**: `anything` contains `thing`; naive global replace → `anyparty`. `info` if fenced; `severe` under an unanchored sed.

**Tolerable only with strict targeting**:
1. Rename only via backticked/grammar-token literals — `` `thing` ``, `thing(`, `thing=`, `ijb_primitive = "thing"`, `ijb:Thing`, `"thing"` in code arrays. Never bare-word substring replace.
2. Add a disambiguation note: the *primitive* is always code/backticked/capitalized `Party`; the English noun "party" stays prose — so spec.md:177/1544 are deliberately left unchanged.
3. **Flag to requester**: on collision grounds `party` is a *worse* name than `thing`. This is consistent with the 2026-05-31 naming review, which adopted `party` despite its legal-register loading. Confirm the trade is still wanted before landing.

## 5. Soft changes (prose/examples/docs — non-breaking, consistency only)

- spec.md prose primitive references (~5): L456/458/577/603/760. (L764 English "things", L648 "anything" — leave.)
- profile-descriptor-kind.toml `thing/structural` tags: L102, L236.
- core/ontology.toml header prose L41–42.
- RDF/DB comments: schema.ttl L146, postgres schema.sql:125, cypher L19–20.
- IJB examples README L112.
- High-density prose files (mostly English "things" — change only primitive references): primitives.md, core-specification.md, README.md, why-this-matters.md, faq.md, getting-started.md, fco-im-integration*.md, worked examples 01/02/03/06.

## 6. Migration order (steps 1–5 must be atomic)

1. **Grammar + spec normative core** — grammar ABNF tokens/rule names/replay templates/worked-example bytes (L41–145); spec.md §10.2 closed-set + mapping (598/629/652/663).
2. **Ontology pins** — core/ontology.toml (17) + six core `*-kind.toml` (+ profile pins).
3. **All three validators simultaneously** — Go + Rust + Python. Landing one ahead means validators disagree on the closed set = conformance failure.
4. **RDF emitters then regenerate** — edit Go + Rust emitter source, then regenerate `schema.ttl` (do NOT hand-edit; it is generated). Verify `#Thing`→`#Party` + all 30 `ijb:Thing`.
5. **DB schemas + seeds** — enum/CHECK members and `'thing'` seed values together (or inserts violate the constraint).
6. **Recompute shas — NO-OP** (see §3). Bump `schema_version` instead. Document this so reviewers don't hunt for shas to bump.
7. **Examples** — worked-example bodies with the grammar; example `*.toml` need no closure_root recompute.
8. **Docs/prose** — last, non-atomic; apply the §4 fence (leave English "party"/"things"/"anything").

## 7. Coverage statement

**Verified in full against bytes**: all six core `*-kind.toml` pins; core/ontology.toml
(17 pins); all three validator sources; both RDF emitters + generated schema.ttl (30
`ijb:Thing`); all four DB schemas + cypher; grammar L41–145; spec.md §10 + entire §12
(L883–1232 confirmed token-free); the two inverse-collision sites + the `anything`
hazard; all 36 committed `closure_root` literals (35 sentinel + 1 non-sentinel).

**Completeness**: 2 critic rounds on top of the surveyor inventory (~189) and
adversarial per-group verifiers; 11 missed/clarified sites independently re-confirmed
(notably grammar L124/L145 and 5 of 6 kind-descriptor pins).

**Residual uncertainty**: (a) exact soft-prose count in high-density doc files is
verifier-reported, not re-counted (~189 total ±a handful in the prose tail); (b)
`seed.sql` `'thing'` row counts confirmed present but not individually enumerated; (c)
whether `party` is the desired target given §4 — a design question flagged, not
resolved. None affects the load-bearing findings: §2 hard-breakage set is
byte-confirmed; §3 sha no-op is byte-confirmed.
