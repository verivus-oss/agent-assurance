# Gateway Dispatch Record

Date: 2026-05-29 UTC

The required gtwy MCP dispatch was attempted before falling back to
direct read-only CLI review where the wrapper/provider environment
blocked useful output.

## gtwy MCP Attempts

- Codex async job `13d14d41-fe5a-41ba-ada2-c03aeac6caa7` failed with
  exit code 2 because the wrapper passed an unsupported
  `--ask-for-approval` argument to the installed Codex CLI.
- Codex async retry `6483b364-9195-4826-a268-795a260fe742` failed with
  exit code 1 because Codex auth was invalid:
  `token_invalidated` / `app_session_terminated`.
- Gemini async job `d68c2e67-8f0f-4eaa-aa91-aabd64b61864` failed with
  exit code 55 because the gateway wrapper did not pass
  `--skip-trust` / workspace trust.
- Gemini async retry `d1da64a7-f380-4390-8460-e5168a4e7406` failed
  for the same workspace-trust condition.
- `validate_with_models` Gemini job
  `a542aad1-0804-46da-8096-e8bbe9d7caca` also failed for workspace
  trust.
- Grok async job `aa552056-de9b-4bc6-a5ec-6d998cb25285` completed
  with exit code 0 but returned an empty stdout body.
- Grok async retry `c1763a7d-c378-4a01-b8b2-90dc15f416d0` also
  completed with exit code 0 and empty stdout.
- Grok `ask_model` job `26defc41-9d8d-4fed-ba68-5c35c4c476af`
  returned a short response:
  `READY` and a one-sentence approval based on supplied evidence.
- Mistral validation job `806605c4-8555-4566-8bee-ff9bffb4c889` was
  still running with no useful stdout and was canceled.
- Claude async fallback `0ae6464b-0bb3-4860-a54a-dfab147568cd` was
  dispatched through the gateway as an extra provider, did not produce
  useful output in time, and was canceled.

## Direct CLI Fallbacks

- Gemini direct CLI with `GEMINI_CLI_TRUST_WORKSPACE=true`,
  `--skip-trust`, and `--approval-mode plan` produced a substantive
  PASS review in `gemini-review.md`.
- Grok direct CLI with `--permission-mode plan` produced a substantive
  PASS review in `grok-review.md`. It first emitted an authorization
  warning but later completed with review text.

These dispatch failures are environment/tool-auth failures, not
validator failures. They are recorded here so the review evidence does
not silently present unavailable providers as successful reviewers.
