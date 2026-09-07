#!/usr/bin/env python3
"""Empirical parity sweep: do rs, go and py agree on accept/reject?

`enforced_by_primaries` in the kind descriptors is under-declared, so
declarations cannot be trusted as the audit key. This measures behaviour:
every fixture is run through the Rust primary, the Go primary, and the
matching Python reference validator, and any accept/reject disagreement is
reported.

The primary mode is selected for each kind so this compares matching
kind-layer checks. The separate runtime instrument also tests auto dispatch.
"""
import pathlib
import subprocess
import sys
import argparse

REPO = pathlib.Path(__file__).resolve().parents[1]
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
    "adapter-contract": "adapter-contract",
    "adapter-registry-binding": "adapter-registry-binding",
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
    "adapter-contract": ["validators/validate_adapter_contract.py", "--repo-root", "."],
    "adapter-registry-binding": ["validators/validate_adapter_registry_binding.py", "--repo-root", "."],
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
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, timeout=120)  # nosec B603 # noqa: S603
    if p.returncode not in {0, 1}:
        raise RuntimeError("parity subject failed to execute its checks: " + p.stdout + p.stderr)
    return p.returncode == 1


def main() -> int:
    global REPO, RS, GO
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=pathlib.Path, nargs="?", help="legacy positional repository root")
    parser.add_argument("--repo-root", type=pathlib.Path)
    parser.add_argument("--rs", type=pathlib.Path)
    parser.add_argument("--go", type=pathlib.Path)
    args = parser.parse_args()
    if args.repository is not None and args.repo_root is not None:
        parser.error("supply the repository root once")
    REPO = (args.repo_root or args.repository or REPO).resolve()
    RS = (args.rs or REPO / "tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs").resolve()
    GO = (args.go or REPO / "tools/dagtoml-validate-go/dagtoml-validate-go").resolve()
    if not RS.is_file() or not GO.is_file() or not (REPO / "spec.md").is_file():
        parser.error("the source repository and both built primary binaries are required")
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
    no_selector = []
    joint_outcomes = set()
    for t in targets:
        rel = t.relative_to(REPO)
        kind = template_kind(t)
        if kind is None:
            no_selector.append(str(rel))
            continue
        py_cmd = PY_FOR_KIND.get(kind)
        if py_cmd is None:
            no_reference.append((str(rel), kind))
            continue
        checked += 1
        mode = MODE_FOR_KIND[kind]
        r = rejects([str(RS), "--repo-root", ".", "--mode", mode, str(rel)])
        g = rejects([str(GO), "--repo-root", ".", "--mode", mode, str(rel)])
        p = rejects([sys.executable, *py_cmd, str(rel)])
        if not (r == g == p):
            divergences.append((str(rel), kind, r, g, p))
        else:
            joint_outcomes.add(r)

    print(f"fixtures compared: {checked}")
    print(f"divergences:       {len(divergences)}\n")
    if no_selector:
        print("No parseable kind selector (outside this parity comparison): " + ", ".join(no_selector))
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
    if joint_outcomes != {False, True}:
        raise RuntimeError("parity sweep did not observe both accepted and rejected controls")
    return int(bool(divergences) or checked == 0)


if __name__ == "__main__":
    raise SystemExit(main())
