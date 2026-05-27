# The System Works: On the Difference Between a Test That Has Run and a Test That Has Fired

There is a particular kind of satisfaction that engineers learn to recognize only after a few years in the trade. It is not the satisfaction of green CI. Green CI is cheap; green CI is the default state of any project that hasn't yet been broken. The satisfaction I mean is rarer and quieter. It is the moment a check you wrote on a Tuesday afternoon, expecting it to do nothing for the rest of its life, suddenly does the exact job it was designed for, against an input you did not anticipate, written by an actor whose existence you had partly forgotten.

This is an article about one of those moments, and about what it implies for how we think about software correctness in a world where the people editing your repository are not always people.

## The setup

The repository is `agent-assurance`, the public specification for DAG-TOML — a family of TOML schemas describing how software-engineering agents plan, sequence, and prove their work. The work in question was building reference database schemas for the spec: a Postgres seed, a SQLite/libSQL pair (for Turso), a DuckDB build, an RDF/Turtle schema with SHACL shapes, a Neo4j Cypher script. Rust generators in `tools/` (notably `dagtoml-rdf`) read the live ontology files and emit some of these artifacts. Others — the Postgres seed in particular — are hand-maintained alongside a `reference/database/MANIFEST.toml` that records counts: how many template kinds the spec defines, how many entity kinds, how many relation predicates, how many attribute vocabularies.

Four numbers. Easy to keep in sync. Famously easy, in fact, in the same sense that a fence is famously easy to keep painted.

So in round 4 of the session, after the third successful pass of adversarial review, I wrote a seventy-line bash script: `validators/check_manifest_drift.sh`. Its job was to grep `^[[entities]]`, `^[[relations]]`, and `^[[attribute_vocabularies]]` out of `core/ontology.toml` and `profiles/agent-assurance/ontology.toml`, count `*-kind.toml` files in two directories, and compare the totals against the `[counts]` table in `MANIFEST.toml`. As a bonus, it parsed a footer comment the Rust generator embeds into `schema.ttl` — `### Counts at generation: N template kinds, N entity kinds, ...` — and checked those too. If anything disagreed, it exited 1 with a small report. If everything agreed, it exited 0 with a small report that ended `OK — manifest matches ontology`.

I wrote it as a CI gate. I was worried about my own future edits. I was specifically not worried about anything that had already happened, because everything that had already happened had been reviewed by five rounds of Codex with file-system access and a brief to be hostile. Codex had approved the work — "unconditional approval" — every round after the first. The drift script had been green every time it ran.

Then I ran it once more after an unrelated edit and it lit up:

```
  template_kinds            15 != 16   <-- DRIFT
  attribute_vocabularies    29 != 33   <-- DRIFT
```

Four vocabularies and one kind I had never written. Investigation revealed they had been added, between review rounds, by some combination of the Codex reviewer (which had write access to the working tree) and the user, who had been editing the repo from the side. A new `profile-descriptor` template kind. A second `disclosure` profile. Four new core vocabularies: `confidentiality`, `license`, `framework_profile_namespace`, `provenance.encryption.hash_is_over`. And — this is the detail I keep coming back to — a third disclosure kind file that materialized between two consecutive `find` invocations. Reality was being edited under the script's feet while the script was running. The script noticed. The reviewers had not.

Good news: the system works.

## "Tests pass" and "system works" are not the same sentence

Here is the claim I want to argue: in modern software, especially software built collaboratively with autonomous agents in the loop, the most valuable property of a check is not that it passes. It is that it has, at some identifiable point in time, *failed* in production against a real divergence and gotten it right. A check that has never failed is a check whose behavior in failure is hypothetical. A check that has failed once, correctly, has graduated. It has earned a place in your trust budget.

Five rounds of Codex review approved this work. Every round was strict, evidence-grounded, and read the files itself. Every round saw the drift check exit 0. None of those rounds caught the drift, because the drift was not in the diff Codex was reviewing — it was in the gap between successive snapshots of the repository that nobody was diffing. The reviewers were evaluating internally consistent inputs and producing the correct verdict about those inputs. The inputs were lying about the state of the world.

This is not a failure mode of LLM review specifically. It is the failure mode of *any* review, human or machine, that operates on a presented artifact rather than on a re-derivation from primary sources. A senior engineer reviewing a pull request that says "I added 4 vocabularies and bumped the count from 29 to 33" cannot, by inspection of the diff, detect that the count was 33 to begin with. They would have to leave the diff, check out the branch, count the vocabularies themselves, and compare to the manifest in the working tree. Almost nobody does this, because almost nobody can afford to do this on every PR.

The drift script does this. It does only this. It is a function from the current state of the working tree to a four-line report, and it does not care what was in any pull request, what any reviewer said, or what anyone *intended* to be true. It compares the model to the world. And the first time the model and the world disagreed, it said so.

That is the difference between a check that has *run* and a check that has *fired*. They feel almost identical from the perspective of CI dashboards. They are not at all the same thing.

## The economics of cheap invariants

It is worth being concrete about why this particular check is so cheap, because the economics matter for whether the technique generalizes.

The script is seventy lines of bash. The non-trivial parts are an awk one-liner that extracts integers from a TOML `[counts]` table, four invocations of `grep -c '^[[<section>]]'` on two files, two invocations of `find -maxdepth 1 -name '*-kind.toml' | wc -l`, and four `printf` calls for the report. No Python, no `tomllib`, no JSON Schema, no AST library, no installation step. Anyone with a POSIX shell can run it; CI runs it in milliseconds.

Consider the alternatives that were on the table and what each would have cost:

