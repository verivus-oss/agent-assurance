# Deployment tiers (Agent Assurance Profile)

The Agent Assurance Profile ships five deployment tiers as named
bundles of cross-cutting contracts. Tiers are NOT a new
`template_kind`; each tier file is a self-contained, validator-conformant
`contract-declaration` instance (see
[`../../core/contract-declaration-kind.toml`](../../core/contract-declaration-kind.toml)
for the kind shape and
[`../../../validators/validate_review_readiness.py`](../../../validators/validate_review_readiness.py)
for the required `[[contracts]]` row shape).

## The ladder

```
solo  ⊂  team  ⊂  group  ⊂  organization  ⊂  enterprise
```

Each tier's contract set is a strict superset of the prior tier's
intent. Inheritance is NOT a schema feature — each tier file lists
the complete contract set effective at that tier. A RUNTIME-SPEC
implementation MAY compute parent ⊆ child set differences for
display purposes, but the SPEC layer validates each tier file
independently.

| Tier | Primary user | Headline shift from prior tier |
|---|---|---|
| `solo` | One developer | Baseline. Self-sign overrides; any runtime kind; local log. Self-modification gate-decisions are subject to gate-decision INV06 regardless of tier (different-provider AND different-model-family decider required); see `solo.toml` C02 / C05. |
| `team` | 2–10 devs, one repo | Peer-sign overrides; AI self-sign capped at low severity; team log mirror; replay at gate time. |
| `group` | Multiple teams | Role-scoped overrides; AI capped at low+counter-sign; no `os-sandbox`; nightly replay; org log; M-of-N at severity ≥ medium. |
| `organization` | Formal org | RBAC + ABAC; AI restricted to tagged adapters; signed image digests required; external witness; 2-of-5 default; 7y retention; downgrade cooling-off. |
| `enterprise` | Regulated / multi-tenant | M-of-N + AIBAC; AI never sole signer; HSM-backed roots; multi-witness; 3-of-7 default; quarterly third-party replay; downgrade forbidden without external attestation. |

> **Cross-tier rule.** The self-modification cross-provider requirement
> (gate-decision INV06) applies at every tier. It is not part of the
> ladder's tier-by-tier shift; it is a profile-level posture rooted in
> the multi-provider scope described in `../overview.md` "Scope and
> posture". Deployments that cannot reach a second provider for
> self-modification gates cannot achieve full assurance under this
> profile for those specific gates, regardless of which tier they
> adopt.

## How a project selects a tier

A project document references a tier by adding the relevant tier
file's `review_subject` slug (e.g., `"deployment-tier-group"`) into
its existing `[[contracts]].applies_to` entries, or by citing the
tier file from its review-readiness evidence. The SPEC layer does
not currently define a single `[meta].deployment_tier` field; tier
adoption is a convention recorded through existing reference
patterns. RUNTIME-SPEC implementations MAY add such a field.

## Why no schema-level inheritance

`contract-declaration` enforces `depends_on` / `supersedes` /
`related_to` references against `contracts[*].id` values within the
same document (see
[`../../core/contract-declaration-kind.toml`](../../core/contract-declaration-kind.toml)
hard invariant `INV01`). Cross-document inheritance is not part of
the kind's schema. Rather than invent a new mechanism, each tier
file ships its own complete contract set; the ladder is documented
here in prose and recomputed by consumers as needed.

## Files

- [`solo.toml`](solo.toml)
- [`team.toml`](team.toml)
- [`group.toml`](group.toml)
- [`organization.toml`](organization.toml)
- [`enterprise.toml`](enterprise.toml)

Every `[[contracts]].verified_by` entry in these files names an
adapter contract (e.g., `"adapter-contract:authority-check@1"`).
Those adapters are RUNTIME-SPEC artifacts; the SPEC layer treats
the `verified_by` strings as free-form labels per
[`../../core/contract-declaration-kind.toml`](../../core/contract-declaration-kind.toml)
lines 52-56.
