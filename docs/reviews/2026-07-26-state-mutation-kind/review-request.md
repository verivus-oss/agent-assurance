# Independent design review request: the `state-mutation` kind

Instantiates `tools/review-request-dag.toml`.

- **Initiator (excluded from the standard reviewer set):** Claude (Opus 5),
  in Werner Kasselman's session, 2026-07-26.
- **Reviewer models:** Codex, Gemini, Grok, Mistral. Each reviews
  independently, against the artefacts, not against this summary.
- **Change under review:** commit `8290eb3` on branch
  `profile/state-mutation-kind`.
- **Worktree:** `/srv/repos/external/verivus-oss/aa-state-mutation`
- **Base:** `origin/main` (`f9a37cf`).

## Get the diff yourself

```sh
cd /srv/repos/external/verivus-oss/aa-state-mutation
git show 8290eb3 --stat
git diff origin/main..HEAD
```

Twelve files: a new kind descriptor, a new validator, a positive example plus
its capture, three negatives, ontology and profile-descriptor edits, CI wiring,
CHANGELOG, and `docs/reviews/2026-07-26-state-mutation-kind/design-record.md`.

## Reproduce the verification, do not take it on trust

Every claim in the design record's "What was verified locally" table was run by
the initiator. Re-run them. `PYTHONPATH=validators` from the worktree root.

```sh
PYTHONPATH=validators python3 validators/validate_closure_root.py --repo-root . examples/minimal-state-mutation.toml
PYTHONPATH=validators python3 validators/validate_provenance.py   --repo-root . examples/minimal-state-mutation.toml
PYTHONPATH=validators python3 validators/validate_state_mutation.py --repo-root . examples/minimal-state-mutation.toml
PYTHONPATH=validators python3 validators/validate_kind_descriptor.py profiles/com.verivus.runtime/state-mutation-kind.toml
PYTHONPATH=validators python3 validators/validate_abstraction_class.py profiles/com.verivus.runtime/state-mutation-kind.toml
PYTHONPATH=validators python3 validators/validate_profile_descriptor.py --repo-root . profiles/com.verivus.runtime/PROFILE.toml
PYTHONPATH=validators python3 validators/validate_ijb_conformance.py --repo-root . profiles/com.verivus.runtime/ontology.toml
# the sweep as CI invokes it (excludes are load-bearing)
PYTHONPATH=validators python3 validators/validate_closure_root.py --repo-root . --discover . \
  --exclude examples/negative --exclude conformance/cases/implementation-dag/invalid \
  --exclude conformance/cases/api-snapshot/invalid
# negatives: each MUST fail, and MUST fail for its stated reason
PYTHONPATH=validators python3 validators/validate_closure_root.py  --repo-root . examples/negative/state-mutation-no-proof.toml
PYTHONPATH=validators python3 validators/validate_state_mutation.py --repo-root . examples/negative/state-mutation-unbound-proof.toml
PYTHONPATH=validators python3 validators/validate_state_mutation.py --repo-root . examples/negative/state-mutation-inlined-proof.toml
```

Independently recompute the digests. The example's `closure_root` and its
`execution_proof.binds_sha256` are both claimed to be recomputable from the
document's own fields plus the shipped capture. Verify by recomputation, never
by copying.

## The load-bearing claims to attack

1. **The `required` vs `when-present` asymmetry is the design.** The claim is
   that deleting `[execution_proof]` and honestly re-rooting removes two
   REQUIRED pins and fails the closure gate in all three implementations, so a
   state-mutation cannot be downgraded by deletion the way an unwitnessed
   api-snapshot legitimately can. Is that true in the Rust and Go primaries and
   not merely in Python? Is there any way to produce a document that reads as a
   state-mutation, carries no usable proof, and still validates?

2. **RKM04 bound-tuple consistency.** `binds_sha256` must equal the digest of
   the canonical bound tuple over `target_id`, `operation`,
   `authorization_sha256`, `effect_sha256`, `performed_at`. Is the tuple the
   right set? The design record's gap 4 asks whether it should also cover
   `provenance.source_sha256`. Is the canonical form well defined enough that a
   second implementer would produce identical bytes, given that it currently
   lives only in `validate_state_mutation.py` and the kind prose?

3. **The contested decision.** Proof is MANDATORY in the kind, on the grounds
   that the kind's name asserts execution. The alternative, argued by most of
   the earlier board, was typed slots in the kind with mandatoriness deferred
   entirely to the tier binding. The initiator adopted the former. Argue the
   other side properly before accepting it, and say what it costs: a producer
   with a real mutation and no proof now has no kind to use, and no such
   companion kind exists.

4. **Vocabulary design.** `execution_proof_scheme` is closed and includes
   `provider-receipt`, which is materially weaker than the other three. Does
   including it reintroduce the good-will tier the mandatory-proof rule was
   meant to remove? Is `finality_basis` a coherent axis, or is it two things
   (ledger inclusion versus counterparty acknowledgement) wearing one name?

5. **Ontology version.** Adding two vocabularies bumped
   `ontology_version` 1 to 2. Confirm that matches the profile's own
   `version_bump_rule` given the profile is publicly released.

6. **The gaps the initiator declared.** Design record section "Known gaps".
   Are they accurate, and more importantly, are they complete? What did the
   initiator miss?

## Rules

- Verify against files. Cite `path:line`. Do not accept this document as
  evidence of anything.
- Do not approve on intent, on plan-compliance, or on "should be fixed".
  Approve only what you inspected, or name one concrete blocker.
- If you cannot run a primary (Rust or Go) because no binary is present, say so
  explicitly rather than inferring parity from the Python result.
- Never use the em dash character in prose you write.
