# DAG-TOML Protocol Comparison

DAG-TOML is complementary to agent protocols. It is the evidence and governance artifact, not the transport, identity layer, runtime, or capability manifest.

| Surface | Primary question | DAG-TOML relationship |
| --- | --- | --- |
| MCP | How does a model or agent access tools, resources, and context? | DAG-TOML can capture the plan, evidence, and review state around work performed through tools. |
| A2A | How do independent agents discover one another and delegate tasks? | DAG-TOML can describe task intent, dependencies, provenance, and readiness after delegation. |
| ACP | How do agents communicate through a general-purpose REST-style protocol? | DAG-TOML remains a portable evidence artifact outside the transport channel. |
| ANP | How do agents discover and collaborate across an open network identity layer? | DAG-TOML can bind claims to provenance and closure roots without defining identity itself. |
| Agent Manifest / agent.json / JSON Agents | What is this agent, what can it do, and what boundaries does it declare? | DAG-TOML describes what a particular work package did, depended on, and proved. |

## Summary

MCP connects tools. A2A and ACP connect agents. Agent manifests describe actors. DAG-TOML describes governed work products and their evidence.
