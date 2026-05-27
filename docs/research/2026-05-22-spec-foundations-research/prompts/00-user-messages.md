# User messages — verbatim

The complete chain of user-originated prompts that drove the research,
in order. Reproduced as faithfully as possible (typos preserved).

## Turn 1 — initial research ask (2026-05-21)

> use exa and do extensive research and searching for guidance and challenges associated with creating these types of specifications. Start with the ijb primitives.  use subagents to ask for the same independent research from codex, gemini and grok, using exa!  if they don;t have a configuration for exa - you need to add it for them.

## Turn 2 — check on jobs

> check on researh - it's not persisted for a long time

## Turn 3 — design directives after first synthesis

> save the full synthesis plus the four raw agent reports + Exa deep researcher report under
>   docs/research/2026-05-22-spec-foundations-research/
>
> 2. TOML-only spec design — load-bearing risks json has problems that are insurmountable for the use in this context, validators should be safe rust and safe golang and "safe c" primary, the rest can be ports, I don;t get the rest of the argument
>
> 3. Kind-descriptor / self-describing-schema drift -> I need a) solution options,  b) create something new
>
> 4. a) + b) Provenance paradox. the consumer of the artifact should only have to check the last artifact, and make provenance possible for the next.  it can only be established with sha256 minimum hash of the source i.e. supply chain attacks imply trusting a / the proces not the artifact, this puts more responsibility on the artifact providers, not on the consumers.  however when a consumer has accepted an artifact, they only accept that sha'ed artifact, no upgrades, no previous versions, the attested provenance is a one shot, immutable, attestation. we are designing a authentication / authorisation method using current stacks, this needs to be a requirement for anyone who can "ship" an artifact.  it needs to be able to prove in a legal sense that the person who signed, a) intended to sign, b) can withdraw authority (age), invalidate a signature, each of these attestations will break an upstream sha and indicate an issue.  this needs carefull documentation and exploration.  the problem space exists, there are no solutions yet, this is creating something new
> c) Gate Gaming - the agent(human, program, llm, whatever) cannot validate it's own work, the validation of (i.e. did we build and did we pass the gates we said we would) is the mechanical check - we're showing what we intend to do, then doing it, then proof that we did it, and at the end of the day it's auditable (similar in concept to ISO 9001 and other similar standards) - I'll reiterate that the proof must not depend on the agent who created the work.  need to create a separate research and validation stream
>
> 5. record it, we'll come back later
>
> 6. is there ANY other format, mechanism, standard that would be more suited?  should / can we create something new? brittleness is not really a bug for this, it's a feature. trust is the currency

## Turn 4 — persistence check

> have you recorded everything (ask, submissions, responses(complete), synthesis ) on disk in a persisting NON-ephemeral location?

(Triggered the creation of this `prompts/` directory.)

## Turn 5 — save remaining ephemeral, commit, fetch Grok share, explore "more processing power"

> write everything else that is still ephemeral to a saved state and then commit.
>
> ask grok to get the entire conversation history from https://grok.com/share/c2hhcmQtMi1jb3B5_8bddbdcc-14f9-4339-a313-b1c3c39724c0 and save that, we need to incorporate that thinking and discussion going forward
>
> we also need to explore the "what did we do with more processing power" type discussion.  i.e. what we're building may seem overkill and too complex to maintain and too difficult to implement, this would be a mistake.  what do we do once 'lighter' cognitive tasks are taken care of?  we get to start focussing on problems that seemed insurmountable before!  there is an analogy and lineage that we can build on that scenario

## Turn 5 (addendum) — HW/SW/cognition layering

> also, as inference costs decline and fpga solutions emerge, I get the sense that a combination of hardware, software and 'intelligence/cognition' will be needed in various ratios at different layers or levels

Recorded as a design observation in
[`../06-user-design-directives.md`](../06-user-design-directives.md)
and as research-stream input in
[`07-followup-research-streams.md`](../07-followup-research-streams.md).
