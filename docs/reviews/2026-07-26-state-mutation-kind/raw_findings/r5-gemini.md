# Round 5, Gemini: NO VERDICT (provider timeout, third consecutive)

Gateway job `3ecd3fb5-bd4c-473c-8a50-47efc56486c3`. Dispatched
2026-07-27T02:12:52Z, failed 02:18:00Z after 5m08s, exit 1, zero bytes stdout,
stderr in full:

```
Error: timeout waiting for response
```

**This dispatch set `idleTimeoutMs: 900000` (15 minutes) and still died at
5m08s**, the same duration as the round-3 failure. The ceiling is therefore
inside the gateway's Gemini adapter and is not controllable by the caller, so
retrying with a longer timeout is not the fix. That is now an established fact
rather than a guess, having been tested.

Gemini has produced no verdict for rounds 3, 4 or 5. Two of its own positions
have now been decided without it:

- **SPEC 12.8.2 Unicode normalization.** Gemini demanded a normalization form
  be mandated. The opposite was done, requiring none, and Grok and Mistral both
  independently endorsed that. Encoded in the corpus only indirectly.
- **Absent `meta.template_kind`.** Two round-4 reviewers wanted absence
  rejected; SPEC 12 was read as ratifying it, and
  `conformance/cases/state-mutation/valid/escape-hatch-absent-template-kind.toml`
  now asserts MUST-ACCEPT. If that reading is wrong, the corpus enshrines it.

Both were flagged to Gemini explicitly in the round-5 prompt as fair game. The
board has been effectively three reviewers since round 3, and the record should
say so rather than implying four.
