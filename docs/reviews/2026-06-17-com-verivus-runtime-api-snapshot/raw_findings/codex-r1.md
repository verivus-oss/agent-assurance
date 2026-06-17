# Codex review — iteration 1 — CONCRETE BLOCKERS (2)

Job 6d936510-7f43-4126-99a3-6b7835fe3689 (codex-cli 0.140.0, gpt-5.5), exit 0.
Reviewer recomputed digests, ran validators, probed for bypasses.

BLOCKER 1 (RKV02 bypass): validate_api_snapshot.py only rejected secret-named
header keys; a raw NON-secret significant-header value (`accept = "application/json"`
under [snapshot.request] with significant_headers=["accept"]) was ACCEPTED,
contradicting RKV02 ("every significant request-header value carried as a digest,
never raw"). Probe: PASSED (exit 0) — bug.

BLOCKER 2 (RKV01 overclaim): the kind says descriptor_sha256/body_sha256 sub-part
consistency is "checked by validate_api_snapshot.py", but the validator only
checked digest scalar shape, never reading the capture. A wrong descriptor_sha256
(sha256:000…) was ACCEPTED. Probe: PASSED (exit 0) — bug.

Materially verified everything else (closure fold source-only byte-identical in
py/rs/go; capture sha256 1af17d…eab7, 620 bytes, closure f251f6…98c; sub-digests
recompute; positives pass; bad-closure/bad-ijb rejected by all three; RKV02/RKV03
supplied negatives rejected).
