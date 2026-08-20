#!/usr/bin/env python3
"""Empirical parity sweep: do rs, go and py agree on accept/reject?

`enforced_by_primaries` in the kind descriptors is under-declared, so
declarations cannot be trusted as the audit key. This measures behaviour:
every fixture is run through the Rust primary, the Go primary, and the
matching Python reference validator, and any accept/reject disagreement is
reported.

Both primaries are run in `--mode auto` (dispatch by template_kind), which
is how CI's canonical sweep invokes them.
"""
import pathlib
import subprocess
import sys

REPO = pathlib.Path(sys.argv[1]).resolve()
RS = REPO / "tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs"
GO = REPO / "tools/dagtoml-validate-go/dagtoml-validate-go"

# kind -> primary --mode, so the comparison is kind layer against kind layer
# rather than "everything auto does" against one Python validator.
MODE_FOR_KIND = {
    "api-snapshot": "api-snapshot",
    "state-mutation": "mutation-kinds",
    "mutation-claim": "mutation-kinds",
    "implementation-dag": "implementation-dag",
    "traceability": "traceability",
    "readiness-gate": "review-readiness",
    "contract-declaration": "review-readiness",
    "evidence-matrix": "review-readiness",
    "cost-record": "cost-record",
    "rollback-plan": "rollback-plan",
    "gate-decision": "gate-decision",
    "disclosure-attestation": "disclosure",
    "redaction-manifest": "disclosure",
    "selective-disclosure-proof": "disclosure",
    "kind-descriptor": "kind-descriptor",
    "profile-descriptor": "profile",
    "ontology": "ijb",
}

# kind -> reference validator (plus any extra args it needs)
PY_FOR_KIND = {
    "api-snapshot": ["validators/validate_api_snapshot.py", "--repo-root", "."],
    "state-mutation": ["validators/validate_state_mutation.py", "--repo-root", "."],
    "mutation-claim": ["validators/validate_state_mutation.py", "--repo-root", "."],
    "implementation-dag": ["validators/validate_implementation_dag.py"],
    "traceability": ["validators/validate_traceability.py"],
    "readiness-gate": ["validators/validate_review_readiness.py"],
    "contract-declaration": ["validators/validate_review_readiness.py"],
    "evidence-matrix": ["validators/validate_review_readiness.py"],
    "cost-record": ["validators/validate_cost.py", "--repo-root", "."],
    "rollback-plan": ["validators/validate_rollback_plan.py", "--repo-root", "."],
    "gate-decision": ["validators/validate_gate_decision.py", "--repo-root", "."],
    "disclosure-attestation": ["validators/validate_disclosure.py", "--repo-root", "."],
    "redaction-manifest": ["validators/validate_disclosure.py", "--repo-root", "."],
    "selective-disclosure-proof": ["validators/validate_disclosure.py", "--repo-root", "."],
    "kind-descriptor": ["validators/validate_kind_descriptor.py", "--repo-root", "."],
    "profile-descriptor": ["validators/validate_profile_descriptor.py", "--repo-root", "."],
    "ontology": ["validators/validate_ijb_conformance.py"],
}


def template_kind(path: pathlib.Path):
    sys.path.insert(0, str(REPO / "validators"))
    import _toml11 as tomllib

    try:
        doc = tomllib.loads(path.read_text())
    except Exception:
        return None
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        return None
    tk = meta.get("template_kind")
    return tk if isinstance(tk, str) else None


def rejects(cmd) -> bool:
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, timeout=120)
    return p.returncode != 0


def main() -> int:
    targets = []
    for pattern in ("examples/negative/*.toml", "examples/*.toml",
                    "examples/minimal-review-readiness/*.toml",
                    "conformance/cases/*/invalid/*.toml",
                    "conformance/cases/*/valid/*.toml"):
        targets.extend(sorted(REPO.glob(pattern)))
    targets = [t for t in targets if not t.name.endswith(".expected.toml")]

    divergences = []
    no_reference = []
    checked = 0
    for t in targets:
        rel = t.relative_to(REPO)
        kind = template_kind(t)
        if kind is None:
            continue
        py_cmd = PY_FOR_KIND.get(kind)
        if py_cmd is None:
            no_reference.append((str(rel), kind))
            continue
        checked += 1
        mode = MODE_FOR_KIND[kind]
        r = rejects([str(RS), "--repo-root", ".", "--mode", mode, str(rel)])
        g = rejects([str(GO), "--repo-root", ".", "--mode", mode, str(rel)])
        p = rejects(["python3", *py_cmd, str(rel)])
        if not (r == g == p):
            divergences.append((str(rel), kind, r, g, p))

    print(f"fixtures compared: {checked}")
    print(f"divergences:       {len(divergences)}\n")
    if divergences:
        print(f"{'fixture':<62} {'kind':<22} rs go py")
        for rel, kind, r, g, p in divergences:
            print(f"{rel:<62} {kind:<22} {int(r):>2} {int(g):>2} {int(p):>2}")
    if no_reference:
        print("\nno Python reference registered for these kinds (not compared):")
        seen = sorted({k for _, k in no_reference})
        for k in seen:
            n = sum(1 for _, kk in no_reference if kk == k)
            print(f"  {k:<28} {n} fixture(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