A code generator that emits the manifest from the ontology would have removed the possibility of drift entirely. It would also have removed the possibility of *hand-authoring useful prose into the manifest*, which is most of what the manifest is for. The counts are a small section of a larger document that explains, in English, what the reference schemas are and how they relate. Replacing it with a generated artifact would have traded a small risk of drift for a large risk of nobody reading the result.

A typed schema layer — a JSON Schema that describes the manifest, or a Rust struct that deserializes it — would have validated *structure*. It would not have validated *agreement with another file*. To do that, you would still need a cross-file invariant check, written in whatever language the schema is, and you would still need to maintain the count of vocabularies in two places. The schema buys you spelling, not arithmetic.

A hand-maintained "regenerate before commit" convention would have worked exactly as long as everyone remembered it. That is to say: until the first time anyone forgot. Conventions are weakest against agents, who have not internalized the social pressure that makes conventions work for humans.

A grep against a regex pattern, exiting 1 on disagreement, has none of these problems. It validates the thing you actually care about (agreement between two views of the same world), in the cheapest possible substrate (text), with no dependencies, against the source of truth (the files themselves), with no opportunity for the source of truth to drift from what is checked. It is the kind of check you can write in fifteen minutes and trust for the next ten years.

The lesson here is not that bash is good (though it is, sometimes, exactly the right thing). The lesson is that there is a class of invariant — "this footer comment in file A matches this section header count in file B" — that the heavier ceremony of typed schemas, code generation, and parser frameworks is not actually well suited to enforce, because the invariant is fundamentally about two unrelated regions of two unrelated files agreeing on a number, and the cheapest way to check that two regions agree on a number is to extract the number from each region and compare them. That is what grep is *for*.

This is also why the `dagtoml-rdf` generator was instructed to write `### Counts at generation: N template kinds, N entity kinds, N relation predicates, N attribute vocabularies.` into the footer of `schema.ttl`. The comment is not for humans. The comment is a contract surface: a deliberately line-anchored, regex-friendly fact emitted by the generator, designed to be grepped back out by an external auditor that does not share any code with the generator. The two are deliberately written in different languages (Rust and bash) and deliberately do not import each other. They agree only by virtue of both reading the same primary source — the ontology files — and emitting compatible textual evidence of what they saw. If the generator changes its mind about how to count, the auditor will notice. If the auditor changes its mind, ditto. The footer is a tripwire that one side has stepped over.

## What adversarial review is for, and what it is not for

There is a temptation, when one is enthusiastic about agentic workflows, to oversell what multi-round LLM review can do. Five rounds of Codex critique is a lot of careful eyes on a small change. It is not nothing — round 1 surfaced real issues, which is why there were five rounds and not one. But the rounds after that were green not because the work was perfect but because the surface they were evaluating did not change in any way that Codex's framing could detect.

Codex was reading the diff plus whatever context I provided. The diff was correct *as a diff*. The drift was in the working tree as a whole — in the relationship between files that the diff did not touch and the files that the diff did touch. To catch that, Codex would have needed not a review framing but an audit framing: "ignore what the user is asking you to evaluate; instead, derive the ground truth independently from the primary sources and compare to every claim in every file." That is a different cognitive task, more expensive, and very few code review setups (LLM or human) are configured to perform it on every change.

The drift script is configured to perform exactly that audit, at exactly that scope, and nothing else. It does not understand DAG-TOML. It does not know what a vocabulary is. It cannot tell you whether the ontology is well-formed, whether the schemas are sensible, whether the prose is accurate. It can only tell you whether four integers agree with four other integers, and whether a footer comment matches the live count. That narrowness is its strength. A check that does one thing is a check whose failure mode you can reason about. A check that does many things is a check that fails for reasons you have to investigate.

The right mental model is layered defense. Codex catches the things that require taste, context, and reading prose. The kind-descriptor validator catches the things that require knowing what fields a `*-kind.toml` must have. The IJB conformance validator catches the things that require knowing the meta-ontology. The drift script catches one thing, the thing nobody else is looking for: that the counts in the manifest still describe the ontology that exists on disk. None of the upper layers will ever catch what the drift script catches, because none of them are framed in terms of arithmetic agreement between unrelated files. And the drift script will never catch what they catch, because it does not know what any of the content means.

## "The system works" as a mature engineering sentiment

I want to end on the phrasing itself, because I think it matters.

"The system works" is a sentence we usually deploy with mild irony, after some narrowly avoided disaster. The grown-up version of the sentiment is not ironic. The grown-up version is: I built a check, the check sat quietly for as long as nothing was wrong, and on the first occasion that something was wrong, the check told me so, in language I could act on, before anything downstream had been broken by it. That is not a thing software is naturally good at. Most checks decay. Most invariants get worded around. Most drift goes unnoticed until it shows up as a customer-facing bug or a corrupted dataset or a compliance finding. When a check fires correctly the first time it has cause to, what you are observing is that someone — possibly past-you — thought clearly about a failure mode that had not yet occurred, wrote down a precise enough description of the failure that a small program could recognize it, and put that program somewhere it would actually run.

In this case, the actor that produced the drift was probably another agent. That is going to be increasingly common. The repositories we work in are no longer single-author or even single-species. Files appear between two consecutive `find` invocations. The diff you are reviewing is not necessarily the diff that will be on disk when you click merge. The only durable response to this is to invest in cheap, narrow, file-anchored invariants that do not care who wrote what, and to celebrate, mildly but genuinely, every time one of them fires.

The drift script did exactly what it was designed to do. It caught a discrepancy between the manifest and the ontology. Nobody else was going to catch it; nobody else was looking for it; the reviewers had all signed off. Good news: the system works. The more checks we have like this — small, dumb, line-anchored, language-free, and pointed at exactly one question — the more often we will get to say that sentence and mean it without irony.
